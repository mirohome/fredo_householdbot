from dbhelper import DBHelper
db = DBHelper()

chat = "-245116892"

for i in db.todo_get_items(chat):
    print(i)
