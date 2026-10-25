"""
DocuVault — Duplicate Document Detection Engine
Detects exact duplicates via cryptographic SHA-256 hashing and
near-duplicates via text sequence and token similarity metrics.
"""

import difflib
from typing import Any, Dict, List, Optional, Tuple


class DuplicateDetector:
    """
    Engine to identify duplicate and near-duplicate documents within the vault.
    Uses SHA-256 for exact matches and token-level Jaccard / SequenceMatcher for near duplicates.
    """

    @staticmethod
    def check_exact_duplicate(
        sha256_hash: str,
        catalog_docs: List[Dict[str, Any]],
        exclude_doc_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Checks if a document with the exact same SHA-256 hash already exists.
        Returns the matching document record if found.
        """
        if not sha256_hash:
            return None

        for doc in catalog_docs:
            if exclude_doc_id and doc.get("doc_id") == exclude_doc_id:
                continue
            if doc.get("sha256_hash", "").lower() == sha256_hash.lower():
                return doc
        return None

    @staticmethod
    def calculate_text_similarity(text1: str, text2: str) -> float:
        """
        Calculates similarity ratio between two texts (0.0 to 1.0)
        using quick character-level and token-level metrics.
        """
        if not text1 or not text2:
            return 0.0

        # Quick length check
        len1, len2 = len(text1), len(text2)
        if len1 == 0 or len2 == 0:
            return 0.0

        # Token set Jaccard similarity for speed
        tokens1 = set(text1.lower().split())
        tokens2 = set(text2.lower().split())

        if not tokens1 or not tokens2:
            return 0.0

        intersection = len(tokens1 & tokens2)
        union = len(tokens1 | tokens2)
        jaccard = intersection / union if union > 0 else 0.0

        # SequenceMatcher for refined similarity on sample
        sample1 = text1[:1500]
        sample2 = text2[:1500]
        seq_ratio = difflib.SequenceMatcher(None, sample1, sample2).quick_ratio()

        # Weighted combination
        return round(0.4 * jaccard + 0.6 * seq_ratio, 3)

    @classmethod
    def find_near_duplicates(
        cls,
        target_text: str,
        catalog_docs: List[Dict[str, Any]],
        threshold: float = 0.75,
        exclude_doc_id: Optional[str] = None
    ) -> List[Tuple[Dict[str, Any], float]]:
        """
        Finds all documents whose text content exceeds the similarity threshold.
        Returns list of (doc_dict, similarity_score) sorted descending.
        """
        matches = []
        if not target_text:
            return matches

        for doc in catalog_docs:
            if exclude_doc_id and doc.get("doc_id") == exclude_doc_id:
                continue

            doc_text = ""
            for p in doc.get("pages", []):
                doc_text += p.get("text", "") + "\n"

            if not doc_text:
                continue

            sim = cls.calculate_text_similarity(target_text, doc_text)
            if sim >= threshold:
                matches.append((doc, sim))

        matches.sort(key=lambda x: x[1], reverse=True)
        return matches

    @classmethod
    def scan_repository_duplicates(
        cls,
        docs: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Scans all documents in the repository for exact and near-duplicates.
        """
        exact_groups: Dict[str, List[Dict[str, Any]]] = {}
        near_matches: List[Dict[str, Any]] = []

        # 1. Exact duplicates by hash
        for d in docs:
            h = d.get("sha256_hash", "")
            if h:
                exact_groups.setdefault(h, []).append(d)

        exact_duplicates = [group for group in exact_groups.values() if len(group) > 1]

        # 2. Near duplicates
        doc_texts = {}
        for d in docs:
            txt = " ".join(p.get("text", "") for p in d.get("pages", []))
            doc_texts[d.get("doc_id")] = txt

        doc_list = list(docs)
        for i in range(len(doc_list)):
            for j in range(i + 1, len(doc_list)):
                d1 = doc_list[i]
                d2 = doc_list[j]
                if d1.get("sha256_hash") == d2.get("sha256_hash"):
                    continue  # Already caught as exact

                t1 = doc_texts.get(d1.get("doc_id"), "")
                t2 = doc_texts.get(d2.get("doc_id"), "")
                if t1 and t2:
                    sim = cls.calculate_text_similarity(t1, t2)
                    if sim >= 0.70:
                        near_matches.append({
                            "doc_a": d1,
                            "doc_b": d2,
                            "similarity": round(sim * 100, 1),
                        })

        return {
            "total_documents_scanned": len(docs),
            "exact_duplicate_clusters": exact_duplicates,
            "near_duplicate_pairs": near_matches,
        }
