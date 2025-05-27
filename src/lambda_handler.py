import os
import json
from common import HTTPException, standard_response, parse_body
from users import update_ls_with_token, add_ls, query_dynamodb_for_app, get_ls_by_api_key, update_ls_with_x_api_key, get_ls_by_token

stack_prefix = os.environ.get('StackPrefix')

def lambda_function(event, context):
    try:
        path = event.get("path", "")
        if path == f"/{stack_prefix}/fetch_all_ls_of_connected_users":
            return standard_response(501, {"error": "Not Implemented"})

        elif path == f"/{stack_prefix}/get_app":
            query_params = event.get("queryStringParameters", {}) or {}
            token = event.get('headers', {}).get('Authorization')
            x_api_key = event.get('headers', {}).get('x-api-key')
            print("here is tokx_api_keyen",token,x_api_key)

            if token:
                print("where way arer1")
                result = get_ls_by_token(token, query_params)
            elif x_api_key:
                print("where way arer2")
                result = get_ls_by_api_key(x_api_key, query_params)

    
    
            # result = query_dynamodb_for_app(
            #     u_type=query_params.get("type", "user_type"),
            #     tenant_name=query_params.get("tenant_name"),
            #     version=query_params.get("version"),
            #     app_name=query_params.get("app_name"),
            #     user_id=query_params.get("user_id"),
            #     uid_key=query_params.get("uid_key","id"),
            #     app_type=query_params.get("app_type", "P2A")
            # )

            # result = {"anmy":"thing"}
            return standard_response(200, result)

        elif path == f"/{stack_prefix}/add_ls_user":
            body = parse_body(event)
            result = add_ls(body)
            return standard_response(200, result)

        elif path == f"/{stack_prefix}/update_ls_user":
            token = event.get('headers', {}).get('Authorization')
            body = parse_body(event)

            skip_ls_sending = False

            if token:
                print("wehrwersdftoken",token)

                if event.get('queryStringParameters'):
                    skip_ls_sending = event['queryStringParameters'].get('skip_ls_sending', False)
                    
                    

                soc_server_ip = body.get('soc_server_ip', "dev.addchat.tech")

                extra = {
                    "request_body": body,
                    "skip_ls_sending": skip_ls_sending,
                    "soc_server_ip": soc_server_ip,
                    **body  # flatten relevant fields for update_ls_with_x_api_key
                }

                print("whatlewir werextrea",extra)
                result = update_ls_with_token(token, extra)
            else:

                if event.get('queryStringParameters'):
                    skip_ls_sending = event['queryStringParameters'].get('skip_ls_sending', False)
                    version = event['queryStringParameters'].get('version', None)
                    app_name = event['queryStringParameters'].get('app_name', None)
                    user_id = event['queryStringParameters'].get('user_id', None)
                    tenant_id = event['queryStringParameters'].get('tenant_id', None)
                    app_type = event['queryStringParameters'].get('app_type', None)
                
                if not version and not app_name:
                    raise HTTPException(400, "version and app_name are required in query params")

                soc_server_ip = body.get('soc_server_ip', "dev.addchat.tech")

                extra = {
                    "version":version,
                    "app_name":app_name,
                    "request_body": body,
                    "skip_ls_sending": skip_ls_sending,
                    "soc_server_ip": soc_server_ip,
                    "user_id":user_id,
                    "tenant_id":tenant_id,
                    "app_type":app_type,
                    **body  # flatten relevant fields for update_ls_with_x_api_key
                }


                result = update_ls_with_x_api_key(extra, soc_server_ip)

            return standard_response(200, result)

        else:
            return standard_response(404, {"error": "Endpoint not found"})

    except HTTPException as he:
        return standard_response(he.status_code, {"error": str(he)})
    except Exception as e:
        print(f"Error: {str(e)}")
        return standard_response(500, {"error": "Internal server error"})
