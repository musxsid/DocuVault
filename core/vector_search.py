"""
DocuVaultAI — Pure NumPy TF-IDF Vector Engine (Unit 5: NumPy Matrix Computations)
Constructs term-frequency inverse-document-frequency matrices using pure NumPy
arrays without scikit-learn, performs cosine similarity via vectorized dot products,
applies boolean masking filters, and uses structured arrays for ranking.
"""

import math
import os
import re
from typing import Any, Dict, List, Optional, Set, Tuple

import matplotlib
matplotlib.use("Agg")  # Non-interactive backend for headless/desktop plotting
import matplotlib.pyplot as plt
import numpy as np

from core.exceptions import VectorIndexError


class TextChunk:
    """Represents a text segment with provenance metadata."""

    def __init__(
        self,
        chunk_id: str,
        doc_id: str,
        filename: str,
        category: str,
        page_number: int,
        text: str,
    ) -> None:
        self.chunk_id = chunk_id
        self.doc_id = doc_id
        self.filename = filename
        self.category = category
        self.page_number = page_number
        self.text = text
        self.tokens: List[str] = []


class VectorSearchEngine:
    """
    High-performance in-memory semantic retrieval engine implemented in pure NumPy.
    Performs tokenization, TF-IDF matrix computation, cosine dot-product ranking,
    boolean array masking, and structured array sorting.
    """

    # Common English stopwords to prune noise
    STOPWORDS: Set[str] = {
        "a", "about", "above", "after", "again", "against", "all", "am", "an", "and",
        "any", "are", "aren't", "as", "at", "be", "because", "been", "before", "being",
        "below", "between", "both", "but", "by", "can", "cannot", "could", "couldn't",
        "did", "didn't", "do", "does", "doesn't", "doing", "don't", "down", "during",
        "each", "few", "for", "from", "further", "had", "hadn't", "has", "hasn't",
        "have", "haven't", "having", "he", "her", "here", "hers", "herself", "him",
        "himself", "his", "how", "i", "if", "in", "into", "is", "isn't", "it", "its",
        "itself", "let's", "me", "more", "most", "mustn't", "my", "myself", "no",
        "nor", "not", "of", "off", "on", "once", "only", "or", "other", "ought",
        "our", "ours", "ourselves", "out", "over", "own", "same", "shan't", "she",
        "should", "shouldn't", "so", "some", "such", "than", "that", "the", "their",
        "theirs", "them", "themselves", "then", "there", "these", "they", "this",
        "those", "through", "to", "too", "under", "until", "up", "very", "was",
        "wasn't", "we", "were", "weren't", "what", "when", "where", "which", "while",
        "who", "whom", "why", "with", "won't", "would", "wouldn't", "you", "your",
        "yours", "yourself", "yourselves",
    }

    # Structured array dtype for ranked results
    RESULT_DTYPE = np.dtype([
        ("chunk_idx", np.int32),
        ("doc_id", "U32"),
        ("filename", "U128"),
        ("category", "U32"),
        ("page_number", np.int32),
        ("score", np.float32),
    ])

    def __init__(self, max_vocab_size: int = 5000) -> None:
        self.max_vocab_size = max_vocab_size
        self.chunks: List[TextChunk] = []
        self.vocab: Dict[str, int] = {}
        self.inverse_vocab: Dict[int, str] = {}
        self.idf_vector: Optional[np.ndarray] = None
        self.tfidf_matrix: Optional[np.ndarray] = None  # Shape: (N_chunks, V)
        self.is_indexed: bool = False

    def tokenize(self, text: str) -> List[str]:
        """Regex tokenization, lowercase normalization, and stopword pruning."""
        words = re.findall(r"\b[A-Za-z0-9]{2,}\b", text.lower())
        return [w for w in words if w not in self.STOPWORDS and not w.isdigit()]

    def add_document_chunks(
        self,
        doc_id: str,
        filename: str,
        category: str,
        pages: List[Dict[str, Any]],
        chunk_size: int = 400,
    ) -> int:
        """
        Splits document pages into text chunks and registers them for indexing.
        Returns the number of chunks added.
        """
        count = 0
        for page in pages:
            page_num = page.get("page_number", 1)
            raw_text = page.get("text", "")
            if not raw_text.strip():
                continue

            # Segment by paragraphs or character windows
            paragraphs = [p.strip() for p in raw_text.split("\n\n") if p.strip()]
            if not paragraphs:
                paragraphs = [raw_text]

            current_chunk = ""
            for p in paragraphs:
                if len(current_chunk) + len(p) < chunk_size:
                    current_chunk += " " + p
                else:
                    if current_chunk.strip():
                        c_id = f"{doc_id}_p{page_num}_c{count}"
                        chunk = TextChunk(c_id, doc_id, filename, category, page_num, current_chunk.strip())
                        chunk.tokens = self.tokenize(current_chunk)
                        if chunk.tokens:
                            self.chunks.append(chunk)
                            count += 1
                    current_chunk = p

            if current_chunk.strip():
                c_id = f"{doc_id}_p{page_num}_c{count}"
                chunk = TextChunk(c_id, doc_id, filename, category, page_num, current_chunk.strip())
                chunk.tokens = self.tokenize(current_chunk)
                if chunk.tokens:
                    self.chunks.append(chunk)
                    count += 1

        self.is_indexed = False
        return count

    def build_index(self) -> None:
        """
        Constructs pure NumPy TF-IDF matrix:
        1. Builds vocabulary from all registered chunks.
        2. Computes Term Frequency (TF) matrix: TF(t, d) = count(t, d) / total_terms(d).
        3. Computes Inverse Document Frequency (IDF) array: log((1 + N) / (1 + df(t))) + 1.0.
        4. Calculates TF-IDF matrix = TF * IDF.
        5. Performs L2 normalization along axis 1 using np.linalg.norm.
        """
        if not self.chunks:
            self.tfidf_matrix = np.empty((0, 0), dtype=np.float32)
            self.vocab = {}
            self.is_indexed = True
            return

        num_chunks = len(self.chunks)

        # Step 1: Vocabulary construction
        doc_frequencies: Dict[str, int] = {}
        for chunk in self.chunks:
            unique_words = set(chunk.tokens)
            for w in unique_words:
                doc_frequencies[w] = doc_frequencies.get(w, 0) + 1

        # Select top frequent terms up to max_vocab_size
        sorted_vocab = sorted(doc_frequencies.items(), key=lambda x: x[1], reverse=True)[:self.max_vocab_size]
        self.vocab = {term: idx for idx, (term, _) in enumerate(sorted_vocab)}
        self.inverse_vocab = {idx: term for term, idx in self.vocab.items()}
        vocab_size = len(self.vocab)

        if vocab_size == 0:
            self.tfidf_matrix = np.zeros((num_chunks, 1), dtype=np.float32)
            self.is_indexed = True
            return

        # Step 2: Compute TF Matrix
        tf_matrix = np.zeros((num_chunks, vocab_size), dtype=np.float32)
        for i, chunk in enumerate(self.chunks):
            total_tokens = len(chunk.tokens)
            if total_tokens == 0:
                continue
            for token in chunk.tokens:
                if token in self.vocab:
                    col_idx = self.vocab[token]
                    tf_matrix[i, col_idx] += 1.0
            # Normalize by total tokens in chunk
            tf_matrix[i, :] /= float(total_tokens)

        # Step 3: Compute IDF Vector using smooth formula: log((1 + N) / (1 + df)) + 1.0
        df_array = np.zeros(vocab_size, dtype=np.float32)
        for term, col_idx in self.vocab.items():
            df_array[col_idx] = doc_frequencies.get(term, 1)

        # Pure NumPy vectorized computation
        self.idf_vector = np.log((1.0 + num_chunks) / (1.0 + df_array)) + 1.0

        # Step 4: TF-IDF calculation (broadcasting across rows)
        self.tfidf_matrix = tf_matrix * self.idf_vector

        # Step 5: L2 vector normalization for cosine similarity
        norms = np.linalg.norm(self.tfidf_matrix, axis=1, keepdims=True)
        # Avoid division by zero
        norms[norms == 0] = 1.0
        self.tfidf_matrix = self.tfidf_matrix / norms
        self.is_indexed = True

    def _vectorize_query(self, query: str) -> np.ndarray:
        """Transforms a user search query into an L2-normalized TF-IDF vector."""
        if not self.is_indexed or not self.vocab or self.idf_vector is None:
            return np.zeros(0, dtype=np.float32)

        vocab_size = len(self.vocab)
        tokens = self.tokenize(query)
        if not tokens:
            return np.zeros(vocab_size, dtype=np.float32)

        tf_query = np.zeros(vocab_size, dtype=np.float32)
        for t in tokens:
            if t in self.vocab:
                tf_query[self.vocab[t]] += 1.0

        # Normalize TF
        tf_query /= float(len(tokens))

        # Multiply with precomputed IDF vector
        query_tfidf = tf_query * self.idf_vector

        # L2 normalize
        norm = np.linalg.norm(query_tfidf)
        if norm > 0:
            query_tfidf = query_tfidf / norm
        return query_tfidf

    def search(
        self,
        query: str,
        top_k: int = 5,
        category_filter: Optional[str] = None,
        min_score: float = 0.01,
    ) -> List[Dict[str, Any]]:
        """
        Executes sub-second semantic search:
        1. Computes cosine similarity via array dot-product: scores = np.dot(matrix, query_vec).
        2. Applies boolean masking to filter by category.
        3. Packages top matches into structured NumPy arrays.
        """
        if not self.is_indexed:
            self.build_index()

        if self.tfidf_matrix is None or len(self.chunks) == 0:
            return []

        query_vec = self._vectorize_query(query)
        if query_vec.size == 0 or np.all(query_vec == 0):
            # Keyword not in vocabulary
            return []

        # Vectorized dot product cosine similarity across all document chunks
        scores = np.dot(self.tfidf_matrix, query_vec)  # Shape: (num_chunks,)

        # Boolean Masking Filter (Category and threshold)
        mask = scores >= min_score
        if category_filter and category_filter != "All":
            category_arr = np.array([c.category for c in self.chunks])
            category_mask = (category_arr == category_filter)
            mask = mask & category_mask

        matching_indices = np.where(mask)[0]
        if len(matching_indices) == 0:
            return []

        # Use NumPy structured array for sorting and provenance
        matched_scores = scores[matching_indices]
        structured_results = np.empty(len(matching_indices), dtype=self.RESULT_DTYPE)

        for i, idx in enumerate(matching_indices):
            chunk = self.chunks[idx]
            structured_results[i] = (
                idx,
                chunk.doc_id,
                chunk.filename,
                chunk.category,
                chunk.page_number,
                matched_scores[i],
            )

        # Sort descending by score using numpy argsort
        sorted_indices = np.argsort(structured_results["score"])[::-1]
        top_results = structured_results[sorted_indices][:top_k]

        # Convert to serializable dictionary format with citations
        output: List[Dict[str, Any]] = []
        for row in top_results:
            c_idx = int(row["chunk_idx"])
            chunk = self.chunks[c_idx]
            output.append({
                "chunk_id": chunk.chunk_id,
                "doc_id": str(row["doc_id"]),
                "filename": str(row["filename"]),
                "category": str(row["category"]),
                "page_number": int(row["page_number"]),
                "score": float(row["score"]),
                "text": chunk.text,
                "citation": f"Source: [{chunk.filename}], Page: [{chunk.page_number}]",
            })
        return output

    def generate_similarity_plot(
        self,
        query: str,
        results: List[Dict[str, Any]],
        output_image_path: str = "similarity_distribution.png",
    ) -> Optional[str]:
        """
        Generates a Matplotlib visual bar plot of semantic cosine similarity scores.
        Satisfies Unit 5: Matplotlib visualizations.
        """
        if not results:
            return None

        filenames = [f"{r['filename'][:15]} (p.{r['page_number']})" for r in results]
        scores = [r["score"] for r in results]

        fig, ax = plt.subplots(figsize=(7, 3.5), dpi=120)
        bars = ax.barh(filenames[::-1], scores[::-1], color="#6366f1", edgecolor="#4338ca", height=0.55)

        ax.set_xlabel("Cosine Similarity Score (Pure NumPy Dot-Product)", fontsize=9, fontweight="bold")
        ax.set_title(f"Semantic Search Relevance for: '{query[:30]}'", fontsize=10, fontweight="bold", pad=10)
        ax.set_xlim(0, max(max(scores) * 1.25, 0.5))

        # Add score labels on bars
        for bar in bars:
            width = bar.get_width()
            ax.text(
                width + 0.01,
                bar.get_y() + bar.get_height() / 2,
                f"{width:.3f}",
                va="center",
                fontsize=8,
                fontweight="bold",
                color="#1e293b",
            )

        plt.tight_layout()
        os.makedirs(os.path.dirname(os.path.abspath(output_image_path)), exist_ok=True)
        plt.savefig(output_image_path, dpi=120)
        plt.close(fig)
        return output_image_path
