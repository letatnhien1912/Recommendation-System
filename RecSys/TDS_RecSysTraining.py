from RecSys.ProductPreference import ProductInfo
from RecSys.ContentKNNAlgorithm import ContentKNNAlgorithm
from surprise import SVD

import pickle, os

def load_data():
    print("Loading dataset...")
    ml = ProductInfo()
    data = ml.loadRatingData()
    full_trainSet = data.build_full_trainset()

    return full_trainSet

def save_model(relative_path, algorithm):
    base_path = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(base_path, relative_path)
    with open(path, 'wb') as model_file:
        pickle.dump(algorithm, model_file)

def collab_filter_recsys():
    full_trainSet = load_data()

    # SVD recommender
    SVDAlgorithm = SVD(n_factors=50, n_epochs=30, lr_all= 0.01, reg_all= 0.05, random_state=1)
    SVDAlgorithm.fit(full_trainSet)

    save_model('../app/svd_model.pkl', SVDAlgorithm)
    print("\nCollaborative Filtering model saved.")

def content_filter_recsys():
    full_trainSet = load_data()

    # Content KNN Algorithm
    algo = ContentKNNAlgorithm(k=20)
    algo.fit(full_trainSet)

    save_model('../app/content_knn_model.pkl', algo)
    print("\nContent-based Filtering model saved.")

def main():
    collab_filter_recsys()
    content_filter_recsys()
    print('\nRecsys models saved.')

if __name__ == "__main__":
    main()