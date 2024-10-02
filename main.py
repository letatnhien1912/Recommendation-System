from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

import pandas as pd
from pydantic import BaseModel
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager

from RecSys import TDS_DataRefresh
from RecSys import TDS_GetRecs
from RecSys import TDS_RecSysTraining
import queries, server_info

from typing import Optional

### Class settings
class Customer(BaseModel):
    customer_id: int

class Cookie(BaseModel):
    cookie: str

class Product(BaseModel):
    product_id: int

class Category(BaseModel):
    category_id: Optional[int]

class RSInput(BaseModel):
    product_id: int
    customer_id: Optional[int]

class customer_data(BaseModel):
    customer_id: list[int]
    height: list[int]
    weight: list[int]

### FastAPI app settings
app = FastAPI()
origins = [
    "http://localhost",
    "http://localhost:8080",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Connection string for SQLAlchemy
DATABASE_URL = (
    f"mssql+pyodbc://{server_info.DB_UID}:{server_info.DB_PWD.replace('@', '%40')}"
    f"@{server_info.DB_SERVER}:{server_info.DB_PORT}/{server_info.DB_NAME}"
    "?driver=SQL+Server"
)

# Create SQLAlchemy engine
engine = create_engine(DATABASE_URL)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

pd.set_option('future.no_silent_downcasting', True)
pd.options.mode.chained_assignment = None

@contextmanager
def get_cnxn():
    """Return SQLAlchemy session with the default settings"""

    print("\nConnect to database...")
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()

def query_sql(sql_query, cnxn, **kwargs):
        """Return dataframe with the query, connection, and vars as args"""

        formatted_query = sql_query.format(**kwargs)
        recs = pd.read_sql(formatted_query, cnxn)
        return recs

@app.get("/")
async def home():
    return "RECOMMENDATION SYSTEM"

# Refresh User Recommendation System datasets
@app.get("/refesh_recsys_data")
async def refesh_recsys_data():
    with get_cnxn() as session:
        with session.connection() as cnxn:
            TDS_DataRefresh.main(cnxn)
    return "Recommendation System datasets refreshed!"

# Re-train User Recommendation System model
@app.get("/retrain_recsys_model")
async def retrain_recsys_model():
    TDS_RecSysTraining.main()
    return "Recommendation System models retrained!"

# Get recommendations by userID - Content-Based Filtering
@app.post("/recommend")
async def recommend_product(customer: Customer, model: str = Query("collaborative", enum=['collaborative', 'content_based'])):
    model_map = {'collaborative': 'svd', 'content_based': 'knn'}
    return TDS_GetRecs.main(model = model_map[model], user_id = customer.customer_id)

# Get recommendations by Cookie
@app.post('/recommend_cookie')
async def recommend_product_cookie(cookie: Cookie):
    return TDS_GetRecs.main(model='cookie_knn', user_id=cookie.cookie)

# Get similar items - Content-based Filtering
@app.post("/get_similar_items")
async def get_similar_items(product: Product):
    recommended_items = TDS_GetRecs.main(model = 'knn', item_id = product.product_id)
    return [int(i) for i in recommended_items]

# Get perfered product recommendations by category
@app.post("/get_favorite_items")
async def get_favorite_items(category: Category):
    recommended_items = TDS_GetRecs.get_top_n_prefered_products(category=category.category_id)
    return recommended_items #{"recommended_items": recommended_items}

# Get cross-sell recommendations by userID and productID
@app.post("/cross_sell_rec")
async def cross_sell_recommend(input: RSInput):

    with get_cnxn() as session:
        with session.connection() as cnxn:

            product_id = input.product_id
            customer_id = input.customer_id

            if customer_id:
                sql_query = queries.cross_sell_rec
                rec_df = query_sql(sql_query, cnxn=cnxn, ProductId=product_id, CustomerId=customer_id)
                recommended_items = rec_df['item_2'].tolist()
                return {'rec_items': recommended_items}
            else:
                sql_query = queries.cross_sell_rec_all_customer
                rec_df = query_sql(sql_query, cnxn=cnxn, ProductId=product_id)
                recommended_items = rec_df['item_2'].tolist()
                return {'rec_items': recommended_items}