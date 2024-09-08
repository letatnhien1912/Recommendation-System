import pickle
from RecSys.ProductPreference import ProductInfo
import os

def load_model(relative_path):
    """Load the saved model from the given path."""
    base_path = os.path.dirname(os.path.abspath(__file__))
    model_path = os.path.join(base_path, relative_path)
    with open(model_path, 'rb') as model_file:
        model = pickle.load(model_file)
    return model

def get_top_n_recommendations(user_id, model, ml, n=10):
    """Get top N recommendations for the given user using the provided model."""
    item_ids = ml.getAllProductIDs()  # Adjust this method as needed to get all item IDs
    purchased_items = ml.getPurchasedItems(user_id) # Fetch the items already purchased by the user
    active_items = ml.getActiveProductIDs() # Fetch the active items

    user_predictions = []
    for item_id in item_ids:
        if item_id not in purchased_items and item_id in active_items:  # Exclude purchased items
            prediction = model.predict(str(user_id), str(item_id))
            user_predictions.append((item_id, prediction.est))
    
    # Sort predictions by estimated rating
    user_predictions.sort(key=lambda x: x[1], reverse=True)
    
    return [item_id for item_id, _ in user_predictions[:n]]

def main(user_id, model):
    # Load the model
    print("Loading the model...")

    if model == 'svd':
        model = load_model('../app/svd_model.pkl')
    elif model == 'knn':
        model = load_model('../app/content_knn_model.pkl')
    else:
        return 'Model name must be among: "svd", "knn"'
    
    # Load product information
    ml = ProductInfo()

    top_recommendations = get_top_n_recommendations(user_id, model, ml, n=10)

    return top_recommendations

if __name__ == "__main__":
    main()