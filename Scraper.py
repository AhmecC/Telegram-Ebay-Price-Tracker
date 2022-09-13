from selenium import webdriver
# from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from time import sleep
import os

# chrome_options = Options()
# chrome_options.add_argument('--no-sandbox')
# chrome_options.add_argument('--disable-dev-shm-usage')

ids_Database = sqlite3.connect("ids.db", check_same_thread=False)

class Scraper:
    def __init__(self):
        self.driver = webdriver.Chrome(options=chrome_options)
        self.ready_to_send = []
        self.all = []
        self.item_list_finder()
        self.item_storage()

    def item_list_finder(self):
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
                track_database.commit()  # Adds Item, Price to database
                if len(items) != 0:
                    for x in items:
                        self.ebay_scraper(x[0], float(x[1]))
                        

    def ebay_scraper(self, item, target_price):
        """Searches item on ebay and collects raw DATA inc Hyperlink"""

        # ---------- Search Item on Ebay ---------- #
        self.driver.get("https://www.ebay.co.uk/")
        self.item = item
        sleep(2)
        search = self.driver.find_element(By.XPATH, '//*[@id="gh-ac"]')
        search.send_keys(f"{self.item}")
        search.send_keys(Keys.ENTER)  # Search up item using saved name
        sleep(4)

        # ---------- Obtain Raw Item Data & Hyperlinks ---------- #
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

        self.complete_sorter(TEXT_DATA, target_price)

    def complete_sorter(self, TEXT_DATA, target_price):
        """Cleans Data, and finds matches"""

        # ---------- Reorganise to have only Relevant Data ---------- #
        ORGANISED = []
        for x in TEXT_DATA:
            # OBTAIN Item_Name #
            if x[0] == "GREAT PRICE":
                item_name = x[1]
            elif x[0][:11] == "NEW LISTING":
                item_name = x[0][11:]
            else:
                item_name = x[0]
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
            ORGANISED.append([item_type, item_name, price, x[-1]])

        # ---------- Check Num of Search Results to ensure relevant results are recorded ---------- #
        relevant_items = self.driver.find_element(By.CLASS_NAME, 'srp-controls__count-heading').text
        try:
            num = int(relevant_items[:3])
            # If num<61 then only that will be shown
            # Items >num could be irrelevant to the search
        except:
            num = 0

        # ---------- Given >0 Search Results we now find Matches ---------- #
        if num == 0:
            print("No Search Results")
        else:
            try:
                ORGANISED = ORGANISED[:num] # If num<61, we remove irrelevant search results
            except:
                pass

            # ------ Check for Satisfactory Items ------ #
            SATISFIED = []
            for i in ORGANISED:
                try:  # Auction Item satisfied if <6hrs left and <Target
                    if i[0][1][1] == "h":
                        if int(i[0][1][0]) < 6:
                            if int(i[2]) <= target_price:
                                SATISFIED.append(i)
                except:  # Item Satisfied if <Target, we ignore Best Offer Items
                    if i[0] == "Buy it now":
                        # i[0] == "Best Offer" or
                        if int(i[2]) <= target_price:
                            SATISFIED.append(i)

            # ------ Remove Dodgy Items ------ #
            for i in SATISFIED:
                print(i)
            SATISFIED = [i for i in SATISFIED if i[2] > 0.5*target_price]
            SATISFIED = sorted(SATISFIED, key=lambda x: x[2], reverse=False)  # Lowest to Highest Price

            nice = []
            for x in SATISFIED:
                price = ""
                for i in str(x[2]):
                    if i in ".":
                        price += f"\{i}"
                    else:
                        price += i

                hyper = ""
                for i in x[3]:
                    if i in "\'_*[],()~>#+-_=|!":
                        hyper += f"\{i}"
                    else:
                        hyper += i



                if x[0][0] == "Auction":
                    nice.append(f"{x[0][0]} Item with {x[0][1][:-13]}is currently [£{price}]({hyper})")
                else:
                    nice.append(f"{x[0]} Item is [£{price}]({hyper})")


            # ------ Report Back Satisfied Items ------ #
            if len(nice) >= 3:
                for i in nice[:3]:
                    self.ready_to_send.append(i)
                    print(nice)
            else:
                try:
                    for i in nice[:len(nice)]:
                        self.ready_to_send.append(i)
                        print(nice)
                except:
                    pass

            # ------ Add all items to big list ------ #
            for i in ORGANISED:
                # Appends all data to self list#
                if i[0][0] == "Auction":
                    self.all.append(f"{self.item}, {i[0][0]}, {i[1]}, {i[2]}, {i[3]}")
                else:
                    self.all.append(f"{self.item}, {i[0]}, {i[1]}, {i[2]}, {i[3]}")

#     def item_storage(self):
#         """IRRELEVANT FOR NOW"""

#         if os.stat(f"{self.id}_item_list").st_size == 0:
#             with open(f"{self.id}_item_list", "a", encoding="utf-8") as file:
#                 file.write(f"UserPrompt, ItemType, ItemName, ItemPrice, ItemLink")  # Checks if file is empty and then creates headings
#                 for i in self.all:
#                     file.write(f"\n{i}")

#         else:
#             with open(f"{self.id}_item_list", "r", encoding="utf-8") as file:
#                 repeat = []
#                 for i in self.all:
#                     comparable_links = []
#                     for x in file.readlines()[1:]:  # Compares Hyperlinks to see if they're the same
#                         comparable_links.append(x.split(", ")[-1])

#                     if i.split(", ")[-1] not in comparable_links:
#                         repeat.append(i)
#                     if i.split(", ")[-1] in comparable_links:
#                         repeat.append(i)
#                         # Everything in repeat will stay in file, otherwise its deleted

#             with open(f"{self.id}_item_list", "w", encoding="utf-8") as f:
#                 f.write(f"UserPrompt, ItemType, ItemName, ItemPrice, ItemLink")

#             with open(f"{self.id}_item_list", "a", encoding="utf-8") as fp:
#                 for i in repeat:
#                     fp.write(f"\n{i}")


