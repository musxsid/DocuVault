"""
DocuVaultAI — Document OOP Hierarchy & Regex Extractor (Unit 1: OOP & Regex)
Implements polymorphic Document classes (BaseDocument, LegalDocument, MedicalDocument,
AcademicDocument, FinancialDocument, GenericDocument), regex entity validation,
and a polymorphic DocumentFactory.
"""

import os
import re
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import uuid4

from core.exceptions import (
    CorruptFileError,
    InvalidFormError,
    MissingClauseError,
    TamperedFileError,
)
from core.parsers.binary_parser import BinaryParser
from core.parsers.pdf_parser import PDFDocumentParser
from core.parsers.xml_parser import XMLDocumentParser


class BaseDocument(ABC):
    """
    Abstract Base Class for all indexed documents in DocuVault.
    Enforces polymorphic interface for entity extraction and compliance verification.
    """

    # Comprehensive compiled Regular Expressions for entities across all document types
    REGEX_DATE_ISO = re.compile(r"\b\d{4}[-/](?:0[1-9]|1[0-2])[-/](?:0[1-9]|[12]\d|3[01])\b")
    REGEX_DATE_DMY = re.compile(r"\b(?:0[1-9]|[12]\d|3[01])[-/.](?:0[1-9]|1[0-2])[-/.]\d{4}\b")
    REGEX_DATE_VERBOSE = re.compile(
        r"\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}\b",
        re.IGNORECASE,
    )
    REGEX_CURRENCY = re.compile(
        r"(?:[\$\€\£\₹]|USD|EUR|GBP|INR)\s*(?:[0-9]{1,3}(?:,[0-9]{3})*|\d+)(?:\.\d{2})?\b",
        re.IGNORECASE,
    )
    REGEX_DEADLINE = re.compile(
        r"(?:due\s+date|payment\s+due|effective\s+until|expiry\s+date|expires\s+on|terminate\s+on|deadline|within)\s*[:\-]?\s*([^\n\.,;]+)",
        re.IGNORECASE,
    )
    REGEX_EMAIL = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b")
    REGEX_PHONE = re.compile(r"\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b")

    def __init__(
        self,
        filepath: str,
        raw_text: str = "",
        pages: Optional[List[Dict[str, Any]]] = None,
        doc_id: Optional[str] = None,
    ) -> None:
        self.doc_id: str = doc_id or str(uuid4())[:8]
        self.filepath: str = filepath
        self.filename: str = Path(filepath).name
        self.file_type: str = Path(filepath).suffix.lower()
        self.raw_text: str = raw_text
        self.pages: List[Dict[str, Any]] = pages or [{"page_number": 1, "text": raw_text}]
        self.created_at: str = datetime.now().isoformat()
        self.size_bytes: int = os.path.getsize(filepath) if os.path.exists(filepath) else len(raw_text.encode())
        self.sha256_hash: str = BinaryParser.calculate_sha256(filepath) if os.path.exists(filepath) else ""
        self.status: str = "Verified"
        self.extracted_entities: Dict[str, Any] = {}
        self.clauses: Dict[str, str] = {}

    @abstractmethod
    def extract_clauses_and_entities(self) -> Dict[str, Any]:
        """Extract domain-specific legal or record clauses using regular expressions."""
        pass

    @abstractmethod
    def validate_compliance(self) -> bool:
        """Validate compliance standards; raises MissingClauseError on critical omissions."""
        pass

    @abstractmethod
    def get_category(self) -> str:
        """Return the category folder name (e.g. Legal, Medical, Financial, Academic)."""
        pass

    def extract_dates(self) -> List[str]:
        """Extract all date strings matching ISO, DMY, or verbose formats."""
        dates: List[str] = []
        dates.extend(self.REGEX_DATE_ISO.findall(self.raw_text))
        dates.extend(self.REGEX_DATE_DMY.findall(self.raw_text))
        dates.extend(self.REGEX_DATE_VERBOSE.findall(self.raw_text))
        return list(dict.fromkeys(dates))  # Preserve unique order

    def extract_currency_amounts(self) -> List[str]:
        """Extract all monetary values with currency symbols or codes."""
        amounts = self.REGEX_CURRENCY.findall(self.raw_text)
        return list(dict.fromkeys(amounts))

    def extract_deadlines(self) -> List[str]:
        """Extract potential deadlines and contractual timeframes."""
        deadlines: List[str] = []
        for match in self.REGEX_DEADLINE.finditer(self.raw_text):
            clause = match.group(0).strip()
            deadlines.append(clause)
        return deadlines

    def verify_integrity(self) -> bool:
        """Verify file on disk matches the recorded SHA-256 hash."""
        if not os.path.exists(self.filepath):
            return False
        try:
            return BinaryParser.verify_integrity(self.filepath, self.sha256_hash)
        except TamperedFileError:
            self.status = "Tampered"
            return False

    def to_dict(self) -> Dict[str, Any]:
        """Convert document state to dictionary for APIs, UI tables, and catalog indexing."""
        return {
            "doc_id": self.doc_id,
            "filename": self.filename,
            "filepath": self.filepath,
            "category": self.get_category(),
            "file_type": self.file_type,
            "size_bytes": self.size_bytes,
            "sha256_hash": self.sha256_hash,
            "status": self.status,
            "created_at": self.created_at,
            "raw_text": self.raw_text,
            "pages": self.pages,
            "extracted_dates": self.extract_dates(),
            "currency_amounts": self.extract_currency_amounts(),
            "clauses": self.clauses,
            "entities": self.extracted_entities,
            "page_count": len(self.pages),
        }

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} id='{self.doc_id}' name='{self.filename}' category='{self.get_category()}'>"


class LegalDocument(BaseDocument):
    """
    Subclass for contracts, agreements, NDAs, and terms of service.
    Enforces rigorous regex verification of legal clauses.
    """

    # Legal clause regex patterns
    CLAUSE_PATTERNS = {
        "Jurisdiction": re.compile(
            r"(?:jurisdiction|governing\s+law|laws\s+of)\s*(?:is|shall\s+be|under)?\s*[:\-]?\s*([A-Za-z\s]{3,35}(?:State|District|Court|County|England|Wales|India|California|New York|Delaware))",
            re.IGNORECASE,
        ),
        "Notice Period": re.compile(
            r"(?:notice\s+period|prior\s+written\s+notice)\s*(?:of)?\s*[:\-]?\s*(\d+\s*(?:days|weeks|months))",
            re.IGNORECASE,
        ),
        "Effective Date": re.compile(
            r"(?:effective\s+date|commencement\s+date)\s*(?:is|shall\s+be)?\s*[:\-]?\s*(\b\d{4}[-/]\d{2}[-/]\d{2}\b|\b\d{1,2}[-/]\d{1,2}[-/]\d{4}\b|(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4})",
            re.IGNORECASE,
        ),
        "Liability": re.compile(
            r"(?:limitation\s+of\s+liability|maximum\s+liability|aggregate\s+liability)[^\.\n]{5,100}",
            re.IGNORECASE,
        ),
        "Confidentiality": re.compile(
            r"(?:confidential\s+information|non-disclosure|keep\s+confidential)[^\.\n]{5,100}",
            re.IGNORECASE,
        ),
        "Termination": re.compile(
            r"(?:termination\s+for\s+cause|right\s+to\s+terminate|termination\s+clause)[^\.\n]{5,100}",
            re.IGNORECASE,
        ),
    }

    def get_category(self) -> str:
        return "Legal"

    def extract_clauses_and_entities(self) -> Dict[str, Any]:
        """Extracts legal compliance clauses using regular expressions."""
        for clause_name, pattern in self.CLAUSE_PATTERNS.items():
            match = pattern.search(self.raw_text)
            if match:
                # Capture group 1 if present, else full match
                val = match.group(1).strip() if match.groups() else match.group(0).strip()
                self.clauses[clause_name] = val

        self.extracted_entities["parties"] = re.findall(
            r"(?:between|among|Party\s+A|Party\s+B)\s*[:\-]?\s*([A-Z][A-Za-z0-9\s,\.]{3,40}(?:Inc\.|LLC|Corp\.|Ltd\.|Company|Corporation)?)",
            self.raw_text,
        )
        return self.clauses

    def validate_compliance(self, strict: bool = False) -> bool:
        """
        Validates presence of essential legal clauses.
        Raises MissingClauseError if strict mode is enabled and critical clauses are absent.
        """
        self.extract_clauses_and_entities()
        # Minimum required clauses for a valid contract
        mandatory_clauses = ["Jurisdiction", "Effective Date"]
        missing = [c for c in mandatory_clauses if c not in self.clauses]

        if missing and strict:
            raise MissingClauseError(
                document_id=self.doc_id,
                missing_clauses=missing,
                jurisdiction=self.clauses.get("Jurisdiction"),
            )
        return len(missing) == 0


class MedicalDocument(BaseDocument):
    """Subclass for clinical records, lab reports, and prescription orders."""

    PATTERNS = {
        "Patient ID": re.compile(r"(?:patient\s*id|mrn|record\s*#)\s*[:\-]?\s*([A-Za-z0-9\-]{4,15})", re.IGNORECASE),
        "Physician": re.compile(r"(?:dr\.|doctor|physician)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)", re.IGNORECASE),
        "Diagnosis": re.compile(r"(?:diagnosis|condition|assessment)\s*[:\-]?\s*([^\n\.;]+)", re.IGNORECASE),
        "HIPAA Notice": re.compile(r"(?:hipaa|privacy\s+act|confidential\s+medical\s+record)", re.IGNORECASE),
    }

    def get_category(self) -> str:
        return "Medical"

    def extract_clauses_and_entities(self) -> Dict[str, Any]:
        for field, pattern in self.PATTERNS.items():
            match = pattern.search(self.raw_text)
            if match:
                self.extracted_entities[field] = match.group(1).strip() if match.groups() else "Acknowledged"
        return self.extracted_entities

    def validate_compliance(self) -> bool:
        self.extract_clauses_and_entities()
        return "Patient ID" in self.extracted_entities


class AcademicDocument(BaseDocument):
    """Subclass for research papers, preprints, and academic theses."""

    PATTERNS = {
        "DOI": re.compile(r"\b10\.\d{4,9}/[-._;()/:A-Za-z0-9]+\b"),
        "Abstract": re.compile(r"abstract\s*[:\-]?\s*([\s\S]{30,500}?)(?:\n\n|keywords|introduction)", re.IGNORECASE),
        "Keywords": re.compile(r"keywords\s*[:\-]?\s*([^\n\.]+)", re.IGNORECASE),
    }

    def get_category(self) -> str:
        return "Academic"

    def extract_clauses_and_entities(self) -> Dict[str, Any]:
        for field, pattern in self.PATTERNS.items():
            match = pattern.search(self.raw_text)
            if match:
                self.extracted_entities[field] = match.group(1).strip() if match.groups() else match.group(0).strip()
        return self.extracted_entities

    def validate_compliance(self) -> bool:
        self.extract_clauses_and_entities()
        return "Abstract" in self.extracted_entities or "DOI" in self.extracted_entities


class FinancialDocument(BaseDocument):
    """Subclass for invoices, financial balance sheets, and purchase orders."""

    PATTERNS = {
        "Invoice Number": re.compile(r"(?:invoice\s*#|inv\s*no|bill\s*#)\s*[:\-]?\s*([A-Za-z0-9\-]+)", re.IGNORECASE),
        "Tax ID": re.compile(r"(?:tax\s*id|vat\s*#|ein|gstin)\s*[:\-]?\s*([A-Za-z0-9\-]+)", re.IGNORECASE),
        "Payment Terms": re.compile(r"(?:net\s+\d+|due\s+on\s+receipt|payment\s+terms\s*[:\-]?\s*[^\n\.]+)", re.IGNORECASE),
    }

    def get_category(self) -> str:
        return "Financial"

    def extract_clauses_and_entities(self) -> Dict[str, Any]:
        for field, pattern in self.PATTERNS.items():
            match = pattern.search(self.raw_text)
            if match:
                self.extracted_entities[field] = match.group(1).strip() if match.groups() else match.group(0).strip()
        amounts = self.extract_currency_amounts()
        if amounts:
            self.extracted_entities["Detected Amounts"] = amounts
        return self.extracted_entities

    def validate_compliance(self) -> bool:
        self.extract_clauses_and_entities()
        return len(self.extract_currency_amounts()) > 0 or "Invoice Number" in self.extracted_entities


class GenericDocument(BaseDocument):
    """Fallback subclass for general documents, notes, and unclassified texts."""

    def get_category(self) -> str:
        return "General"

    def extract_clauses_and_entities(self) -> Dict[str, Any]:
        self.extracted_entities["dates"] = self.extract_dates()
        self.extracted_entities["currencies"] = self.extract_currency_amounts()
        return self.extracted_entities

    def validate_compliance(self) -> bool:
        return True


class DocumentFactory:
    """
    Polymorphic Factory for validating, parsing, and instantiating
    appropriate BaseDocument subclasses.
    """

    @classmethod
    def create_document(
        cls,
        filepath: str,
        raw_text: Optional[str] = None,
        category_hint: Optional[str] = None,
        enforce_magic_bytes: bool = True,
    ) -> BaseDocument:
        """
        Ingests a file, verifies binary magic bytes, extracts text,
        determines subclass, and instantiates the concrete document model.
        """
        path = Path(filepath)
        ext = path.suffix.lower()

        # Step 1: Binary validation
        if enforce_magic_bytes and path.exists():
            BinaryParser.validate_file(str(path))

        # Step 2: Content extraction
        pages: List[Dict[str, Any]] = []
        if raw_text is None and path.exists():
            if ext == ".pdf":
                pdf_data = PDFDocumentParser.parse_file(str(path))
                raw_text = pdf_data["raw_text"]
                pages = pdf_data["pages"]
            elif ext == ".xml":
                xml_data = XMLDocumentParser.parse_file(str(path))
                raw_text = xml_data["raw_text"]
                pages = [{"page_number": 1, "text": raw_text}]
            elif ext in [".png", ".jpg", ".jpeg", ".webp"]:
                from core.ocr_engine import OCREngine
                ocr_res = OCREngine.extract_text_from_image(str(path))
                raw_text = ocr_res.get("text", "")
                pages = ocr_res.get("pages", [{"page_number": 1, "text": raw_text}])
            else:
                # Text file handling
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        raw_text = f.read()
                except UnicodeDecodeError:
                    with open(path, "r", encoding="latin-1") as f:
                        raw_text = f.read()
                pages = [{"page_number": 1, "text": raw_text}]
        elif raw_text is None:
            raw_text = ""
            pages = [{"page_number": 1, "text": ""}]

        # Step 3: Determine document subclass based on category hint or heuristic content analysis
        text_lower = raw_text.lower()

        target_class = GenericDocument
        if category_hint:
            hint = category_hint.strip().capitalize()
            if hint == "Legal":
                target_class = LegalDocument
            elif hint == "Medical":
                target_class = MedicalDocument
            elif hint == "Academic":
                target_class = AcademicDocument
            elif hint == "Financial":
                target_class = FinancialDocument
        else:
            # Heuristic keyword classifiers
            if any(k in text_lower for k in ["agreement", "contract", "nda", "jurisdiction", "liability", "hereby", "parties"]):
                target_class = LegalDocument
            elif any(k in text_lower for k in ["patient", "diagnosis", "prescription", "clinic", "hospital", "physician", "hipaa"]):
                target_class = MedicalDocument
            elif any(k in text_lower for k in ["invoice", "subtotal", "tax", "balance due", "gstin", "payment terms"]):
                target_class = FinancialDocument
            elif any(k in text_lower for k in ["abstract", "doi:", "references", "hypothesis", "ieee", "springer", "arxiv"]):
                target_class = AcademicDocument

        doc_instance = target_class(filepath=str(path), raw_text=raw_text, pages=pages)
        doc_instance.extract_clauses_and_entities()
        return doc_instance
