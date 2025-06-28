
import json
import time
import jwt

from functools import wraps
from enum import Enum
import base64

from typing import Dict, Any


JWT_ISSUER = "com.zalando.connexion"
JWT_SECRET = "change_this"
JWT_LIFETIME_SECONDS = 6000000
JWT_ALGORITHM = "HS256"

encoded_secret = base64.b64encode(JWT_SECRET.encode('utf-8')).decode()

class HTTPException(Exception):
    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(message)

def standard_response(status_code: int, body: Dict[str, Any]) -> Dict[str, Any]:
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'OPTIONS,POST,GET,PUT',
            'Access-Control-Allow-Headers': 'Content-Type,Authorization,X-API-Key'
        },
        'body': json.dumps(body)
    }


def parse_body(event: Dict[str, Any]) -> Dict[str, Any]:
    try:
        return json.loads(event.get('body', '{}'))
    except json.JSONDecodeError:
        raise HTTPException("Invalid JSON in request body", 400)

def decode_token(token):
    try:
        return jwt.decode(token, encoded_secret, algorithms=[JWT_ALGORITHM])
    except Exception as e:
        raise e
