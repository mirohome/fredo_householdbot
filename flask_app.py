from flask import Flask, request
import telepot
import urllib3
import os

from dbhelper import DBHelper
db = DBHelper()

# Setup
proxy_url = "http://proxy.server:3128"
telepot.api._pools = {
    'default': urllib3.ProxyManager(proxy_url=proxy_url, num_pools=3, maxsize=10, retries=False, timeout=30),
}
telepot.api._onetime_pool_spec = (urllib3.ProxyManager, dict(proxy_url=proxy_url, num_pools=1, maxsize=1, retries=False, timeout=30))

secret = os.environ["RUN_SECRET"]
telegram_token = os.environ["TG_TOKEN"]
bot = telepot.Bot(telegram_token)
bot.setWebhook("https://miroahti.pythonanywhere.com/{}".format(secret), max_connections=1)

# Helper functions: should probably be in another file.
# Copied from stack overflow.
def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False

# Instructions
def instructions(chat,start=False):
    text_back = "/mb_add: Add money to your balance. This money is owed to the household by other participants. /a is a shortcut for this. \n"
    text_back = text_back + "/mb_show: See the current balance of each participant. \n"
    text_back = text_back + "/mb_stats: Shows basic statistics of the household spending. \n\n"
    text_back = text_back + "/mb_budget: Set a budget for this conversation"

    if start:
        intro ="Hello. I'm Fredo, a bot for managing your household expenses. \n"
        intro = intro + "The main functionality is for each member of the chat to input the amount of money they have spend for the shared expenses of the household.\n"
        intro = intro + "This will allow keeping track of who needs to spend and how much for the common good. \n"
        intro = intro + "The app is best used as a member of a group conversation. \n"
        intro = intro + "Currently we have the following functionality available: \n \n"

        text_back = intro + text_back

        bot.sendMessage(chat,text_back)
    else:
        bot.sendMessage(chat,text_back)

# Moneybox:
def moneybox(text,chat,user,user_id):
    db_owner = str(chat)
    command = text.split(" ")[0]

    if len(command.split('_')) == 1:
        message = 'Message not understood.'
        bot.sendMessage(chat,message)

    elif command.split('_')[1].lower() == 'add':
        try:
            amount = float(text.split(' ')[1].lower())
            db.mb_add_item(user,db_owner,amount)

            str_amount = "{0:.2f}".format(amount)
            message = str_amount + " euro added for " + user
            bot.sendMessage(chat,message)
        except:
            message = "Please state the amount in euro."
            db.set_user_state(user_id = user_id,chat_id=chat,new_state='adding')
            bot.sendMessage(chat,message)

    elif command.split('_')[1].lower() == 'show':
        items = db.mb_get_items(db_owner)

        messages = [item[0] + ": " + "{0:.2f}".format(item[1]) + " euro" for item in items]
        message = "\n".join(messages)
        if message == "":
            message = "No balance to show yet. Add to your balance first."

        # Show difference between participants
        try:
            minimum = min(db.mb_get_items(chat))[1]
            message += "\n \n*Difference in balance:* \n"
            messages = [item[0] + ": " + "{0:.2f}".format(item[1] - minimum) + " euro" for item in items]
            message_addition = "\n".join(messages)
            message += message_addition
        except:
            message += ""

        # Show what is the current budget
        budget = db.show_budget(db_owner)
        if budget is not None:
            message = message + "\n \n Weekly budget for this chat is " + str(budget)

        bot.sendMessage(chat,message, parse_mode= 'Markdown')

    # Statistics on spending so far.
    elif command.split('_')[1].lower() == 'stats':
        budget = db.show_budget(db_owner)

        message = ''
        if budget is None:
            for i in db.mb_weekly_spend(chat):
                message += str(i[0]) + ' ' + str(i[1]) + ': ' + str(i[2]) + '\n'
            if message == '':
                message = 'No statistics to show yet. Add to your balance first.'
        else:
            for i in db.mb_weekly_spend(chat):
                message += "*Week " + str(i[0]) + ' ' + str(i[1]) + ':* ' + "{0:.2f}".format(i[2]) + " euro spent. " + "{0:.0f}%".format((i[2]/budget)*100) + " of budget" '\n'
            if message == '':
                message = 'No statistics to show yet. Add to your balance first.'
        bot.sendMessage(chat,message, parse_mode= 'Markdown')

    # Setting budget
    elif command.split('_')[1].lower() == 'budget':
        if len(text.split(' ')) > 1:
            amount = text.split(' ')[1].lower()

            if is_number(amount):
                amount = float(amount)
                print("Budget amount is: " + str(amount))

                db.add_budget(db_owner,amount)

                str_amount = "{0:.2f}".format(amount)
                message = "New budget for chat is " + str_amount
                bot.sendMessage(chat,message)
            else:
                db.set_user_state(user_id = user_id,chat_id=chat,new_state='Budgeting')

                message = "Please state the budget in euro."
                bot.sendMessage(chat,message)
        else:
            db.set_user_state(user_id = user_id,chat_id=chat,new_state='Budgeting')

            message = "Please state the budget in euro."
            bot.sendMessage(chat,message)

    else:
        message = 'Message not understood.'
        bot.sendMessage(chat,message)

# The app code:
app = Flask(__name__)

@app.route('/{}'.format(secret), methods=["POST"])
def telegram_webhook():
    update = request.get_json()
    print(update)

    if "message" in update:
        db.setup()
        try:
            text = update["message"]["text"]
            chat = update["message"]["chat"]["id"]
        except:
            print("Message not recognized")
            return "OK"

        try:
            from_user = update["message"]["from"]["username"]
        except:
            from_user = update["message"]["from"]["first_name"]

        from_user_id = update["message"]["from"]["id"]
        try:
            user_state = db.get_state(from_user_id,chat)
            print("User state is:" + str(user_state))
        except:
            user_state = None
            print("User state is None.")


        if user_state is None:
            try:
                db.add_user(from_user_id,chat)
            except:
                 db.set_user_state(user_id = from_user_id,chat_id=chat,new_state='initial')

        if user_state == 'adding':
            try:
                amount = float(text.split(' ')[0].lower())
                print("Amount recognized")
            except ValueError:
                message = "Amount not recognized."
                bot.sendMessage(chat,message)
                db.set_user_state(user_id = from_user_id,chat_id=chat,new_state='initial')
                user_state = 'initial'
                print("Amount not recognized")
                return "OK"

        if user_state == 'adding':
            db.mb_add_item(from_user,str(chat),amount)
            message = str(amount) + " euro added for " + from_user
            bot.sendMessage(chat,message)
            db.set_user_state(user_id = from_user_id,chat_id=chat,new_state='initial')
            return "OK"

        if user_state == 'Budgeting':
            amount = text.split(' ')[0].lower()
            if is_number(amount):
                amount = float(amount)
                print("Budget amount is: " + str(amount))

                db.add_budget(chat,amount)

                str_amount = "{0:.2f}".format(amount)
                message = "New budget for chat is " + str_amount
                bot.sendMessage(chat,message)
                db.set_user_state(user_id = from_user_id,chat_id=chat,new_state='initial')
                return "OK"
            else:
                db.set_user_state(user_id = from_user_id,chat_id=chat,new_state='Budgeting')

                message = "Please state the budget in euro."
                bot.sendMessage(chat,message)
                return "OK"

        if text.split(' ')[0] == '/start':
            db.set_user_state(user_id = from_user_id,chat_id=chat,new_state='initial')
            instructions(chat,start=True)
        elif text.split('_')[0] == '/mb':
            db.set_user_state(user_id = from_user_id,chat_id=chat,new_state='initial')
            moneybox(text,chat,from_user,user_id=from_user_id)
        elif text.split(' ')[0] == '/a':
            try:
                amount = float(text.split(' ')[1].lower())
                db.mb_add_item(from_user,str(chat),amount)

                str_amount = "{0:.2f}".format(amount)
                message = str_amount + " euro added for " + from_user
                bot.sendMessage(chat,message)
            except:
                message = "Please state the amount in euro."
                db.set_user_state(user_id = from_user_id,chat_id=chat,new_state='adding')
                bot.sendMessage(chat,message)
        elif not text.startswith('/'):
            db.set_user_state(user_id = from_user_id,chat_id=chat,new_state='initial')
            return "OK"
    return "OK"
