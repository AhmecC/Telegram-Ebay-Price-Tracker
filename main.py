import os
import telebot

bot_token = "TELEGRAM BOT TOKEN"
bot = telebot.TeleBot(bot_token)

# -------------------- /start RESPONSE -------------------- #
@bot.message_handler(commands=['start'])
def info(message):
    bot.send_message(message.chat.id, "😁 I can help you track items on ebay, so you don't have to spend hours looking for the perfect price"
                                      "\n\n/track_new - track a new item"
                                      "\n/manage - view/delete your tracked items")

    
# -------------------- /track_new RESPONSE -------------------- #
@bot.message_handler(commands=['track_new'])
def new_item(message):
    sent = bot.send_message(message.chat.id, "🧐 Enter the Item you would like to Track followed by your Target Price, please be specific \n\nE.G. Ipad Pro 2020 11 inch, 400")
    bot.register_next_step_handler(sent, check_item)
    # Inform format to track items and refers to check_item ater user replies

def no_comma_error(message):
    sent = bot.send_message(message.chat.id, "🧐 No comma was found!\n\n Please enter in this format: Ipad Pro 2020 11 inch, 400")
    bot.register_next_step_handler(sent, check_item)

def check_item(message):
    info = message.text.split(", ")
    if len(info) != 2:
        no_comma_error(message)  # If not formatted correctly, informs them and lets them send again
    else:
        bot.reply_to(message, "🥳Added to Track List")

    # NEED ADDITIONAL VERIFICATION FOR IF ITEM YIELDS ANY RESULTS

    request = message.text
    chat_id = message.chat.id
    with open(f"{chat_id}_Items","a") as file:
        if os.stat(f"{chat_id}_Items").st_size == 0:  # Checks if file is empty and then creates headings
            file.write(f"ITEM, PRICE")

        file.write(f"\n{message.text}")

        
# -------------------- /manage RESPONSE -------------------- #
@bot.message_handler(commands=['manage'])
def manage_items(message):
    chat_id = message.chat.id
    if os.stat(f"{chat_id}_Items").st_size == 0:
        bot.send_message(message.chat.id, "You have no tracked items!\n\nUse /track_new to track an item")


    with open(f"{chat_id}_Items", "r") as file:
        mytable = file.read()
        bot.send_message(message.chat.id, mytable)


bot.polling()

