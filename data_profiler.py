"""Interactive Streamlit entry point for profiling, quality checks, and cleaning."""

from __future__ import annotations

from io import BytesIO
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
import streamlit as st

from data_quality import (
    clean_dataframe,
    dataframe_csv_bytes,
    detect_outliers,
    duplicate_summary,
    html_report,
    generate_insights,
    missing_value_summary,
    quality_metrics,
)


st.set_page_config(page_title="Data Profiler", page_icon="📊", layout="wide")
st.markdown(
    """
    <style>
    .block-container {padding-top: 2rem; padding-bottom: 3rem; max-width: 1400px;}
    .hero {padding: 1.5rem 1.75rem; border-radius: 18px; background: linear-gradient(120deg, #123b5d, #197278); color: white; margin-bottom: 1.5rem;}
    .hero h1 {margin: 0; font-size: 2.25rem;}
    .hero p {margin: .5rem 0 0; color: #e3f5f3;}
    [data-testid="stMetric"] {background: #f5f8fa; border: 1px solid #e4ebef; padding: .8rem; border-radius: 12px;}
    </style>
    """,
    unsafe_allow_html=True,
)
st.markdown(
    '<div class="hero"><h1>Interactive Data Profiling</h1>'
    "<p>Explore patterns, identify quality issues, and apply controlled cleaning operations.</p></div>",
    unsafe_allow_html=True,
)


@st.cache_data(show_spinner=False)
def read_csv(uploaded: bytes) -> tuple[pd.DataFrame, str]:
    """Read common CSV encodings while preserving pandas' duplicate-column handling."""
    errors: list[str] = []
    for encoding in ("utf-8-sig", "utf-8", "cp1252", "latin-1"):
        try:
            frame = pd.read_csv(BytesIO(uploaded), encoding=encoding)
            if frame.shape[1] == 0:
                raise ValueError("The file has no columns.")
            return frame, encoding
        except (UnicodeDecodeError, pd.errors.ParserError, ValueError) as exc:
            errors.append(f"{encoding}: {exc}")
    raise ValueError("Could not parse this CSV file. " + " | ".join(errors))


@st.cache_data(show_spinner=False)
def excel_sheets(uploaded: bytes) -> list[str]:
    """Return workbook sheet names without loading every sheet into the app."""
    try:
        return pd.ExcelFile(BytesIO(uploaded)).sheet_names
    except (ImportError, OSError, ValueError) as exc:
        raise ValueError(f"Could not open this Excel workbook: {exc}") from exc


@st.cache_data(show_spinner=False)
def read_excel(uploaded: bytes, sheet_name: str) -> pd.DataFrame:
    """Read one selected Excel sheet as a DataFrame."""
    try:
        frame = pd.read_excel(BytesIO(uploaded), sheet_name=sheet_name)
    except (ImportError, OSError, ValueError, pd.errors.ParserError) as exc:
        raise ValueError(f"Could not read the selected Excel sheet: {exc}") from exc
    if frame.shape[1] == 0:
        raise ValueError("The selected Excel sheet has no columns.")
    return frame


def numeric_columns(frame: pd.DataFrame) -> list[str]:
    return frame.select_dtypes(include="number").columns.tolist()


def categorical_columns(frame: pd.DataFrame) -> list[str]:
    return frame.select_dtypes(include=["object", "string", "category", "bool"]).columns.tolist()


def show_overview(frame: pd.DataFrame) -> None:
    summary = {
        "Rows": len(frame),
        "Columns": len(frame.columns),
        "Numeric": len(numeric_columns(frame)),
        "Categorical": len(categorical_columns(frame)),
        "Date/time": len(frame.select_dtypes(include=["datetime", "datetimetz"]).columns),
        "Duplicate rows": int(frame.duplicated().sum()),
        "Memory (MB)": round(frame.memory_usage(deep=True).sum() / 1024**2, 2),
    }
    cards = st.columns(len(summary))
    for card, (label, value) in zip(cards, summary.items()):
        card.metric(label, value)
    st.dataframe(
        pd.DataFrame({"column": frame.columns, "dtype": frame.dtypes.astype(str).values}),
        use_container_width=True,
        hide_index=True,
    )


def show_missing(frame: pd.DataFrame) -> pd.DataFrame:
    treat_blank = st.checkbox("Treat empty and whitespace-only text as missing", value=True)
    missing = missing_value_summary(frame, treat_blank)
    st.dataframe(missing, use_container_width=True, hide_index=True)
    nonzero = missing[missing["missing_count"] > 0]
    if nonzero.empty:
        st.success("No missing values detected using the selected rule.")
    else:
        st.bar_chart(nonzero.set_index("column")["missing_percent"])
        high = nonzero[nonzero["missing_percent"] >= 50]
        if not high.empty:
            st.warning("High missingness: " + ", ".join(high["column"].tolist()))
    return missing


def show_statistics(frame: pd.DataFrame) -> None:
    st.dataframe(frame.describe(include="all").transpose(), use_container_width=True)
    for column in categorical_columns(frame):
        with st.expander(f"Frequencies: {column}"):
            top_n = st.slider(f"Top categories for {column}", 3, 50, 10, key=f"top_{column}")
            counts = frame[column].astype("string").value_counts(dropna=False).head(top_n)
            st.dataframe(
                pd.DataFrame({"count": counts, "percent": (counts / max(len(frame), 1) * 100).round(2)}),
                use_container_width=True,
            )


def show_distributions(frame: pd.DataFrame) -> None:
    columns = numeric_columns(frame)
    selected = st.multiselect("Select numeric columns", columns, key="distribution_columns")
    chart = st.selectbox("Chart type", ["Histogram", "Box plot", "Density plot"])
    for column in selected:
        values = pd.to_numeric(frame[column], errors="coerce").dropna()
        if len(values) < 2 or values.nunique() < 2:
            st.info(f"`{column}` has insufficient valid variation for a distribution chart.")
            continue
        fig, ax = plt.subplots(figsize=(8, 4))
        if chart == "Box plot":
            sns.boxplot(x=values, ax=ax)
        elif chart == "Density plot":
            sns.kdeplot(x=values, fill=True, ax=ax)
        else:
            sns.histplot(x=values, kde=True, ax=ax)
        ax.set_title(f"{chart}: {column}")
        ax.set_xlabel(column)
        st.pyplot(fig, clear_figure=True)
        plt.close(fig)


def show_correlation(frame: pd.DataFrame) -> None:
    columns = numeric_columns(frame)
    if len(columns) < 2:
        st.info("At least two numeric columns are required for correlation analysis.")
        return
    selected = st.multiselect("Select columns", columns, default=columns, key="correlation_columns")
    method = st.selectbox("Method", ["pearson", "spearman"])
    if len(selected) < 2:
        st.info("Select at least two columns.")
        return
    corr = frame[selected].corr(method=method).replace([np.inf, -np.inf], pd.NA).dropna(how="all").dropna(axis=1, how="all")
    if corr.empty:
        st.info("There are not enough valid observations for correlation.")
        return
    fig, ax = plt.subplots(figsize=(max(6, len(selected)), 5))
    sns.heatmap(corr, annot=True, fmt=".2f", cmap="coolwarm", vmin=-1, vmax=1, ax=ax)
    st.pyplot(fig, clear_figure=True)
    plt.close(fig)
    pairs = corr.where(~np.tril(np.ones(corr.shape), 0).astype(bool)).stack()
    if not pairs.empty:
        strongest = pairs.abs().sort_values(ascending=False).index[0]
        st.caption(f"Strongest observed relationship: {strongest[0]} and {strongest[1]} ({pairs[strongest]:.2f}). Correlation does not establish causation.")


def show_quality(frame: pd.DataFrame) -> None:
    metrics = quality_metrics(frame)
    st.metric("Overall heuristic quality score", f"{metrics['overall']}/100")
    st.caption("This transparent score is not an industry standard and does not prove that data is accurate.")
    cards = st.columns(4)
    for card, key in zip(cards, ("completeness", "uniqueness", "validity", "consistency")):
        card.metric(key.title(), f"{metrics[key]}/100")
    st.dataframe(pd.DataFrame([metrics]), use_container_width=True, hide_index=True)
    duplicates = duplicate_summary(frame)
    if duplicates["duplicate_rows"]:
        st.warning(f"{duplicates['duplicate_rows']} rows belong to exact duplicate groups.")
        st.dataframe(frame[duplicates["mask"]].head(100), use_container_width=True)


def show_outliers(frame: pd.DataFrame) -> None:
    columns = st.multiselect("Columns to inspect", numeric_columns(frame), key="outlier_columns")
    method = st.selectbox("Detection method", ["IQR", "Z-score"])
    if not columns:
        st.info("Select one or more numeric columns.")
        return
    mask = detect_outliers(frame, columns, method)
    flagged = mask.any(axis=1)
    st.write(f"Flagged rows: {int(flagged.sum())} (review only; nothing is deleted automatically)")
    st.dataframe(frame.loc[flagged].head(100), use_container_width=True)


def show_cleaning(frame: pd.DataFrame) -> tuple[pd.DataFrame, list[dict[str, Any]]]:
    st.write("All operations apply to a working copy and are previewed before download.")
    trim = st.checkbox("Trim text whitespace", key="trim")
    case = st.checkbox("Standardize text capitalization", key="case")
    fill = st.selectbox("Missing-value method", ["None", "Mean", "Median", "Mode", "Custom"])
    custom = st.text_input("Custom value", disabled=fill != "Custom")
    remove = st.checkbox("Remove exact duplicate rows", key="remove_duplicates")
    preview, operations = clean_dataframe(
        frame, trim_text=trim, standardize_case=case, fill_method=fill, custom_value=custom, remove_duplicates=remove
    )
    if operations:
        st.dataframe(pd.DataFrame(operations), use_container_width=True, hide_index=True)
        st.write("Preview")
        st.dataframe(preview.head(100), use_container_width=True)
    else:
        st.info("Select a cleaning operation to generate a preview.")
    return preview, operations


uploaded_file = st.file_uploader(
    "Upload a dataset",
    type=["csv", "xlsx", "xls"],
    help="Supported formats: CSV, modern Excel (.xlsx), and legacy Excel (.xls).",
)
if uploaded_file is None:
    st.info("Upload a CSV or Excel file to begin. Your data stays in this application.")
else:
    if uploaded_file.size == 0:
        st.error("The uploaded file is empty.")
        st.stop()
    uploaded_bytes = uploaded_file.getvalue()
    extension = Path(uploaded_file.name).suffix.lower()
    selected_sheet = ""
    if extension in {".xlsx", ".xls"}:
        try:
            sheet_names = excel_sheets(uploaded_bytes)
        except ValueError as exc:
            st.error(str(exc))
            st.stop()
        if not sheet_names:
            st.error("The Excel workbook does not contain any worksheets.")
            st.stop()
        selected_sheet = st.selectbox(
            "Choose a worksheet",
            sheet_names,
            help="Only the selected worksheet is analyzed. You can switch sheets at any time.",
        )
        try:
            original = read_excel(uploaded_bytes, selected_sheet)
        except ValueError as exc:
            st.error(str(exc))
            st.stop()
        source_label = f"{uploaded_file.name} / {selected_sheet}"
        encoding = "Excel"
    else:
        try:
            original, encoding = read_csv(uploaded_bytes)
        except ValueError as exc:
            st.error(str(exc))
            st.stop()
        source_label = uploaded_file.name
    if original.empty:
        st.error("The CSV contains headers but no data rows.")
        st.stop()
    st.success(f"Loaded {source_label}" + (f" using {encoding} encoding." if encoding != "Excel" else "."))
    if "working" not in st.session_state or st.session_state.get("source_name") != source_label:
        st.session_state.working = original.copy(deep=True)
        st.session_state.source_name = source_label
        st.session_state.operations = []
    working = st.session_state.working
    st.download_button("Download original data as CSV", dataframe_csv_bytes(original), "original_data.csv", "text/csv")
    tabs = st.tabs(["Overview", "Missing values", "Statistics", "Distributions", "Correlation", "Quality", "Outliers", "Cleaning", "Report"])
    with tabs[0]:
        st.subheader("Dataset preview")
        rows = st.slider("Preview rows", 1, min(100, max(1, len(working))), min(10, len(working)))
        st.dataframe(working.head(rows), use_container_width=True)
        show_overview(working)
        st.subheader("Evidence-based insights")
        insights = generate_insights(working)
        if insights:
            for insight in insights:
                st.write(f"- {insight}")
        else:
            st.info("No insights can be generated from the available columns.")
    with tabs[1]:
        show_missing(working)
    with tabs[2]:
        show_statistics(working)
    with tabs[3]:
        show_distributions(working)
    with tabs[4]:
        show_correlation(working)
    with tabs[5]:
        show_quality(working)
    with tabs[6]:
        show_outliers(working)
    with tabs[7]:
        preview, operations = show_cleaning(working)
        if operations and st.button("Apply cleaning to working copy"):
            st.session_state.working = preview
            st.session_state.operations.extend(operations)
            st.rerun()
        if st.button("Reset working copy"):
            st.session_state.working = original.copy(deep=True)
            st.session_state.operations = []
            st.rerun()
        st.download_button("Download cleaned CSV", dataframe_csv_bytes(working), "cleaned_data.csv", "text/csv")
    with tabs[8]:
        metrics = quality_metrics(working)
        missing = missing_value_summary(working)
        report = html_report(working, metrics, missing, st.session_state.operations)
        st.download_button("Download HTML report", report, "data_profiler_report.html", "text/html")
        st.components.v1.html(report, height=500, scrolling=True)
