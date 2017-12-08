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

    def setup(self):
        stmt = """
            CREATE TABLE IF NOT EXISTS
            items (
                id MEDIUMINT NOT NULL AUTO_INCREMENT,
                description text,
                owner text,
                deleted boolean default false,
                created_at TIMESTAMP NOT NULL DEFAULT NOW(),

                PRIMARY KEY(id)
                );"""
        self.conn.execute(stmt)

        mb_stmt = """
                CREATE TABLE IF NOT EXISTS
                moneybox (
                    id MEDIUMINT NOT NULL AUTO_INCREMENT,
                    owner text,
                    chat text,
                    amount double precision,
                    category text,
                    created_at TIMESTAMP NOT NULL DEFAULT NOW(),

                    PRIMARY KEY(id)
                    );
                """
        self.conn.execute(mb_stmt)

    def mb_add_item(self, owner,chat,amount):
        stmt = "INSERT INTO moneybox (owner, chat,amount) VALUES (%s, %s, %s)"
        args = (owner,chat,amount)
        self.conn.execute(stmt, args)

    def add_item(self, item_text, owner):
        stmt = "INSERT INTO items (description, owner) VALUES (%s, %s)"
        args = (item_text, owner )
        self.conn.execute(stmt, args)

    def delete_item(self, item_text,owner):
        stmt = "DELETE FROM items WHERE description = (%s) AND owner = (%s)"
        args = (item_text, owner )
        self.conn.execute(stmt, args)

    def delete_all(self,owner):
        stmt = "DELETE FROM items WHERE owner = (%s)"
        args = (owner, )
        self.conn.execute(stmt,args)

    def get_items(self,owner):
        stmt = "SELECT description FROM items WHERE owner = (%s)"
        args = (owner,)
        return [x[0] for x in self.conn.execute(stmt,args)]

    def mb_get_items(self,chat):
        stmt = "SELECT owner, sum(amount) as amount FROM moneybox WHERE chat = (%s) GROUP BY owner"
        args = (chat,)
        return [x for x in self.conn.execute(stmt,args)]

    def mb_weekly_spend(self,chat):
        stmt = """
                SELECT
                    YEAR(created_at),
                    WEEK(created_at),
                    sum(amount) as amount
                FROM moneybox
                WHERE
                    chat = (%s) AND
                    created_at >= DATE_SUB(DATE_SUB(curdate(), INTERVAL 7 WEEK), INTERVAL 7 + DAYOFWEEK(curdate()) DAY)
                GROUP BY
                    YEAR(created_at),
                    WEEK(created_at)
                """
        args = (chat,)
        return [x for x in self.conn.execute(stmt,args)]