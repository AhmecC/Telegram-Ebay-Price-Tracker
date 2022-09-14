import sqlite3
from selenium import webdriver
# from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from time import sleep
path = ""

# chrome_options = Options()
# chrome_options.add_argument('--no-sandbox')
# chrome_options.add_argument('--disable-dev-shm-usage')

ids_Database = sqlite3.connect("ids.db", check_same_thread=False)

class Scraper:
    def __init__(self):
#         self.driver = webdriver.Chrome(options=chrome_options)  # - Replit
        self.driver = webdriver.Chrome(executable_path=path)
        self.item_list_finder()

    def item_list_finder(self):
        """Obtain IDs and respective list of what they're tracking and searches for matches"""
        cur = ids_Database.cursor()
        cur.execute(f"SELECT * FROM ids")
        ids = cur.fetchall()  # Obtain all ids
        if ids != "None":
            for i in ids:
                self.id = i[0]
                track_database = sqlite3.connect(f"{self.id}_Track.db", check_same_thread=False)
                cur = track_database.cursor()
                cur.execute(f"SELECT * FROM '{self.id}_Track'")
                items = cur.fetchall()
                track_database.commit()  # Obtain Item/Price
                if len(items) != 0:
                    for x in items:
                        self.ebay_scraper(x[0], float(x[1]))  # Go Through Each Item for Each ID
                        
    def ebay_scraper(self, item, target_price):
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

        self.cleaner(TEXT_DATA, target_price)

    def cleaner(self, TEXT_DATA, target_price):
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

        self.relevance(cleaned, target_price)
        self.big_list(cleaned)

    def relevance(self, cleaned, target_price):
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

        self.satisfactory(cleaned, target_price)

    def satisfactory(self, cleaned, target_price):
        """Sorts out so only items that satisfy conditions are left"""
        satisfied = []
        for i in cleaned:
            try:  # Auction Item satisfied if <6hrs left and <Target
                if i[0][1][1] == "h":
                    if int(i[0][1][0]) < 6:
                        if int(i[2]) <= target_price:
                            satisfied.append(i)
            except:  # Item Satisfied if <Target, we ignore Best Offer Items
                if i[0] == "Buy it now":
                    # i[0] == "Best Offer" or
                    if int(i[2]) <= target_price:
                        satisfied.append(i)

        satisfied = [i for i in satisfied if i[2] > 0.5*target_price]
        satisfied = sorted(satisfied, key=lambda x: x[2], reverse=False)  # Lowest to Highest Price

        self.ready_for_send(satisfied)

    def ready_for_send(self, satisfied):
        """Make sure formatted properly for telegram message"""
        send_database = sqlite3.connect(f"{self.id}_Send.db", check_same_thread=False)
        cur = send_database.cursor()

        nice = []
        for x in satisfied:
            # Fix Price #
            price = ""
            for i in str(x[2]):
                if i in ".":
                    price += f"\{i}"
                else:
                    price += i
            # Fix Hyperlink #
            hyper = ""
            for i in x[3]:
                if i in "\'_*[],()~>#+-_=|!":
                    hyper += f"\{i}"
                else:
                    hyper += i

            if x[0][0] == "Auction":
                nice.append(f"('{x[0][0]}', '{x[0][1][:-13]}', '{price}', '{hyper}')")
            else:
                nice.append(f"('{x[0]}', '?', '{price}', '{hyper}')")

        # the chosen ones #
        if len(nice) >= 3:
            for i in nice[:3]:
                cur.execute(f"INSERT INTO '{self.id}_Send' VALUES {i}")
                send_database.commit()
        else:
            try:
                for i in nice[:len(nice)]:
                    cur.execute(f"INSERT INTO '{self.id}_Send' VALUES {i}")
                    send_database.commit()
            except:
                pass

    def big_list(self, cleaned):
        list_database = sqlite3.connect(f"{self.id}_List.db", check_same_thread=False)
        cur = list_database.cursor()
        for i in cleaned:
            try:
                if i[0][0] == "Auction":
                    cur.execute(f"INSERT INTO '{self.id}_List' VALUES('{self.item}', '{i[0][0]}', '{i[2]}', '{i[3]}', '{i[3][27:39]}')")
                else:
                    cur.execute(f"INSERT INTO '{self.id}_List' VALUES('{self.item}', '{i[0]}', '{i[2]}', '{i[3]}', '{i[3][27:39]}')")
                list_database.commit()
            except:
                pass
