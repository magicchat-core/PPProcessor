# utils.py
import hmac
import hashlib

import razorpay
import os
import boto3
import uuid
from boto3.dynamodb.conditions import Key
from datetime import datetime
from decimal import Decimal

dynamodb = boto3.resource("dynamodb")
stack_prefix = os.environ.get("StackPrefix", "dev")

RazApiKey = os.environ.get("RazApiKey")
RazSecr = os.environ.get("RazSecr")



# Razorpay credentials from environment
razorpay_client = razorpay.Client(
    auth=(
        RazApiKey,
        RazSecr
    )
)


class PaymentManager:
    def __init__(self):
        self.table = dynamodb.Table(f"{stack_prefix}-Payments")

    def verify_razorpay_signature(self, order_id, payment_id, signature):
        payload = f"{order_id}|{payment_id}".encode("utf-8")
        secret = "I6iGphtRi3o8M333rdJ3SBp1"
        generated_signature = hmac.new(
            secret.encode("utf-8"),
            payload,
            hashlib.sha256
        ).hexdigest()
        return hmac.compare_digest(generated_signature, signature)

    def create_razorpay_order(self, amount, currency="INR"):
        # Razorpay expects amount in paise
        print("make rzorapya mapyasd")
        order = razorpay_client.order.create({
            "amount": int(float(amount) * 100),
            "currency": currency,
            "payment_capture": 1
        })
        print("make rzorapya done", order)

        return order

    def get_all(self, tenant_id, **kwargs):
        return self.table.query(
            KeyConditionExpression=Key('tenant_id').eq(tenant_id)
        )['Items']

    def get_by_id(self, tenant_id, payment_id):
        items = self.table.query(
            IndexName='PaymentIdIndex',
            KeyConditionExpression=Key('payment_id').eq(payment_id)
        )['Items']
        return next((i for i in items if i['tenant_id'] == tenant_id), None)

    def create(self, tenant_id, data):
        item = {
            'tenant_id': tenant_id,
            'payment_id': str(uuid.uuid4()),
            'created_on': datetime.utcnow().isoformat(),
            **data
        }
        self.table.put_item(Item=item)
        return item

    def update(self, tenant_id, payment_id, data):
        item = self.get_by_id(tenant_id, payment_id)
        if not item:
            raise ValueError("Payment not found")

        data['updated_on'] = datetime.utcnow().isoformat()

        # Prepare UpdateExpression, ExpressionAttributeValues, and ExpressionAttributeNames
        update_clauses = []
        expr_values = {}
        expr_names = {}

        for k, v in data.items():
            if k in ['tenant_id', 'payment_id']:
                continue
            placeholder = f":{k}"
            attr_name = f"#{k}" if k.lower() in ['plan'] else k
            update_clauses.append(f"{attr_name} = {placeholder}")
            expr_values[placeholder] = v
            if attr_name.startswith('#'):
                expr_names[attr_name] = k

        update_expr = "SET " + ", ".join(update_clauses)

        kwargs = {
            "Key": {'tenant_id': tenant_id, 'created_on': item['created_on']},
            "UpdateExpression": update_expr,
            "ExpressionAttributeValues": expr_values
        }

        if expr_names:
            kwargs["ExpressionAttributeNames"] = expr_names

        self.table.update_item(**kwargs)

        return self.get_by_id(tenant_id, payment_id)


class PlanManager:
    def __init__(self):
        self.table = dynamodb.Table(f"{stack_prefix}-TenantPlans")

    def get_plan(self, tenant_id):
        response = self.table.get_item(Key={'tenant_id': tenant_id})
        return response.get('Item', {}).get('plan')

    def add_plan(self, tenant_id, plan, mau_limit=100):
        print("arrrrr v here?", str(tenant_id), plan)
        res = self.table.put_item(Item={
            'tenant_id': str(tenant_id),
            'plan': plan,
            'mau_limit': mau_limit,
            'created_on': datetime.utcnow().isoformat()
        })
        print("done", res)
        return res

    def update_plan(self, tenant_id, new_plan):
        response = self.table.update_item(
            Key={'tenant_id': tenant_id},
            UpdateExpression="SET #p = :val1",
            ExpressionAttributeNames={'#p': 'plan'},
            ExpressionAttributeValues={':val1': new_plan},
            ReturnValues="UPDATED_NEW"
        )
        return response
