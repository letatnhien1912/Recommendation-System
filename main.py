from fastapi import FastAPI, Request, Form, Query
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware

import pandas as pd
from pydantic import BaseModel
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager
import os

from RecSys import TDS_DataRefresh
from RecSys import TDS_GetRecs
from RecSys import TDS_RecSysTraining
import queries, server_info

from typing import Optional
from datetime import date

### Class settings
class Customer(BaseModel):
    customer_id: int

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

@contextmanager
def get_cnxn():
    """Return SQLAlchemy session with the default settings"""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()

def query_sql(sql_query, cnxn, **kwargs):
        """Return dataframe"""

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

# Get recommendations by userID from User Recommendation System - Content-Based Filtering
@app.post("/recommend")
async def recommend_product(customer: Customer, model: str = Query("collaborative", enum=['collaborative', 'content_based'])):
    model_map = {'collaborative': 'svd', 'content_based': 'knn'}
    return TDS_GetRecs.main(customer.customer_id, model = model_map[model])

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


### Recommender Report

# Serve static files
app.mount("/static", StaticFiles(directory="rec_report/assets"), name="static")

# Initialize Jinja2Templates with the templates directory
templates = Jinja2Templates(directory="rec_report")

# Custom filter
def format_number(value) -> str:
    return "{:,}".format(int(value))
def format_percentage(value) -> str:
    return "{:.2%}".format(float(value))
def format_date(value: date) -> str:
    return value.strftime("%d/%m/%Y")
def format_money(value: float) -> str:
    return "{:,} ₫".format(int(value))
templates.env.filters['format_number'] = format_number
templates.env.filters['format_percentage'] = format_percentage
templates.env.filters['format_date'] = format_date
templates.env.filters['format_money'] = format_money

# Recommendations Report
@app.get("/recommendation_report", response_class=HTMLResponse)
async def get_rec_report(request: Request):
    
    today = date.today()
    start_month = today.replace(day=1)
    dateformat = 'yyyy-MM-dd'

    with get_cnxn() as session:
        with session.connection() as cnxn:
            sql_query = queries.cross_sell_report
            cross_sell_stat = query_sql(sql_query=sql_query, cnxn=cnxn, from_date=start_month, to_date=today, dateformat=dateformat)

    agg_stat = cross_sell_stat.agg({'distinct_product':'sum',
                                    'distinct_guest':'sum',
                                    'impression':'sum',
                                    'ask_info':'sum',
                                    'add_cart':'sum',
                                    'success_order':'sum',
                                    'revenue':'sum'})
    agg_stat['ask_impress_cvr'] = agg_stat['ask_info'] / agg_stat['impression']
    agg_stat['cart_impress_cvr'] = agg_stat['add_cart'] / agg_stat['impression']
    agg_stat['order_impress_cvr'] = agg_stat['success_order'] / agg_stat['impression']

    return templates.TemplateResponse("report.html", 
                                      {"request": request,
                                       "from_date": start_month, 
                                        "to_date": today,
                                        "cross_sell_stat": cross_sell_stat,
                                        "agg_stat": agg_stat})

@app.post("/recommendation_report", response_class=HTMLResponse)
async def post_rec_report(request: Request, from_date: str = Form(...), to_date: str = Form(...), dateformat: str = Form(...)):
    from_date = date.fromisoformat(from_date)  
    to_date = date.fromisoformat(to_date)

    with get_cnxn() as session:
        with session.connection() as cnxn:
            sql_query = queries.cross_sell_report
            cross_sell_stat = query_sql(sql_query=sql_query, cnxn=cnxn, from_date=from_date, to_date=to_date, dateformat=dateformat)
    agg_stat = cross_sell_stat.agg({'distinct_product':'sum',
                                    'distinct_guest':'sum',
                                    'impression':'sum',
                                    'ask_info':'sum',
                                    'add_cart':'sum',
                                    'success_order':'sum',
                                    'revenue':'sum'})
    agg_stat['ask_impress_cvr'] = agg_stat['ask_info'] / agg_stat['impression']
    agg_stat['cart_impress_cvr'] = agg_stat['add_cart'] / agg_stat['impression']
    agg_stat['order_impress_cvr'] = agg_stat['success_order'] / agg_stat['impression']

    return templates.TemplateResponse("report.html", {"request": request, 
                                                      "from_date": from_date, 
                                                      "to_date": to_date, 
                                                      "cross_sell_stat": cross_sell_stat,
                                                      "agg_stat": agg_stat})
