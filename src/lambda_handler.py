import json
import os
import requests
from functools import wraps
from http import HTTPStatus
from utils import get_all_payments, get_payment_by_id, add_payment, update_payment, get_tenant_plan
from datetime import datetime
from decimal import Decimal


class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            if obj % 1 == 0:
                return int(obj)
            else:
                return float(obj)
        return super().default(obj)


# Environment setup
stack_prefix = os.environ.get("STACK_PREFIX", "dev")


# Custom HTTP Exception
class HTTPException(Exception):
    def __init__(self, message, status_code=400):
        super().__init__(message)
        self.status_code = status_code
        self.message = message


# Decorator for auth
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

        headersList = {
            "Accept": "*/*",
            "Authorization": token 
        }

        response = requests.get(req_url, headers=headersList)
        print("Auth response:", response, response.status_code, req_url)
        if response.status_code != 200:
            raise HTTPException("Authentication failed", HTTPStatus.UNAUTHORIZED)

        me = response.json()
        kwargs["me"] = me
        return func(self, token, *args, **kwargs)

    return wrapper


# Payment handler class
class PaymentHandler:

    @get_me_by_token
    def get_all_payments(self, token, query, me):
        return get_all_payments(me['id'], **query)

    @get_me_by_token
    def get_payment(self, token, query, me):
        payment_id = query.get("payment_id")
        if not payment_id:
            raise HTTPException("Missing payment_id in query", HTTPStatus.BAD_REQUEST)
        return get_payment_by_id(me['id'], payment_id)

    @get_me_by_token
    def add_payment(self, token, body, me):
        body['tenant_id'] = me['id']
        body['created_on'] = datetime.utcnow().isoformat()  # Add creation timestamp
        return add_payment(me['id'], body)

    @get_me_by_token
    def update_payment(self, token, body, me):
        payment_id = body.get("payment_id")
        if not payment_id:
            raise HTTPException("Missing payment_id in body", HTTPStatus.BAD_REQUEST)
        # update_payment already adds updated_on internally, so optional here
        return update_payment(me['id'], payment_id, body)


# Lambda entrypoint
def lambda_function(event, context):
    print("Received event:", json.dumps(event))

    path = event.get("path", "")
    method = event.get("httpMethod", "GET").upper()
    query = event.get("queryStringParameters") or {}
    body = json.loads(event.get("body") or "{}")
    token = event.get("headers", {}).get("Authorization")

    handler = PaymentHandler()

    try:
        if path.endswith(f"/all_payments") and method == "GET":
            response = handler.get_all_payments(token, query)
        elif path.endswith(f"/get_payment") and method == "GET":
            response = handler.get_payment(token, query)
        elif path.endswith(f"/add_payment") and method == "POST":
            response = handler.add_payment(token, body)
        elif path.endswith(f"/update_payment") and method == "PUT":
            response = handler.update_payment(token, body)

        elif path.endswith("/get_tenant_plan") and method == "GET":
            tenant_id = query.get("tenant_id")
            if not tenant_id:
                raise HTTPException("Missing tenant_id", HTTPStatus.BAD_REQUEST)
            plan = get_tenant_plan(tenant_id)
            return {
                "statusCode": HTTPStatus.OK,
                "body": json.dumps({"success": True, "plan": plan}, cls=DecimalEncoder)
            }
        else:
            raise HTTPException("Invalid path or method", HTTPStatus.NOT_FOUND)

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
        print("Unexpected error:", str(e))
        return {
            "statusCode": 500,
            "body": json.dumps({"success": False, "message": "Internal Server Error"})
        }
