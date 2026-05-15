"""Parsers for financial documents (CSV and PDF)."""

import os
from typing import Dict, Any

import pandas as pd

try:
    import pdfplumber
except ImportError:
    pdfplumber = None

from financial_document_analyzer.core import build_metrics_dict, _normalize_key, _extract_numeric


# Column name mappings: normalized key -> list of possible column names
REVENUE_KEYS = ["revenue", "total_revenue", "revenues", "total sales", "sales", "turnover", "net sales", "net_revenue"]
COGS_KEYS = ["cost of goods", "cogs", "cost of goods sold", "cost of revenue", "cost_of_goods"]
GROSS_PROFIT_KEYS = ["gross profit", "gross_profit", "gross margin", "gross_margin"]
OPERATING_INCOME_KEYS = [
    "operating income", "operating_income", "operating profit", "operating_profit",
    "ebit", "income from operations", "income_from_operations",
]
NET_INCOME_KEYS = [
    "net income", "net_income", "net profit", "net_profit",
    "profit for the period", "profit_for_the_period", "bottom line",
    "earnings", "net earnings", "net_earnings",
]


def _find_column(df: pd.DataFrame, keys: list) -> str:
    """Find a column in the DataFrame matching one of the given keys.

    Prioritizes exact matches over partial matches.
    """
    # Exact match first
    for col in df.columns:
        norm = _normalize_key(col)
        if norm in keys:
            return col
    # Partial match — only match if the key is a substring of the column name
    # (not the other way around, to avoid "cost of revenue" matching "Revenue")
    for col in df.columns:
        norm = _normalize_key(col)
        for key in keys:
            if key in norm:
                return col
    return ""


def parse_csv(file_path: str) -> Dict[str, Any]:
    """Parse a financial CSV file and extract key metrics.

    Handles both standard formats:
    - Standard: columns are metrics (Revenue, COGS, etc.), rows are periods
    - Transposed: rows are line items (Revenue, COGS, etc.), columns are periods

    Args:
        file_path: Path to the CSV file.

    Returns:
        A dict with keys: filename, metrics, margins, raw_rows.
    """
    if not os.path.isfile(file_path):
        raise FileNotFoundError(f"CSV file not found: {file_path}")

    try:
        df = pd.read_csv(file_path)
    except pd.errors.EmptyDataError:
        df = pd.DataFrame()

    raw_rows = len(df)
    if df.empty:
        return build_metrics_dict(os.path.basename(file_path))

    def _extract_metrics(df: pd.DataFrame) -> Dict[str, float]:
        is_transposed = False
        for col in df.columns:
            vals = df[col].dropna().astype(str).str.strip().str.lower()
            for key in REVENUE_KEYS + COGS_KEYS + GROSS_PROFIT_KEYS + OPERATING_INCOME_KEYS + NET_INCOME_KEYS:
                if vals.str.contains(key, regex=False).any():
                    is_transposed = True
                    break
            if is_transposed:
                break

        if is_transposed:
            # Pivot: find the column that contains the metrics
            non_numeric_cols = []
            for col in df.columns:
                try:
                    pd.to_numeric(df[col].astype(str).str.replace(r'[^\d.-]', '', regex=True))
                except Exception:
                    non_numeric_cols.append(col)
            
            pivot_col = non_numeric_cols[0] if non_numeric_cols else df.columns[0]
            df_pivot = df.set_index(pivot_col).T
        else:
            df_pivot = df

        rev_col = _find_column(df_pivot, REVENUE_KEYS)
        cogs_col = _find_column(df_pivot, COGS_KEYS)
        gp_col = _find_column(df_pivot, GROSS_PROFIT_KEYS)
        op_col = _find_column(df_pivot, OPERATING_INCOME_KEYS)
        ni_col = _find_column(df_pivot, NET_INCOME_KEYS)

        def _first_nonzero(col_name: str) -> float:
            if not col_name:
                return 0.0
            series = df_pivot[col_name].apply(lambda x: _extract_numeric(str(x)) if pd.notna(x) else 0.0)
            nonzero = series[series != 0]
            if len(nonzero) == 0:
                return 0.0
            return float(nonzero.iloc[0])

        revenue = _first_nonzero(rev_col)
        cogs = _first_nonzero(cogs_col)
        gross_profit = _first_nonzero(gp_col)
        operating_income = _first_nonzero(op_col)
        net_income = _first_nonzero(ni_col)

        if gross_profit == 0 and revenue != 0 and cogs != 0:
            gross_profit = revenue - cogs

        return {
            "revenue": revenue,
            "cogs": cogs,
            "gross_profit": gross_profit,
            "operating_income": operating_income,
            "net_income": net_income,
        }

    metrics = _extract_metrics(df)

    return build_metrics_dict(
        filename=os.path.basename(file_path),
        revenue=metrics["revenue"],
        cogs=metrics["cogs"],
        gross_profit=metrics["gross_profit"],
        operating_income=metrics["operating_income"],
        net_income=metrics["net_income"],
        raw_rows=raw_rows,
    )


def parse_pdf(file_path: str) -> Dict[str, Any]:
    """Parse a financial PDF file and extract key metrics.

    Uses pdfplumber to extract tables, then searches for financial line items.

    Args:
        file_path: Path to the PDF file.

    Returns:
        A dict with keys: filename, metrics, margins, raw_rows.
    """
    if not os.path.isfile(file_path):
        raise FileNotFoundError(f"PDF file not found: {file_path}")

    if pdfplumber is None:
        raise ImportError("pdfplumber is required for PDF parsing. Install with: pip install pdfplumber")

    all_rows = []
    all_headers = []

    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            tables = page.extract_tables()
            for table in tables:
                # Filter out empty rows
                table = [row for row in table if any(cell is not None and str(cell).strip() for cell in row)]
                if not table:
                    continue
                # First row is typically the header
                if len(table) > 1:
                    header = [str(cell).strip() if cell else "" for cell in table[0]]
                    all_headers.append(header)
                    rows = table[1:]
                    for row in rows:
                        # Pad row to match header length
                        while len(row) < len(header):
                            row.append("")
                        all_rows.append(row)

    if not all_rows:
        raise ValueError("No tables found in the PDF")

    # Use the first header found
    if not all_headers:
        raise ValueError("No table headers found in the PDF")

    headers = all_headers[0]

    # Create DataFrame
    df = pd.DataFrame(all_rows, columns=headers)

    # Clean up: remove rows where all cells are empty
    df = df.dropna(how='all')
    df = df.map(lambda x: str(x).strip() if isinstance(x, str) else x)
    df = df[df.apply(lambda row: any(str(cell).strip() for cell in row), axis=1)]

    raw_rows = len(df)

    # Normalize column names
    df.columns = [_normalize_key(c) for c in df.columns]

    def _extract_metrics(df: pd.DataFrame) -> Dict[str, float]:
        is_transposed = False
        for col in df.columns:
            vals = df[col].dropna().astype(str).str.strip().str.lower()
            for key in REVENUE_KEYS + COGS_KEYS + GROSS_PROFIT_KEYS + OPERATING_INCOME_KEYS + NET_INCOME_KEYS:
                if vals.str.contains(key, regex=False).any():
                    is_transposed = True
                    break
            if is_transposed:
                break

        if is_transposed:
            # Pivot: find the column that contains the metrics
            non_numeric_cols = []
            for col in df.columns:
                try:
                    pd.to_numeric(df[col].astype(str).str.replace(r'[^\d.-]', '', regex=True))
                except Exception:
                    non_numeric_cols.append(col)
            
            pivot_col = non_numeric_cols[0] if non_numeric_cols else df.columns[0]
            df_pivot = df.set_index(pivot_col).T
        else:
            df_pivot = df

        rev_col = _find_column(df_pivot, REVENUE_KEYS)
        cogs_col = _find_column(df_pivot, COGS_KEYS)
        gp_col = _find_column(df_pivot, GROSS_PROFIT_KEYS)
        op_col = _find_column(df_pivot, OPERATING_INCOME_KEYS)
        ni_col = _find_column(df_pivot, NET_INCOME_KEYS)

        def _first_nonzero(col_name: str) -> float:
            if not col_name:
                return 0.0
            series = df_pivot[col_name].apply(lambda x: _extract_numeric(str(x)) if pd.notna(x) else 0.0)
            nonzero = series[series != 0]
            if len(nonzero) == 0:
                return 0.0
            return float(nonzero.iloc[0])

        revenue = _first_nonzero(rev_col)
        cogs = _first_nonzero(cogs_col)
        gross_profit = _first_nonzero(gp_col)
        operating_income = _first_nonzero(op_col)
        net_income = _first_nonzero(ni_col)

        if gross_profit == 0 and revenue != 0 and cogs != 0:
            gross_profit = revenue - cogs

        return {
            "revenue": revenue,
            "cogs": cogs,
            "gross_profit": gross_profit,
            "operating_income": operating_income,
            "net_income": net_income,
        }

    metrics = _extract_metrics(df)

    return build_metrics_dict(
        filename=os.path.basename(file_path),
        revenue=metrics["revenue"],
        cogs=metrics["cogs"],
        gross_profit=metrics["gross_profit"],
        operating_income=metrics["operating_income"],
        net_income=metrics["net_income"],
        raw_rows=raw_rows,
    )
