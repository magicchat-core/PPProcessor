import os
import socketio
import boto3
import json
import requests
from functools import wraps
from boto3.dynamodb.conditions import Key, Attr
from common import HTTPException
from decimal import Decimal

stack_prefix = os.environ.get('StackPrefix')
dynamodb = boto3.resource('dynamodb')

class LiveStatusManager:
    def __init__(self):
        self.table = dynamodb.Table(f"{stack_prefix}-PPProcessorData")

    def add_ls(self, request_body):
        version = request_body.get('version', "Unknown")
        user_data = request_body['user_data']
        tenant = request_body['tenant']
        app_name = request_body.get('app_name', "Unknown")

        if version in ["Unknown", "V1"]:
            user_id = user_data['id']
        else:
            user_id = user_data['uid']

        sort_key = f"{tenant}#{version}#{app_name}#{user_id}"

        item = {
            'tenant': tenant,
            'sort_key': sort_key,
            'app_name': app_name,
            'version': version,
            'user_data': user_data,
            'is_online': False
        }
        self.table.put_item(Item=item)
        return item

    def query_dynamodb_for_app(self, **kwargs):
        # Query DynamoDB based on kwargs - simplified example

        response = {}
        tenant_name = kwargs.get('tenant_name')
        app_type = kwargs.get('app_type', None)
        user_id = kwargs.get('user_id')
        version = kwargs.get('version')
        app_name = kwargs.get('app_name')

        print(app_name,"kwkwargssfdsadfargssfdsadf",kwargs,type(kwargs))

        u_type = kwargs.get('u_type', "user_type")
        uid_key = kwargs.get('uid_key')

        if u_type == "tenant_type":


             # Non user_type query
            print("dowe have userid",user_id)

            if user_id and not version:
                sort_key = f"{tenant_name}#Unknown#Unknown#{user_id}"
             
                response = self.table.query(
                    KeyConditionExpression=Key('tenant').eq(tenant_name) & Key('sort_key').eq(sort_key)
                )


            elif user_id and version and app_name:
                # djangoboy#V1#v1app1#12
                sort_key = f"{tenant_name}#{version}#{app_name}#{user_id}"
                print("is it an y differe",sort_key)
                response = self.table.query(
                    KeyConditionExpression=Key('tenant').eq(tenant_name) & Key('sort_key').eq(sort_key)
                )
            else:
                # to LIST OUT MULTIPLE ITEMS'S LIVE STATUS AT ONCE AS NEEDED IN ADMIN
                sort_key = f"{tenant_name}#{version}#{app_name}#"

                print(sort_key,"here is the tenant_name",tenant_name,app_name)
                response = self.table.query(
                    # KeyConditionExpression=Key('tenant').eq(tenant_name)
                     KeyConditionExpression=Key('tenant').eq(tenant_name) & Key('sort_key').begins_with(sort_key)
                )
                print("here wiatha is ther espose?",response)


        else:
            print(kwargs,uid_key,"uid_keydowe have useridsdsdffsfsd",app_type)
            # Example of filter expression
            filter_expression = Attr('app_name').eq(app_name) if app_name else Attr('app_name').ne("Unknown")
            if app_type == "P2A" and user_id:
                print(uid_key,"sdfsduser_idfsafdsdf",user_id)
                # filter_expression = filter_expression & Attr(f"user_data.{uid_key}").eq(user_id)
            
                sort_key = f"{tenant_name}#Unknown#Unknown#{user_id}"


                print("CANWE SEE SORT KEYES?",sort_key)
                response = self.table.query(
                    KeyConditionExpression=Key('tenant').eq(tenant_name) & Key('sort_key').eq(sort_key)
                )

            
            # elif app_type == "P2A" and user_id:
            #     # djangoboy#V1#myp2p1#3
            #     sort_key = f"{tenant_name}#{version}#{app_name}#{user_id}"
            #     print("sort ekye",sort_key)

            #     response = self.table.query(
            #         KeyConditionExpression=Key('tenant').eq(tenant_name) & Key('sort_key').eq(sort_key)
            #     )
            #     print("how come response has no items?",response)

            
            elif app_type == "P2P" and user_id:
                # djangoboy#V1#myp2p1#3
                sort_key = f"{tenant_name}#{version}#{app_name}#{user_id}"
                print("sort ekye",sort_key)

                response = self.table.query(
                    KeyConditionExpression=Key('tenant').eq(tenant_name) & Key('sort_key').eq(sort_key)
                )
                print("how come response has no itemsDSF?",response)


        items = response.get('Items', [])
        if not items:
            raise HTTPException("No matching items found", 404)

        # Convert Decimals to int (simplified)
        def convert_decimals(item):
            for k, v in item.items():
                if isinstance(v, Decimal):
                    item[k] = int(v)
            return item

        return [convert_decimals(item) for item in items]


class UserService:
    def __init__(self):
        self.table = dynamodb.Table(f"{stack_prefix}-PPProcessorData")
        self.auth_endpoint = "https://auth.magichat.io/prod/me" if stack_prefix == "prod" else "https://auth.addchat.tech/dev/me"

    # Fix decorator to accept self properly and work on instance methods
    
    def get_me_by_token(func):
        @wraps(func)
        def wrapper(self, token, *args, **kwargs):
            if not token:
                raise HTTPException("Unauthorized", 401)

            # Make /me call with token
            reqUrl = "https://auth.magichat.io/prod/me" if stack_prefix == "prod" else "https://auth.addchat.tech/dev/me"
            headersList = {
                "Accept": "*/*",
                "User-Agent": "Thunder Client (https://www.thunderclient.com)",
                "Authorization": token 
            }

            response1 = requests.get(reqUrl, headers=headersList)
            if response1.status_code != 200:
                raise HTTPException("Authentication failed", 401)
            me = response1.json()

            kwargs['me'] = me
            return func(self, token, *args, **kwargs)

        return wrapper



    @get_me_by_token
    def get_ls_by_token(self, token, extra, me):
        print(extra,"ssddfdowe i have me??",me['id'])

        result = ls_manager.query_dynamodb_for_app(
            u_type=extra.get("type", "user_type"),
            tenant_name=extra.get("tenant_name"),
            version=extra.get("version"),
            app_name=extra.get("app_name"),
            user_id=extra.get("user_id"),
            uid_key=extra.get("uid_key","id"),
            app_type=extra.get("app_type", "P2A")
        )
        
        return result



    def get_ls_by_api_key(self, api_key, extra):
        print("ssddfdowe i have mesafsafsa??",api_key, extra)

        result = ls_manager.query_dynamodb_for_app(
            u_type=extra.get("type", "user_type"),
            tenant_name=extra.get("tenant_name"),
            version=extra.get("version"),
            app_name=extra.get("app_name"),
            user_id=extra.get("user_id"),
            uid_key=extra.get("uid_key","id"),
            app_type=extra.get("app_type", None)
        )
        print("here is the result", result)
        # result1 = []
        return result




    @get_me_by_token
    def update_ls_with_token(self, token, extra, me):

        def get_online_users_by_key(key):
            response = self.table.query(
                KeyConditionExpression=Key('tenant').eq(me['tenant']),
                FilterExpression=Attr('is_online').eq(True),
                ProjectionExpression=f"user_data.{key}"
            )
            return [item for item in response.get("Items", []) if item]

        def emit_to_users(users, key, is_uid=False):
            for user in users:
                user_data = user.get('user_data', {})
                user_id = user_data.get(key) or user_data.get('id')
                if not user_id or user_id == me['id']:
                    continue

                payload = {
                    "frm_user": {"id": me['id']} if not is_uid else me['id'],
                    "room": f"global_for__{user_id}",
                    "status": is_online
                }

                print("Emitting payload:", payload)
                sio.emit("ON_USER_LIVE_STATUS", payload)



        print(extra,"dowe i have me??",me)
        version = extra['request_body'].get('version', "V1")
        is_online = extra['request_body']['is_online']
        soc_server_ip = extra['request_body'].get("soc_server_ip", "dev.addchat.tech").replace("http://", "").replace("https://", "").replace("ws://", "").replace("wss://", "").split('/')[0]

        print(type(extra['request_body']), extra['request_body'], "howabout heresoc_server_ip?",soc_server_ip)
        if me['type'] == "tenant_type":
            sort_key = f"{me['tenant']}#Unknown#Unknown#{me['id']}"
        elif version == "V1":
            sort_key = f"{me['tenant']}#{version}#{me.get('app_name', 'Unknown')}#{me['id']}"
        else:
            sort_key = f"{me['tenant']}#{version}#{me.get('app_name', 'Unknown')}#{me['uid']}"

        print("here is the sort key",sort_key)
        
        response = self.table.update_item(
            Key={'tenant': me['tenant'], 'sort_key': sort_key},
            UpdateExpression="SET is_online = :online",
            ExpressionAttributeValues={':online': is_online},
            ReturnValues="UPDATED_NEW"
        )

        print("DynamoDB update succeeded!!:", response)


        if extra.get("skip_ls_sending"):
            return


        print("Connecting to socket server at:", soc_server_ip)
        sio = socketio.Client()
        sio.connect(f"ws://{soc_server_ip}")

        # Emit to users with `id`
        id_users = get_online_users_by_key("id")
        print("Online users (by id):", id_users)
        emit_to_users(id_users, "id")

        # Emit to users with `uid`
        uid_users = get_online_users_by_key("uid")
        print("Online users (by uid):", uid_users)
        emit_to_users(uid_users, "uid", is_uid=True)

        sio.disconnect()

        print("returning success!",extra,type(extra))
        return {"status": "success"}


    def update_ls_with_x_api_key(self, extra, soc_server_ip):
        """
        Updates the user's live status in DynamoDB and sends a socket event.

        Args:
            extra (dict): User metadata including tenant, user ID, app details, etc.
            soc_server_ip (str): IP or hostname of the socket server.

        Returns:
            dict: Result of the operation.
        """
        try:
            print(soc_server_ip, "Incomingsdf socket server IP")
            print("Extra payload:", extra)

            # Extract tenant info
            tenant_info = extra.get('tenant_info', {})
            # tenant_id = tenant_info.get('id')

            # Initialize DynamoDB table
            dynamodb = boto3.resource('dynamodb')
            table = dynamodb.Table(stack_prefix + '-PPProcessorData')

            # Extract required fields
            version = extra.get('version')
            email = extra.get('email')
            user_id = extra.get('user_id',None)
            app_name = extra.get('app_name')
            tenant = extra.get('tenant')
            apptyp = extra.get('apptyp')
            is_online = extra.get('is_online')
            frm_user = extra.get('frm_user')
            app_type = extra.get('app_type')
            tenant_id = extra.get('tenant_id')

            sort_key = f"{tenant}#{version}#{app_name}#{user_id}"
            print(user_id,"Constructed sort_key:", extra)

            # Update user's online status in DynamoDB
            response = table.update_item(
                Key={
                    'tenant': tenant,
                    'sort_key': sort_key
                },
                UpdateExpression="set is_online = :online",
                ExpressionAttributeValues={
                    ':online': is_online
                },
                ReturnValues="UPDATED_NEW"
            )
            print(extra,"DynamoDB update succeeded:", response)
            inform_to_ids =[]
            if app_type == 'P2P':

                # Emit socket event to server
                sio = socketio.Client()

                print("soc_server_ipSDFsdfsdfssadfd",soc_server_ip)
                # sio.connect(f"{soc_server_ip}")
                sio.connect(f"ws://{soc_server_ip}")

                begin_sort_key = f"{tenant}#{version}#{app_name}#"
                response333 = self.table.query(
                    KeyConditionExpression=Key('tenant').eq(tenant) & Key('sort_key').begins_with(begin_sort_key)
                )

                print(response333,"INFORM THESE ONES",begin_sort_key)


                inform_to_ids = [user for user in response333.get('Items', [])]

            elif app_type == 'P2A':
                                # Emit socket event to server
                sio = socketio.Client()

                print(extra,"does it have tenant_idsoc_server_ipSDFsdfsdfssadfd",soc_server_ip)
                # sio.connect(f"{soc_server_ip}")
                sio.connect(f"ws://{soc_server_ip}")

                tenant_sort_key = f"{tenant}#Unknown#Unknown#{tenant_id}"
                response333 = self.table.query(
                    KeyConditionExpression=Key('tenant').eq(tenant) & Key('sort_key').eq(tenant_sort_key)
                )

                print(response333,"INFORM THESE ONES",tenant_sort_key)


                inform_to_ids = [user for user in response333.get('Items', [])]
            
            
            for user in inform_to_ids:
                user_id = user.get('user_data', {}).get('id')
                print("wjrowsdfer")

                if user_id:
                    emit_payload = {
                        'room': f"global_for__{user_id}",
                        "status": is_online,
                        "frm_user":frm_user
                    }
                    print("emit_pasdfylDSFoad", emit_payload)
                    # sio.emit('ON_USER_LIVE_STATUS', emit_payload)
                    if sio.connected:
                        sio.emit('ON_USER_LIVE_STATUS', emit_payload)
                    else:
                        print("Socket not connected, skipping emit for", user_id)


            # LET'S GRAB ALL THE USERS OF AN APP SPECIALLY WHEN IT'S P2P
                                #  KeyConditionExpression=Key('tenant').eq(tenant_name) & Key('sort_key').begins_with(sort_key)

            

            return {"success": True}

        except Exception as e:
            print("Error updating item:", str(e))
            return {
                'statusCode': 500,
                'body': json.dumps({
                    'message': 'Failed to update the item',
                    'error': str(e)
                })
            }


# Instantiate services for import usage
user_service = UserService()
ls_manager = LiveStatusManager()

update_ls_with_x_api_key= user_service.update_ls_with_x_api_key
update_ls_with_token = user_service.update_ls_with_token
add_ls = ls_manager.add_ls
query_dynamodb_for_app = ls_manager.query_dynamodb_for_app
get_ls_by_token = user_service.get_ls_by_token
get_ls_by_api_key = user_service.get_ls_by_api_key