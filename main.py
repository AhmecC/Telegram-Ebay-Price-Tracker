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

db = sqlite3.connect('Telegram_Ebay.db', check_same_thread=False)
cur = db.cursor()

def TelegramHandler():
    @bot.message_handler(commands=['start'])
    def start(message):  # Start Message for New Users
        bot.send_message(message.chat.id, """😎 I can help you track items on ebay, 
        so you don't have to spend hours looking for the Perfect Price! 
        💸\n\n/track_new -- Track a New Item
        \n/manage -- View/Delete your Tracked Items""")
        ID = message.chat.id

        Unique = cur.execute(f"SELECT * FROM Identifiers where Id = {ID}").fetchone()
        if Unique is None:
            cur.execute(f"INSERT INTO Identifiers VALUES({ID})")  # Store Unique Telegram IDs
            db.commit()

            
    @bot.message_handler(commands=['track_new'])
    def new(message):
        ADD_NEW = bot.send_message(message.chat.id, "🧐 Specify the Item to be Tracked and your Target Price, "
                                                    "separated by a Comma. Be Specific!"
                                                    "\n\nE.g. Pixel 7 Pro 256gb, 600")

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
            response = message.text.split(", ")  # Check id Add_New is in correct format
            num = num_results(response)
            if len(response) != 2 or response[1].isdigit() is False or num == 0:
                no_comma_error(message, num)  # Error if response has formatting issues
            else:
                bot.reply_to(message, "🥳 Added to Track List!")
                ID = message.chat.id
                cur.execute(f"INSERT INTO Tracked_Items VALUES ('{ID}', '{response[0]}', '{response[1]}')")
                db.commit()  # Adds ID/Item/Price to Tracked_Items

    def num_results(response):  # Check if Item exists
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
        ID = message.chat.id
        items = cur.execute(f"SELECT Item, Price FROM Tracked_Items WHERE Id = {ID}").fetchall() # Obtain Tracked Items

        if len(items) == 0:
            bot.send_message(message.chat.id,
                             "You have no tracked items!\n\nUse /track_new to track an item")
        else:
            mytable = "[#] [NAME] [PRICE]"
            count = 1
            for x in items:
                mytable += f"\n[{count}] {x[0]} - £{x[1]}"  # Generates Visual Item-Price Table for given ID
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
            ID = message.chat.id
            items = cur.execute(f"SELECT Item, Price FROM Tracked_Items WHERE Id = {ID}").fetchall() # Get Tracked Items

            if response[0] == "Del" and int(response[1]) <= len(items):
                bot.send_message(message.chat.id, "🥳 Deleted from Track List!")
                chosen = items[int(response[1])-1]

                cur.execute(f"DELETE FROM Tracked_Items WHERE Item = '{chosen[0]}' AND Id = '{ID}'")
                db.commit()  # Delete Specified Item from being Tracked
                cur.execute(f"DELETE FROM Tracked_List WHERE Name = '{chosen[0]}' AND Id = '{ID}'")
                db.commit()  # Delete instances for Tracked_List.db

            else:
                delete_error(message)  # If not in correct format



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

    bot.polling(none_stop=True)  # Waits Non-Stop for Messages


# -------------------- ROUTINE MATCH CHECKER -------------------- #
def daily_checker():  # Checks Items at 8am, 2pm and 6pm
    while True:
        sleep(120)
        tp = (int(time.time()) % 86400) + 60 * 60  # Adjusts for time discrepancy
        times = [28800, 50400, 72000]
        if 28700 <= tp <= 72100:
            for i in times:
                if i - 60 <= tp <= i + 60:
                    Scraper()
                    sendoff()


def sendoff():  # Sends Best 3 Matches to User
    ids = cur.execute(f'SELECT * FROM Identifiers').fetchall()
    for ID in ids:
        items = cur.execute(f"SELECT Item, Price FROM Tracked_Items WHERE Id = '{ID[0]}'").fetchall()

        for Item in items:
            lower = float(0.5 * int(Item[1]))
            upper = float(Item[1])

            matches = cur.execute(f"""SELECT Type, Time, Price, Hyperlink FROM Tracked_List WHERE Id = '{ID[0]}' AND Name = '{Item[0]}' AND Status IS NULL
                AND ((Type = 'Auction' AND Price BETWEEN '{lower}' AND '{upper}' AND CAST(SUBSTR(Time, 1, LENGTH(Time) - 1) AS INTEGER) <= 6) OR (Type = 'Buy it now' AND Price BETWEEN '{lower}' AND '{upper}'))
                ORDER BY Price ASC LIMIT 3""",).fetchall()

            for X in matches:
                price = fix(X[2])
                hyper = fix(X[3])

                if X[0] == 'Auction':
                    message = f"{X[0]} Item with {X[1]} left is currently [£{price}]({hyper})"
                else:
                    message = f"{X[0]} Item is [£{price}]({hyper})"
                bot.send_message(ID[0], message, parse_mode='MarkdownV2')


def fix(txt):  # message must be in specific format
    out = ""
    for i in str(txt):
        if i in "\_*[],()~>#+-_=|!.'":
            out += f"\{i}"
        else:
            out += i
    return out


def weekly_checker():  # 6pm Sunday sends weekly report
    while True:
        sleep(300)
        day = datetime.now().weekday()
        now = (int(time.time()) % 86400) + 60 * 60
        if day == 6:  # Sunday
            if 64650 <= now <= 64950 # 6pm with 5 minute leeway
                report()


def report():  # Gives guidance on if target price is too high/low or okay
    ids = cur.execute('SELECT * FROM Identifiers')

    if ids != 'None':
        for ID in ids:
            items = cur.execute(f"SELECT Item, Price FROM Tracked_Items WHERE Id = '{ID[0]}'").fetchall()
            for Item in items:
                BIN = cur.execute(
                    f"SELECT Price FROM Tracked_List WHERE Id = '{ID[0]}' AND Name = '{Item[0]}' AND Type = 'Buy it now'").fetchall()
                AUC = cur.execute(
                    f"SELECT Price FROM Tracked_List WHERE Id = '{ID[0]}' AND Name = '{Item[0]}' AND (Type = 'Auction' OR Type = 'Best Offer')").fetchall()

                message = stats(BIN, AUC, Item[1])
                send = fix(f"You should {message} for {Item[0]} with target price £{Item[1]}")

                bot.send_message(ID[0], send, parse_mode="MarkdownV2")
                cur.execute(f"DELETE FROM Tracked_List WHERE Id = '{ID[0]}' AND Name = '{Item[0]}'")
                db.commit()


def stats(BIN, AUC, target):
    BIN = round(statistics.median([X[0] for X in BIN]), 2)
    AUC = round(statistics.median([X[0] for X in AUC]), 2)

    BIN_perc = round((target - BIN) / BIN * 100, 2)
    AUC_perc = round((target - BIN) / AUC * 100, 2)

    if BIN_perc > 30 and AUC_perc > 25:
        a = "Increase your Target Price"
    elif BIN_perc < -30 and AUC_perc < -25:
        a = "Decrease your Target Price"
    else:
        a = "keep the same Target Price"
    return a
                    
x = threading.Thread(target=TelegramHandler, args=())
x.start()
y = threading.Thread(target=daily_checker(), args=())
y.start()
z = threading.Thread(target=weekly_checker, args=())
z.start()
                         
