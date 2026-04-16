import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st

# Set config & style
st.set_page_config(page_title="E-Commerce Dashboard", page_icon="🛒", layout="wide")
sns.set(style='darkgrid')

# --- 1. FUNGSI HELPER UNTUK AGREGASI (DIPANGGIL SETELAH FILTER) ---
def create_category_revenue_df(df):
    category_revenue = df.groupby(by="product_category_name_english").agg({
        "payment_value": "sum"
    }).sort_values(by="payment_value", ascending=False).reset_index()
    return category_revenue

def create_review_delivery_df(df, order_reviews_df):
    df['delivery_delay_days'] = (df['order_delivered_customer_date'] - df['order_estimated_delivery_date']).dt.days
    df['delivery_status'] = df['delivery_delay_days'].apply(
        lambda x: 'Late' if x > 0 else ('On Time/Early' if x <= 0 else 'Unknown')
    )
    delivery_review_df = pd.merge(df, order_reviews_df, how="inner", on="order_id")
    review_by_delivery = delivery_review_df.groupby(by="delivery_status").agg({"review_score": "mean"}).reset_index()
    return review_by_delivery

def create_rfm_df(df, customers_df):
    recent_date = df["order_purchase_timestamp"].max()
    rfm = df.groupby("customer_unique_id").agg({
        "order_purchase_timestamp": lambda x: (recent_date - x.max()).days,
        "order_id": "nunique",
        "payment_value": "sum"
    }).reset_index()
    rfm.rename(columns={"order_purchase_timestamp": "recency", "order_id": "frequency", "payment_value": "monetary"}, inplace=True)
    return rfm

# --- 2. LOAD DATA MENTAH ---
@st.cache_data
def load_raw_data():
    customers_df = pd.read_csv("https://raw.githubusercontent.com/laventilizz/submission_data/refs/heads/main/data/customers_dataset.csv")
    orders_df = pd.read_csv("https://raw.githubusercontent.com/laventilizz/submission_data/refs/heads/main/data/orders_dataset.csv")
    order_items_df = pd.read_csv("https://raw.githubusercontent.com/laventilizz/submission_data/refs/heads/main/data/order_items_dataset.csv")
    order_payments_df = pd.read_csv("https://raw.githubusercontent.com/laventilizz/submission_data/refs/heads/main/data/order_payments_dataset.csv")
    order_reviews_df = pd.read_csv("https://raw.githubusercontent.com/laventilizz/submission_data/refs/heads/main/data/order_reviews_dataset.csv")
    products_df = pd.read_csv("https://raw.githubusercontent.com/laventilizz/submission_data/refs/heads/main/data/products_dataset.csv")
    category_translation_df = pd.read_csv("https://raw.githubusercontent.com/laventilizz/submission_data/refs/heads/main/data/product_category_name_translation.csv")
    
    # Format Datetime
    datetime_cols = ["order_purchase_timestamp", "order_delivered_customer_date", "order_estimated_delivery_date"]
    for col in datetime_cols:
        orders_df[col] = pd.to_datetime(orders_df[col])
        
    # Gabungkan menjadi satu Master Dataframe untuk memudahkan filtering
    main_df = pd.merge(orders_df, order_items_df, on="order_id")
    main_df = pd.merge(main_df, order_payments_df, on="order_id")
    main_df = pd.merge(main_df, products_df, on="product_id")
    main_df = pd.merge(main_df, category_translation_df, on="product_category_name")
    main_df = pd.merge(main_df, customers_df, on="customer_id")
    
    return main_df, order_reviews_df

main_df, order_reviews_df = load_raw_data()

# --- 3. SIDEBAR FILTER ---
with st.sidebar:
    st.title("Filter Data")
    min_date = main_df["order_purchase_timestamp"].min()
    max_date = main_df["order_purchase_timestamp"].max()
    
    start_date, end_date = st.date_input(
        label='Rentang Waktu',
        min_value=min_date,
        max_value=max_date,
        value=[min_date, max_date]
    )

# Filter Master Dataframe berdasarkan input user
main_df_filtered = main_df[(main_df["order_purchase_timestamp"] >= str(start_date)) & 
                           (main_df["order_purchase_timestamp"] <= str(end_date))]

# --- 4. SIAPKAN DATA UNTUK GRAFIK (BERDASARKAN DATA FILTERED) ---
category_revenue = create_category_revenue_df(main_df_filtered)
review_by_delivery = create_review_delivery_df(main_df_filtered, order_reviews_df)
rfm = create_rfm_df(main_df_filtered, main_df) # Menggunakan data terfilter

# --- 5. TAMPILKAN UI ---
st.title("E-Commerce Dashboard")

# Row 1: Metrics
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Total Orders", value=main_df_filtered.order_id.nunique())
with col2:
    st.metric("Total Revenue", value=f"{main_df_filtered.payment_value.sum():,.2f}")
with col3:
    st.metric("Total Customers", value=main_df_filtered.customer_unique_id.nunique())

# Bagian Visualisasi (Gunakan bar plot seperti yang sudah kamu buat sebelumnya)
st.header("Performa Kategori Produk")
fig, ax = plt.subplots(figsize=(10, 5))
sns.barplot(x="payment_value", y="product_category_name_english", data=category_revenue.head(5), palette="viridis", ax=ax)
st.pyplot(fig)

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