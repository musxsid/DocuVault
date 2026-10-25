"""
Test Suite for Production Features:
- Directory Tracker (Git-like auto-ingestion)
- Hierarchical Chunking
- Dense + Sparse Hybrid Search (RRF)
- Response Hallucination Guardrail & Multi-Doc Synthesis
- Executive Summary, Risk Profiling & Legal Rebuttal Drafting
- Zero-Knowledge AES-256 Client Encryption
- Batch Dossier Compiler (.zip)
- Automated Retention Policy Enforcement
"""

import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path

from core.ai_assistant import ExplainableAIAssistant
from core.batch_exporter import BatchDossierExporter
from core.document_analyzer import DocumentAnalyzer
from core.encryption import ZeroKnowledgeVaultCrypto
from core.folder_tracker import DirectoryTracker
from core.retention_policy import RetentionPolicyManager
from core.vector_search import VectorSearchEngine


class TestProductionFeatures(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.sample_contract = (
            "# MASTER SERVICES AGREEMENT\n\n"
            "ARTICLE 1: PARTIES AND SCOPE\n"
            "This Master Services Agreement is entered into between Acme Corporation and Global Logistics Inc.\n\n"
            "ARTICLE 2: TERMINATION NOTICE\n"
            "Either party may terminate this agreement upon delivering sixty (60) days prior written notice.\n\n"
            "ARTICLE 3: PAYMENT TERMS\n"
            "Client shall pay all undisputed invoice amounts within Net-30 days of receipt.\n\n"
            "ARTICLE 4: LIMITATION OF LIABILITY\n"
            "Total aggregate liability under this agreement shall be capped at the total amount paid.\n\n"
            "ARTICLE 5: GOVERNING LAW\n"
            "This agreement is governed by the laws of the State of New York.\n"
        )

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_hierarchical_chunking_and_hybrid_rrf_search(self):
        engine = VectorSearchEngine()
        pages = [{"page_number": 1, "text": self.sample_contract}]
        chunks_added = engine.add_hierarchical_document_chunks(
            doc_id="doc_msa_01",
            filename="master_agreement.txt",
            category="Legal",
            pages=pages,
        )
        self.assertGreater(chunks_added, 0)
        self.assertTrue(engine.chunks[0].section_title.startswith("ARTICLE") or "MASTER" in engine.chunks[0].section_title or "Page" in engine.chunks[0].section_title)

        # Execute Dense + Sparse Hybrid Search via Reciprocal Rank Fusion
        results = engine.hybrid_search("termination notice period 60 days", top_k=3)
        self.assertGreater(len(results), 0)
        top = results[0]
        self.assertIn("score", top)
        self.assertIn("dense_score", top)
        self.assertIn("sparse_score", top)
        self.assertIn("citation", top)
        self.assertIn("termination", top["text"].lower())

    def test_response_hallucination_guardrail(self):
        engine = VectorSearchEngine()
        pages = [{"page_number": 1, "text": self.sample_contract}]
        engine.add_hierarchical_document_chunks("doc_msa_01", "msa.txt", "Legal", pages)

        assistant = ExplainableAIAssistant(engine)

        # Grounded query
        grounded_resp = assistant.answer_query("What is the termination notice period?")
        self.assertTrue(grounded_resp["found_source"])
        self.assertTrue(grounded_resp["guardrail"]["is_grounded"])
        self.assertGreater(grounded_resp["guardrail"]["confidence_score"], 0.3)

        # Verify hallucination detector with completely made-up response
        fake_response = "Quantum entanglement superconductors yield 99% thermodynamic efficiency on Mars."
        guard = assistant.verify_response_hallucination(fake_response, [self.sample_contract])
        self.assertFalse(guard["is_grounded"])
        self.assertIsNotNone(guard["warning"])

    def test_multi_document_synthesis(self):
        engine = VectorSearchEngine()
        invoice_text = (
            "INVOICE #INV-2026-99\n"
            "Vendor: Acme Corporation\n"
            "Total Amount: $45,000.00 USD\n"
            "Payment Due: Net-30 days\n"
            "Governing terms: Under Master Services Agreement\n"
        )
        engine.add_hierarchical_document_chunks("doc_1", "msa.txt", "Legal", [{"page_number": 1, "text": self.sample_contract}])
        engine.add_hierarchical_document_chunks("doc_2", "invoice.txt", "Financial", [{"page_number": 1, "text": invoice_text}])

        assistant = ExplainableAIAssistant(engine)
        synth = assistant.multi_document_synthesis("payment terms and invoice amount")
        self.assertTrue(synth["success"])
        self.assertGreater(len(synth["documents_analyzed"]), 0)
        self.assertIn("Consolidated Assessment", synth["synthesis_text"])

    def test_document_analyzer_risk_summary_and_rebuttal(self):
        doc_dict = {
            "doc_id": "test_doc_01",
            "filename": "vendor_agreement.pdf",
            "category": "Legal",
            "pages": [{"page_number": 1, "text": self.sample_contract}],
            "clauses": {
                "Termination Notice": "60 days",
                "Governing Law": "State of New York",
            },
        }

        # 1. Executive Summary
        summary = DocumentAnalyzer.extract_executive_summary(self.sample_contract, "vendor_agreement.pdf")
        self.assertEqual(len(summary), 3)

        # 2. Counterparties
        counterparties = DocumentAnalyzer.extract_counterparties(self.sample_contract)
        self.assertIn("Acme Corporation", counterparties)

        # 3. Risk Profile
        risk = DocumentAnalyzer.calculate_risk_profile(self.sample_contract, doc_dict["clauses"])
        self.assertIn(risk["risk_badge"], ["Low", "Medium", "High"])
        self.assertIn("score", risk)

        # 4. Legal Rebuttal Drafting
        rebuttal = DocumentAnalyzer.draft_rebuttal_letter(doc_dict)
        self.assertIn("letter_text", rebuttal)
        self.assertIn("CONTRACT AMENDMENT & CLARIFICATION REQUEST", rebuttal["letter_text"])

    def test_zero_knowledge_client_encryption(self):
        secret_passphrase = "UltraSecureVaultPassphrase_2026!"
        sensitive_text = "Highly confidential trade secret formula and bank routing: 1234-5678-9012"

        # Encrypt
        encrypted = ZeroKnowledgeVaultCrypto.encrypt_text(sensitive_text, secret_passphrase)
        self.assertIn("ciphertext_base64", encrypted)
        self.assertIn("salt_hex", encrypted)
        self.assertIn("iv_hex", encrypted)

        # Decrypt
        decrypted = ZeroKnowledgeVaultCrypto.decrypt_text(encrypted, secret_passphrase)
        self.assertEqual(decrypted, sensitive_text)

        # Bad passphrase fails
        with self.assertRaises(Exception):
            ZeroKnowledgeVaultCrypto.decrypt_text(encrypted, "WrongPassword")

    def test_batch_dossier_export(self):
        docs = [
            {
                "doc_id": "d1",
                "filename": "contract.txt",
                "category": "Legal",
                "sha256_hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
                "raw_text": "Sample contract body text.",
            }
        ]
        zip_path = os.path.join(self.test_dir, "test_dossier.zip")
        res = BatchDossierExporter.export_dossier(docs, zip_path)
        self.assertTrue(res["success"])
        self.assertTrue(os.path.exists(zip_path))
        self.assertEqual(res["documents_exported"], 1)

    def test_retention_policy_enforcement(self):
        retention = RetentionPolicyManager()
        docs = [
            {"doc_id": "d_new", "filename": "new.pdf", "created_at": "2026-10-01T00:00:00"},
            {"doc_id": "d_old", "filename": "old.pdf", "created_at": "2023-01-01T00:00:00"},
            {"doc_id": "d_ancient", "filename": "ancient.pdf", "created_at": "2020-01-01T00:00:00"},
        ]
        summary = retention.get_retention_summary(docs)
        self.assertEqual(summary["total_evaluated"], 3)
        self.assertGreater(summary["archivable_count"] + summary["shreddable_count"], 0)

        enforce_res = retention.enforce_retention_policies(docs)
        self.assertTrue(enforce_res["success"])


if __name__ == "__main__":
    unittest.main()
