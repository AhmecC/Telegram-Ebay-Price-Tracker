# Telegram-Ebay-Price-Tracker

Description:
> This bot allows users to type in a product and a target price. The bot will then periodically search the item on ebay and see if it satisfies the target price. For Buy-it-now items the user will be notified straight away (with a link sending them to the item). For Auction items the user will only be notified when there is six hours left of the Auction and it still satisfies the target price. It will include the postage price in the total price that is compared with the target. The bot allows you to see your tracked items and also delete them if need be. This bot is hosted on Replit (paid) and is intended to run 24/7

**Upcoming Functionality:**
- /manage Output to look nicer
- /track_new checks how many search results there are (if 0 it won't track it, if < 20 it will ask if user is sure, if > 20 no notifying needed)
- Actual Track Functionality

**Fixes:**
- Fixed Issue where upon selection an option (/track_new) users could not move to another section (i.e. /manage)
