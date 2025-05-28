import razorpay


# lambda_handler.py
import json
import os
import requests
from functools import wraps
from http import HTTPStatus
from utils import PaymentManager, PlanManager
from datetime import datetime
from decimal import Decimal


class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return int(obj) if obj % 1 == 0 else float(obj)
        return super().default(obj)


# Environment setup
stack_prefix = os.environ.get("STACK_PREFIX", "dev")


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

        req_url = (
            "https://auth.magichat.io/prod/me"
            if stack_prefix == "prod"
            else "https://auth.addchat.tech/dev/me"
        )

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
    def add_payment(self, token, body, me):
        body['tenant_id'] = me['id']
        body['created_on'] = datetime.utcnow().isoformat()
        return self.manager.create(me['id'], body)

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
    def get_tenant_plan(self, token, query, me):
        return self.manager.get_plan(me['id'])


def lambda_function(event, context):
    path = event.get("path", "")
    method = event.get("httpMethod", "GET").upper()
    query = event.get("queryStringParameters") or {}
    body = json.loads(event.get("body") or "{}")
    token = event.get("headers", {}).get("Authorization")

    payment_handler = PaymentHandler()
    plan_handler = PlanHandler()

    try:
        if path.endswith("/all_payments") and method == "GET":
            response = payment_handler.get_all_payments(token, query)
        elif path.endswith("/get_payment") and method == "GET":
            response = payment_handler.get_payment(token, query)
        elif path.endswith("/add_payment") and method == "POST":
            response = payment_handler.add_payment(token, body)
        elif path.endswith("/update_payment") and method == "PUT":
            response = payment_handler.update_payment(token, body)
        elif path.endswith("/get_tenant_plan") and method == "GET":
            response = plan_handler.get_tenant_plan(token, query)
        else:
            raise HTTPException("Not Found", HTTPStatus.NOT_FOUND)

        return {
            "statusCode": HTTPStatus.OK,
            "body": json.dumps({"success": True, "data": response}, cls=DecimalEncoder)
        }

    except HTTPException as e:
        return {
            "statusCode": e.status_code,
            "body": json.dumps({"success": False, "message": e.message})
        }
    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps({"success": False, "message": "Internal Error"})
        }