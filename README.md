# 📊 Data Profiler – Interactive Data Profiling Tool

## Project Overview

**Data Profiler** is an interactive web application built using **Streamlit** that helps users quickly understand and explore datasets.  
The tool allows users to upload a CSV file and automatically generates **data summaries, missing value reports, descriptive statistics, visualizations, and correlations**.

This project simulates a real-world **data analyst utility tool** used during the **Exploratory Data Analysis (EDA)** phase.

---

## Key Features

- Upload and analyze any CSV file
- Preview dataset with interactive table
- Display dataset shape and column data types
- Detect and report missing values
- Generate descriptive statistics
- Plot numeric distributions (histograms with KDE)
- Analyze categorical value distributions
- Visualize correlation matrix using heatmaps
- Fully interactive and user-friendly interface

---

## Technologies Used

- **Python**
- **Streamlit** – Interactive web application framework
- **Pandas** – Data manipulation and analysis
- **Seaborn** – Statistical data visualization
- **Matplotlib** – Plotting and chart rendering

---

## How the Application Works

1. User uploads a CSV file
2. The dataset is loaded using Pandas
3. Basic metadata such as shape and column types are displayed
4. Missing values are identified column-wise
5. Descriptive statistics are generated for numeric data
6. Users can select numeric columns to view distribution plots
7. Users can select categorical columns to view value counts
8. Correlation matrix is displayed when sufficient numeric columns exist

---

## Use Case

This tool is useful for:

- Exploratory Data Analysis (EDA)
- Data quality assessment
- Understanding dataset structure
- Identifying missing data issues
- Supporting data preprocessing decisions
