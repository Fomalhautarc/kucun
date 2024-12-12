# auth.py
from functools import wraps
from flask import request
import jwt

def requires_role(required_role):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            auth_header = request.headers.get('Authorization')
            if not auth_header:
                return {"message": "Token is missing!"}, 403

           
            try:
                token = auth_header.split(" ")[1]
                data = jwt.decode(token, "SECRET_KEY", algorithms=["HS256"])
                user_role = data.get('role')
                if user_role != required_role:
                    return {"message": "权限不足"}, 403
            except IndexError:
                return {"message": "Token format is invalid!"}, 403
            except jwt.ExpiredSignatureError:
                return {"message": "Token has expired!"}, 403
            except jwt.InvalidTokenError:
                return {"message": "Token is invalid!"}, 403

            return f(*args, **kwargs)
        return decorated_function
    return decorator
