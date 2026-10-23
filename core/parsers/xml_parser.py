"""
DocuVaultAI — XML Parser (Unit 4: File Handling & xml.etree.ElementTree)
Parses structured XML documents such as electronic invoices, medical records,
and legal filings, extracting elements, attributes, and tabular line items.
"""

import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, Dict, List, Optional

from core.exceptions import ParsingError


class XMLDocumentParser:
    """Parses XML files using standard xml.etree.ElementTree with robust error handling."""

    @classmethod
    def parse_file(cls, filepath: str) -> Dict[str, Any]:
        """
        Parses an XML file and extracts structured elements and formatted plain text.
        Returns a dictionary with parsed metadata, elements, and full text.
        """
        if not Path(filepath).exists():
            raise FileNotFoundError(f"XML file not found: {filepath}")

        try:
            tree = ET.parse(filepath)
            root = tree.getroot()
        except ET.ParseError as e:
            raise ParsingError(
                parser_name="XMLDocumentParser",
                filepath=filepath,
                reason=f"XML syntax error: {str(e)}",
            )
        except Exception as e:
            raise ParsingError(
                parser_name="XMLDocumentParser",
                filepath=filepath,
                reason=f"Unexpected read error: {str(e)}",
            )

        # Extract tags and text
        extracted_data: Dict[str, Any] = {
            "root_tag": root.tag,
            "attributes": root.attrib,
            "fields": {},
            "line_items": [],
            "raw_text": "",
        }

        text_lines: List[str] = [f"XML Document Root: <{root.tag}>"]

        for child in root:
            # Strip XML namespace if present: {http://...}tag -> tag
            tag_name = child.tag.split("}")[-1] if "}" in child.tag else child.tag

            # Check if this child represents a collection of items (like <items> or <records>)
            if len(child) > 0:
                sub_items = []
                for sub in child:
                    sub_tag = sub.tag.split("}")[-1] if "}" in sub.tag else sub.tag
                    item_dict = {
                        k: v for k, v in sub.attrib.items()
                    }
                    if sub.text and sub.text.strip():
                        item_dict["_value"] = sub.text.strip()
                    for leaf in sub:
                        leaf_tag = leaf.tag.split("}")[-1] if "}" in leaf.tag else leaf.tag
                        item_dict[leaf_tag] = leaf.text.strip() if leaf.text else ""
                    sub_items.append(item_dict)
                extracted_data["line_items"].extend(sub_items)
                text_lines.append(f"Section {tag_name}: {len(sub_items)} items")
            else:
                val = child.text.strip() if child.text else ""
                extracted_data["fields"][tag_name] = val
                text_lines.append(f"{tag_name}: {val}")

        # Assemble full text representation for semantic indexing
        extracted_data["raw_text"] = "\n".join(text_lines)
        return extracted_data

    @classmethod
    def extract_text(cls, filepath: str) -> str:
        """Convenience method returning plain text extracted from XML."""
        data = cls.parse_file(filepath)
        return data.get("raw_text", "")
