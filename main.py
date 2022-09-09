import os
import threading
import telebot
import time
from time import sleep
from selenium import webdriver
# from selenium.webdriver.chrome.options import Options # - For Replit
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from Scrape import Scraper
path = r"C:\Users\aqeel\OneDrive\Desktop\Code\chromedriver.exe"
bot_token = "5564448511:AAHM64pB01SaRkilGu4mexIZVRrMB2urrA8"
bot = telebot.TeleBot(bot_token)

# chrome_options = Options()
# chrome_options.add_argument('--no-sandbox')
# chrome_options.add_argument('--disable-dev-shm-usage')# - For Replit

# -------------------- TELEGRAM HANDLER -------------------- #
def hosting():
    # -------------------- /start RESPONSE -------------------- # ALL GOOD
    @bot.message_handler(commands=['start'])
    def start(message):
        """/start sends instructions and stores Chat ID"""
        bot.send_message(message.chat.id,
                         "😎 I can help you track items on ebay, "
                         "so you don't have to spend hours looking for the Perfect Price! 💸"
                         "\n\n/track_new -- Track a New Item"
                         "\n/manage -- View/Delete your Tracked Items")

        # ------ STORE USER ID ------ #
        ID = message.chat.id
        with open("Ids", "a+") as file:
            ids = file.readlines()
            if ID not in ids:
                file.write(f"\n{ID}")

    # -------------------- /track_new RESPONSE -------------------- # ALL GOOD
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
                chat_id = message.chat.id
                with open(f"{chat_id}_Track", "a") as file:
                    if os.stat(f"{chat_id}_Track").st_size == 0:
                        file.write(f"[#], ITEM, PRICE")  # Checks if file is empty and then creates headings
                with open(f"{chat_id}_Track", "r") as f:
                    a = len(f.readlines())  # Length of file is used to number the entries
                with open(f"{chat_id}_Track", "a") as fil:
                    fil.write(f"\n[{a}], {message.text}")

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
        chat_id = message.chat.id
        with open(f"{chat_id}_Track", "r") as file:
            length = len(file.readlines())

        if os.stat(f"{chat_id}_Track").st_size == 0 or length == 1:
            bot.send_message(message.chat.id,
                             "You have no tracked items!\n\nUse /track_new to track an item")  # If nothing in file or just the title
        else:
            with open(f"{chat_id}_Track", "r") as file:
                mytable = file.read()
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
            with open(f"{ID}_Track", "r") as file:
                length = len(file.readlines())
                if response[0] == "Del" and int(response[1]) <= length:
                    A = file.readlines()
                    B = A[int(response[1])]
                    A.remove(B)
                    with open(f"{ID}_Track", "w") as f:
                        f.write("[#], ITEM, PRICE")
                        A.remove("[#], ITEM, PRICE\n")  # remove the title from a, as we just added it to file

                    try:
                        with open(f"{ID}_Track", "a") as fp:
                            count = 1
                            for i in A:
                                y = i[2:]
                                fp.write(f"\n[{count}{y}")
                                count += 1
                    except:
                        pass
                    bot.reply_to(message, "🥳 Deleted from Track List!")
                else:
                    delete_error(message)



    def delete_error(message):
        sent = bot.reply_to(message,
                            "🧐 Did you try to delete a message? You have to type 'del' then the corresponding row number\n\nThe Correct form is: Del 5")
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
    with open(f"Ids", "r", encoding="utf-8") as f:
        IDs = f.readlines()  # Obtain IDs to open send files
        for ID in IDs:
            with open(f"{ID}_send", "r", encoding="utf-8") as file:
                content = file.readlines()
                if len(content) == 3:  # Then we have 3 Matches
                    for x in content:
                        bot.send_message(ID, x, parse_mode="MarkdownV2")

x = threading.Thread(target=hosting, args=())
x.start()
y = threading.Thread(target=checker(), args=())
y.start()

                         
