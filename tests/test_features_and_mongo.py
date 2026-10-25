"""
DocuVault — Unit Tests for New High-Value Features and Realtime MongoDB
Tests:
1. Duplicate Document Detection
2. Explainable AI Document Assistant with Provenance Citations
3. Document Version History & difflib Text Diffing
4. OCR for Scanned Documents
5. Document Health & Compliance Score Diagnostics
6. Smart Deadline Reminders with Holiday Shifts & iCalendar Export
7. MongoDB Realtime Database Persistence Layer
"""

import os
import unittest
from datetime import date, datetime, timedelta

from core.ai_assistant import ExplainableAIAssistant
from core.deadlines import DeadlineManager
from core.duplicate_detector import DuplicateDetector
from core.health_score import DocumentHealthEngine
from core.mongo_database import MongoDatabase
from core.ocr_engine import OCREngine
from core.vector_search import VectorSearchEngine
from core.versioning import DocumentVersionManager


class TestHighValueFeatures(unittest.TestCase):

    def test_duplicate_detection_exact_and_near(self):
        """Verify exact SHA-256 duplicate detection and near-duplicate text similarity."""
        docs = [
            {
                "doc_id": "doc1",
                "filename": "Contract.pdf",
                "sha256_hash": "abcdef123456",
                "pages": [{"page_number": 1, "text": "This Agreement is entered into by and between Party A and Party B."}],
            },
            {
                "doc_id": "doc2",
                "filename": "Contract_final.pdf",
                "sha256_hash": "abcdef123456",  # exact match
                "pages": [{"page_number": 1, "text": "This Agreement is entered into by and between Party A and Party B."}],
            },
            {
                "doc_id": "doc3",
                "filename": "Contract_v2.pdf",
                "sha256_hash": "different999",
                "pages": [{"page_number": 1, "text": "This Agreement is entered into by and between Party A and Party B with slight amendment."}],
            },
        ]

        # Exact match check
        exact = DuplicateDetector.check_exact_duplicate("abcdef123456", docs, exclude_doc_id="doc1")
        self.assertIsNotNone(exact)
        self.assertEqual(exact["doc_id"], "doc2")

        # Near match check
        near = DuplicateDetector.find_near_duplicates(
            "This Agreement is entered into by and between Party A and Party B.",
            docs,
            threshold=0.75,
            exclude_doc_id="doc1"
        )
        self.assertGreater(len(near), 0)

        # Full repository scan
        report = DuplicateDetector.scan_repository_duplicates(docs)
        self.assertEqual(len(report["exact_duplicate_clusters"]), 1)

    def test_explainable_ai_assistant_grounding(self):
        """Verify AI assistant cites source file and page, and declines ungrounded queries."""
        vec = VectorSearchEngine()
        vec.add_document_chunks(
            "doc_legal_1",
            "Master_Agreement.txt",
            "Legal",
            [{"page_number": 1, "text": "Either party may terminate this agreement upon thirty (30) days prior written notice."}]
        )
        vec.build_index()

        assistant = ExplainableAIAssistant(vec)

        # Grounded query
        res = assistant.answer_query("What is the termination notice period?")
        self.assertTrue(res["found_source"])
        self.assertIn("Master_Agreement.txt", res["answer_text"])
        self.assertGreater(len(res["citations"]), 0)
        self.assertEqual(res["citations"][0]["page_number"], 1)

        # Ungrounded query
        un_res = assistant.answer_query("What is the quantum teleportation frequency threshold?")
        self.assertFalse(un_res["found_source"])
        self.assertIn("No reliable source found", un_res["answer_text"])

    def test_version_history_and_diff(self):
        """Verify version text comparison and clause diff generation."""
        v1 = "Clause 1: Payment within 15 days.\nClause 2: Notice period 10 days."
        v2 = "Clause 1: Payment within 30 days.\nClause 2: Notice period 10 days.\nClause 3: Confidentiality for 2 years."

        diff_res = DocumentVersionManager.compare_versions(v1, v2)
        self.assertGreater(diff_res["additions_count"], 0)
        self.assertGreater(diff_res["deletions_count"], 0)

        html = DocumentVersionManager.generate_html_diff(v1, v2)
        self.assertIn("Comparison Summary", html)
        self.assertIn("clauses added", html)

    def test_ocr_engine_detection(self):
        """Verify low-density scanned document detection and text extraction."""
        scanned_doc = {
            "filename": "Scanned_Marksheet.pdf",
            "page_count": 2,
            "pages": [{"page_number": 1, "text": ""}, {"page_number": 2, "text": "   "}],
        }
        is_scanned, reason = OCREngine.is_scanned_document(scanned_doc)
        self.assertTrue(is_scanned)
        self.assertIn("Low text density", reason)

        ocr_res = OCREngine.process_ocr(scanned_doc)
        self.assertGreater(ocr_res["overall_confidence"], 90.0)
        self.assertIn("Percentage", ocr_res["full_text"])

    def test_health_and_compliance_score(self):
        """Verify Document Health and Compliance Score calculations."""
        doc = {
            "filename": "NDA_Apex.pdf",
            "category": "Legal",
            "status": "Verified",
            "sha256_hash": "5ecc09606da43950288ba941cb915d58460b49faed03776b60bdaf91",
            "clauses": {"Jurisdiction": "New York"},
            "dates": ["2026-10-15"],
            "pages": [{"page_number": 1, "text": "This agreement is between the parties governed under New York law."}],
        }
        health = DocumentHealthEngine.calculate_health(doc)
        self.assertGreaterEqual(health["score"], 70)
        self.assertIn(health["grade"], ["A+", "A", "B", "C"])
        self.assertEqual(len(health["checks"]), 5)
        self.assertIn("Automated Document Health Score", health["disclaimer"])

    def test_deadlines_manager_and_ical_export(self):
        """Verify deadline reminders, holiday shifts, and CSV/iCalendar output."""
        mgr = DeadlineManager()
        today = date.today()
        dl = {
            "id": "DL-01",
            "title": "Vendor Invoice Settlement",
            "document": "Invoice.xml",
            "due_date": (today + timedelta(days=3)).isoformat(),
            "priority": "High",
        }
        res = mgr.evaluate_deadline(dl)
        self.assertIn("Urgent", res["computed_status"])
        self.assertEqual(res["days_left"], 3)

        # Export CSV
        csv_str = DeadlineManager.export_csv([dl])
        self.assertIn("Vendor Invoice Settlement", csv_str)

        # Export iCalendar
        ical_str = DeadlineManager.export_icalendar([dl])
        self.assertIn("BEGIN:VCALENDAR", ical_str)
        self.assertIn("SUMMARY:Vendor Invoice Settlement", ical_str)

    def test_mongodb_realtime_persistence(self):
        """Verify MongoDB database connection, document CRUD, versioning, and audit logging."""
        mongo = MongoDatabase()
        if not mongo.is_connected:
            self.skipTest("MongoDB server not reachable on localhost:27017")

        test_doc_id = "test_doc_mongo_001"
        test_doc = {
            "doc_id": test_doc_id,
            "filename": "Mongo_Test_Contract.pdf",
            "category": "Legal",
            "sha256_hash": "test_hash_12345",
            "status": "Verified",
            "size_bytes": 1024,
            "pages": [{"page_number": 1, "text": "Test clause in MongoDB"}],
        }

        # Save
        saved = mongo.save_document(test_doc)
        self.assertTrue(saved)

        # Read
        fetched = mongo.get_document(test_doc_id)
        self.assertIsNotNone(fetched)
        self.assertEqual(fetched["filename"], "Mongo_Test_Contract.pdf")

        # Find by hash
        by_hash = mongo.find_by_hash("test_hash_12345")
        self.assertIsNotNone(by_hash)
        self.assertEqual(by_hash["doc_id"], test_doc_id)

        # Update status
        mongo.update_document_status(test_doc_id, "Tampered")
        updated = mongo.get_document(test_doc_id)
        self.assertEqual(updated["status"], "Tampered")

        # Versioning
        mongo.save_version(test_doc_id, {
            "version_number": "1.0",
            "text_snapshot": "Test clause in MongoDB",
            "sha256_hash": "test_hash_12345",
        })
        versions = mongo.get_versions(test_doc_id)
        self.assertGreater(len(versions), 0)

        # Audit
        mongo.log_audit("TEST_RUN", "Automated unit test execution", test_doc_id)
        logs = mongo.get_audit_logs(limit=10)
        self.assertGreater(len(logs), 0)

        # Delete
        mongo.delete_document(test_doc_id)
        self.assertIsNone(mongo.get_document(test_doc_id))
        mongo.close()


if __name__ == "__main__":
    unittest.main(verbosity=2)
