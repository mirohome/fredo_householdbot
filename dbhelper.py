import sqlite3

class DBHelper:
    def __init__(self, dbname="shopping_list.sqlite"):
        self.dbname = dbname
        self.conn = sqlite3.connect(dbname)
    
    def setup(self):
        stmt = "CREATE TABLE IF NOT EXISTS items (description text, owner text)"
        itemidx = "CREATE INDEX IF NOT EXISTS itemIndex ON items (description ASC)" 
        ownidx = "CREATE INDEX IF NOT EXISTS ownIndex ON items (owner ASC)"
        self.conn.execute(stmt)
        self.conn.execute(itemidx)
        self.conn.execute(ownidx)
        
        mb_stmt = "CREATE TABLE IF NOT EXISTS moneybox (owner text, chat text, amount double precision)"
        self.conn.execute(mb_stmt)
        self.conn.commit()
    
    def mb_add_item(self, owner,chat,amount):
        stmt = "INSERT INTO moneybox (owner, chat,amount) VALUES (?, ?, ?)"
        args = (owner,chat,amount)
        self.conn.execute(stmt, args)
        self.conn.commit()
    
    def add_item(self, item_text, owner):
        stmt = "INSERT INTO items (description, owner) VALUES (?, ?)"
        args = (item_text, owner )
        self.conn.execute(stmt, args)
        self.conn.commit()
    
    def delete_item(self, item_text,owner):
        stmt = "DELETE FROM items WHERE description = (?) AND owner = (?)"
        args = (item_text, owner )
        self.conn.execute(stmt, args)
        self.conn.commit()
        
    def delete_all(self,owner):
        stmt = "DELETE FROM items WHERE owner = (?)"
        args = (owner, )
        self.conn.execute(stmt,args)
        self.conn.commit()
    
    def get_items(self,owner):
        stmt = "SELECT description FROM items WHERE owner = (?)"
        args = (owner,)
        return [x[0] for x in self.conn.execute(stmt,args)]
        
    def mb_get_items(self,chat):
        stmt = "SELECT owner, sum(amount) as amount FROM moneybox WHERE chat = (?) GROUP BY owner"
        args = (chat,)
        return [x for x in self.conn.execute(stmt,args)]