import os
import telebot
import time
from time import sleep
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from Scrape import Scraper
path = "CHROMEDRIVER PATH"
bot_token = ""
bot = telebot.TeleBot(bot_token)


a = True
while a:
    
    # -------------------- /start RESPONSE -------------------- #
    @bot.message_handler(commands=['start']
    def info(message):
        """If /start is sent, then an Info message is returned. Their Chat ID is stored if a new user"""
        bot.send_message(message.chat.id,
                         "😎 I can help you track items on ebay, "
                         "so you don't have to spend hours looking for the Perfect Price! 💸"
                         "\n\n/track_new -- Track a New Item"
                         "\n/manage -- View/Delete your Tracked Items")
        x = message.chat.id  # Record User ID and add to file
        with open("Ids", "a+") as file:
            ids = file.readlines()
            if x not in ids:
                file.write(f"\n{x}")


    # -------------------- /track_new RESPONSE -------------------- #
    @bot.message_handler(commands=['track_new'])
    def new_item(message):
        """If /track new is selected:
        - Instructions on how to add message is sent
        - ADD_NEW records their response, and check_item() verifies if its correct format"""

        ADD_NEW = bot.send_message(message.chat.id, "🧐 Specify the Item to be Tracked and your Target Price, "
                                                    "separated by a Comma. Be Specific!"
                                                    "\n\nE.g. Ipad Pro 2020 11 inch, 400")
        bot.register_next_step_handler(ADD_NEW, check_item)


    def check_item(message):
        """Prompts Re-input if: Wrong Format, Price not an integer, No Search Results for their item
        Successful if: Correct Format, /manage or /start entered"""
                         
        response = message.text.split(", ")
        try:
            num = results(response)
        except:
            num = 0

        if len(response) != 2 or response[1].isdigit() == False or num == 0:
            # Allows 'escape' of section, or goes to error checker #
            a = message.text
            if a == "/track_new":
                new_item(message)
            elif a == "/start":
                info(message)
            elif a == "/manage":
                manage_items(message)
            else:
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


    def results(response):
        """This checks if item yields any results"""

        # Search Up item #
        driver = webdriver.Chrome(executable_path=path)
        driver.get("https://www.ebay.co.uk/")
        sleep(2)
        search = driver.find_element(By.XPATH, '//*[@id="gh-ac"]')
        search.send_keys(response[0])
        search.send_keys(Keys.ENTER)
        sleep(2)

        # Check how many results there are #
        num_results = driver.find_element(By.CLASS_NAME, 'srp-controls__count-heading').text
        try:
            num = int(num_results[:3])
        except:
            num = 0

        return num


    def no_comma_error(message, num):
        """Handles error message and allows user to go again (or stop)"""
        if num == 0:
            sent2 = bot.reply_to(message, "🧐 Oh No! That Item had no results!")
        else:
            sent2 = bot.reply_to(message,
                                 "🧐 This isn't in the correct Format!\n\nPlease enter in this format: ITEM, PRICE")
        a = message.text
        if a == "/track_new":
            new_item(message)
        elif a == "/start":
            info(message)
        elif a == "/manage":
            manage_items(message)
        else:
            bot.register_next_step_handler(sent2, check_item)


    # -------------------- /manage RESPONSE -------------------- #
    @bot.message_handler(commands=['manage'])
    def manage_items(message):
        """User selects /manage. If no items and just header in file, then informs them
        Otherwse prints out table for them to visualise items"""

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
        """User can delete item, and this fixes ID_Track.txt format"""

        a = message.text
        response = a.split(" ")
        chat_id = message.chat.id
        with open(f"{chat_id}_Track", "r") as file:
            length = len(file.readlines())
            if response[0] == "Del" or int(response[1]) <= length:
                a = file.readlines()
                b = a[int(response[1])]
                a.remove(b)
                with open(f"{chat_id}_Track", "w") as f:
                    f.write("[#], ITEM, PRICE")
                    a.remove("[#], ITEM, PRICE\n")  # remove the title from a, as we just added it to file

                try:
                    with open(f"{chat_id}_Track", "a") as fp:
                        count = 1
                        for i in a:
                            y = i[2:]
                            fp.write(f"\n[{count}{y}")
                            count += 1
                except:
                    pass
                bot.reply_to(message, "🥳 Deleted from Track List!")

            else:
                if a == "/track_new":
                    new_item(message)
                elif a == "/start":
                    info(message)
                elif a == "/manage":
                    manage_items(message)
                else:
                    delete_error(message)


    def delete_error(message):
        sent = bot.reply_to(message,
                            "🧐 Did you try to delete a message? You have to type 'del' then the corresponding row number\n\nThe Correct form is: Del 5")
        a = message.text
        if a == "/track_new":
            new_item(message)
        elif a == "/start":
            info(message)
        elif a == "/manage":
            manage_items(message)
        else:
            bot.register_next_step_handler(sent, delete_item)


    def checker():
        tp = (int(time.time()) % 86400) + 60 * 60  # Adjusts for time discrepancy
        print(tp)
        times = [28800, 50400, 42780, 72000] # 8am, 2pm and 8pm

        if 28700 <= tp <= 72100:  # if between 8am-8pm
            for i in times:
                if i - 60 <= tp <= i + 60:
                    Scraper()

    checker()
    bot.polling()


























# -------------------- /start RESPONSE -------------------- #
@bot.message_handler(commands=['start'])
def info(message):
    bot.send_message(message.chat.id, "😎 I can help you track items on ebay, so you don't have to spend hours looking for the perfect price 💸"
                                      "\n\n/track_new -- Track a New Item"
                                      "\n/manage -- View/Delete your Tracked Items")


# -------------------- /track_new RESPONSE -------------------- #
@bot.message_handler(commands=['track_new'])
def new_item(message):
    global sent1
    sent1 = bot.send_message(message.chat.id, "🧐 Specify the Item to be Tracked and your Target Price, seperated by a Comma. Be Specific!\n\nE.g. Ipad Pro 2020 11 inch, 400")
    bot.register_next_step_handler(sent1, check_item)
    # Inform format to track items and refers to check_item ater user replies


def check_item(message):
    response = message.text.split(", ")
    if len(response) != 2:
        a = message.text
        if a == "/track_new":
            new_item(message)
        elif a == "/start":
            info(message)
        elif a == "/manage":
            manage_items(message)
        else:
            no_comma_error(message)  # If not formatted correctly, informs them and lets them send again
    else:
        bot.reply_to(message, "🥳 Added to Track List!")
        chat_id = message.chat.id
        with open(f"{chat_id}_Items","a") as file:
            if os.stat(f"{chat_id}_Items").st_size == 0:
                file.write(f"ITEM, PRICE")  # Checks if file is empty and then creates headings

            with open(f"{chat_id}_Items","r") as f:
                A = len(f.readlines())
            file.write(f"\n[{A}], {message.text}")


def no_comma_error(message):
    sent2 = bot.reply_to(message, "🧐 No Comma Found!\n\nPlease enter in this format: Ipad Pro 2020 11 inch, 400")
    a = message.text
    if a == "/track_new":
        new_item(message)
    elif a == "/start":
        info(message)
    elif a == "/manage":
        manage_items(message)
    else:
        bot.register_next_step_handler(sent2, check_item)


# -------------------- /manage RESPONSE -------------------- #
@bot.message_handler(commands=['manage'])
def manage_items(message):
    print("10")
    global sent3
    chat_id = message.chat.id
    if os.stat(f"{chat_id}_Items").st_size == 0:
        bot.send_message(message.chat.id, "You have no tracked items!\n\nUse /track_new to track an item")

    with open(f"{chat_id}_Items", "r") as file:
        mytable = file.read()
        sent3 = bot.send_message(message.chat.id, f"{mytable}\n\nTo delete find the corresponding row number and type 'del' before it\n\nE.g. Del 5")
        bot.register_next_step_handler(sent3, delete_item)


def delete_item(message):
    response = message.text.split(" ")
    a = message.text
    chat_id = message.chat.id
    if response[0] == "Del":
        try:
            with open(f"{chat_id}_Items", "r") as file:
                a = file.readlines()
                b = a[int(response[1])]
                a.remove(b)
                with open(f"{chat_id}_Items", "w") as f:
                    for i in a:
                        f.write(i)
                bot.reply_to(message, "🥳 Deleted from Track List!")
        except:
            if a == "/track_new":
                new_item(message)
            elif a == "/start":
                info(message)
            elif a == "/manage":
                manage_items(message)
            else:
                delete_error(message)
    else:
        if a == "/track_new":
            new_item(message)
        elif a == "/start":
            info(message)
        elif a == "/manage":
            manage_items(message)
        else:
            delete_error(message)


def delete_error(message):
    sent = bot.reply_to(message, "🧐 Did you try to delete a message? You have to type 'del' then the corresponding row number\n\nThe Correct form is: Del 5")
    a = message.text
    if a == "/track_new":
        new_item(message)
    elif a == "/start":
        info(message)
    elif a == "/manage":
        manage_items(message)
    else:
        bot.register_next_step_handler(sent, delete_item)


bot.polling()
