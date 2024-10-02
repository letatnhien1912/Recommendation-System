import pandas as pd
from sklearn.preprocessing import MinMaxScaler, RobustScaler
import os
import queries

def robust_minmax(column_2d, minmax_range=(0,1)):
        robust_scaler = RobustScaler()
        robust_recency = robust_scaler.fit_transform(column_2d)

        minmax_scaler = MinMaxScaler(feature_range=minmax_range)
        scaled_column = minmax_scaler.fit_transform(robust_recency)
        
        return scaled_column

def get_iqr(column):
    q1 = column.quantile(0.25)
    q3 = column.quantile(0.75)
    iqr = q3 - q1
    return q1, q3, iqr

def getRawData(cnxn):
    ### Get dataset
    print("\nGet users' preference data...")
    sql_query = queries.recsys_dataset_refresh
    rating_df = pd.read_sql(sql_query, cnxn)

    rating_df.drop_duplicates(subset=['CustomerId', 'ProductId', 'action_type', 'recency'], keep='first', inplace=True)
    ### Transform rating dataset

    # Reverese 'Recency'
    rating_df['recency_inverse'] = rating_df.recency.max() - rating_df.recency

    # Scale 'Recency'
    rating_df['recency_scaled'] = robust_minmax(rating_df[['recency']])

    # Multiple scaled recency with preference score
    rating_df['scaled_preference_score'] = rating_df['preference_score'] * rating_df['recency_scaled']

    # Sum the preference score by customer and product
    rating_df_preprocessed = rating_df.groupby(['CustomerId', 'ProductId'], as_index=False)[['preference_score','scaled_preference_score']].sum()

    # Drop outliers
    q1, q3, iqr = get_iqr(rating_df_preprocessed.scaled_preference_score)

    # Calculate the threshold
    threshold = q3 + 1.5 * iqr

    # Assign values to rows where the condition is met
    rating_df_preprocessed.loc[rating_df_preprocessed['scaled_preference_score'] > threshold, 'scaled_preference_score'] = q3

    # Scale the preference score to 1-5 scale
    minmax_scaler = MinMaxScaler(feature_range=(1,5))
    rating_df_preprocessed['likert_scaled_preference_score'] = minmax_scaler.fit_transform(rating_df_preprocessed[['scaled_preference_score']])

    # Finalize the dataset
    rating_dataset = rating_df_preprocessed[['CustomerId', 'ProductId', 'likert_scaled_preference_score']]
    rating_dataset.columns = ['userId', 'productId', 'rating']
    rating_dataset['userId'] = rating_dataset['userId'].apply(lambda x: str(x).split('.')[0])
    rating_dataset['productId'] = rating_dataset['productId'].apply(lambda x: str(x).split('.')[0])
    return rating_dataset

def getProductPreferenceData(cnxn):
    ### Get dataset
    print("Get product preference data...")
    sql_query = queries.recsys_product_preference
    rating_df = pd.read_sql(sql_query, cnxn)

    ### Transform rating dataset

    # Reverese 'Recency'
    rating_df['recency_inverse'] = rating_df.recency.max() - rating_df.recency

    # Scale 'Recency'
    rating_df['recency_scaled'] = robust_minmax(rating_df[['recency']])

    # Multiple scaled recency with preference score
    rating_df['scaled_preference_score'] = rating_df['preference_score'] * rating_df['recency_scaled']

    # Sum the preference score by customer and product
    rating_df_preprocessed = rating_df.groupby(['ProductId', 'CategoryId'], as_index=False)[['preference_score','scaled_preference_score']].sum()

    # Drop outliers
    q1, q3, iqr = get_iqr(rating_df_preprocessed.scaled_preference_score)

    # Calculate the threshold
    threshold = q3 + 1.5 * iqr

    # Assign values to rows where the condition is met
    rating_df_preprocessed.loc[rating_df_preprocessed['scaled_preference_score'] > threshold, 'scaled_preference_score'] = q3

    # Finalize the dataset
    rating_dataset = rating_df_preprocessed[['ProductId', 'CategoryId', 'scaled_preference_score']]
    rating_dataset.columns = ['productId', 'categoryId', 'rating']
    rating_dataset.loc[:, 'productId'] = rating_dataset['productId'].astype(int)
    rating_dataset.loc[:, 'CategoryId'] = rating_dataset['categoryId'].astype(int)
    return rating_dataset

def getProductData(cnxn):
    print('Get product data...')
    sql_query = queries.recsys_product_dataset
    product_dataset = pd.read_sql(sql_query, cnxn)
    product_dataset['productId'] = product_dataset['productId'].astype(int)
    return product_dataset

def getPurchaseData(cnxn):
    print('Get purchase data...')
    sql_query = queries.recsys_purchase_dataset
    purchase_dataset = pd.read_sql(sql_query, cnxn)
    purchase_dataset = purchase_dataset.astype(int)
    return purchase_dataset

def getCookieData(cnxn):
    print("Get cookie data...")
    sql_query = queries.recsys_cookie_dataset
    rating_df = pd.read_sql(sql_query, cnxn)
    rating_df.columns = ['userId', 'productId', 'rating']
    rating_df['userId'] = rating_df['userId'].apply(lambda x: str(x).split("'")[0])
    rating_df['productId'] = rating_df['productId'].apply(lambda x: str(x).split('.')[0])
    return rating_df

def main(cnxn):
    
    rating_dataset = getRawData(cnxn)
    rating_dataset.to_csv('dataset/rating_dataset.csv', index=False)
    print("Users' Preference data saved.")

    product_dataset = getProductData(cnxn)
    product_dataset.to_csv('dataset/product_dataset.csv', index=False)
    print('Product data saved.')

    purchase_dataset = getPurchaseData(cnxn)
    purchase_dataset.to_csv('dataset/purchase_dataset.csv', index=False)
    print('Purchase data saved.')

    purchase_dataset = getProductPreferenceData(cnxn)
    purchase_dataset.to_csv('dataset/product_preference_dataset.csv', index=False)
    print('Product prefernce data saved.')

    cookie_dataset = getCookieData(cnxn)
    cookie_dataset.to_csv('dataset/cookie_rating_dataset.csv', index=False)

    print("\nDatasets refreshed!")