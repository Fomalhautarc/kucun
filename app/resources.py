from flask_restful import Resource, reqparse
import pymysql
from werkzeug.security import generate_password_hash, check_password_hash
from flask import request
import jwt
import datetime
from app.db import get_db
from flask_restful import Resource, reqparse
from .auth import requires_role 



class UserRegisterAPI(Resource):
    def post(self):
        """
        注册新用户
        ---
        tags:
          - User
        parameters:
          - name: body
            in: body
            required: true
            schema:
              id: User
              required:
                - username
                - password
                - role
              properties:
                username:
                  type: string
                password:
                  type: string
                role:
                  type: string
                  enum: [user, admin]
        responses:
          201:
            description: 用户注册成功
          400:
            description: 输入无效
        """
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        role = data.get('role', 'user')  # 默认角色为普通用户

        if not username or not password or not role:
            return {"message": "用户名、密码和角色是必需的"}, 400

        if role not in ['user', 'admin']:
            return {"message": "角色无效"}, 400

        password_hash = generate_password_hash(password)

        connection = get_db()
        cursor = connection.cursor()
        try:
            cursor.execute(
                "INSERT INTO users (username, password_hash, role) VALUES (%s, %s, %s);",
                (username, password_hash, role)
            )
            connection.commit()
        except Exception as e:
            return {"message": str(e)}, 400
        finally:
            cursor.close()

        return {"message": "用户注册成功"}, 201

class UserLoginAPI(Resource):
    def post(self):
        """
        用户登录
        ---
        tags:
          - User
        parameters:
          - name: body
            in: body
            required: true
            schema:
              id: UserLogin
              required:
                - username
                - password
              properties:
                username:
                  type: string
                password:
                  type: string
        responses:
          200:
            description: 登录成功
          401:
            description: 用户名或密码错误
        """
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')

        if not username or not password:
            return {"message": "用户名和密码是必需的"}, 400

        connection = get_db()
        cursor = connection.cursor()
        cursor.execute(
            "SELECT id, password_hash, role FROM users WHERE username = %s;",
            (username,)
        )
        user = cursor.fetchone()
        cursor.close()

        if user and check_password_hash(user[1], password):
            token = jwt.encode({
                'user_id': user[0],
                'role': user[2],
                'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=1)
            }, "SECRET_KEY", algorithm="HS256")

            return {"token": token}, 200

        return {"message": "用户名或密码错误"}, 401

class UserMeAPI(Resource):
    @requires_role('admin')
    def get(self):
        """
        获取当前用户信息
        ---
        tags:
          - User
        responses:
          200:
            description: 返回当前用户信息
          403:
            description: Token无效或缺失
        """
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return {"message": "Token is missing!"}, 403

        try:
            token = auth_header.split(" ")[1]
            data = jwt.decode(token, "SECRET_KEY", algorithms=["HS256"])
            current_user = data
        except IndexError:
            return {"message": "Token format is invalid!"}, 403
        except jwt.ExpiredSignatureError:
            return {"message": "Token has expired!"}, 403
        except jwt.InvalidTokenError:
            return {"message": "Token is invalid!"}, 403

        return {"user": current_user}, 200



class ProductsAPI(Resource):
    @requires_role('admin')
    def post(self):
        '''
        添加单个产品
        ---
        tags:
          - Products
        description: 添加⼀个新产品到库存
        parameters:
          - name: body
            in: body
            required: true
            schema:
              type: object
              properties:
                name:
                  type: string
                inventory:
                  type: integer
                price:
                  type: number
        responses:
          201:
            description: 产品成功添加
        '''
        parser = reqparse.RequestParser()
        parser.add_argument('name', required=True, type=str, help="产品名称必需")
        parser.add_argument('inventory', required=True, type=int, help="库存数量必需")
        parser.add_argument('price', required=True, type=float, help="价格必需")
        args = parser.parse_args()
        connection = get_db()
        cursor = connection.cursor()
        cursor.execute(
            "INSERT INTO products (name, inventory, price) VALUES (%s, %s, %s);",
            (args['name'], args['inventory'], args['price'])
        )
        connection.commit()
        cursor.close()
        
        return {"message": "产品成功添加"}, 201
    
    @requires_role('admin')
    def put(self, product_id):
        '''
        以 ID 修改单个产品
        ---
        tags:
          - Products
        description: 以 ID 更新单个产品的详情
        parameters:
          - name: product_id
            in: path
            required: true
            type: integer
            description: 要更新的产品 ID
          - name: body
            in: body
            required: true
            schema:
              type: object
              properties:
                name:
                  type: string
                inventory:
                  type: integer
                price:
                  type: number
        responses:
          200:
            description: 产品成功更新
        '''
        parser = reqparse.RequestParser()
        parser.add_argument('name', required=False, type=str)
        parser.add_argument('inventory', required=False, type=int)
        parser.add_argument('price', required=False, type=float)
        args = parser.parse_args()

        connection = get_db()
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM products WHERE id = %s;", (product_id,))
        if not cursor.fetchone():
            cursor.close()
            return {"message": "找不到产品"}, 404
        # Update fields dynamically
        updates = []
        values = []
        for key, value in args.items():
            if value is not None:
                updates.append(f"{key} = %s")
                values.append(value)
        values.append(product_id)
        update_query = f"UPDATE products SET {', '.join(updates)} WHERE id = %s;"
        cursor.execute(update_query, tuple(values))
        connection.commit()
        cursor.close()
        return {"message": "产品成功更新"}, 200





class ProductAPI(Resource):
    '''
    产品 (Products)
    '''
    def get(self,product_id=None):
        '''
        以 ID 获取单个产品
        ---
        tags:
          - Products
        description: 以 ID 检索单个产品
        parameters:
          - name: product_id
            in: path
            type: integer
            required: false
            description: 要检索的产品 ID
        responses:
          200:
            description: 单个产品
        '''
        connection = get_db()
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM products WHERE id = %s;", (product_id,))
        row = cursor.fetchone()
        cursor.close()
        if row:
            return {"product": {"id": row[0], "name": row[1], "inventory": row[2], 
"price": float(row[3])}}, 200
        else:
            return {"message": "找不到产品"}, 404

class ProductsQueryAPI(Resource):
    def get(self):
        '''
        以条件组合查询产品
        ---
        tags:
          - Products
        description: 基于 name、inventory、price 和 category 查询产品
        parameters:
          - name: name
            in: query
            type: string
            required: false
          - name: inventory
            in: query
            type: integer
            required: false
          - name: price_min
            in: query
            type: float
            required: false
          - name: price_max
            in: query
            type: float
            required: false
          - name: category
            in: query
            type: string
            required: false
        responses:
          200:
            description: 匹配查询条件的产品列表
        '''
        parser = reqparse.RequestParser()
        parser.add_argument('name', type=str, location='args')
        parser.add_argument('inventory', type=int, location='args')
        parser.add_argument('price_min', type=float, location='args')
        parser.add_argument('price_max', type=float, location='args')
        parser.add_argument('category', type=str, location='args')
        args = parser.parse_args()
        
        query = "SELECT products.* FROM products LEFT JOIN categories ON products.category_id = categories.id WHERE 1=1"
        values = []

        if args['name']:
            query += " AND products.name LIKE %s"
            values.append(f"%{args['name']}%")
        if args['inventory']:
            query += " AND products.inventory >= %s"
            values.append(args['inventory'])
        if args['price_min']:
            query += " AND products.price >= %s"
            values.append(args['price_min'])
        if args['price_max']:
            query += " AND products.price <= %s"
            values.append(args['price_max'])
        if args['category']:
            query += " AND categories.name = %s"
            values.append(args['category'])

        connection = get_db()
        cursor = connection.cursor()
        cursor.execute(query, tuple(values))
        rows = cursor.fetchall()
        cursor.close()

        if rows:
            products = [
                {"id": row[0], "name": row[1], "inventory": row[2], "price": float(row[3]), "category_id": row[4]} for row in rows
            ]
            return {"products": products}, 200
        else:
            return {"message": "找不到产品"}, 404
        


class CategoryAPI(Resource):
    def post(self):
        """
        创建新分类
        ---
        tags:
          - Categories
        parameters:
          - name: body
            in: body
            required: true
            schema:
              type: object
              properties:
                name:
                  type: string
        responses:
          201:
            description: 分类创建成功
          400:
            description: 输入无效或分类已存在
        """
        data = request.get_json()
        name = data.get('name')

        if not name:
            return {"message": "分类名称是必需的"}, 400

        connection = get_db()
        cursor = connection.cursor()
        try:
            cursor.execute(
                "INSERT INTO categories (name) VALUES (%s);",
                (name,)
            )
            connection.commit()
        except pymysql.err.IntegrityError:
            return {"message": "分类已存在"}, 400
        finally:
            cursor.close()

        return {"message": "分类创建成功"}, 201
