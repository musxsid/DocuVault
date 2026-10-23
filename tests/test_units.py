"""
DocuVaultAI — Comprehensive Course Curriculum Unit Test Suite (Units 1 to 5)
Strictly asserts requirements across OOP, Regex, APIs, Automation, Flask, Pandas, and NumPy.
"""

import os
import shutil
import tempfile
import unittest
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

from backend.api_client import PublicHolidayClient
from backend.app_flask import app as flask_app
from core.base_document import (
    AcademicDocument,
    BaseDocument,
    DocumentFactory,
    FinancialDocument,
    LegalDocument,
    MedicalDocument,
)
from core.catalog_manager import CatalogManager
from core.exceptions import (
    CorruptFileError,
    DocuVaultError,
    MissingClauseError,
    TamperedFileError,
)
from core.organizer import AuditLogger, FileOrganizerDaemon, RegexFormValidator
from core.parsers.binary_parser import BinaryParser
from core.parsers.xml_parser import XMLDocumentParser
from core.storage_providers import LocalStorageProvider
from core.vector_search import VectorSearchEngine


class TestUnit1AdvancedOOPAndRegex(unittest.TestCase):
    """Unit 1: OOP, Custom Exceptions, Regular Expressions."""

    def test_abstract_base_class_instantiation(self):
        """Verify that BaseDocument cannot be directly instantiated without implementing abstract methods."""
        with self.assertRaises(TypeError):
            BaseDocument(filepath="test.txt")

    def test_polymorphic_document_subclasses(self):
        """Verify polymorphic subclasses and category mapping."""
        legal_text = (
            "Jurisdiction: Under the laws of the State of Delaware.\n"
            "Effective Date: 2026-10-15.\n"
            "Prior written notice of 30 days required.\n"
            "Limitation of Liability: Maximum $500,000 USD."
        )
        legal_doc = LegalDocument(filepath="dummy_contract.txt", raw_text=legal_text)
        self.assertEqual(legal_doc.get_category(), "Legal")
        clauses = legal_doc.extract_clauses_and_entities()
        self.assertIn("Jurisdiction", clauses)
        self.assertTrue(legal_doc.validate_compliance(strict=False))

    def test_missing_clause_exception(self):
        """Verify MissingClauseError is raised when critical clauses are missing."""
        incomplete_legal = "This is an informal memo without any jurisdiction clause."
        doc = LegalDocument(filepath="memo.txt", raw_text=incomplete_legal)
        with self.assertRaises(MissingClauseError) as ctx:
            doc.validate_compliance(strict=True)
        self.assertEqual(ctx.exception.error_code, "ERR_MISSING_CLAUSE")
        self.assertIn("Jurisdiction", ctx.exception.missing_clauses)

    def test_regex_entity_extraction(self):
        """Verify compiled regex patterns for dates, currency amounts, and emails."""
        sample = "Invoice dated 2026-10-15 for $4,500.50 USD. Contact admin@docuvault.io or +1-800-555-0199."
        doc = FinancialDocument(filepath="fin.txt", raw_text=sample)
        dates = doc.extract_dates()
        currencies = doc.extract_currency_amounts()

        self.assertIn("2026-10-15", dates)
        self.assertTrue(any("4,500.50" in c for c in currencies))
        self.assertTrue(RegexFormValidator.validate_field("email", "admin@docuvault.io"))
        self.assertTrue(RegexFormValidator.validate_field("date", "2026-10-15"))


class TestUnit2APIsAndAutomation(unittest.TestCase):
    """Unit 2: RESTful APIs, Working-Day Calendar Engine & File Automation."""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.organizer = FileOrganizerDaemon(vault_root=self.test_dir, log_file=f"{self.test_dir}/ops.log")

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_holiday_api_and_working_day_shift(self):
        """Verify working-day deadline adjustment shifts weekends and holidays."""
        client = PublicHolidayClient(default_country="US")

        # Saturday test: 2026-10-10 is a Saturday -> should shift to Monday 2026-10-12
        sat_date = date(2026, 10, 10)
        self.assertFalse(client.is_working_day(sat_date))
        calc_weekend = client.calculate_working_deadline(start_date=sat_date, business_days=0)
        self.assertTrue(calc_weekend["was_shifted"])
        # Should shift to Monday or next working day
        self.assertNotEqual(calc_weekend["working_deadline"], "2026-10-10")

        # Christmas test: 2026-12-25 is Christmas public holiday -> should shift
        xmas_date = date(2026, 12, 25)
        self.assertFalse(client.is_working_day(xmas_date))
        calc_xmas = client.calculate_working_deadline(start_date=xmas_date, business_days=0)
        self.assertTrue(calc_xmas["was_shifted"])

    def test_file_sorter_and_audit_log(self):
        """Verify file sorter moves files into categorical folders and logs entries."""
        test_file = Path(self.test_dir) / "test_contract.txt"
        test_file.write_text("Governing Law: State of New York agreement between Party A and Party B.")

        result = self.organizer.sort_file(str(test_file))
        self.assertTrue(result["success"])
        self.assertEqual(result["category"], "Legal")

        # Destination must exist in /Legal
        self.assertTrue(Path(result["destination"]).exists())

        # Audit log verification
        logs = self.organizer.logger.get_recent_logs(5)
        self.assertTrue(len(logs) > 0)
        self.assertIn("SORT", logs[-1])
        self.assertIn("/Legal/", logs[-1])


class TestUnit3WebFrameworksFlask(unittest.TestCase):
    """Unit 3: Flask REST API backend endpoints."""

    def setUp(self):
        flask_app.config["TESTING"] = True
        self.client = flask_app.test_client()

    def test_health_endpoint(self):
        resp = self.client.get("/api/health")
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertEqual(data["status"], "healthy")
        self.assertIn("active_storage_mode", data)

    def test_storage_mode_toggle_endpoint(self):
        # GET mode
        resp = self.client.get("/api/storage/mode")
        self.assertEqual(resp.status_code, 200)

        # POST mode switch
        resp_post = self.client.post("/api/storage/mode", json={"mode": "Cloud Vault"})
        self.assertEqual(resp_post.status_code, 200)
        self.assertEqual(resp_post.get_json()["active_storage_mode"], "Cloud Vault")

        # Switch back
        self.client.post("/api/storage/mode", json={"mode": "Local Drive"})


class TestUnit4FileHandlingAndPandas(unittest.TestCase):
    """Unit 4: Binary Magic Bytes, Cryptographic Hashes, XML ElementTree & Pandas MultiIndex."""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_binary_magic_byte_validation_and_disguised_file_detection(self):
        """Verify binary inspection flags disguised executables and verifies magic numbers."""
        # Create genuine PDF header
        pdf_path = Path(self.test_dir) / "genuine.pdf"
        pdf_path.write_bytes(b"%PDF-1.5 test binary stream")
        report = BinaryParser.validate_file(str(pdf_path))
        self.assertEqual(report["status"], "VALID")

        # Create malicious disguised file (PE executable 'MZ' disguised as .pdf)
        malicious_path = Path(self.test_dir) / "trojan.pdf"
        malicious_path.write_bytes(b"MZ\x90\x00corrupt PE executable")
        with self.assertRaises(CorruptFileError) as ctx:
            BinaryParser.validate_file(str(malicious_path))
        self.assertEqual(ctx.exception.error_code, "ERR_CORRUPT_FILE")

    def test_xml_element_tree_parsing(self):
        """Verify ElementTree parsing extracts nodes, attributes, and text."""
        xml_content = """<?xml version="1.0"?>
        <record id="REC-100">
            <patient_id>PT-1234</patient_id>
            <diagnosis>Hypertension</diagnosis>
            <items>
                <item code="A1">Medication A</item>
                <item code="B2">Medication B</item>
            </items>
        </record>"""
        xml_path = Path(self.test_dir) / "record.xml"
        xml_path.write_text(xml_content, encoding="utf-8")

        parsed = XMLDocumentParser.parse_file(str(xml_path))
        self.assertEqual(parsed["root_tag"], "record")
        self.assertEqual(parsed["fields"]["patient_id"], "PT-1234")
        self.assertEqual(len(parsed["line_items"]), 2)

    def test_pandas_multiindex_catalog_and_imputation(self):
        """Verify Pandas MultiIndex DataFrame slicing and missing data imputation."""
        cat_mgr = CatalogManager()

        # Add records
        doc1 = {
            "doc_id": "doc_001",
            "category": "Legal",
            "filename": "contract.pdf",
            "size_bytes": 1024,
            "sha256_hash": "abc123hash",
            "currency_amounts": ["$5,000.00"],
            "clauses": {"Jurisdiction": "Delaware"},
        }
        # Doc 2 missing jurisdiction and currency
        doc2 = {
            "doc_id": "doc_002",
            "category": "Legal",
            "filename": "memo.pdf",
            "size_bytes": 512,
            "sha256_hash": "def456hash",
            "currency_amounts": [],
            "clauses": {},
        }
        cat_mgr.add_document(doc1, storage_mode="Local Drive")
        cat_mgr.add_document(doc2, storage_mode="Local Drive")

        # MultiIndex assertions
        self.assertEqual(cat_mgr.df.index.names, ["Storage_Mode", "Category", "Doc_ID"])
        sliced_legal = cat_mgr.query_by_category("Legal")
        self.assertEqual(len(sliced_legal), 2)

        # Imputation check
        imputed_df = cat_mgr.impute_missing_values()
        # Missing jurisdiction should be imputed
        missing_count = imputed_df["jurisdiction"].isnull().sum()
        self.assertEqual(missing_count, 0)


class TestUnit5NumPyComputationsAndRAG(unittest.TestCase):
    """Unit 5: Pure NumPy TF-IDF vector matrix computations and cosine similarity ranking."""

    def test_pure_numpy_tfidf_and_cosine_similarity(self):
        """
        Verify TF-IDF computation, L2 normalization, and cosine similarity
        via vectorized array dot products without scikit-learn.
        """
        engine = VectorSearchEngine()

        pages1 = [{"page_number": 1, "text": "Quantum computing error mitigation in high dimensional Hilbert spaces."}]
        pages2 = [{"page_number": 1, "text": "Medical diagnosis for patient with hypertension and clinical monitoring."}]
        pages3 = [{"page_number": 1, "text": "Governing law of the state of Delaware confidentiality contract liability."}]

        engine.add_document_chunks("doc1", "quantum.txt", "Academic", pages1)
        engine.add_document_chunks("doc2", "medical.txt", "Medical", pages2)
        engine.add_document_chunks("doc3", "legal.txt", "Legal", pages3)

        engine.build_index()

        # Assert pure NumPy matrix properties
        self.assertIsInstance(engine.tfidf_matrix, np.ndarray)
        self.assertEqual(engine.tfidf_matrix.shape[0], 3)
        self.assertTrue(engine.is_indexed)

        # L2 norm check: each row vector norm must be approx 1.0
        norms = np.linalg.norm(engine.tfidf_matrix, axis=1)
        for n in norms:
            self.assertAlmostEqual(n, 1.0, places=4)

        # Semantic Search Query: "quantum computing qubits"
        results = engine.search("quantum computing error", top_k=2)
        self.assertTrue(len(results) > 0)
        top_match = results[0]
        self.assertEqual(top_match["filename"], "quantum.txt")
        self.assertEqual(top_match["category"], "Academic")
        self.assertGreater(top_match["score"], 0.2)

        # Boolean Masking Test: Search only within 'Legal' category
        legal_results = engine.search("quantum", top_k=2, category_filter="Legal")
        self.assertEqual(len(legal_results), 0)  # Should filter out non-legal matches


if __name__ == "__main__":
    unittest.main(verbosity=2)
