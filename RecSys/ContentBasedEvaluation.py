from ProductPreference import ProductInfo
from surprise import accuracy
from surprise.model_selection import train_test_split
from ContentKNNAlgorithm import ContentKNNAlgorithm
import numpy as np
import random

# Set random seeds for reproducibility
np.random.seed(0)
random.seed(0)

# Load product data
def LoadProductData():
    ml = ProductInfo()
    print("Loading product preferences...")
    data = ml.loadRatingData()
    return data

# Initialize evaluation data and algorithms
evaluationData = LoadProductData()

# Initialize the SVD algorithm
algo = ContentKNNAlgorithm(k=20)
trainset, testset = train_test_split(evaluationData, test_size=0.25)
algo.fit(trainset)
predictions = algo.test(testset)

# Calculate metrics
rmse = accuracy.rmse(predictions)
mae = accuracy.mae(predictions)

# RMSE: 0.5686
# MAE:  0.3757