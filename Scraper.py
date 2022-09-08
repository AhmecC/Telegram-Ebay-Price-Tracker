from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from time import sleep
import os
path = "CHROMEDRIVER PATH"


class Scraper:
    def __init__(self):
        self.driver = webdriver.Chrome(executable_path=path)
        self.all = []
        self.item_list_finder()
        self.item_storage()

        
    def item_list_finder(self):
        """Obtain IDs and respective list of what they're tracking and searches for matches"""
        with open("Ids", "r") as file:
            IDs = file.readlines()
            if len(IDs) != 0:  # Proceed only if ID is inside
                for i in IDs:
                    self.id = i
                    with open(f"{i}_Track", "r") as f:
                        items = f.readlines()
                        if len(items) != 0 or len(items) != 1:  # Proceed if list has items
                            for i in items[1:]:  # Don't include Header
                                A = i.split(", ")
                                self.ebay_scraper(A[1], float(A[2]))  # Send Item and Price to actual info gatherer

                                
    def ebay_scraper(self, item, target_price):
        """Searches item on ebay and collects data inc Hyperlink"""

        self.driver.get("https://www.ebay.co.uk/")
        self.item = item
        sleep(2)
        search = self.driver.find_element(By.XPATH, '//*[@id="gh-ac"]')
        search.send_keys(f"{self.item}")
        search.send_keys(Keys.ENTER)  # Search up item using saved name
        sleep(4)

        data = self.driver.find_elements(By.CLASS_NAME, "s-item")  # Data found from website
        hyperlinks = []
        for x in range(1, 61):  # Hyperlinks not in data, so we find here
            try:
                link = self.driver.find_element(By.XPATH, f"/html/body/div[5]/div[4]/div[2]/div[1]/div[2]/ul/li[{x}]/div/div[2]/a")
                hyperlinks.append(link.get_attribute("href"))
            except:
                pass

        item_info = []
        count = 0
        for entry in data[1:]:  # First item is always empty so we ignore that
            try:
                info = entry.text  # Get text of each data variable
                form = info.split("\n")  # Create a list of data variable
                form.append(hyperlinks[count])
                if count != len(hyperlinks):
                    count += 1  # Makes sure hyperlinks are allocated to correct data piece
                item_info.append(form)
            except:
                pass

        self.item_sorter(item_info, target_price)

        
    def item_sorter(self, itms, target_price):
        """Stores relevant info for item, and if any results are yielded we move to checker()"""
        all_organised = []
        for x in itms:

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

            all_organised.append([item_type, item_name, price, x[-1]])

        # CHECK NUMBER OF SEARCH RESULTS #
        relevant_items = self.driver.find_element(By.CLASS_NAME, 'srp-controls__count-heading').text
        try:
            num = int(relevant_items[:3])  # If there is < 61 search results it will give only those results
        except:
            num = 0

        if num != 0:
            try:
                check_items = all_organised[:num]
                print(check_items)
            except:
                check_items = all_organised
            self.checker(check_items, target_price)
        else:
            print("No Search Results")  # Create a Proper Error handler

            
    def checker(self, items, target_price):
        """Checks if Items satisfy demands of user"""
        for i in items:
            # Appends all data to self list#
            if i[0][0] == "Auction":
                self.all.append(f"{self.item}, {i[0][0]}, {i[1]}, {i[2]}, {i[3]}")
            else:
                self.all.append(f"{self.item}, {i[0]}, {i[1]}, {i[2]}, {i[3]}")

        satisfied = []

        for i in items:
            try:
                if i[0][1][1] == "h":
                    if int(i[0][1][0]) < 6:
                        if int(i[2]) <= target_price:
                            satisfied.append(i)
                            # Auction item satisfied if <Target_£ & <6hrs left #
            except:
                if i[0] == "Best Offer" or i[0]== "Buy it now":
                    if int(i[2]) <= target_price:
                        satisfied.append(i)
                        # Item satisfied if <Target_£ #

        # REPORT BACK SATISFIED ITEMS (IF ANY) #
        if len(satisfied) == 0:
            print("No Matches")
        else:
            for i in satisfied:
                print(i)

                
#     def item_storage(self):
#         """THIS FUNCTION DOESNT WORK"""

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
