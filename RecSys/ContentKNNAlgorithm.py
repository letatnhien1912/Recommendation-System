from surprise import AlgoBase
from surprise import PredictionImpossible
from RecSys.ProductPreference import ProductInfo
import math
import numpy as np
import heapq

class ContentKNNAlgorithm(AlgoBase):

    def __init__(self, k=40, sim_options={}):
        AlgoBase.__init__(self)
        self.k = k

    def fit(self, trainset):
        AlgoBase.fit(self, trainset)

        # Compute item similarity matrix based on content attributes

        # Load up genre vectors for every product
        ml = ProductInfo()
        tags = ml.getTags()
        
        print("Computing content-based similarity matrix...")
            
        # Compute genre distance for every product combination as a 2x2 matrix
        self.similarities = np.zeros((self.trainset.n_items, self.trainset.n_items))
        
        for thisRating in range(self.trainset.n_items):
            if (thisRating % 100 == 0):
                print(thisRating, " of ", self.trainset.n_items)
            for otherRating in range(thisRating+1, self.trainset.n_items):
                thisProductID = int(self.trainset.to_raw_iid(thisRating))
                otherProductID = int(self.trainset.to_raw_iid(otherRating))
                genreSimilarity = self.computeTagSimilarity(thisProductID, otherProductID, tags)
                self.similarities[thisRating, otherRating] = genreSimilarity
                self.similarities[otherRating, thisRating] = self.similarities[thisRating, otherRating]
                
        print("...done.")
                
        return self
    
    def computeTagSimilarity(self, product1, product2, tags):
        tags1 = tags[product1]
        tags2 = tags[product2]

        sumxx, sumxy, sumyy = 0, 0, 0
        for i in range(len(tags1)):
            x = tags1[i]
            y = tags2[i]
            sumxx += x * x
            sumyy += y * y
            sumxy += x * y
        
        return sumxy/math.sqrt(sumxx*sumyy)

    def estimate(self, u, i):

        if not (self.trainset.knows_user(u) and self.trainset.knows_item(i)):
            raise PredictionImpossible('User and/or item is unkown.')
        
        # Build up similarity scores between this item and everything the user rated
        neighbors = []
        for rating in self.trainset.ur[u]:
            genreSimilarity = self.similarities[i,rating[0]]
            neighbors.append( (genreSimilarity, rating[1]) )
        
        # Extract the top-K most-similar ratings
        k_neighbors = heapq.nlargest(self.k, neighbors, key=lambda t: t[0])
        
        # Compute average sim score of K neighbors weighted by user ratings
        simTotal = weightedSum = 0
        for (simScore, rating) in k_neighbors:
            if (simScore > 0):
                simTotal += simScore
                weightedSum += simScore * rating
            
        if (simTotal == 0):
            raise PredictionImpossible('No neighbors')

        predictedRating = weightedSum / simTotal

        return predictedRating
    
    def get_similar_items(self, i, top_n=10):
        """Get top-N most similar items to the given itemID based on content similarity."""
        
        # Convert the raw itemID to the internal item index
        inner_id = self.trainset.to_inner_iid(str(i))

        # Get similarity scores for the item with all other items
        similarity_scores = list(enumerate(self.similarities[inner_id]))

        # Exclude the item itself from the similarity list and find the top-N most similar items
        similarity_scores = [(item, score) for item, score in similarity_scores if item != inner_id]
        top_n_similar = heapq.nlargest(top_n, similarity_scores, key=lambda t: t[1])

        # Convert inner ids back to raw itemIDs and return the results
        top_n_similar = [self.trainset.to_raw_iid(item) for item, score in top_n_similar]

        return top_n_similar