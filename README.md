# Data Profiler

## Interactive Data Profiling, Quality, Cleaning, and EDA Application

Data Profiler is a local Streamlit application that helps users understand datasets, identify data-quality problems, explore patterns, apply controlled cleaning operations, and export useful results.

The application supports both CSV and Excel files. Uploaded data is processed locally by the application and is not sent to an external service.

---

## Current project status

The project currently includes:

- CSV file support
- Excel workbook support
- Excel worksheet selection
- Dataset profiling and exploratory analysis
- Missing-value analysis
- Duplicate detection
- Outlier detection
- Data-quality scoring
- Controlled data cleaning
- Automated dataset insights
- HTML report generation
- Original and cleaned CSV downloads
- Responsive Streamlit dashboard styling

The application is ready to run locally with Streamlit.

---

## Main features

### 1. CSV and Excel upload

The application accepts:

- `.csv`
- `.xlsx`
- `.xls`

For CSV files, the application attempts these encodings:

- UTF-8 with BOM
- UTF-8
- Windows CP1252
- Latin-1

For Excel workbooks:

- A worksheet selector is displayed
- Only the selected worksheet is analyzed
- The worksheet can be changed without changing the rest of the application

The application validates:

- Empty uploaded files
- CSV parsing errors
- Empty datasets
- Excel workbook errors
- Excel files without worksheets
- Excel worksheets without columns

---

### 2. Dataset overview

The Overview section displays:

- Interactive data preview
- Configurable preview row count
- Total rows
- Total columns
- Numeric-column count
- Categorical-column count
- Date/time-column count
- Duplicate-row count
- Approximate memory usage
- Column names
- Inferred data types

The original uploaded dataset is kept separate from the cleaning working copy.

---

### 3. Missing-value analysis

The Missing values section provides:

- Missing count for every column
- Missing percentage for every column
- Optional detection of empty strings
- Optional detection of whitespace-only values
- Missing-value bar chart
- High-missingness warning for columns with at least 50% missing values

The missing-value analysis does not modify the source dataset.

---

### 4. Descriptive statistics

The Statistics section provides:

- Count
- Mean
- Standard deviation
- Minimum
- Quartiles
- Median
- Maximum
- Statistics for suitable numeric and categorical columns
- Frequency summaries for categorical columns
- Configurable Top-N category selection

Columns that are not suitable for a particular calculation are handled by Pandas and displayed where appropriate.

---

### 5. Numeric distributions

The Distributions section allows users to select numeric columns and choose:

- Histogram
- Box plot
- Density plot

Charts include:

- Clear titles
- Column labels
- Responsive sizing
- Missing-value-safe calculations

Columns with too few valid values or no meaningful variation are reported instead of producing misleading charts.

---

### 6. Correlation analysis

The Correlation section supports:

- Pearson correlation
- Spearman correlation
- Numeric-column selection
- Annotated correlation heatmaps
- Correlation values between -1 and 1
- Strongest observed relationship summary

The application displays a reminder that correlation does not establish causation.

Constant columns and insufficient numeric data are handled safely.

---

### 7. Data-quality dashboard

The Quality section calculates a transparent heuristic score out of 100 using:

- Completeness
- Uniqueness
- Validity
- Consistency

It also reports:

- Missing cells
- Duplicate rows
- Blank text values
- Text-label inconsistencies

The quality score is diagnostic only. It is not an industry-standard score and does not prove that the dataset is accurate, complete, or fit for a particular purpose.

---

### 8. Duplicate detection

The application detects exact duplicate rows and displays:

- Duplicate-row count
- Duplicate percentage
- Duplicate groups
- Preview of duplicated records

Duplicates are not removed automatically. They can be removed only from the cleaning working copy after the user selects that operation.

---

### 9. Outlier detection

The Outliers section supports:

- IQR detection
- Z-score detection
- User-selected numeric columns
- Flagged-row count
- Flagged-record preview

Outlier detection is intended for review. The application never deletes outliers automatically.

---

### 10. Cleaning workspace

The Cleaning section works on a separate working copy.

Available operations:

- Trim text whitespace
- Standardize text capitalization
- Fill missing numeric values with the mean
- Fill missing numeric values with the median
- Fill missing values with the mode
- Fill missing values with a custom value
- Remove exact duplicate rows

Cleaning workflow:

1. Select one or more cleaning operations.
2. Review the operation log.
3. Review the cleaned-data preview.
4. Apply the changes to the working copy.
5. Download the cleaned CSV if required.

The original uploaded data is not changed.

The cleaning workspace also provides:

- Reset working copy
- Affected-column information
- Affected-row counts
- Before/after operation information
- Cleaned CSV download

---

### 11. Automated insights

The application generates insights from actual calculated values, including:

- Highest numeric average
- Lowest numeric average
- Most frequent categorical values
- Columns with substantial missingness
- Strongest numeric correlation

Insights are not generated from fixed or fabricated text. If the dataset does not contain enough suitable information, the application shows an appropriate empty state.

---

### 12. Downloadable report

The Report section generates a self-contained HTML report containing:

- Dataset size
- Data-quality score
- Quality components
- Column data types
- Missing-value analysis
- Descriptive statistics
- Cleaning-operation log

The application also provides:

- Original data download as CSV
- Cleaned data download as CSV

Excel uploads are analyzed correctly, but downloaded original and cleaned files are currently exported as CSV for consistent behavior.

---

## Technology stack

- Python 3.10+
- Streamlit
- Pandas
- NumPy
- Matplotlib
- Seaborn
- OpenPyXL for `.xlsx` files
- xlrd for `.xls` files

Dependencies are listed in [requirements.txt](./requirements.txt).

---

## Project structure

```text
TCS XPLORE LEAGUE/
├── data_profiler.py      # Streamlit user interface and application flow
├── data_quality.py       # Data-quality, cleaning, insight, and report helpers
├── requirements.txt      # Python dependencies
├── README.md             # Project documentation
└── students.csv          # Optional sample dataset
```

Generated folders such as `__pycache__`, `.pytest_cache`, and virtual environments are not required by the application and should not be committed.

---

## Installation

Open PowerShell in the project directory:

Install the dependencies:

```powershell
python -m pip install -r requirements.txt
``
```

---

## Run the application

```powershell
streamlit run data_profiler.py
```

Streamlit will display a local address, normally:

```text
http://localhost:8501
```

Open that address in a browser and upload a CSV or Excel file.

---

## Recommended user workflow

1. Upload a CSV or Excel file.
2. Select an Excel worksheet if the file has multiple sheets.
3. Review the Overview tab.
4. Check missing values and duplicate records.
5. Review statistics and visualizations.
6. Inspect correlations and possible outliers.
7. Open the Quality tab to understand the quality indicators.
8. Use the Cleaning tab to preview controlled changes.
9. Apply the selected cleaning operations to the working copy.
10. Download the cleaned CSV.
11. Download the HTML analysis report.

---

## Important behavior and limitations

- Only one Excel worksheet is analyzed at a time.
- Excel uploads are currently downloaded as CSV files.
- Cleaning operations apply to a working copy, not the original upload.
- Outliers are flagged for review and are never deleted automatically.
- The quality score is a heuristic diagnostic and is not an accuracy guarantee.
- Correlation results do not prove causation.
- Automatic type conversion is not currently applied to every possible text/date column.
- Large files may require additional memory depending on the computer and available resources.
- The application does not transmit uploaded datasets to external services.

---
