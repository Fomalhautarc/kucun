from flask import current_app, g
import pymysql


 
def get_db():
    config = current_app.config
    connection = pymysql.connect(
        host=config['MYSQL_HOST'],
        port=config['MYSQL_PORT'],
        user=config['MYSQL_USER'],
        password=config['MYSQL_PASSWORD'],
        database=config['MYSQL_DB']
    )
    if 'db' not in g:
        g.db = connection
    return g.db