import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st

st.set_page_config(page_title="E-Commerce Dashboard", layout="wide")
sns.set(style='darkgrid')

@st.cache_data
def load_data():
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    DATA_DIR = os.path.join(BASE_DIR, "..", "data")

    # Load dataset
    customers_df = pd.read_csv(os.path.join(DATA_DIR, "customers_dataset.csv"))
    orders_df = pd.read_csv(os.path.join(DATA_DIR, "orders_dataset.csv"))
    order_items_df = pd.read_csv(os.path.join(DATA_DIR, "order_items_dataset.csv"))
    order_payments_df = pd.read_csv(os.path.join(DATA_DIR, "order_payments_dataset.csv"))
    order_reviews_df = pd.read_csv(os.path.join(DATA_DIR, "order_reviews_dataset.csv"))
    products_df = pd.read_csv(os.path.join(DATA_DIR, "products_dataset.csv"))
    category_translation_df = pd.read_csv(os.path.join(DATA_DIR, "product_category_name_translation.csv"))
    
    # 1. cleaning & format datetime
    datetime_cols = ["order_purchase_timestamp", "order_delivered_customer_date", "order_estimated_delivery_date"]
    for col in datetime_cols:
        orders_df[col] = pd.to_datetime(orders_df[col])
        
    products_df = pd.merge(products_df, category_translation_df, how="left", on="product_category_name")
    products_df['product_category_name_english'].fillna('other', inplace=True)
    
    # 2. proses data eertanyaan 1 (revenue)
    revenue_df = pd.merge(order_items_df, order_payments_df, how="left", on="order_id")
    revenue_df = pd.merge(revenue_df, products_df, how="left", on="product_id")
    category_revenue = revenue_df.groupby(by="product_category_name_english").agg({
        "payment_value": "sum"
    }).sort_values(by="payment_value", ascending=False).reset_index()
    
    # 3. proses data pertanyaan 2 (delivery & reviews)
    orders_df['delivery_delay_days'] = (orders_df['order_delivered_customer_date'] - orders_df['order_estimated_delivery_date']).dt.days
    orders_df['delivery_status'] = orders_df['delivery_delay_days'].apply(
        lambda x: 'Late' if x > 0 else ('On Time/Early' if x <= 0 else 'Unknown')
    )
    delivery_review_df = pd.merge(orders_df, order_reviews_df, how="inner", on="order_id")
    review_by_delivery = delivery_review_df.groupby(by="delivery_status").agg({"review_score": "mean"}).reset_index()
    
    # 4. proses data RFM
    rfm_df = pd.merge(orders_df, customers_df, how="left", on="customer_id")
    rfm_df = pd.merge(rfm_df, order_payments_df, how="left", on="order_id")
    recent_date = orders_df["order_purchase_timestamp"].max()
    rfm = rfm_df.groupby("customer_unique_id").agg({
        "order_purchase_timestamp": lambda x: (recent_date - x.max()).days,
        "order_id": "nunique",
        "payment_value": "sum"
    }).reset_index()
    rfm.rename(columns={"order_purchase_timestamp": "recency", "order_id": "frequency", "payment_value": "monetary"}, inplace=True)
    
    return category_revenue, review_by_delivery, rfm

# load data
category_revenue, review_by_delivery, rfm = load_data()

# DASHBOARD UI
st.title("E-Commerce Public Data Dashboard")
st.markdown("---")

# 1: performa produk
st.header("1. Performa Kategori Produk (Revenue)")
col1, col2 = st.columns(2)

with col1:
    st.subheader("Top 5 Kategori Tertinggi")
    fig, ax = plt.subplots(figsize=(8, 5))
    colors = ["#72BCD4", "#D3D3D3", "#D3D3D3", "#D3D3D3", "#D3D3D3"]
    sns.barplot(x="payment_value", y="product_category_name_english", data=category_revenue.head(5), palette=colors, ax=ax)
    ax.set_xlabel("Total Pendapatan (BRL)")
    ax.set_ylabel(None)
    st.pyplot(fig)

with col2:
    st.subheader("Top 5 Kategori Terendah")
    fig, ax = plt.subplots(figsize=(8, 5))
    sns.barplot(x="payment_value", y="product_category_name_english", data=category_revenue.tail(5).sort_values(by="payment_value", ascending=True), palette=colors, ax=ax)
    ax.set_xlabel("Total Pendapatan (BRL)")
    ax.set_ylabel(None)
    ax.invert_xaxis()
    ax.yaxis.tick_right()
    st.pyplot(fig)

st.markdown("---")

# 2: logistik
st.header("2. Dampak Keterlambatan Pengiriman pada Skor Ulasan")
fig, ax = plt.subplots(figsize=(10, 5))
colors_review = ["#72BCD4" if status == 'On Time/Early' else "#FF7276" for status in review_by_delivery.sort_values(by="review_score", ascending=False)['delivery_status']]
sns.barplot(x="delivery_status", y="review_score", data=review_by_delivery.sort_values(by="review_score", ascending=False), palette=colors_review, ax=ax)
ax.set_xlabel("Status Pengiriman")
ax.set_ylabel("Rata-rata Skor Ulasan")
ax.set_ylim(0, 5)
for index, row in enumerate(review_by_delivery.sort_values(by="review_score", ascending=False).itertuples()):
    ax.text(index, row.review_score + 0.1, round(row.review_score, 2), color='black', ha="center")
st.pyplot(fig)

st.markdown("---")

# 3: RFM analysis
st.header("3. RFM Analysis - Pelanggan Terbaik")
tab1, tab2, tab3 = st.tabs(["Recency", "Frequency", "Monetary"])

with tab1:
    fig, ax = plt.subplots(figsize=(12, 6))
    sns.barplot(y="recency", x="customer_unique_id", data=rfm.sort_values(by="recency", ascending=True).head(5), palette=["#72BCD4"]*5, ax=ax)
    ax.set_title("Berdasarkan Recency (Hari)")
    ax.tick_params(axis='x', rotation=45)
    st.pyplot(fig)

with tab2:
    fig, ax = plt.subplots(figsize=(12, 6))
    sns.barplot(y="frequency", x="customer_unique_id", data=rfm.sort_values(by="frequency", ascending=False).head(5), palette=["#72BCD4"]*5, ax=ax)
    ax.set_title("Berdasarkan Frequency (Jumlah Transaksi)")
    ax.tick_params(axis='x', rotation=45)
    st.pyplot(fig)

with tab3:
    fig, ax = plt.subplots(figsize=(12, 6))
    sns.barplot(y="monetary", x="customer_unique_id", data=rfm.sort_values(by="monetary", ascending=False).head(5), palette=["#72BCD4"]*5, ax=ax)
    ax.set_title("Berdasarkan Monetary (Total Pembelanjaan)")
    ax.tick_params(axis='x', rotation=45)
    st.pyplot(fig)

st.caption("Fahalliza Nastitie")