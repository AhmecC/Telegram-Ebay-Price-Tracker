import threading, telebot, time, sqlite3, statistics
from time import sleep
from selenium import webdriver
# from selenium.webdriver.chrome.options import Options # - For Replit
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from Scrape import Scraper
from datetime import datetime

path = ""
bot_token = ""
bot = telebot.TeleBot(bot_token)

# chrome_options = Options()
# chrome_options.add_argument('--no-sandbox')
# chrome_options.add_argument('--disable-dev-shm-usage')# - For Replit

ids_Database = sqlite3.connect("ids.db", check_same_thread=False)

def TelegramHandler():
    @bot.message_handler(commands=['start'])
    def start(message):
        bot.send_message(message.chat.id,"""😎 I can help you track items on ebay, 
        so you don't have to spend hours looking for the Perfect Price! 
        💸\n\n/track_new -- Track a New Item
        \n/manage -- View/Delete your Tracked Items""")
        id = message.chat.id

        cur = ids_Database.cursor()
        cur.execute(f"SELECT * FROM ids where id = {id}")
        if cur.fetchone() == "None":
            cur.execute(f"INSERT INTO ids VALUES({id})")
            ids_Database.commit()  # Stores Unique Telegram ids

            
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
                track_database.commit()  # Adds item/price to id-specific database

    def num_results(response):
#         driver = webdriver.Chrome(options=chrome_options) # - For Replit
        driver = webdriver.Chrome(executable_path=path)
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
        items = cur.fetchall()  # Obtain tracked items
        track_database.commit()
        if len(items) == 0:
            bot.send_message(message.chat.id,
                             "You have no tracked items!\n\nUse /track_new to track an item")
        else:
            mytable = "[#] [NAME] [PRICE]"
            count = 1
            for x in items:
                mytable += f"\n[{count}] {x[0]} - £{x[1]}"  # Generate Item Table
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
            items = cur.fetchall()  # Obtain Track List
            track_database.commit()
            if response[0] == "Del" and int(response[1]) <= len(items):
                chosen = items[int(response[1])-1]
                cur.execute(f"DELETE FROM '{id}_Track' where item = '{chosen[0]}'")
                track_database.commit()  # Delete Specific item from Database
                bot.reply_to(message, "🥳 Deleted from Track List!")

                list = sqlite3.connect(f"{id}_List.db", check_same_thread=False)
                curs = list.cursor()
                curs.execute(f"DELETE FROM '{id}_List' where Name = '{chosen[0]}'")
                list.commit()
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
def daily_checker():
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
    ids = cur.fetchall()
    for i in ids:
        send_database = sqlite3.connect(f"{i[0]}_Send.db", check_same_thread=False)
        curs = send_database.cursor()
        curs.execute(f"SELECT * FROM '{i[0]}_Send'")
        ready = curs.fetchall()
        send_database.commit()

        for x in ready:
            if x[0] == "Auction":
                message = f"{x[0]} Item with {x[1]}is currently [£{x[2]}]({x[3]})"
            else:
                message = f"{x[0]} Item is [£{x[2]}]({x[3]})"
            bot.send_message(i[0], message, parse_mode="MarkdownV2")

        curs.execute(f"DELETE FROM '{i[0]}_Send'")
        send_database.commit()

def weekly_checker():
    while True:
        sleep(300)
        day = datetime.now().weekday()
        now = (int(time.time()) % 86400) + 60 * 60
        if day == 6:  # Sunday
            if 64650 <= now <= 64950:  # 6pm with 5 minute leeway
                report()


def report():
    curID = ids_Database.cursor()
    curID.execute("SELECT * FROM ids")
    ids = curID.fetchall()

    if ids != "None":
        for X in ids:  # For Each ID
            track_db = sqlite3.connect(f"{X[0]}_Track.db", check_same_thread=False)
            curTR = track_db.cursor()
            curTR.execute(f"SELECT * FROM '{X[0]}_Track'")
            trackList = curTR.fetchall()

            send_db = sqlite3.connect(f"{X[0]}_List.db", check_same_thread=False)
            curSN = send_db.cursor()
            for I in trackList:
                curSN.execute(f"SELECT * FROM '{X[0]}_List' where Name='{I[0]}'")
                items = curSN.fetchall()

                message = stats(items, I[1], I[0])

                send = ""
                for i in message:
                    if i in "=.":
                        send += f"\{i}"
                    else:
                        send += i

                bot.send_message(X[0], send, parse_mode="MarkdownV2")
                curSN.execute(f"DELETE FROM '{X[0]}_List' where Name='{I[0]}'")
                send_db.commit()


def stats(items, target, name):
    BIN = [y[2] for y in items if y[1] == "Buy it now"]
    AUC = [y[2] for y in items if y[1] == "Auction" or y[1] == "Best Offer"]

    BIN_median = round(statistics.median(BIN), 2)
    AUC_median = round(statistics.median(AUC), 2)

    BIN_cent = round((target-BIN_median)/BIN_median * 100, 2)
    AUC_cent = round((target-AUC_median)/AUC_median * 100, 2)

    if BIN_cent > 30 and AUC_cent > 25:
        a = "Increase your Target Price"
    elif BIN_cent < -30 and AUC_cent < -25:
        a = "Decrease your Target Price"
    else:
        a = "keep the same Target Price"

    message = f"""Weekly Report for: {name}\n\nMedian for BIN Items = £{BIN_median} & Auction Items = £{AUC_median}\n\nYou should {a}"""
    return message
                    
x = threading.Thread(target=TelegramHandler, args=())
x.start()
y = threading.Thread(target=daily_checker(), args=())
y.start()
z = threading.Thread(target=weekly_checker, args=())
z.start()
                         
