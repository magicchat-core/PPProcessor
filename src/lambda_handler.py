# lambda_handler.py
import json
import os
import requests
import boto3
from functools import wraps
from http import HTTPStatus
from utils import PaymentManager, PlanManager
from datetime import datetime
from decimal import Decimal
from botocore.exceptions import ClientError

print("Loading lambda_handler")

class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return int(obj) if obj % 1 == 0 else float(obj)
        return super().default(obj)

stack_prefix = os.environ.get("StackPrefix", "dev")
dynamodb = boto3.resource('dynamodb')
settings_table = dynamodb.Table(f'{stack_prefix}-GlobalSettings')

class HTTPException(Exception):
    def __init__(self, message, status_code=400):
        super().__init__(message)
        self.status_code = status_code
        self.message = message

def get_me_by_token(func):
    @wraps(func)
    def wrapper(self, token, *args, **kwargs):
        if not token:
            raise HTTPException("Unauthorized!", HTTPStatus.UNAUTHORIZED)

        domain_base = "magicchat.io" if stack_prefix == "prod" else "addchat.tech"
        env_suffix = "prod" if stack_prefix == "prod" else "dev"
        req_url = f"https://auth.{domain_base}/{env_suffix}/me"

        response = requests.get(
            req_url,
            headers={"Accept": "*/*", "Authorization": token}
        )

        if response.status_code != 200:
            raise HTTPException("Authentication failed", HTTPStatus.UNAUTHORIZED)

        kwargs["me"] = response.json()
        return func(self, token, *args, **kwargs)
    return wrapper

class PaymentHandler:
    def __init__(self):
        self.manager = PaymentManager()

    @get_me_by_token
    def get_all_payments(self, token, query, me):
        return self.manager.get_all(me['id'], **query)

    @get_me_by_token
    def get_payment(self, token, query, me):
        payment_id = query.get("payment_id")
        if not payment_id:
            raise HTTPException("Missing payment_id", HTTPStatus.BAD_REQUEST)
        return self.manager.get_by_id(me['id'], payment_id)

    @get_me_by_token
    def add_payment(self, token, body, query, me):
        print("Processing payment")
        action = query.get("action", "order")
        currency = body.get('currency', 'INR')
        
        if action == "order":
            amount = body.get('amount')
            if not amount:
                raise HTTPException("Missing amount", HTTPStatus.BAD_REQUEST)

            razorpay_order = self.manager.create_razorpay_order(amount, currency)
            body['razorpay_order_id'] = razorpay_order['id']
            body['tenant_id'] = me['id']
            body['created_on'] = datetime.utcnow().isoformat()
            body['currency'] = currency
            return self.manager.create(me['id'], body)

        elif action == "payment":
            razorpay_order_id = body.get("razorpay_order_id")
            razorpay_payment_id = body.get("razorpay_payment_id")
            razorpay_signature = body.get("razorpay_signature")

            if not all([razorpay_order_id, razorpay_payment_id, razorpay_signature]):
                raise HTTPException("Missing Razorpay payment details", HTTPStatus.BAD_REQUEST)

            if not self.manager.verify_razorpay_signature(
                razorpay_order_id,
                razorpay_payment_id,
                razorpay_signature
            ):
                raise HTTPException("Invalid payment signature", HTTPStatus.UNAUTHORIZED)

            body['tenant_id'] = me['id']
            body['verified_on'] = datetime.utcnow().isoformat()

            payment = self.manager.create(me['id'], body)

            try:
                plan_manager = PlanManager()
                plan_manager.update_plan(me['id'], "ADVANCE")
            except Exception as e:
                print(f"Plan upgrade failed: {e}")

            return payment

        else:
            raise HTTPException("Invalid action", HTTPStatus.BAD_REQUEST)

    @get_me_by_token
    def update_payment(self, token, body, me):
        payment_id = body.get("payment_id")
        if not payment_id:
            raise HTTPException("Missing payment_id", HTTPStatus.BAD_REQUEST)
        return self.manager.update(me['id'], payment_id, body)

class PlanHandler:
    def __init__(self):
        self.manager = PlanManager()

    @get_me_by_token
    def get_tenant_plan_by_token(self, token, query, me):
        return self.manager.get_plan(me['id'])

    def get_tenant_plan_by_tenant_id(self, query):
        tenant_id = query.get("tenant_id")
        if not tenant_id:
            raise HTTPException("Missing tenant_id", HTTPStatus.BAD_REQUEST)
        return self.manager.get_plan(tenant_id)
  
    def add_tenant_plan(self, body):
        plan = body.get("plan", "BASIC")
        tenant_id = body.get('tenant_id')
        if not tenant_id:
            raise HTTPException("Missing tenant_id", HTTPStatus.BAD_REQUEST)
        return self.manager.add_plan(tenant_id, plan)

    @get_me_by_token
    def update_tenant_plan(self, token, body, me):
        new_plan = body.get("plan")
        if not new_plan:
            raise HTTPException("Missing plan", HTTPStatus.BAD_REQUEST)
        return self.manager.update_plan(me['id'], new_plan)

class SettingsHandler:
    def __init__(self):
        self.table = settings_table

    def get_settings(self, tenant_id):
        try:
            response = self.table.get_item(Key={'tenant_id': tenant_id})
            item = response.get('Item')
            if not item:
                raise HTTPException("Settings not found", HTTPStatus.NOT_FOUND)
            return item.get('settings', {})
        except ClientError as e:
            raise HTTPException(f"DynamoDB error: {e.response['Error']['Message']}", HTTPStatus.INTERNAL_SERVER_ERROR)

    # @get_me_by_token
    def add_settings(self, body):
        tenant_id = body['tenant_id']
        settings = body.get('settings')
        if not settings:
            raise HTTPException("Missing settings", HTTPStatus.BAD_REQUEST)
        
        try:
            self.table.put_item(
                Item={
                    'tenant_id': tenant_id,
                    'settings': settings
                },
                ConditionExpression='attribute_not_exists(tenant_id)'
            )
            return {"message": "Settings added successfully"}
        except ClientError as e:
            if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
                raise HTTPException("Settings already exist for tenant", HTTPStatus.CONFLICT)
            raise HTTPException(f"DynamoDB error: {e.response['Error']['Message']}", HTTPStatus.INTERNAL_SERVER_ERROR)

    @get_me_by_token
    def update_settings(self, token, body, me):
        tenant_id = me['id']
        settings = body.get('settings')
        if not settings:
            raise HTTPException("Missing settings", HTTPStatus.BAD_REQUEST)
        
        try:
            self.table.update_item(
                Key={'tenant_id': tenant_id},
                UpdateExpression="SET settings = :s",
                ExpressionAttributeValues={':s': settings},
                ReturnValues="UPDATED_NEW"
            )
            return {"message": "Settings updated successfully"}
        except ClientError as e:
            raise HTTPException(f"DynamoDB error: {e.response['Error']['Message']}", HTTPStatus.INTERNAL_SERVER_ERROR)

def lambda_function(event, context):
    path = event.get("path", "")
    method = event.get("httpMethod", "GET").upper()
    query = event.get("queryStringParameters") or {}
    body = json.loads(event.get("body") or "{}")
    token = event.get("headers", {}).get("Authorization")

    payment_handler = PaymentHandler()
    plan_handler = PlanHandler()
    settings_handler = SettingsHandler()

    try:
        if path.endswith("/all_payments") and method == "GET":
            response = payment_handler.get_all_payments(token, query)
        elif path.endswith("/get_payment") and method == "GET":
            response = payment_handler.get_payment(token, query)
        elif path.endswith("/add_payment") and method == "POST":
            response = payment_handler.add_payment(token, body, query)
        elif path.endswith("/update_payment") and method == "PUT":
            response = payment_handler.update_payment(token, body)

        elif path.endswith("/get_tenant_plan") and method == "GET":
            if token:
                response = plan_handler.get_tenant_plan_by_token(token, query)
            else:
                response = plan_handler.get_tenant_plan_by_tenant_id(query)

        elif path.endswith("/add_tenant_plan") and method == "POST":
            response = plan_handler.add_tenant_plan(body)
        elif path.endswith("/update_tenant_plan") and method == "PUT":
            response = plan_handler.update_tenant_plan(token, body)

        elif path.endswith('/get_global_settings') and method == 'GET':
            tenant_id = query.get('tenant_id')
            if not tenant_id:
                raise HTTPException("Missing tenant_id", HTTPStatus.BAD_REQUEST)
            response = settings_handler.get_settings(tenant_id)

        elif path.endswith('/add_global_settings') and method == 'POST':
            response = settings_handler.add_settings(body)

        elif path.endswith('/update_global_settings') and method == 'PUT':
            response = settings_handler.update_settings(token, body)
        else:
            raise HTTPException("Not Found", HTTPStatus.NOT_FOUND)

        return {
            "statusCode": HTTPStatus.OK,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'OPTIONS,POST,GET,PUT',
                'Access-Control-Allow-Headers': 'Content-Type,Authorization,X-API-Key',
                'Access-Control-Allow-Credentials': 'true'
            },
            "body": json.dumps({"success": True, "data": response}, cls=DecimalEncoder)
        }

    except HTTPException as e:
        return {
            "statusCode": e.status_code,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            "body": json.dumps({"success": False, "message": e.message})
        }
    except Exception as e:
        print(f"Unhandled exception: {str(e)}")
        return {
            "statusCode": HTTPStatus.INTERNAL_SERVER_ERROR,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            "body": json.dumps({"success": False, "message": "Internal Server Error"})
        }