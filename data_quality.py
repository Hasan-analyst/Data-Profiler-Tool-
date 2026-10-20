"""Reusable data-quality and cleaning helpers for the Streamlit application."""

from __future__ import annotations

from io import StringIO
from typing import Any

import numpy as np
import pandas as pd


def missing_value_summary(
    frame: pd.DataFrame, treat_blank_as_missing: bool = True
) -> pd.DataFrame:
    """Return missing counts and percentages for every column."""
    missing = frame.isna().copy()
    if treat_blank_as_missing:
        for column in frame.select_dtypes(include=["object", "string"]).columns:
            missing[column] |= frame[column].astype("string").str.strip().eq("").fillna(False)
    counts = missing.sum().astype("int64")
    return pd.DataFrame(
        {
            "column": frame.columns,
            "missing_count": counts.to_numpy(),
            "missing_percent": (counts / max(len(frame), 1) * 100).round(2).to_numpy(),
        }
    )


def duplicate_summary(frame: pd.DataFrame) -> dict[str, Any]:
    """Summarize exact duplicate rows without changing the input frame."""
    duplicate_mask = frame.duplicated(keep=False)
    duplicate_rows = int(duplicate_mask.sum())
    return {
        "duplicate_rows": duplicate_rows,
        "duplicate_groups": int(frame.duplicated().sum()),
        "duplicate_percent": round(duplicate_rows / max(len(frame), 1) * 100, 2),
        "mask": duplicate_mask,
    }


def detect_outliers(
    frame: pd.DataFrame, columns: list[str], method: str = "IQR", z_threshold: float = 3.0
) -> pd.DataFrame:
    """Return a boolean row-by-column mask for suspected numeric outliers."""
    result = pd.DataFrame(False, index=frame.index, columns=columns)
    for column in columns:
        values = pd.to_numeric(frame[column], errors="coerce")
        valid = values.dropna()
        if len(valid) < 4 or valid.nunique() < 2:
            continue
        if method == "Z-score":
            std = valid.std()
            if std == 0 or pd.isna(std):
                continue
            result.loc[valid.index, column] = ((valid - valid.mean()).abs() / std) > z_threshold
        else:
            first, third = valid.quantile([0.25, 0.75])
            spread = third - first
            if spread == 0 or pd.isna(spread):
                continue
            result.loc[valid.index, column] = (valid < first - 1.5 * spread) | (
                valid > third + 1.5 * spread
            )
    return result


def quality_metrics(frame: pd.DataFrame) -> dict[str, Any]:
    """Calculate transparent, heuristic quality indicators on a 0-100 scale."""
    cells = max(frame.shape[0] * frame.shape[1], 1)
    missing_cells = int(frame.isna().sum().sum())
    completeness = max(0.0, 100.0 * (1 - missing_cells / cells))
    duplicates = int(frame.duplicated().sum())
    uniqueness = max(0.0, 100.0 * (1 - duplicates / max(len(frame), 1)))

    invalid = 0
    for column in frame.select_dtypes(include=["object", "string"]).columns:
        values = frame[column].dropna().astype("string")
        invalid += int(values.str.strip().eq("").sum())
    validity = max(0.0, 100.0 * (1 - invalid / cells))

    inconsistencies = 0
    for column in frame.select_dtypes(include=["object", "string"]).columns:
        values = frame[column].dropna().astype("string")
        inconsistencies += int(values.nunique() - values.str.strip().str.casefold().nunique())
    consistency = max(0.0, 100.0 * (1 - inconsistencies / max(len(frame), 1)))
    overall = round((completeness + uniqueness + validity + consistency) / 4, 2)
    return {
        "overall": overall,
        "completeness": round(completeness, 2),
        "uniqueness": round(uniqueness, 2),
        "validity": round(validity, 2),
        "consistency": round(consistency, 2),
        "missing_cells": missing_cells,
        "duplicate_rows": duplicates,
        "blank_values": invalid,
        "inconsistencies": inconsistencies,
    }


def clean_dataframe(
    frame: pd.DataFrame,
    *,
    trim_text: bool = False,
    standardize_case: bool = False,
    fill_method: str = "None",
    custom_value: str = "",
    remove_duplicates: bool = False,
) -> tuple[pd.DataFrame, list[dict[str, Any]]]:
    """Apply explicit cleaning operations to a copy and return an operation log."""
    cleaned = frame.copy(deep=True)
    operations: list[dict[str, Any]] = []
    text_columns = cleaned.select_dtypes(include=["object", "string"]).columns

    if trim_text:
        affected = 0
        for column in text_columns:
            before = cleaned[column].copy()
            cleaned[column] = cleaned[column].astype("string").str.strip()
            affected += int((before.fillna("") != cleaned[column].fillna("")).sum())
        operations.append({"action": "Trim whitespace", "columns": list(text_columns), "rows": affected})

    if standardize_case:
        affected = 0
        for column in text_columns:
            before = cleaned[column].copy()
            cleaned[column] = cleaned[column].astype("string").str.title()
            affected += int((before.fillna("") != cleaned[column].fillna("")).sum())
        operations.append(
            {"action": "Standardize text capitalization", "columns": list(text_columns), "rows": affected}
        )

    if fill_method != "None":
        columns: list[str] = []
        affected = 0
        for column in cleaned.columns:
            missing = cleaned[column].isna()
            if not missing.any():
                continue
            if fill_method == "Mean" and pd.api.types.is_numeric_dtype(cleaned[column]):
                value = cleaned[column].mean()
            elif fill_method == "Median" and pd.api.types.is_numeric_dtype(cleaned[column]):
                value = cleaned[column].median()
            elif fill_method == "Mode":
                modes = cleaned[column].mode(dropna=True)
                value = modes.iloc[0] if not modes.empty else None
            elif fill_method == "Custom":
                value = custom_value
            else:
                continue
            if value is not None and not pd.isna(value):
                cleaned.loc[missing, column] = value
                columns.append(column)
                affected += int(missing.sum())
        operations.append({"action": f"Fill missing values ({fill_method})", "columns": columns, "rows": affected})

    if remove_duplicates:
        before = len(cleaned)
        cleaned = cleaned.drop_duplicates().reset_index(drop=True)
        operations.append({"action": "Remove exact duplicate rows", "columns": [], "rows": before - len(cleaned)})
    return cleaned, operations


def dataframe_csv_bytes(frame: pd.DataFrame) -> bytes:
    """Serialize a frame for Streamlit download without writing to disk."""
    return frame.to_csv(index=False).encode("utf-8")


def generate_insights(frame: pd.DataFrame) -> list[str]:
    """Generate short insights only when the supporting statistic is available."""
    insights: list[str] = []
    numeric = frame.select_dtypes(include="number")
    if not numeric.empty:
        means = numeric.mean(numeric_only=True).dropna()
        if not means.empty:
            highest, lowest = means.idxmax(), means.idxmin()
            insights.append(f"Highest numeric average: {highest} ({means[highest]:.2f}).")
            if highest != lowest:
                insights.append(f"Lowest numeric average: {lowest} ({means[lowest]:.2f}).")
    for column in frame.select_dtypes(include=["object", "string", "category"]).columns:
        counts = frame[column].dropna().value_counts()
        if not counts.empty:
            insights.append(f"Most frequent value in {column}: {counts.index[0]!s} ({counts.iloc[0]} rows).")
    missing = missing_value_summary(frame)
    high_missing = missing[missing["missing_percent"] >= 50]["column"].tolist()
    if high_missing:
        insights.append("At least 50% missing: " + ", ".join(high_missing) + ".")
    if len(numeric.columns) >= 2:
        correlation = numeric.corr().where(~np.tril(np.ones((len(numeric.columns), len(numeric.columns)))).astype(bool))
        pairs = correlation.stack()
        if not pairs.empty:
            pair = pairs.abs().idxmax()
            insights.append(f"Strongest numeric correlation: {pair[0]} and {pair[1]} ({pairs[pair]:.2f}).")
    return insights


def html_report(
    frame: pd.DataFrame,
    metrics: dict[str, Any],
    missing: pd.DataFrame,
    operations: list[dict[str, Any]],
) -> str:
    """Build a self-contained HTML report from computed values."""
    stats = frame.describe(include="all").transpose().fillna("")
    operation_rows = pd.DataFrame(operations)
    sections = [
        "<h1>Data Profiler Analysis Report</h1>",
        f"<p>Rows: {len(frame)} | Columns: {len(frame.columns)}</p>",
        f"<h2>Data quality score: {metrics['overall']}/100</h2>",
        pd.DataFrame([metrics]).drop(columns=["overall"]).T.to_html(header=False),
        "<h2>Column types</h2>" + pd.DataFrame(
            {"column": frame.columns, "dtype": [str(dtype) for dtype in frame.dtypes]}
        ).to_html(index=False),
        "<h2>Missing values</h2>" + missing.to_html(index=False),
        "<h2>Descriptive statistics</h2>" + stats.to_html(),
        "<h2>Cleaning operations</h2>" + (
            operation_rows.to_html(index=False) if not operation_rows.empty else "<p>None</p>"
        ),
    ]
    return "<!doctype html><html><head><meta charset='utf-8'><title>Data Profiler Report</title></head><body>" + "".join(
        sections
    ) + "</body></html>"
