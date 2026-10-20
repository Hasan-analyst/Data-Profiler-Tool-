import streamlit as st
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

st.set_page_config(page_title="Data Profiler", layout="centered")
st.title("📊 Interactive Data Profiling Tool")

# Upload CSV
uploaded_file = st.file_uploader("Upload your CSV file", type=["csv"])

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    st.success("File uploaded successfully!")

    # Show DataFrame
    st.subheader("🔎 Preview of Data")
    st.dataframe(df.head())

    # Data Summary
    st.subheader("📄 Dataset Summary")
    st.write(f"Shape: {df.shape[0]} rows, {df.shape[1]} columns")
    st.write("Column Types:")
    st.write(df.dtypes)

    # Missing values
    st.subheader("🚫 Missing Values")
    missing = df.isnull().sum()
    st.write(missing[missing > 0])

    # Descriptive stats
    st.subheader("📊 Descriptive Statistics")
    st.write(df.describe())

    # Distribution plots
    st.subheader("📈 Numeric Column Distributions")
    numeric_cols = df.select_dtypes(include='number').columns.tolist()
    selected_num = st.multiselect("Select numeric columns", numeric_cols)

    for col in selected_num:
        st.write(f"📌 Histogram for `{col}`")
        fig, ax = plt.subplots()
        sns.histplot(df[col].dropna(), kde=True, ax=ax)
        st.pyplot(fig)

    # Value counts for categorical
    st.subheader("🧾 Categorical Columns")
    cat_cols = df.select_dtypes(include='object').columns.tolist()
    selected_cat = st.multiselect("Select categorical columns", cat_cols)

    for col in selected_cat:
        st.write(f"📌 Value Counts for `{col}`")
        st.bar_chart(df[col].value_counts())

    # Correlation matrix
    st.subheader("🔗 Correlation Matrix")
    if len(numeric_cols) >= 2:
        corr = df[numeric_cols].corr()
        fig, ax = plt.subplots(figsize=(10, 6))
        sns.heatmap(corr, annot=True, cmap="coolwarm", ax=ax)
        st.pyplot(fig)
    else:
        st.info("Not enough numeric columns for correlation matrix.")
