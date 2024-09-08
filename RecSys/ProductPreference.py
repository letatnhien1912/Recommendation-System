from surprise import Dataset
from surprise import Reader

import os
import csv

from collections import defaultdict

class ProductInfo:

    def __init__(self):
        # Resolve the base path relative to the module location
        base_path = os.path.dirname(os.path.abspath(__file__))
        # Define paths to the datasets relative to the module location
        self.rating_dataset = os.path.join(base_path, '../dataset/rating_dataset.csv')
        self.product_dataset = os.path.join(base_path, '../dataset/product_dataset.csv')
        self.purchase_dataset = os.path.join(base_path, '../dataset/purchase_dataset.csv')

        self.productID_to_name = {}
        self.name_to_productID = {}
    
    def loadRatingData(self):
        ratingsDataset = 0
        self.productID_to_name = {}
        self.name_to_productID = {}

        reader = Reader(line_format='user item rating', sep=',', skip_lines=1)

        ratingsDataset = Dataset.load_from_file(self.rating_dataset, reader=reader)

        with open(self.product_dataset, newline='', encoding='ISO-8859-1') as csvfile:
                productReader = csv.reader(csvfile)
                next(productReader)  #Skip header line
                for row in productReader:
                    productID = int(row[0])
                    productName = row[1]
                    self.productID_to_name[productID] = productName
                    self.name_to_productID[productName] = productID

        return ratingsDataset
    
    def getUserRatings(self, user):
        userRatings = []
        hitUser = False
        with open(self.rating_dataset, newline='') as csvfile:
            ratingReader = csv.reader(csvfile)
            next(ratingReader)
            for row in ratingReader:
                userID = int(row[0])
                if (user == userID):
                    productID = int(row[1])
                    rating = float(row[2])
                    userRatings.append((productID, rating))
                    hitUser = True
                if (hitUser and (user != userID)):
                    break

        return userRatings

    def getPopularityRanks(self):
        ratings = defaultdict(int)
        rankings = defaultdict(int)
        with open(self.rating_dataset, newline='') as csvfile:
            ratingReader = csv.reader(csvfile)
            next(ratingReader)
            for row in ratingReader:
                try:
                    productID = int(float(row[1]))  # Convert to float first, then to int
                    ratings[productID] += 1
                except ValueError:
                    print(f"Skipping row with invalid productID: {row[1]}")
        rank = 1
        for productID, ratingCount in sorted(ratings.items(), key=lambda x: x[1], reverse=True):
            rankings[productID] = rank
            rank += 1
        return rankings
    
    def getTags(self):
        tags = defaultdict(list)
        tagIDs = {}
        maxtagID = 0
        with open(self.product_dataset, newline='', encoding='ISO-8859-1') as csvfile:
            productReader = csv.reader(csvfile)
            next(productReader)  #Skip header line
            for row in productReader:
                productID = int(row[0])
                tagList = row[2].split('|')
                tagIDList = []
                for tag in tagList:
                    if tag in tagIDs:
                        tagID = tagIDs[tag]
                    else:
                        tagID = maxtagID
                        tagIDs[tag] = tagID
                        maxtagID += 1
                    tagIDList.append(tagID)
                tags[productID] = tagIDList
        # Convert integer-encoded tag lists to bitfields that we can treat as vectors
        for (productID, tagIDList) in tags.items():
            bitfield = [0] * maxtagID
            for tagID in tagIDList:
                bitfield[tagID] = 1
            tags[productID] = bitfield            
        
        return tags
    
    def getProductName(self, productID):
        if productID in self.productID_to_name:
            return self.productID_to_name[productID]
        else:
            return ""
        
    def getProductID(self, productName):
        if productName in self.name_to_productID:
            return self.name_to_productID[productName]
        else:
            return 0
        
    def getAllProductIDs(self):
        # Get all product ids from the first column of product_dataset csv file
        product_ids = []
        with open(self.product_dataset, newline='', encoding='ISO-8859-1') as csvfile:
            productReader = csv.reader(csvfile)
            next(productReader)  # Skip header line
            for row in productReader:
                productID = int(row[0])
                product_ids.append(productID)
        return product_ids
    
    def getActiveProductIDs(self):
        # Get active product ids from the first column of product_dataset csv file
        product_ids = []
        with open(self.product_dataset, newline='', encoding='ISO-8859-1') as csvfile:
            productReader = csv.reader(csvfile)
            next(productReader)  # Skip header line
            for row in productReader:
                if row[3] == 'True':
                    productID = int(row[0])
                    product_ids.append(productID)
        return product_ids
    
    def getPurchasedItems(self, user_id):
        # Get all purchased product from the purchase_dataset csv file (the file contains 2 columns: CustomerId ProductId)
        purchased_items = []
        with open(self.purchase_dataset, newline='', encoding='ISO-8859-1') as csvfile:
            purchaseReader = csv.reader(csvfile)
            next(purchaseReader)  # Skip header line
            for row in purchaseReader:
                customerID = int(row[0])
                if customerID == user_id:
                    productID = int(row[1])
                    purchased_items.append(productID)
        return purchased_items