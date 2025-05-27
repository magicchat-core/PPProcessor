# utils.py
import os
import boto3
import uuid
from boto3.dynamodb.conditions import Key
from datetime import datetime
from decimal import Decimal

dynamodb = boto3.resource("dynamodb")
stack_prefix = os.environ.get("STACK_PREFIX", "dev")


class PaymentManager:
    def __init__(self):
        self.table = dynamodb.Table(f"{stack_prefix}-Payments")

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
        update_expr = "SET " + ", ".join(
            f"{k}=:{k}" for k in data if k not in ['tenant_id', 'payment_id']
        )
        
        self.table.update_item(
            Key={'tenant_id': tenant_id, 'created_on': item['created_on']},
            UpdateExpression=update_expr,
            ExpressionAttributeValues={
                f":{k}": v for k, v in data.items() 
                if k not in ['tenant_id', 'payment_id']
            }
        )
        return self.get_by_id(tenant_id, payment_id)


class PlanManager:
    def __init__(self):
        self.table = dynamodb.Table(f"{stack_prefix}-TenantPlans")

    def get_plan(self, tenant_id):
        response = self.table.get_item(Key={'tenant_id': tenant_id})
        return response.get('Item', {}).get('plan', 'BASIC')

    def update_plan(self, tenant_id, new_plan):
        self.table.update_item(
            Key={'tenant_id': tenant_id},
            UpdateExpression="SET plan = :plan",
            ExpressionAttributeValues={':plan': new_plan}
        )
        return self.get_plan(tenant_id)