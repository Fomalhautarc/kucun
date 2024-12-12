from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flasgger import Swagger
from flask_restful import Api



def create_app():
    app = Flask(__name__)
    app.config.from_object('app.config.Config')
    
    swagger_config = {
        "swagger": "2.0",
        "info": {
            "title": "库存管理 API",
            "description": "是库存管理系统的 API 文档？",
            "version": "2048.0.1",
        }
    }
    Swagger(app, template=swagger_config)

    api = Api(app)
    # 在这里注册资源
    from app.resources import ProductsAPI, ProductAPI, ProductsQueryAPI, UserRegisterAPI, UserLoginAPI, UserMeAPI,CategoryAPI
    api.add_resource(ProductsAPI, '/api/products')
    api.add_resource(ProductAPI, '/api/products/<int:product_id>')
    api.add_resource(ProductsQueryAPI, '/api/products/query')
    api.add_resource(UserRegisterAPI, '/api/users/register')
    api.add_resource(UserLoginAPI, '/api/users/login')
    api.add_resource(UserMeAPI, '/api/users/me')
    api.add_resource(CategoryAPI, '/api/categories')

    return app
