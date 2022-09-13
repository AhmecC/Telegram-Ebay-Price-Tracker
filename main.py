import threading, telebot, time, sqlite3
from time import sleep
from selenium import webdriver
# from selenium.webdriver.chrome.options import Options # - For Replit
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from Scrape import Scraper
bot_token = ""
bot = telebot.TeleBot(bot_token)

# chrome_options = Options()
# chrome_options.add_argument('--no-sandbox')
# chrome_options.add_argument('--disable-dev-shm-usage')# - For Replit

def hosting():
    @bot.message_handler(commands=['start'])
    def start(message):
        """/start sends instructions and stores Chat ID"""
        bot.send_message(message.chat.id,
                         "😎 I can help you track items on ebay, "
                         "so you don't have to spend hours looking for the Perfect Price! 💸"
                         "\n\n/track_new -- Track a New Item"
                         "\n/manage -- View/Delete your Tracked Items")
        ID = message.chat.id

        cur = ids_Database.cursor()
        # cursor.execute("CREATE TABLE ids (id INTEGER NOT NULL UNIQUE)")
        cur.execute(f"SELECT * FROM ids where id = {ID}")
        if cur.fetchone() == "None":
            print("yes")
            cur.execute(f"INSERT INTO ids VALUES({message.chat.id})")
            ids_Database.commit()

            
    @bot.message_handler(commands=['track_new'])
    def new(message):
        ADD_NEW = bot.send_message(message.chat.id, "🧐 Specify the Item to be Tracked and your Target Price, "
                                                    "separated by a Comma. Be Specific!"
                                                    "\n\nE.g. Ipad Pro 2020 11 inch, 400")

        bot.register_next_step_handler(ADD_NEW, check)

    def check(message):
        first_check = message.text
        if first_check == "/track_new":
            new(message)
        elif first_check == "/start":
            start(message)
        elif first_check == "/manage":
            manage(message)
        else:
            response = message.text.split(", ")
            num = num_results(response)
            if len(response) != 2 or response[1].isdigit() == False or num == 0:
                no_comma_error(message, num)
            else:
                bot.reply_to(message, "🥳 Added to Track List!")
                id = message.chat.id
                track_database = sqlite3.connect(f"{id}_Track.db", check_same_thread=False)
                cur = track_database.cursor()
                cur.execute(f"INSERT INTO '{id}_Track' VALUES ('{response[0]}', '{response[1]}')")
                track_database.commit()  # Adds Item, Price to database

    def num_results(response):
#         driver = webdriver.Chrome(options=chrome_options) # - For Replit
        try:
            driver.get("https://www.ebay.co.uk/")
            search = driver.find_element(By.XPATH, '//*[@id="gh-ac"]')
            search.send_keys(response[0])
            search.send_keys(Keys.ENTER)
            sleep(2)
            result = driver.find_element(By.CLASS_NAME, 'srp-controls__count-heading').text
            num = int(result[:2])
        except:
            num = 0
        return num

    def no_comma_error(message, num):
        if num == 0:
            sent2 = bot.reply_to(message, "🧐 Oh No! That Item had no results!")
        else:
            sent2 = bot.reply_to(message,
                                 "🧐 This isn't in the correct Format!\n\nPlease enter in this format: ITEM, PRICE")

        a = message.text
        if a == "/track_new":
            new(message)
        elif a == "/start":
            start(message)
        elif a == "/manage":
            manage(message)
        else:
            bot.register_next_step_handler(sent2, check)


    # -------------------- /manage RESPONSE -------------------- #
    @bot.message_handler(commands=['manage'])
    def manage(message):
        id = message.chat.id
        track_database = sqlite3.connect(f"{id}_Track.db", check_same_thread=False)
        cur = track_database.cursor()
        cur.execute(f"SELECT * FROM '{id}_Track'")
        items = cur.fetchall()
        track_database.commit()  # Obtain Track List
        if len(items) == 0:
            bot.send_message(message.chat.id,
                             "You have no tracked items!\n\nUse /track_new to track an item")
        else:
            mytable = "[#] [NAME] [PRICE]"
            count = 1
            for x in items:
                mytable += f"\n[{count}] {x[0]} - £{x[1]}"  # Generate Table
                count += 1
            sent3 = bot.send_message(message.chat.id,
                                     f"{mytable}\n\nTo delete find the corresponding row number and type 'del' before it\n\nE.g. Del 5")
            bot.register_next_step_handler(sent3, delete_item)

    def delete_item(message):
        second_check = message.text
        if second_check == "/track_new":
            new(message)
        elif second_check == "/start":
            start(message)
        elif second_check == "/manage":
            manage(message)
        else:
            response = second_check.split(" ")
            id = message.chat.id
            track_database = sqlite3.connect(f"{id}_Track.db", check_same_thread=False)
            cur = track_database.cursor()
            cur.execute(f"SELECT * FROM '{id}_Track'")
            items = cur.fetchall()
            track_database.commit()  # Obtain Track List
            if response[0] == "Del" and int(response[1]) <= len(items):
                chosen = items[int(response[1])-1]
                cur.execute(f"DELETE FROM '{id}_Track' where item = '{chosen[0]}'")
                track_database.commit()
                bot.reply_to(message, "🥳 Deleted from Track List!")
            else:
                delete_error(message)



    def delete_error(message):
        sent = bot.reply_to(message,
                            "🧐 Did you try to delete an Item? You have to type 'del' then the corresponding row number\n\nThe Correct form is: Del 5")
        a = message.text
        if a == "/track_new":
            new(message)
        elif a == "/start":
            start(message)
        elif a == "/manage":
            manage(message)
        else:
            bot.register_next_step_handler(sent, delete_item)

    bot.polling(none_stop=True)


# -------------------- ROUTINE MATCH CHECKER -------------------- #
def checker():
    """Checks if its Time to look for Matches"""
    while True:
        sleep(120)
        tp = (int(time.time()) % 86400) + 60 * 60  # Adjusts for time discrepancy
        times = [28800, 61200, 50400, 72000]  # 8am, 2pm and 8pm
        if 28700 <= tp <= 72100:  # if between 8am-8pm
            for i in times:
                if i - 60 <= tp <= i + 60:
                    Scraper()
                    sendoff()

def sendoff():
    """Sends Best 3 Matches to the User"""
    cur = ids_Database.cursor()
    cur.execute(f"SELECT * FROM ids")
    ids = cur.fetchall()  # Obtain all ids
    for i in ids:
        with open(f"{i[0]}_send", "r", encoding="utf-8") as file:
            content = file.readlines()
            if len(content) == 3:  # Then we have 3 Matches
                for x in content:
                    bot.send_message(i[0], x, parse_mode="MarkdownV2")

                    
x = threading.Thread(target=hosting, args=())
x.start()
y = threading.Thread(target=checker(), args=())
y.start()

                         
