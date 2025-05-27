import os
import boto3
import uuid
from boto3.dynamodb.conditions import Key
from datetime import datetime

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table("dev-Payments")  # adjust table name if needed

stack_prefix = os.environ.get("StackPrefix", "dev")

# New function to get tenant plan
def get_tenant_plan(tenant_id):
    tenant_plans_table = dynamodb.Table(f"{stack_prefix}-TenantPlans")
    response = tenant_plans_table.get_item(Key={'tenant_id': tenant_id})
    return response.get('Item', {}).get('plan', 'BASIC')



def get_all_payments(tenant_id, **query):
    try:
        # Query on tenant_id as partition key
        response = table.query(
            KeyConditionExpression=Key('tenant_id').eq(tenant_id)
        )
        return response.get("Items", [])
    except Exception as e:
        print("Error in get_all_payments:", e)
        raise


def get_payment_by_id(tenant_id, payment_id):
    try:
        # DynamoDB primary key assumed: tenant_id + created_on
        # You don't have created_on, so use GSI query by payment_id to get the item
        response = table.query(
            IndexName='PaymentIdIndex',  # Your GSI on payment_id
            KeyConditionExpression=Key('payment_id').eq(payment_id)
        )
        items = response.get("Items", [])
        # Ensure that tenant_id matches too (for security)
        for item in items:
            if item.get('tenant_id') == tenant_id:
                return item

        return None

    except Exception as e:
        print("Error in get_payment_by_id:", e)
        raise


def add_payment(tenant_id, payment_data):
    try:
        payment_id = str(uuid.uuid4())
        item = {
            "tenant_id": tenant_id,
            "payment_id": payment_id,
            **payment_data
        }
        table.put_item(Item=item)
        return item
    except Exception as e:
        print("Error in add_payment:", e)
        raise


def update_payment(tenant_id, payment_id, payment_data):
    try:
        # Query item by payment_id GSI
        response = table.query(
            IndexName='PaymentIdIndex',
            KeyConditionExpression=Key('payment_id').eq(payment_id)
        )
        items = response.get('Items', [])
        if not items:
            raise Exception("Payment not found")

        # Verify tenant_id matches
        item = None
        for i in items:
            if i.get('tenant_id') == tenant_id:
                item = i
                break

        if item is None:
            raise Exception("Payment not found or access denied")

        created_on = item['created_on']

        # Prepare update expressions
        update_expr = []
        expr_attrs = {}
        expr_attr_names = {}

        # Set updated_on timestamp
        payment_data["updated_on"] = datetime.utcnow().isoformat()

        for key, value in payment_data.items():
            if key in ["tenant_id", "created_on", "payment_id"]:
                continue
            if key == "status":
                expr_attr_names[f"#{key}"] = key
                placeholder = f"#{key}"
            else:
                placeholder = key

            value_placeholder = f":{key}"
            update_expr.append(f"{placeholder} = {value_placeholder}")
            expr_attrs[value_placeholder] = value

        update_expression = "SET " + ", ".join(update_expr)

        table.update_item(
            Key={
                "tenant_id": tenant_id,
                "created_on": created_on
            },
            UpdateExpression=update_expression,
            ExpressionAttributeNames=expr_attr_names if expr_attr_names else None,
            ExpressionAttributeValues=expr_attrs
        )

        # Return updated item
        updated_item = table.get_item(
            Key={
                "tenant_id": tenant_id,
                "created_on": created_on
            }
        ).get('Item')

        return updated_item

    except Exception as e:
        print("Error in update_payment:", e)
        raise
