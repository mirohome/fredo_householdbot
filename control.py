import json 
import requests
import time
import urllib
import os

from yahoo_finance import Share

from dbhelper import DBHelper
db = DBHelper()

TOKEN = os.getenv("TG_TOKEN")
URL = "https://api.telegram.org/bot{}/".format(TOKEN)

NEWS_TOKEN = os.getenv("NEWS_TOKEN")
NEWS_URL = "https://newsapi.org/v1/articles?source={source}&sortBy=top&apiKey={token}".format(token = NEWS_TOKEN, source = '{source}')

# Code for requests and dealing with telegram api.

def get_url(url):
    response = requests.get(url)
    content = response.content.decode("utf8")
    return content
   
def get_json_from_url(url):
    content = get_url(url)
    js = json.loads(content)
    return js
    
def get_updates(offset=None):
    url = URL + "getUpdates?timeout=100"
    if offset:
        url += "&offset={}".format(offset)
    js = get_json_from_url(url)
    return js

def get_last_update_id(updates):
    update_ids = []
    for update in updates["result"]:
        update_ids.append(int(update["update_id"]))
    return max(update_ids)
    
def get_last_chat_id_and_text(updates):
    num_updates = len(updates["result"])
    last_update = num_updates - 1
    text = updates["result"][last_update]["message"]["text"]
    chat_id = updates["result"][last_update]["message"]["chat"]["id"]
    return (text, chat_id)
    
def send_message(text, chat_id, reply_markup=None):
    text = urllib.parse.quote_plus(text)
    url = URL + "sendMessage?text={}&chat_id={}&parse_mode=Markdown".format(text, chat_id)
    if reply_markup:
        url += "&reply_markup={}".format(reply_markup)
    get_url(url)

def build_keyboard(items):
    keyboard = [[item] for item in items]
    reply_markup = {"keyboard":keyboard, "one_time_keyboard": True}
    return json.dumps(reply_markup)
 
# Code for stock market
def get_current_price(name):
    share = Share(name)
    return share.get_price()
    
# Code for dealing with the news.
def get_news(source):
    url = NEWS_URL.format(source = source)
    data = get_json_from_url(url)
    return data['articles']

def news_controller(text,chat):
    if len(text.split(' ')) == 1:
        news_sources = ['/news techcrunch','/news the-new-york-times','/news the-washington-post']
        send_message("Please specify news source", chat, reply_markup=build_keyboard(news_sources))
    else:
        try:
            for i in get_news(text.split(' ')[1]):
                send_message(i['title'] + '\n' + i['url'], chat)
        except:
            send_message(text.split(' ')[1] + " not found.", chat)    
    
# The main function
def main():
    db.setup()
    
    updates = get_updates()
    if len(updates['result']) > 0:
        last_update_id = get_last_update_id(updates) + 1
    else:
        last_update_id = None
    while True:
        updates = get_updates(last_update_id)
        try:
            text, chat = get_last_chat_id_and_text(updates)
        except:
            continue
        if len(updates["result"]) > 0:
            if text.split(' ')[0] == '/price':
                try:
                    price = get_current_price(text.split(' ')[1].upper())
                    if price is None:
                        send_message(text.split(' ')[1] + " was not found.", chat)
                    else:
                        send_message("Current price is " + str(price), chat)
                except:
                    send_message("Please specify stock", chat)
            elif text.split(' ')[0] == '/news':
                news_controller(text, chat)
            elif text.split(' ')[0] == '/sl' and len(text.split(' ')) == 1: 
                text_back = ''
                text_back = text_back + "/sl add for adding an item to the list \n"
                text_back = text_back + "/sl show for showing contents of the list. \n"
                text_back = text_back + "/sl delete to delete an item."
                send_message(text_back, chat)
            elif text.split(' ')[0] == '/sl' and text.split(' ')[1].lower() == 'add':
                try:
                    text = text.replace('/sl add ', '')
                    for item in text.split(','):
                        add = item.strip()
                        db.add_item(add, chat)
                        send_message(add + " added to the shopping list", chat)
                except:
                    send_message("Please specify item.", chat)
            elif (text.split(' ')[0] == '/sl' and text.split(' ')[1].lower() == 'delete') or text.split(' ')[0] == '/delete_more':
                if len(text.split(' ')) == 2 or text.split(' ')[0] == '/delete_more':
                    items = db.get_items(chat)
                    items = ['/sl delete ' + item for item in items]
                    keyboard = build_keyboard(items)
                    send_message("Select an item to delete", chat, keyboard)
                try:
                    if text.split(' ')[2].lower() == 'all':
                        db.delete_all(chat)
                        send_message("All items removed from shopping list.", chat)
                    else:
                        text = text.replace('/sl delete ', '')
                        text = text.replace('/delete_more', '')
                        db.delete_item(text,chat)
                        message = text + " deleted from the shopping list."
                        
                        options = ['/delete_more','/continue']
                        send_message(message, chat, reply_markup=build_keyboard(options))
                except:
                    send_message("Please specify item.", chat)
            elif text.split(' ')[0] == '/sl' and text.split(' ')[1].lower() == 'show':
                items = db.get_items(chat)
                message = "\n".join(items)
                if len(items) > 0:
                    send_message(message, chat)
                else:
                    send_message("Shopping list is empty.", chat)
            elif text.split(' ')[0] == '/commands':
                text_back = ''
                text_back = text_back + "/price + stock ticker will give you the current price of a stock. \n"
                text_back = text_back + "/news will present you with news. \n"
                text_back = text_back + "/sl will allow you to control shopping list."
                send_message(text_back, chat)
            elif text.split(' ')[0] == '/start':
                text_back = ''
                text_back = 'This is what the bot can do for now: \n'
                text_back = text_back + "/price + stock ticker will give you the current price of a stock. \n"
                text_back = text_back + "/news will present you with news. \n"
                text_back = text_back + "/sl will allow you to control shopping list."
                send_message(text_back, chat)
            elif text.split(' ')[0] == '/continue':
                continue
            elif not text.startswith('/'):
                continue
            else:
                text_back = ''
                text_back = "I don't know what you mean by " + text + '\n'
                text_back = text_back + 'Write /commands to see what the bot can do.'
                send_message(text_back, chat)
            last_update_id = get_last_update_id(updates) + 1
        time.sleep(0.5)


if __name__ == '__main__':
    main()