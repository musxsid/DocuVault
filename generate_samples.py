"""
DocuVaultAI — Sample Document Generator
Generates realistic sample documents (PDF, XML, TXT, and a disguised malicious file)
in vault/intake to demonstrate ingestion, parsing, verification, and auto-sorting live.
"""

import os
import sys
from pathlib import Path

# Fix Windows cp1252 console encoding for emojis
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Try creating genuine PDFs with pymupdf (fitz) or fallback to valid PDF binary header
try:
    import pymupdf as fitz
    PYMUPDF_AVAILABLE = True
except ImportError:
    try:
        import fitz
        PYMUPDF_AVAILABLE = True
    except ImportError:
        PYMUPDF_AVAILABLE = False


def ensure_dirs():
    os.makedirs("vault/intake", exist_ok=True)
    os.makedirs("vault/Legal", exist_ok=True)
    os.makedirs("vault/Medical", exist_ok=True)
    os.makedirs("vault/Financial", exist_ok=True)
    os.makedirs("vault/Academic", exist_ok=True)
    os.makedirs("vault/General", exist_ok=True)
    os.makedirs("vault/quarantine", exist_ok=True)
    os.makedirs("vault/plots", exist_ok=True)


def create_sample_pdf(filepath: str, title: str, content: str):
    """Creates a valid PDF document with %PDF- header."""
    if PYMUPDF_AVAILABLE:
        doc = fitz.open()
        page = doc.new_page()
        # Insert title and content text
        text_full = f"{title.upper()}\n\n{content}"
        rect = fitz.Rect(50, 50, 550, 750)
        page.insert_textbox(rect, text_full, fontsize=11, fontname="helv", color=(0, 0, 0))
        doc.save(filepath)
        doc.close()
    else:
        # Generate minimal valid PDF 1.4 binary structure
        pdf_bytes = (
            b"%PDF-1.4\n"
            b"1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj\n"
            b"2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj\n"
            b"3 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R >> endobj\n"
            b"4 0 obj << /Length " + str(len(content)).encode() + b" >>\nstream\nBT\n/F1 12 Tf\n50 700 Td\n("
            + content.replace("(", "").replace(")", "").encode("latin-1", errors="replace")
            + b") Tj\nET\nendstream\nendobj\nxref\n0 5\n0000000000 65535 f \n0000000009 00000 n \n0000000058 00000 n \n0000000115 00000 n \n0000000214 00000 n \ntrailer << /Size 5 /Root 1 0 R >>\nstartxref\n320\n%%EOF\n"
        )
        with open(filepath, "wb") as f:
            f.write(pdf_bytes)


def generate_all_samples():
    ensure_dirs()
    print("Generating DocuVaultAI sample documents...")

    # 1. Legal NDA Contract (PDF)
    nda_text = (
        "MUTUAL NON-DISCLOSURE AGREEMENT\n\n"
        "This Mutual Non-Disclosure Agreement (the 'Agreement') is entered into as of 2026-10-15 (the 'Effective Date')\n"
        "between Apex Innovations Inc. and Quantum Dynamics LLC.\n\n"
        "1. Governing Law & Jurisdiction: This Agreement shall be governed by and construed in accordance with the laws of\n"
        "the State of Delaware, and the parties submit to the exclusive jurisdiction of the state courts located in Delaware.\n\n"
        "2. Confidentiality: Each party agrees to protect the confidential information of the other party with the same degree\n"
        "of care it uses for its own confidential information.\n\n"
        "3. Notice Period: Either party may terminate this Agreement upon prior written notice of 30 days.\n\n"
        "4. Limitation of Liability: In no event shall aggregate liability exceed $500,000 USD.\n"
        "Payment due date: 2026-11-20."
    )
    create_sample_pdf("vault/intake/NDA_Apex_Quantum_2026.pdf", "Mutual NDA", nda_text)
    print("✓ Created: vault/intake/NDA_Apex_Quantum_2026.pdf")

    # 2. Financial Invoice (XML)
    invoice_xml = """<?xml version="1.0" encoding="UTF-8"?>
<invoice id="INV-2026-9042">
    <vendor>
        <name>CloudScale Enterprise Systems LLC</name>
        <tax_id>TAX-US-993821</tax_id>
        <email>billing@cloudscale.io</email>
    </vendor>
    <customer>
        <name>DocuVault Global Operations</name>
        <account_number>ACC-44120</account_number>
    </customer>
    <invoice_date>2026-10-01</invoice_date>
    <due_date>2026-11-15</due_date>
    <currency>USD</currency>
    <items>
        <item code="SRV-01">
            <description>Dedicated GPU Cluster Infrastructure</description>
            <quantity>2</quantity>
            <unit_price>3200.00</unit_price>
            <total>6400.00</total>
        </item>
        <item code="SEC-09">
            <description>SOC2 Compliance Audit Module</description>
            <quantity>1</quantity>
            <unit_price>1850.00</unit_price>
            <total>1850.00</total>
        </item>
    </items>
    <financial_summary>
        <subtotal>8250.00</subtotal>
        <tax_rate>0.08</tax_rate>
        <tax_amount>660.00</tax_amount>
        <total_amount>$8,910.00</total_amount>
    </financial_summary>
    <payment_terms>Net 30. Penalty of 1.5% for overdue payments.</payment_terms>
</invoice>"""
    with open("vault/intake/Vendor_Invoice_INV-9042.xml", "w", encoding="utf-8") as f:
        f.write(invoice_xml)
    print("✓ Created: vault/intake/Vendor_Invoice_INV-9042.xml")

    # 3. Medical Record / Clinical Protocol (XML)
    medical_xml = """<?xml version="1.0" encoding="UTF-8"?>
<medical_record mrn="MRN-77821">
    <patient>
        <patient_id>PT-89410</patient_id>
        <full_name>Eleanor Vance</full_name>
        <dob>1982-05-14</dob>
    </patient>
    <encounter>
        <date>2026-10-02</date>
        <physician>Dr. Sarah Jenkins</physician>
        <department>Neurology Clinical Research</department>
    </encounter>
    <clinical_assessment>
        <diagnosis>Mild Cognitive Impairment, Protocol Cohort B</diagnosis>
        <treatment_plan>Administer therapeutic dosage bi-weekly with EEG monitoring.</treatment_plan>
        <next_evaluation>2026-12-25</next_evaluation>
    </clinical_assessment>
    <compliance>
        <hipaa_notice>Confidential medical record protected under HIPAA Privacy Act.</hipaa_notice>
    </compliance>
</medical_record>"""
    with open("vault/intake/Medical_Clinical_Record_MRN77821.xml", "w", encoding="utf-8") as f:
        f.write(medical_xml)
    print("✓ Created: vault/intake/Medical_Clinical_Record_MRN77821.xml")

    # 4. Academic Research Paper (TXT)
    academic_txt = (
        "QUANTUM ERROR MITIGATION IN HIGH-DIMENSIONAL HILBERT SPACES\n\n"
        "Authors: Dr. Raymond Chen, Dr. Alistair Finch\n"
        "DOI: 10.1103/PhysRevLett.128.090501\n"
        "Date: 2026-09-18\n\n"
        "Abstract: In this work, we demonstrate a scalable quantum error mitigation protocol designed for\n"
        "noisy intermediate-scale quantum (NISQ) architectures. Using Clifford randomization and dynamic\n"
        "decoupling sequences, we reduce circuit infidelities by 42% on superconducting transmon processors.\n\n"
        "Keywords: Quantum Computing, Error Mitigation, Decoherence, Superconducting Qubits, Fidelity\n\n"
        "References:\n"
        "[1] Preskill, J. Quantum 2, 79 (2018).\n"
        "[2] Nielsen, M. A. & Chuang, I. L. Quantum Computation and Quantum Information (2010)."
    )
    with open("vault/intake/Academic_Quantum_Error_Mitigation.txt", "w", encoding="utf-8") as f:
        f.write(academic_txt)
    print("✓ Created: vault/intake/Academic_Quantum_Error_Mitigation.txt")

    # 5. Master Services Agreement (Legal TXT)
    msa_text = (
        "MASTER SERVICES AGREEMENT\n\n"
        "This Master Services Agreement is entered into on 2026-10-05 between Horizon Cloud Inc. and Titan Media Corp.\n"
        "Effective Date: 2026-10-10.\n\n"
        "Jurisdiction: Under the laws of the State of New York.\n"
        "Prior written notice of 60 days required for termination without cause.\n"
        "Limitation of Liability: Maximum liability shall not exceed $1,250,000 USD.\n"
        "Deliverable deadline: 2026-11-26."
    )
    with open("vault/intake/Master_Services_Agreement_NY.txt", "w", encoding="utf-8") as f:
        f.write(msa_text)
    print("✓ Created: vault/intake/Master_Services_Agreement_NY.txt")

    # 6. Disguised Malicious File (Starts with PE Executable Magic 'MZ', named .pdf to test security alert)
    corrupt_pe = b"MZ\x90\x00\x03\x00\x00\x00\x04\x00\x00\x00\xff\xff\x00\x00This program cannot be run in DOS mode."
    with open("vault/intake/Disguised_Malware_Payload.pdf", "wb") as f:
        f.write(corrupt_pe)
    print("✓ Created: vault/intake/Disguised_Malware_Payload.pdf (Disguised PE to test CorruptFileError & Quarantine)")

    # 7. Clean File for Tamper Detection Testing
    with open("vault/intake/Clean_Integrity_Verification.txt", "w", encoding="utf-8") as f:
        f.write("Official verification test record. Hash integrity verified on 2026-10-05.")
    print("✓ Created: vault/intake/Clean_Integrity_Verification.txt")

    print("\nAll sample documents generated successfully in 'vault/intake'!")


if __name__ == "__main__":
    generate_all_samples()
