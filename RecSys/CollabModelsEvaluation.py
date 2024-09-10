from ProductPreference import ProductInfo
from surprise import SVD, accuracy
from surprise.model_selection import train_test_split
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
SVDAlgorithm = SVD(n_factors=50, n_epochs=30, lr_all= 0.01, reg_all= 0.05, random_state=42)
trainset, testset = train_test_split(evaluationData, test_size=0.25)
SVDAlgorithm.fit(trainset)
predictions = SVDAlgorithm.test(testset)

# Calculate metrics
rmse = accuracy.rmse(predictions)
mae = accuracy.mae(predictions)

# RMSE: 0.3076
# MAE:  0.1768