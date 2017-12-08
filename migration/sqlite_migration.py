import sqlalchemy as sa
import os

db_password = os.environ["DB_PASSWORD"]

SQLALCHEMY_DATABASE_URI = "mysql+mysqlconnector://{username}:{password}@{hostname}/{databasename}".format(
    username="miroahti",
    password=db_password,
    hostname="miroahti.mysql.pythonanywhere-services.com",
    databasename="miroahti$domestic",
)

class DBHelper:
    def __init__(self, dbname="domestic.sqlite"):
        engine = sa.create_engine(SQLALCHEMY_DATABASE_URI,
            pool_recycle=280)
        self.conn = engine.connect()

    def mb_add_item(self, owner,chat,amount):
        stmt = "INSERT INTO moneybox (owner, chat,amount) VALUES (%s, %s, %s)"
        args = (owner,chat,amount)
        self.conn.execute(stmt, args)

    def add_item(self, item_text, owner):
        stmt = "INSERT INTO items (description, owner) VALUES (%s, %s)"
        args = (item_text, owner )
        self.conn.execute(stmt, args)

import sqlite3

class DBHelper_lite:
    def __init__(self, dbname="domestic.sqlite"):
        self.dbname = dbname
        self.conn = sqlite3.connect(dbname)

    def get_moneybox(self):
        stmt = "select * from moneybox;"
        return [x for x in self.conn.execute(stmt)]

    def get_shoppinglist(self):
        stmt = "select * from items;"
        return [x for x in self.conn.execute(stmt)]

db = DBHelper()
db2 = DBHelper_lite()

for i in db2.get_moneybox():
    db.mb_add_item(i[0],i[1],i[2])

for i in db2.get_shoppinglist():
    db.add_item(i[0], i[1])