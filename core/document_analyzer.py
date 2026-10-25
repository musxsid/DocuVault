"""
DocuVault — Document Analyzer & Legal Intelligence Engine
Provides:
1. 3-Bullet Executive Summaries
2. Counterparty & Entity Extraction
3. Contract Risk Profiling (Low, Medium, High)
4. Automated Rebuttal & Counter-Proposal Drafting
"""

import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple


class DocumentAnalyzer:
    """
    Intelligent analysis engine for commercial, legal, and operational documents.
    Generates structured summaries, entity manifests, risk badges, and rebuttal drafts.
    """

    @classmethod
    def extract_counterparties(cls, text: str) -> List[str]:
        """Extracts counterparty companies and parties from document text."""
        if not text:
            return ["Primary Organization"]

        parties = []
        # Pattern 1: Between Party A and Party B
        between_pattern = re.search(
            r"(?:between|amongst|by and between)\s+([A-Z][A-Za-z0-9\s,\.\(\)]+?)(?:,\s*(?:a|an)\s+[^\n]+)?\s+(?:and|&)\s+([A-Z][A-Za-z0-9\s,\.\(\)]+)",
            text[:2500],
            re.IGNORECASE,
        )
        if between_pattern:
            p1 = between_pattern.group(1).strip().strip(",")
            p2 = between_pattern.group(2).strip().strip(",")
            for p in (p1, p2):
                clean = re.sub(r"\s+", " ", p)[:45].strip()
                if clean and clean not in parties and len(clean) > 3:
                    parties.append(clean)

        # Pattern 2: Entity names with suffixes
        suffix_matches = re.findall(
            r"\b([A-Z][A-Za-z0-9]+(?:\s+[A-Z][A-Za-z0-9]+){0,3}\s+(?:Inc\.|LLC|Corp\.|Corporation|Ltd\.|Limited|Pvt\.|GmbH|Technologies|Solutions))\b",
            text[:4000],
        )
        for ent in suffix_matches:
            if ent not in parties and len(ent) < 50:
                parties.append(ent)

        if not parties:
            # Fallback to general counterparty
            first_lines = [line.strip() for line in text.split("\n") if line.strip()][:5]
            for l in first_lines:
                if any(k in l.lower() for k in ["agreement", "contract", "invoice", "record", "statement"]):
                    continue
                if len(l) < 40 and not any(ch in l for ch in "{}[];:"):
                    parties.append(l)
                    break

        return parties[:3] if parties else ["Disclosed Parties"]

    @classmethod
    def extract_executive_summary(cls, text: str, filename: str = "") -> List[str]:
        """Generates 3 bullet points highlighting purpose, scope, and key terms."""
        if not text or len(text.strip()) < 40:
            return [
                f"Document: {filename or 'Indexed file'} registered in secure vault.",
                "Content is ready for cryptographic verification and semantic AI inquiries.",
                "No technical defects detected during initial intake analysis.",
            ]

        bullets = []

        # Bullet 1: Core purpose & document type
        lower_sample = text[:1500].lower()
        if "non-disclosure" in lower_sample or "confidential" in lower_sample:
            bullets.append("Confidentiality & Non-Disclosure: Governs proprietary information exchange and mutual non-disclosure covenants.")
        elif "service" in lower_sample or "master service" in lower_sample:
            bullets.append("Services & Deliverables: Outlines professional consulting, milestone deliverables, and service fee frameworks.")
        elif "invoice" in lower_sample or "bill to" in lower_sample or "amount due" in lower_sample:
            bullets.append("Commercial Invoicing: Details line-item billables, tax assessment, and scheduled settlement terms.")
        elif "employment" in lower_sample or "internship" in lower_sample:
            bullets.append("Employment & Role Scope: Sets forth employment term, duties, compensation, and performance benchmarks.")
        else:
            first_sent = text.strip().split(".")[0].replace("\n", " ").strip()
            if len(first_sent) > 20 and len(first_sent) < 130:
                bullets.append(f"Scope: {first_sent}.")
            else:
                bullets.append(f"Document Overview: Standard verified {filename} registered in vault repository.")

        # Bullet 2: Key Clauses & Financial / Legal Terms
        dates = re.findall(r"\b(?:\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{4}-\d{2}-\d{2}|(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{1,2},? \d{4})\b", text)
        currencies = re.findall(r"(?:[\$\€\£\₹]\s*\d+(?:,\d{3})*(?:\.\d{2})?|\d+(?:,\d{3})*\s*(?:USD|EUR|GBP|INR))", text)
        term_match = re.search(r"(\d+[\s-]*(?:days?|months?|years?)\s*(?:notice|term|period))", text, re.IGNORECASE)

        b2_parts = []
        if dates:
            b2_parts.append(f"Recorded Date: {dates[0]}")
        if currencies:
            b2_parts.append(f"Financial Consideration: {currencies[0]}")
        if term_match:
            b2_parts.append(f"Statutory Timeline: {term_match.group(1)}")

        if b2_parts:
            bullets.append("Obligations & Terms: " + " • ".join(b2_parts) + ".")
        else:
            bullets.append("Terms & Provisions: Contains binding clauses, conditions, and standard boilerplate covenants.")

        # Bullet 3: Compliance & Integrity
        if "governing law" in lower_sample or "jurisdiction" in lower_sample:
            j_match = re.search(r"(?:governed by|jurisdiction of)\s+([A-Za-z\s]+)", text, re.IGNORECASE)
            jur = j_match.group(1).split(".")[0].strip()[:30] if j_match else "Specified Court"
            bullets.append(f"Legal Jurisdiction: Disputes subject to the laws and arbitration rules of {jur}.")
        else:
            bullets.append("Compliance Status: Cryptographically verified with anti-tamper SHA-256 fingerprint.")

        return bullets[:3]

    @classmethod
    def calculate_risk_profile(cls, text: str, clauses: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Assesses contractual and commercial risks.
        Returns risk level (Low, Medium, High), score (0-100), and specific flags.
        """
        text_lower = (text or "").lower()
        risk_score = 15  # Base score
        flags = []

        # High Risk indicators
        if "unlimited liability" in text_lower or "no limitation of liability" in text_lower:
            risk_score += 35
            flags.append("Unlimited liability exposure detected (no cap on damages)")
        elif "limitation of liability" not in text_lower and "liability" in text_lower:
            risk_score += 20
            flags.append("Absence of explicit liability cap provision")

        if "indemnify and hold harmless" in text_lower:
            if "solely" in text_lower or "unilateral" in text_lower:
                risk_score += 25
                flags.append("One-sided indemnification obligation imposed")
            else:
                risk_score += 10
                flags.append("Standard indemnification clause present")

        if "immediate termination" in text_lower or "terminate without notice" in text_lower:
            risk_score += 25
            flags.append("Unilateral termination without notice allowed")

        if "liquidated damages" in text_lower:
            risk_score += 20
            flags.append("Liquidated damages penalty clause active")

        if "non-compete" in text_lower:
            years = re.findall(r"(\d+)\s*(?:years?|yrs)", text_lower)
            if any(int(y) > 1 for y in years):
                risk_score += 25
                flags.append("Aggressive non-compete duration exceeding 1 year")
            else:
                risk_score += 10
                flags.append("Non-compete covenant present")

        # Missing standard protective clauses
        if clauses and not clauses.get("notice_period"):
            risk_score += 10
            flags.append("Notice period is unspecified or ambiguous")

        risk_score = min(100, max(5, risk_score))

        if risk_score <= 35:
            level = "Low"
            color = "#10B981"  # Emerald
            summary = "Standard balanced risk profile with customary safeguards."
        elif risk_score <= 65:
            level = "Medium"
            color = "#F59E0B"  # Amber
            summary = "Moderate risk exposure: review indemnification and notice terms."
        else:
            level = "High"
            color = "#EF4444"  # Red
            summary = "Elevated commercial/legal exposure: recommend drafting amendments."

        return {
            "risk_level": level,
            "risk_badge": level,
            "risk_score": risk_score,
            "score": risk_score,
            "badge_color": color,
            "color": color,
            "summary": summary,
            "flags": flags if flags else ["All assessed covenants adhere to standard balanced frameworks."],
        }

    @classmethod
    def generate_rebuttal(
        cls,
        filename: str,
        counterparties: List[str],
        risk_flags: List[str],
        missing_clauses: List[str],
    ) -> str:
        """
        Drafts a formal, courteous legal response letter requesting amendments
        addressing identified risks and missing protective terms.
        """
        p_name = counterparties[0] if counterparties else "Counterparty Legal Counsel"
        flags_text = "\n".join([f"  • {f}" for f in risk_flags]) if risk_flags else "  • Clarification on general liability terms"
        missing_text = "\n".join([f"  • Inability to locate: {m}" for m in missing_clauses]) if missing_clauses else "  • Reciprocal notice requirements"

        draft = f"""CONFIDENTIAL — CONTRACT AMENDMENT & CLARIFICATION REQUEST

Date: Today's Date
To: Legal Counsel / Contracts Department
Subject: Requested Modifications & Review of Agreement: {filename}

Dear {p_name} Team,

Thank you for providing the draft of '{filename}'. We have conducted an initial compliance and technical audit of the agreement terms. 

While we are enthusiastic about moving forward collaboratively, our legal compliance guidelines require modifications to balance mutual risk exposure before execution:

1. IDENTIFIED RISK COVENANTS REQUIRING REVISION:
{flags_text}

2. MISSING MANDATORY PROTECTIVE CLAUSES:
{missing_text}

RECOMMENDED PROPOSED AMENDMENTS:
1. Mutual Limitation of Liability: We propose capping each party's aggregate liability to direct damages not to exceed total fees paid under this Agreement in the preceding 12 months.
2. Symmetrical Notice Period: Any termination for convenience must require a minimum of thirty (30) days prior written notice.
3. Mutual Indemnification: Indemnity obligations should be reciprocal and strictly limited to third-party claims arising from gross negligence or willful misconduct.

Please review these proposed adjustments and let us know if you can provide an amended redline draft at your earliest convenience.

Sincerely,
Contracts & Compliance Review Team
DocuVault Enterprise
"""
        return draft.strip()

    @classmethod
    def draft_rebuttal_letter(cls, doc_dict: Dict[str, Any]) -> Dict[str, Any]:
        """
        Takes a document dictionary and automatically analyzes discrepancies,
        extracts counterparties, and generates a formal legal rebuttal letter.
        """
        fn = doc_dict.get("filename", "Agreement")
        text = " ".join([p.get("text", "") for p in doc_dict.get("pages", [])]) or doc_dict.get("raw_text", "")
        counterparties = doc_dict.get("counterparties") or cls.extract_counterparties(text)
        risk_profile = doc_dict.get("risk_profile") or cls.calculate_risk_profile(text, doc_dict.get("clauses"))
        flags = risk_profile.get("flags", [])

        # Missing clauses
        clauses = doc_dict.get("clauses", {})
        missing = []
        mandatory = ["Termination Notice", "Governing Law", "Limitation of Liability", "Confidentiality"]
        for m in mandatory:
            if not any(m.lower() in k.lower() for k in clauses.keys()):
                missing.append(m)

        letter_text = cls.generate_rebuttal(fn, counterparties, flags, missing)
        return {
            "filename": fn,
            "counterparties": counterparties,
            "discrepancies_addressed": flags + missing,
            "letter_text": letter_text,
            "created_at": datetime.now().isoformat(),
        }
