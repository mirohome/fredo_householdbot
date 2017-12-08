from flask import Flask, request
import telepot
import urllib3
import json
import os

from dbhelper import DBHelper
db = DBHelper()

proxy_url = "http://proxy.server:3128"
telepot.api._pools = {
    'default': urllib3.ProxyManager(proxy_url=proxy_url, num_pools=3, maxsize=10, retries=False, timeout=30),
}
telepot.api._onetime_pool_spec = (urllib3.ProxyManager, dict(proxy_url=proxy_url, num_pools=1, maxsize=1, retries=False, timeout=30))

secret = os.environ["RUN_SECRET"]
telegram_token = os.environ["TG_TOKEN"]
bot = telepot.Bot(telegram_token)
bot.setWebhook("https://miroahti.pythonanywhere.com/{}".format(secret), max_connections=1)

# Bot related functions:
def build_keyboard(items):
    keyboard = [[item] for item in items]
    reply_markup = {"keyboard":keyboard, "one_time_keyboard": True}
    return json.dumps(reply_markup)

# Temporarily have the control code here:

# Instructions
def instructions(chat,start=False):
    text_back = "/mb Will access moneybox functionality for keeping track of expenses. \n"
    text_back = text_back + "/sl will allow you to control the shopping list."

    if start:
        text_back = 'This is what the bot can do for now: \n' + text_back
        bot.sendMessage(chat,text_back)
    else:
        bot.sendMessage(chat,text_back)

# Moneybox:
def moneybox(text,chat,user):
    db_owner = str(chat)

    if len(text.split(' ')) == 1:
        message = 'Please specify amount'
        bot.sendMessage(chat,message)
    elif text.split(' ')[1].lower() == 'add':
        try:
            amount = float(text.split(' ')[2].lower())
            db.mb_add_item(user,db_owner,amount)
            message = str(amount) + " euro added for " + user
            bot.sendMessage(chat,message)
        except:
            message = "Please state the amount in euro."
            bot.sendMessage(chat,message)
    elif text.split(' ')[1].lower() == 'show':
        items = db.mb_get_items(db_owner)
        messages = [item[0] + ": " + str(item[1]) + " euro" for item in items]
        message = "\n".join(messages)
        if message == "":
            message = "Moneybox is empty."
        bot.sendMessage(chat,message)

    elif text.split(' ')[1].lower() == 'diff':
        items = db.mb_get_items(db_owner)
        minimum = min(db.mb_get_items(chat))[1]

        messages = [item[0] + ": " + str(item[1] - minimum) + " euro" for item in items]
        message = "\n".join(messages)
        if message == "":
            message = "Moneybox is empty."
        bot.sendMessage(chat,message)

    elif text.split(' ')[1].lower() == 'stats':
        message = ''
        for i in db.mb_weekly_spend(chat):
            message += str(i[0]) + ' ' + str(i[1]) + ': ' + str(i[2]) + '\n'
        bot.sendMessage(chat,message)

# Shopping list:
def shopping_list(text,chat):
    db_owner = str(chat)

    if len(text.split(' ')) == 1:
        message = "/sl add for adding an item to the list \n"
        message = message + "/sl show for showing contents of the list. \n"
        message = message + "/sl delete to delete an item."

        bot.sendMessage(chat,message)
    elif text.split(' ')[1].lower() == 'add':
        try:
            text = text.replace('/sl add ', '')
            if len(text.split(',')) == 1:
                for item in text.split(','):
                    add = item.strip()
                    db.add_item(add, db_owner)
                    message = add + " added to the shopping list"
                    bot.sendMessage(chat,message)
            else:
                i = 0
                for item in text.split(','):
                    add = item.strip()
                    db.add_item(add, db_owner)
                    i += 1

                message = str(i) + " items added to the shopping list"
                bot.sendMessage(chat,message)
        except:
            message ="Please specify item."

            bot.sendMessage(chat,message)


    elif (text.split(' ')[1].lower() == 'delete') or (text.split(' ')[1].lower() == 'delete_more'):
        if len(text.split(' ')) == 2 or text.split(' ')[1] == 'delete_more':
            items = db.get_items(db_owner)
            items = ['/sl delete ' + item for item in items]
            keyboard = build_keyboard(items)
            message = "Select an item to delete"

            bot.sendMessage(chat,message,reply_markup=keyboard)
        try:
            if text.split(' ')[2].lower() == 'all':
                db.delete_all(db_owner)
                message = "All items removed from shopping list."

                bot.sendMessage(chat,message)
            else:
                text = text.replace('/sl delete ', '')
                text = text.replace('/sl delete_more', '')
                db.delete_item(text,db_owner)
                message = text + " deleted from the shopping list."

                options = ['/sl delete_more','/exit']
                keyboard = build_keyboard(options)

                bot.sendMessage(chat,message,reply_markup=keyboard)
        except:
            message = "Please specify item."
            bot.sendMessage(chat,message)
    elif text.split(' ')[1].lower() == 'show':
        items = db.get_items(db_owner)
        message = "\n".join(items)
        if len(items) > 0:
            bot.sendMessage(chat,message)
        else:
            message = "Shopping list is empty."
            bot.sendMessage(chat,message)

# The app code:
app = Flask(__name__)

@app.route('/{}'.format(secret), methods=["POST"])
def telegram_webhook():

    update = request.get_json()
    if "message" in update:
        db.setup()
        text = update["message"]["text"]
        chat = update["message"]["chat"]["id"]
        try:
            from_user = update["message"]["from"]["username"]
        except:
            from_user = update["message"]["from"]["first_name"]


        if text.split(' ')[0] == '/start':
            instructions(chat,start=True)
        elif text.split(' ')[0] == '/mb':
            moneybox(text,chat,from_user)
        elif text.split(' ')[0] == '/sl':
            shopping_list(text,chat)
        elif not text.startswith('/'):
            return "OK"
    return "OK"

