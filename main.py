import os
import telebot

bot_token = ""
bot = telebot.TeleBot(bot_token)

# -------------------- /start RESPONSE -------------------- #
@bot.message_handler(commands=['start'])
def info(message):
    bot.send_message(message.chat.id, "😎 I can help you track items on ebay, so you don't have to spend hours looking for the perfect price 💸"
                                      "\n\n/track_new -- Track a New Item"
                                      "\n/manage -- View/Delete your Tracked Items")

    
# -------------------- /track_new RESPONSE -------------------- #
@bot.message_handler(commands=['track_new'])
def new_item(message):
    sent = bot.send_message(message.chat.id, "🧐 Specify the Item to be Tracked and your Target Price, seperated by a Comma. Be Specific!\n\nE.g. Ipad Pro 2020 11 inch, 400")
    bot.register_next_step_handler(sent, check_item)
    # Inform format to track items and refers to check_item ater user replies

def check_item(message):
    response = message.text.split(", ")
    if len(response) != 2:
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
    sent = bot.reply_to(message, "🧐 No Comma Found!\n\nPlease enter in this format: Ipad Pro 2020 11 inch, 400")
    bot.register_next_step_handler(sent, check_item)

        
# -------------------- /manage RESPONSE -------------------- #
@bot.message_handler(commands=['manage'])
def manage_items(message):
    chat_id = message.chat.id
    if os.stat(f"{chat_id}_Items").st_size == 0:
        bot.send_message(message.chat.id, "You have no tracked items!\n\nUse /track_new to track an item")

    with open(f"{chat_id}_Items", "r") as file:
        mytable = file.read()
        sent = bot.send_message(message.chat.id, f"{mytable}\n\nTo delete find the corresponding row number and type 'del' before it\n\nE.g. del 5")
        bot.register_next_step_handler(sent, delete_item)

def delete_item(message):
    response = message.text.split(" ")
    chat_id = message.chat.id
    if response[0] == "del":
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
            delete_error(message)
    else:
        delete_error(message)

def delete_error(message):
    sent = bot.reply_to(message, "🧐 Did you try to delete a message? You have to type 'del' then the corresponding row number\n\nThe Correct form is: del 5")
    bot.register_next_step_handler(sent, delete_item)

    
bot.polling()
