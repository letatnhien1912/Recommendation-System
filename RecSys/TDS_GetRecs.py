import pickle
from RecSys.ProductPreference import ProductInfo
import os
import pandas as pd

def load_model(relative_path):
    """Load the saved model from the given path."""
    base_path = os.path.dirname(os.path.abspath(__file__))
    model_path = os.path.join(base_path, relative_path)
    with open(model_path, 'rb') as model_file:
        model = pickle.load(model_file)
    return model

def get_top_n_recommendations(user_id, model_file, ml, n=10):
    """Get top N recommendations for the given user using the provided model."""

    active_items = ml.getActiveProductIDs() # Fetch the active items
    instock_items = ml.getInstockProductIDs() # Fetch the instock items
    item_ids = ml.getAllProductIDs()  # Adjust this method as needed to get all item IDs
    purchased_items = ml.getPurchasedItems(user_id) # Fetch the items already purchased by the user

    
    user_predictions = []
    for item_id in item_ids:
        # Exclude purchased, inactive and out-of-stock items
        if item_id not in purchased_items and item_id in active_items and item_id in instock_items:  
            prediction = model_file.predict(str(user_id), str(item_id))
            user_predictions.append((item_id, prediction.est))
    
    # Sort predictions by estimated rating
    user_predictions.sort(key=lambda x: x[1], reverse=True)
    
    return [item_id for item_id, _ in user_predictions[:n]]

def get_top_n_prefered_products(category, n=10):
    ml = ProductInfo()
    pro_preference = pd.read_csv('dataset/product_preference_dataset.csv')
    active_items = ml.getActiveProductIDs() # Fetch the active items
    instock_items = ml.getInstockProductIDs() # Fetch the instock items

    sorted_pro_perference = pro_preference.sort_values('rating', ascending=False)
    if category:
        return sorted_pro_perference.loc[(pro_preference.categoryId == category) 
                                                    & pro_preference.productId.isin(active_items)
                                                    & pro_preference.productId.isin(instock_items),
                                                    'productId'][:n].tolist()
    
    return sorted_pro_perference.loc[pro_preference.productId.isin(active_items)
                                     & pro_preference.productId.isin(instock_items),
                                     'productId'][:n].tolist()

def main(model, user_id=None, item_id=None):
    # Load the model
    print("Loading the model...")

    if model == 'svd':
        model_file = load_model('../app/svd_model.pkl')
    elif model == 'knn':
        model_file = load_model('../app/content_knn_model.pkl')
    elif model == 'cookie_knn':
        model_file = load_model('../app/cookie_content_knn_model.pkl')
    else:
        return 'Model name must be among: "svd", "knn", "cookie_knn"'
    
    # Load product information
    ml = ProductInfo()

    if user_id:
        top_recommendations = get_top_n_recommendations(user_id, model_file, ml, n=10)
    if item_id:
        top_recommendations = model_file.get_similar_items(item_id)

    return top_recommendations