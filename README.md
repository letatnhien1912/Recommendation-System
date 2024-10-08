﻿# Recommendation System Project

## Table of Contents
1. [Project Overview](#project-overview)
2. [Features](#features)
3. [Future Work](#future-work)

## Project Overview
This project was initiated to address the need for product recommendations tailored to customers of a fashion retailer, with the primary goal of increasing cross-selling revenue. The recommendation system is designed to function as an API, seamlessly integrating with e-commerce platforms to provide personalized product suggestions to users.

## Features
The recommendation system has 3 approaches:
1. [Frequently-bought-together Recommendation](#1-frequently-bought-together-recommendations)
2. [Collaborative Filtering Recommendation]()
3. [Content-based Filtering Recommendation]()

<p align="center"><img src="./imgs/recommendation_system_approaches.png" width=700px /></p>

### 1. Frequently-bought-together Recommendations
#### Description
This recommendation approach is triggered when a user visits a product page. The eCommerce platform utilizes the ProductID to call the recommendation system's API, retrieving a list of items frequently purchased together with the viewed product. These related items are then presented to the user as potential additions to their purchase.
</br>
</br>
Additionally, when the user is logged in or identified, the system can further personalize the recommendations. By analyzing the user's purchase history or market basket, the recommended items are prioritized based on product categories that are relevant to the user, offering a more tailored shopping experience.

#### Tech Approach
This recommendation method is powered by SQL to transform and query the data. For detailed implementations, refer to the SQL variables [`cross_sell_rec_all_customer`](queries.py) and [`cross_sell_rec`](queries.py) within the `queries.py` file.

### 2. Recommend products with collaborative filtering

<p align="center"><img src="./imgs/collaborative_filtering.png" width=400px /></p>

#### Description
Collaborative filtering is a popular recommendation technique that leverages the behavior and preferences of users to make personalized suggestions. The core idea is to recommend items to a user based on the preferences of similar users (user-based collaborative filtering) or to recommend items similar to those the user has interacted with (item-based collaborative filtering).
</br></br>
In this approach, patterns of interaction, such as ratings, clicks, or purchases, are used to identify relationships between users or items. For example, if two users have shown similar preferences for certain items, the system may suggest items one user liked to the other. Similarly, if an item is frequently purchased together with another item, the system will recommend those items to users who show interest in one of them.
</br></br>
Collaborative filtering does not require detailed item information, making it highly scalable and effective in various domains, such as product recommendations, movie suggestions, and social media content curation.

#### Modeling Approach
##### Collaborative Filtering with SVD Algorithm
The recommendation system employs collaborative filtering using the Singular Value Decomposition (SVD) algorithm, facilitated by the Surprise library. SVD is a matrix factorization technique designed to capture latent factors in user-item interactions, providing a robust method for predicting user preferences and enhancing recommendation accuracy.
</br></br>
In collaborative filtering, the core idea is to predict missing interactions between users and items by learning latent factors representing users and products. SVD decomposes the user-item interaction matrix into three smaller matrices, capturing the hidden patterns in user preferences and item attributes:

1. **User Matrix (U)**: Represents latent factors for each user.
2. **Singular Values Matrix (Σ)**: Captures the strength of each latent factor.
3. **Item Matrix (V)**: Represents latent factors for each product.

Using the Surprise library, the SVD algorithm is applied to these matrices to learn hidden patterns in user behavior and item characteristics. The Surprise library offers efficient implementation and additional functionalities to fine-tune the SVD model and evaluate its performance.

##### Model Training
The SVD model is trained on historical user-item interaction data, focusing on preferences implied by user interactions and purchases. To effectively utilize this data, SQL is employed to transform various types of user interactions into a standardized preference score. These interactions can include likes, shares, comments, social media chats, additions to the cart, and successful purchases.

1. **Data Transformation**: Interactions such as likes, shares, comments, and other engagement metrics are converted into a unified preference score. SQL queries are used to aggregate and normalize these interaction metrics into a format suitable for the SVD model.
2. **Training the Model**: With the preference scores derived from user interactions, the SVD model is trained to uncover latent factors and predict user preferences. The Surprise library is used to train and validate the SVD model on this transformed data, optimizing the latent factors to minimize prediction errors.

##### Prediction and Recommendation
After training, the model can predict user interactions with unseen items by estimating the missing values in the user-item matrix.

##### Evaluation
The performance of the recommendation system is evaluated using two standard metrics for regression-based recommendation models: Root Mean Squared Error (RMSE) and Mean Absolute Error (MAE). These metrics were chosen because they effectively capture the difference between predicted and actual ratings, which are on a scale from 1 to 5 in this system.
- RMSE (Root Mean Squared Error): 0.3076
- MAE (Mean Absolute Error): 0.1768

Both RMSE and MAE values are low, indicating that the model performs well in predicting user ratings with high accuracy. The model can capture user preferences and predict ratings with a minimal average error, showcasing the effectiveness of the collaborative filtering approach using the SVD algorithm.

### 3. Recommend products with content-based filtering

<p align="center"><img src="./imgs/content_based_filtering.png" width=400px /></p>

#### Description
Content-based filtering is a recommendation technique that leverages the attributes and features of items to make personalized suggestions. The core idea is to recommend items to a user based on the similarity between the items’ attributes and the user’s preferences or past interactions. Unlike collaborative filtering, which relies on user behavior data, content-based filtering focuses on the inherent properties of items and how they match user profiles.
</br></br>
In this approach, item attributes such as category, color, measures, and other descriptive features are used to identify items that closely align with a user's interests. This method ensures that recommendations are relevant based on the content and features of the items themselves.
</br></br>
Content-based filtering is particularly effective when detailed item information is available and can be used to make recommendations even for new or less common items, making it suitable for domains where item characteristics play a significant role in user preferences like fashion.

#### Modeling Approach
##### Content-Based Filtering with Custom KNN Algorithm
The recommendation system utilizes a custom K-Nearest Neighbors (KNN) algorithm for content-based filtering. This algorithm computes similarity scores between items based on their content attributes, using a self-written implementation of KNN with a focus on item similarity.
1. **Feature Representation**: Items are represented using content attributes such as tags, categories, or other relevant features. These attributes are used to create feature vectors for each item.
2. **Similarity Computation**: The KNN algorithm calculates similarity scores between items using these feature vectors. The [`ContentKNNAlgorithm`](RecSys/ContentKNNAlgorithm.py) class implements this approach by:
    * Computing a content-based similarity matrix, where similarity scores between item pairs are calculated based on their feature vectors.
    * Using cosine similarity to measure the degree of similarity between items.
3. **Recommendation Generation**: For each user, the system predicts preferences for unseen items based on their similarity to items the user has previously rated. The algorithm:
    * Builds a list of similarity scores between the target item and items the user has rated.
    * Extracts the top-K most similar items.
    * Computes a weighted average of these top-K neighbors' preferences to predict the rating for the target item.

##### Prediction and Recommendation
The system predicts preferences for unseen items by leveraging the similarity scores between items. It identifies items that closely match the user's preferences and provides recommendations based on these predictions.

##### Evaluation
The content-based filtering model was evaluated using Root Mean Squared Error (RMSE) and Mean Absolute Error (MAE), both of which assess the accuracy of predicted ratings against actual user ratings on a scale from 1 to 5.
- RMSE (Root Mean Squared Error): 0.5686
- MAE (Mean Absolute Error): 0.3757

While these error values are higher compared to the collaborative filtering model, they are still within an acceptable range. This difference is expected as content-based filtering relies solely on product attributes and user preferences for similar items, without considering broader user interaction patterns like collaborative filtering does.
</br></br>
The content-based approach excels in providing recommendations for new or less popular items, where collaborative filtering might struggle due to sparse interaction data. By leveraging product attributes, the model can make informed suggestions based on item similarity and user interests.

## Future Work
### Evaluation and Fine-Tuning
The recommendation system will benefit from further evaluation and fine-tuning to enhance its accuracy and effectiveness. Future work should focus on:

- **Comparative Evaluation**: Conduct a comprehensive comparison of the system's predictions against actual user interactions and feedback. This will involve analyzing the performance metrics of the recommendations and identifying areas for improvement.
- **Fine-Tuning Parameters**: Based on the evaluation results, fine-tune the model parameters, such as similarity thresholds, the number of neighbors in KNN, and SVD hyperparameters, to better align the recommendations with user preferences.

### Integration of Collaborative and Content-Based Filtering
To improve recommendation quality and provide more robust suggestions, integrating collaborative filtering with content-based filtering is planned. This hybrid approach will combine the strengths of both techniques:

- **Hybrid Model Development**: Develop a hybrid recommendation model that leverages both collaborative filtering and content-based filtering. This model will utilize collaborative filtering to capture user behavior patterns and content-based filtering to match item attributes with user preferences.
- **System Integration**: Implement mechanisms to seamlessly combine the outputs of both filtering methods, ensuring that recommendations are both personalized and contextually relevant.
- **Performance Assessment**: Evaluate the performance of the hybrid model against standalone collaborative and content-based filtering approaches to determine the most effective strategy for various recommendation scenarios.

By focusing on these future improvements, the recommendation system will be better equipped to provide high-quality, personalized recommendations and adapt to evolving user needs and preferences.
