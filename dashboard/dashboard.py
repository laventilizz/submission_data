import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st
from datetime import datetime

# Set config & style
st.set_page_config(page_title="E-Commerce Dashboard", page_icon="🛒", layout="wide")
sns.set(style='darkgrid')

# --- 1. LOAD DATA MENTAH (Hanya loading dan basic cleaning) ---
@st.cache_data
def load_data():
    customers_df = pd.read_csv("data/customers_dataset.csv")
    orders_df = pd.read_csv("data/orders_dataset.csv")
    order_items_df = pd.read_csv("data/order_items_dataset.csv")
    order_payments_df = pd.read_csv("data/order_payments_dataset.csv")
    order_reviews_df = pd.read_csv("data/order_reviews_dataset.csv")
    products_df = pd.read_csv("data/products_dataset.csv")
    category_translation_df = pd.read_csv("data/product_category_name_translation.csv")
    
    # Format Datetime
    datetime_cols = ["order_purchase_timestamp", "order_delivered_customer_date", "order_estimated_delivery_date"]
    for col in datetime_cols:
        orders_df[col] = pd.to_datetime(orders_df[col])
        
    # Merge basic tables for analysis
    main_df = pd.merge(orders_df, order_items_df, on="order_id")
    main_df = pd.merge(main_df, order_payments_df, on="order_id")
    main_df = pd.merge(main_df, products_df, on="product_id")
    main_df = pd.merge(main_df, category_translation_df, on="product_category_name")
    
    return main_df, order_reviews_df, customers_df

main_df, order_reviews_df, customers_df = load_data()

# --- 2. SIDEBAR FILTERING ---
with st.sidebar:
    st.image("https://github.com/dicodingacademy/assets/raw/main/logo.png") # Opsional: Logo
    
    # Mengambil rentang waktu dari dataset
    min_date = main_df["order_purchase_timestamp"].min()
    max_date = main_df["order_purchase_timestamp"].max()
    
    start_date, end_date = st.date_input(
        label='Rentang Waktu',
        min_value=min_date,
        max_value=max_date,
        value=[min_date, max_date]
    )

# Filter dataframe utama berdasarkan input tanggal
main_df_filtered = main_df[(main_df["order_purchase_timestamp"] >= str(start_date)) & 
                           (main_df["order_purchase_timestamp"] <= str(end_date))]

# --- 3. HELPER FUNCTIONS (Agregasi dilakukan dari data yang sudah difilter) ---
def create_category_revenue_df(df):
    return df.groupby("product_category_name_english").agg({
        "payment_value": "sum"
    }).sort_values(by="payment_value", ascending=False).reset_index()

def create_review_delivery_df(df, reviews):
    df['delivery_delay_days'] = (df['order_delivered_customer_date'] - df['order_estimated_delivery_date']).dt.days
    df['delivery_status'] = df['delivery_delay_days'].apply(lambda x: 'Late' if x > 0 else 'On Time/Early')
    
    merged_reviews = pd.merge(df, reviews, on="order_id")
    return merged_reviews.groupby("delivery_status").agg({"review_score": "mean"}).reset_index()

def create_rfm_df(df, customers):
    # Gunakan df_filtered untuk menghitung RFM
    merged_rfm = pd.merge(df, customers, on="customer_id")
    recent_date = df["order_purchase_timestamp"].max()
    
    rfm = merged_rfm.groupby("customer_unique_id").agg({
        "order_purchase_timestamp": lambda x: (recent_date - x.max()).days,
        "order_id": "nunique",
        "payment_value": "sum"
    }).reset_index()
    
    rfm.columns = ["customer_unique_id", "recency", "frequency", "monetary"]
    return rfm

# Panggil fungsi helper menggunakan main_df_filtered
category_revenue = create_category_revenue_df(main_df_filtered)
review_by_delivery = create_review_delivery_df(main_df_filtered, order_reviews_df)
rfm = create_rfm_df(main_df_filtered, customers_df)

# --- 4. VISUALISASI (Visualisasi akan otomatis terupdate saat helper dipanggil) ---
st.title("🛒 E-Commerce Dashboard")

# (Gunakan kode visualisasi bar chart yang sudah kamu buat sebelumnya di sini)
# Contoh:
st.subheader("Total Revenue per Kategori")
fig, ax = plt.subplots(figsize=(10, 5))
sns.barplot(x="payment_value", y="product_category_name_english", data=category_revenue.head(5), ax=ax)
st.pyplot(fig)