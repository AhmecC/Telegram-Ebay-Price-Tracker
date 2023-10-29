import sqlite3
import numpy as np
from selenium import webdriver
# from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from time import sleep
path = ""

# chrome_options = Options()
# chrome_options.add_argument('--no-sandbox')
# chrome_options.add_argument('--disable-dev-shm-usage')

db = sqlite3.connect('Telegram_Ebay.db', check_same_thread=False)
cur = db.cursor()
class Scraper:
    def __init__(self):
        self.driver = webdriver.Chrome(executable_path=path)
        self.item_list_finder()
        self.id = 1
        self.batch = 1
        self.item = 'item'

    def item_list_finder(self):
        """Obtain IDs and respective list of what they're tracking and searches for matches"""
        ids = cur.execute(f"SELECT * FROM Identifiers").fetchall()

        count = cur.execute('SELECT COUNT(*) FROM Tracked_List').fetchone()[0]
        if count != 0:
            self.batch = cur.execute('SELECT MAX(Batch) FROM Tracked_List').fetchone()[0] + 1

        if ids != "None":
            for i in ids:
                self.id = i[0]
                items = cur.execute(f'SELECT Item, Price FROM Tracked_Items WHERE Id = {self.id}').fetchall()
                if len(items) != 0:
                    for x in items:
                        self.ebay_scraper(x[0])  # Go Through Each Item for Each ID

    
    def ebay_scraper(self, item):
        """Searches item on ebay and collects raw DATA inc Hyperlink"""
        self.driver.get("https://www.ebay.co.uk/")
        self.item = item
        sleep(2)
        search = self.driver.find_element(By.XPATH, '//*[@id="gh-ac"]')
        search.send_keys(f"{self.item}")
        search.send_keys(Keys.ENTER)  # Search up item using saved name
        sleep(4)

        DATA = self.driver.find_elements(By.CLASS_NAME, "s-item")
        hyperlinks = []
        for x in range(1, 61):  # Hyperlinks not in DATA
            try:
                link = self.driver.find_element(By.XPATH, f"/html/body/div[5]/div[4]/div[2]/div[1]/div[2]/ul/li[{x}]/div/div[2]/a")
                hyperlinks.append(link.get_attribute("href"))
            except:
              try:
                  link = self.driver.find_element(By.XPATH, f"/html/body/div[5]/div[4]/div[3]/div[1]/div[2]/ul/li[{x}]/div/div[2]/a")
                  hyperlinks.append(link.get_attribute("href"))
              except:
                  pass

        # ---------- Extracting Text Data ---------- #
        TEXT_DATA = []
        count = 0
        for i in DATA[1:]:  # First item is always empty so we ignore it
            try:
                fat_txt = i.text  # Obtain full text version of each Ebay Listing
                text = fat_txt.split("\n")  # Listing seperated into sections
                text.append(hyperlinks[count])
                if count != len(hyperlinks):
                    count += 1  # Makes Sure Hyperlinks allocated to correct listing
                TEXT_DATA.append(text)  # All listings inside TEXT_DATA
            except:
                pass

        self.cleaner(TEXT_DATA)

    
    def cleaner(self, TEXT_DATA):
        """Cleans Data, only stores relevant info about item"""
        cleaned = []

        for x in TEXT_DATA:
            # OBTAIN Item_Name #
            if x[0] == "GREAT PRICE":
                name = x[1]
            elif x[0][:11] == "NEW LISTING":
                name = x[0][11:]
            else:
                name = x[0]
            # OBTAIN Total_Price #
            price = 0
            for entry in x:
                try:
                    if entry[0] == "£":
                        price += float(entry[1:])
                    if entry[0] == "+":
                        b = entry.split(" ")
                        price += float(b[1][1:])
                    if entry[0:3] == "Free":
                        price += 0
                except:
                    pass
            # OBTAIN Item_type #
            for entry in x:
                try:
                    if "bids" in entry or "bid" in entry:
                        # Also record time left
                        pos = x.index("Time left")
                        item_type = ["Auction", x[pos+1]]
                    if "Buy it now" in entry:
                        item_type = "Buy it now"
                    if "or Best Offer" in entry:
                        item_type = "Best Offer"
                except:
                    item_type = "unknown"
                    pass
            cleaned.append([item_type, name, price, x[-1]])

        self.relevance(cleaned)

    
    def relevance(self, cleaned):
        """Make Sure only relevant items are shown"""
        relevant_items = self.driver.find_element(By.CLASS_NAME, 'srp-controls__count-heading').text
        try:
            num = int(relevant_items[:3])
        except:
            num = 0

        if num == 0:
            print("No Search Results")
        else:
            try:
                cleaned = cleaned[:num]  # If num<61, we remove irrelevant search results
            except:
                pass
        self.big_list(cleaned)

    
    def big_list(self, cleaned): 
        new_identifiers = set([X[3][27:39] for X in cleaned])
        old_identifiers = set([X[0] for X in cur.execute('SELECT Identifier FROM Tracked_List').fetchall()])
        sold = list(old_identifiers - new_identifiers)
        for X in sold:
            cur.execute(f"UPDATE Tracked_List SET Status = 'SOLD' WHERE Identifier = '{X}' AND Name = '{self.item}'""")
            db.commit()

        for i in cleaned:
            try:
                if i[0][0] == "Auction":
                    time = convert_into_hours(i[0][1])
                    db.execute(
                        f"INSERT OR REPLACE INTO Tracked_List (Id, Name, Type, Price, Hyperlink, Identifier, Batch, Time, Status) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                        (self.id, self.item, i[0][0], i[2], i[3], i[3][27:39], self.batch, time, None)
                    )
                else:
                    db.execute(
                        f"INSERT OR REPLACE INTO Tracked_List (Id, Name, Type, Price, Hyperlink, Identifier, Batch, Time, Status) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                        (self.id, self.item, i[0], i[2], i[3], i[3][27:39], self.batch, None, None)
                    )
                db.commit()

            except:
                pass

def convert_into_hours(time):
    split = time.split('(')[0][:-6].split(' ')
    tot = 0

    for i in split:
        if i[-1] == 'd':
            tot += int(i[:-1]) * 24 * 60
        elif i[-1] == 'h':
            tot += int(i[:-1]) * 60
        elif i[-1] == 'm':
            tot += int(i[:-1])

    return f"{int(np.round(tot / 60))}h"
