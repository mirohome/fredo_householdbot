import sqlalchemy as sa
from sqlalchemy.orm import sessionmaker, mapper
import os

db_password = os.environ["DB_PASSWORD"]

SQLALCHEMY_DATABASE_URI = "mysql+mysqlconnector://{username}:{password}@{hostname}/{databasename}".format(
    username="miroahti",
    password=db_password,
    hostname="miroahti.mysql.pythonanywhere-services.com",
    databasename="miroahti$domestic",
)


# ORM set-up
engine_1 = sa.create_engine(SQLALCHEMY_DATABASE_URI,
            pool_recycle=280)
metadata = sa.MetaData(engine_1)

# Set up users table. Created in init method for now.
class Users(object):
    pass

users = sa.Table('users', metadata, autoload=True)
mapper(Users, users)

# Table for budgets
budgets = sa.Table('budgets', metadata,
    sa.Column('chat_id', sa.String(255), primary_key=True),
    sa.Column('budget', sa.Integer)
)

class Budgets(object):
    pass

    def __init__(self, chat_id, budget):
      self.chat_id = chat_id
      self.budget = budget

budgets.create(engine_1,checkfirst=True)
mapper(Budgets, budgets)

# Helper for db
class DBHelper:
    def __init__(self, dbname="domestic.sqlite"):
        engine = sa.create_engine(SQLALCHEMY_DATABASE_URI,
            pool_recycle=280)
        self.conn = engine.connect()
        self.engine=engine

        # create a configured "Session" class
        Session = sessionmaker(bind=engine)

        # create a Session
        self.session = Session()

    def setup(self):
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

        users_stmt = """
                CREATE TABLE IF NOT EXISTS
                users (
                    user_id VARCHAR(255),
                    chat_id VARCHAR(255),
                    state VARCHAR(255),
                    created_at TIMESTAMP NOT NULL DEFAULT NOW(),

                    PRIMARY KEY(user_id,chat_id)
                    );
                """
        self.conn.execute(users_stmt)

    def mb_add_item(self, owner,chat,amount):
        stmt = "INSERT INTO moneybox (owner, chat,amount) VALUES (%s, %s, %s)"
        args = (owner,chat,amount)
        self.conn.execute(stmt, args)

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

    # User functions
    def add_user(self,user_id,chat_id):
        stmt = "INSERT INTO users (user_id,chat_id,state) VALUES (%s, %s, 'initial')"
        args = (user_id,chat_id)
        self.conn.execute(stmt, args)

    # Functions for the state of the user
    def set_user_state(self,user_id,chat_id,new_state):
        self.session.query(Users).filter(Users.user_id==user_id, Users.chat_id==chat_id).update({"state": new_state})
        self.session.commit()
        print("added user to state:" + new_state)

    def get_state(self,user_id,chat_id):
        result = self.session.query(Users.state).filter(Users.user_id==user_id, Users.chat_id==chat_id).scalar()
        return result

    # Add budget & show budget
    def add_budget(self,chat_id,budget):
        new_budget = Budgets(chat_id=chat_id, budget=budget)
        self.session.merge(new_budget)
        self.session.commit()

    def show_budget(self,chat_id):
        result = self.session.query(Budgets.budget).filter(Budgets.chat_id==chat_id).scalar()
        return result

