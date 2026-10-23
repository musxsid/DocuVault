"""
DocuVaultAI — Catalog Manager (Unit 4: Pandas MultiIndex & Missing Value Imputation)
Manages the document catalog using a Pandas MultiIndex DataFrame (Storage_Mode, Category, Doc_ID),
providing statistical aggregations, multi-level slicing, and missing data imputation.
"""

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd


class CatalogManager:
    """
    Manages document catalog metadata with Pandas MultiIndex hierarchical indexing
    and missing data imputation strategies.
    """

    INDEX_NAMES = ["Storage_Mode", "Category", "Doc_ID"]

    COLUMNS = [
        "filename",
        "file_type",
        "size_bytes",
        "sha256_hash",
        "status",
        "created_at",
        "currency_total",
        "jurisdiction",
        "has_clauses",
        "page_count",
    ]

    def __init__(self) -> None:
        self.df: pd.DataFrame = self._create_empty_df()

    def _create_empty_df(self) -> pd.DataFrame:
        """Initializes an empty MultiIndex DataFrame."""
        empty_index = pd.MultiIndex.from_tuples([], names=self.INDEX_NAMES)
        return pd.DataFrame(columns=self.COLUMNS, index=empty_index)

    def add_document(
        self,
        doc_dict: Dict[str, Any],
        storage_mode: str = "Local Drive",
    ) -> None:
        """
        Adds or updates a document in the MultiIndex catalog.
        Extracts metadata and numerical currency values for analytics.
        """
        doc_id = str(doc_dict.get("doc_id", "unknown"))
        category = str(doc_dict.get("category", "General"))
        filename = str(doc_dict.get("filename", "untitled"))
        file_type = str(doc_dict.get("file_type", Path(filename).suffix))
        size_bytes = int(doc_dict.get("size_bytes", 0))
        sha256_hash = str(doc_dict.get("sha256_hash", ""))
        status = str(doc_dict.get("status", "Verified"))
        created_at = str(doc_dict.get("created_at", datetime.now().isoformat()))
        page_count = int(doc_dict.get("page_count", 1))

        # Parse currency amount total
        currency_amounts = doc_dict.get("currency_amounts", [])
        total_val = None
        if currency_amounts:
            numeric_vals = []
            for curr_str in currency_amounts:
                # Remove symbols and commas
                clean = "".join(ch for ch in str(curr_str) if ch.isdigit() or ch == ".")
                try:
                    numeric_vals.append(float(clean))
                except ValueError:
                    pass
            if numeric_vals:
                total_val = sum(numeric_vals)

        # Extract jurisdiction
        clauses = doc_dict.get("clauses", {})
        jurisdiction = clauses.get("Jurisdiction", None)
        has_clauses = len(clauses) > 0

        # Construct row
        index_tuple = (storage_mode, category, doc_id)
        row_data = {
            "filename": filename,
            "file_type": file_type,
            "size_bytes": size_bytes,
            "sha256_hash": sha256_hash,
            "status": status,
            "created_at": created_at,
            "currency_total": total_val,
            "jurisdiction": jurisdiction,
            "has_clauses": has_clauses,
            "page_count": page_count,
        }

        # Create single row DataFrame and concatenate
        row_df = pd.DataFrame([row_data], index=pd.MultiIndex.from_tuples([index_tuple], names=self.INDEX_NAMES))
        if self.df.empty:
            self.df = row_df
        else:
            # Drop existing if duplicate index
            if index_tuple in self.df.index:
                self.df = self.df.drop(index=index_tuple)
            self.df = pd.concat([self.df, row_df])

    def detect_missing_values(self) -> Dict[str, int]:
        """Detect count of missing/NaN values across all columns."""
        if self.df.empty:
            return {col: 0 for col in self.COLUMNS}
        return self.df.isnull().sum().to_dict()

    def impute_missing_values(self, strategy: str = "hybrid") -> pd.DataFrame:
        """
        Performs missing data imputation on DataFrame:
        - Numerical (currency_total): median/mean imputation.
        - Categorical (jurisdiction): mode or fallback constant.
        - Preserves MultiIndex structure.
        """
        if self.df.empty:
            return self.df

        imputed_df = self.df.copy()

        # 1. Numerical Imputation for currency_total
        if "currency_total" in imputed_df.columns:
            median_val = imputed_df["currency_total"].median()
            # If all are NaN, default to 0.0
            fill_num = median_val if pd.notnull(median_val) else 0.0
            imputed_df["currency_total"] = imputed_df["currency_total"].fillna(fill_num)

        # 2. Categorical Imputation for jurisdiction
        if "jurisdiction" in imputed_df.columns:
            imputed_df["jurisdiction"] = imputed_df["jurisdiction"].fillna("Standard Federal / Unspecified")

        # 3. Status and boolean imputation
        if "status" in imputed_df.columns:
            imputed_df["status"] = imputed_df["status"].fillna("Unverified")

        self.df = imputed_df
        return self.df

    def query_by_storage(self, storage_mode: str) -> pd.DataFrame:
        """Slice the MultiIndex DataFrame by level 0 (Storage_Mode)."""
        if self.df.empty:
            return pd.DataFrame()
        try:
            return self.df.xs(storage_mode, level="Storage_Mode")
        except KeyError:
            return pd.DataFrame()

    def query_by_category(self, category: str) -> pd.DataFrame:
        """Slice the MultiIndex DataFrame by level 1 (Category)."""
        if self.df.empty:
            return pd.DataFrame()
        try:
            return self.df.xs(category, level="Category")
        except KeyError:
            return pd.DataFrame()

    def get_category_metrics(self) -> Dict[str, Any]:
        """
        Aggregates document counts and total size by category.
        Used for Streamlit and PyQt visual dashboards.
        """
        if self.df.empty:
            return {}

        cat_counts = self.df.groupby(level="Category").size().to_dict()
        cat_sizes = self.df.groupby(level="Category")["size_bytes"].sum().to_dict()

        return {
            "counts": cat_counts,
            "sizes": cat_sizes,
            "total_documents": len(self.df),
            "total_bytes": int(self.df["size_bytes"].sum()) if not self.df.empty else 0,
        }

    def get_storage_distribution(self) -> Dict[str, Any]:
        """Compares storage distribution between Local Drive and Cloud Vault."""
        if self.df.empty:
            return {"Local Drive": {"count": 0, "bytes": 0}, "Cloud Vault": {"count": 0, "bytes": 0}}

        storage_counts = self.df.groupby(level="Storage_Mode").size().to_dict()
        storage_sizes = self.df.groupby(level="Storage_Mode")["size_bytes"].sum().to_dict()

        return {
            mode: {
                "count": storage_counts.get(mode, 0),
                "bytes": int(storage_sizes.get(mode, 0)),
            }
            for mode in ["Local Drive", "Cloud Vault"]
        }

    def to_records_list(self) -> List[Dict[str, Any]]:
        """Converts MultiIndex DataFrame to flat list of records for REST API serialization."""
        if self.df.empty:
            return []

        records = []
        for (storage, category, doc_id), row in self.df.iterrows():
            item = row.to_dict()
            item["storage_mode"] = storage
            item["category"] = category
            item["doc_id"] = doc_id
            records.append(item)
        return records

    def to_csv_file(self, filepath: str) -> str:
        """Export catalog to CSV preserving hierarchical index."""
        self.df.to_csv(filepath)
        return filepath
