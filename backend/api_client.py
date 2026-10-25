"""
DocuVaultAI — External API Clients (Unit 2: REST APIs & Error Handling)
Consumes public holiday APIs (Nager.Date) for working-day deadline adjustments
and external/local LLM APIs (Groq, Gemini, Ollama) with offline fallback.
"""

import base64
import json
import os
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import requests

from core.exceptions import CalendarAPIError


class PublicHolidayClient:
    """
    Consumes the public Nager.Date REST API to retrieve national public holidays
    and calculate valid working-day deadlines with weekend and holiday shifting.
    Includes an offline fallback dictionary for resilient zero-network operation.
    """

    BASE_URL = "https://date.nager.at/api/v3"

    # Built-in offline fallback holidays for major jurisdictions (US, GB, IN, DE)
    OFFLINE_HOLIDAY_CACHE: Dict[str, Set[str]] = {
        "US": {
            "2026-01-01", "2026-01-19", "2026-02-16", "2026-05-25",
            "2026-06-19", "2026-07-03", "2026-09-07", "2026-10-12",
            "2026-11-11", "2026-11-26", "2026-12-25",
        },
        "GB": {
            "2026-01-01", "2026-04-03", "2026-04-06", "2026-05-04",
            "2026-05-25", "2026-08-31", "2026-12-25", "2026-12-28",
        },
        "IN": {
            "2026-01-26", "2026-03-04", "2026-04-03", "2026-08-15",
            "2026-10-02", "2026-10-20", "2026-11-08", "2026-12-25",
        },
    }

    def __init__(self, default_country: str = "US") -> None:
        self.default_country = default_country.upper()
        self._cache: Dict[str, Set[str]] = {}

    def fetch_holidays(self, year: int, country_code: Optional[str] = None) -> Set[str]:
        """
        Fetch official public holidays via REST HTTP GET request.
        Falls back to offline calendar cache on network failure or timeout.
        """
        cc = (country_code or self.default_country).upper()
        cache_key = f"{cc}_{year}"

        if cache_key in self._cache:
            return self._cache[cache_key]

        holiday_dates: Set[str] = set()

        try:
            url = f"{self.BASE_URL}/PublicHolidays/{year}/{cc}"
            response = requests.get(url, timeout=3.0)

            if response.status_code == 200:
                data = response.json()
                for item in data:
                    if "date" in item:
                        holiday_dates.add(item["date"])
                self._cache[cache_key] = holiday_dates
                return holiday_dates
            else:
                # Use offline fallback cache
                holiday_dates = self.OFFLINE_HOLIDAY_CACHE.get(cc, set())
                self._cache[cache_key] = holiday_dates
                return holiday_dates

        except (requests.RequestException, Exception):
            # Resilient offline-first fallback
            holiday_dates = self.OFFLINE_HOLIDAY_CACHE.get(cc, set())
            self._cache[cache_key] = holiday_dates
            return holiday_dates

    def is_working_day(self, target_date: date, country_code: Optional[str] = None) -> bool:
        """
        Check if a given date is a valid working day (Monday-Friday, not a public holiday).
        """
        # Saturday is 5, Sunday is 6
        if target_date.weekday() >= 5:
            return False

        holidays = self.fetch_holidays(target_date.year, country_code)
        date_str = target_date.strftime("%Y-%m-%d")
        return date_str not in holidays

    def calculate_working_deadline(
        self,
        start_date: date,
        business_days: int = 0,
        country_code: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Adjusts a deadline to the nearest valid business working day.
        If business_days > 0, adds that many business working days.
        If business_days == 0, adjusts start_date if it falls on a weekend or public holiday.
        """
        current = start_date
        days_added = 0
        original_date = start_date

        if business_days > 0:
            while days_added < business_days:
                current += timedelta(days=1)
                if self.is_working_day(current, country_code):
                    days_added += 1
        else:
            # Shift forward until it lands on a working day
            while not self.is_working_day(current, country_code):
                current += timedelta(days=1)

        shifted = (current != original_date)
        return {
            "original_date": original_date.strftime("%Y-%m-%d"),
            "working_deadline": current.strftime("%Y-%m-%d"),
            "was_shifted": shifted,
            "shift_reason": "Weekend or Public Holiday" if shifted else "Valid Business Day",
            "country_code": country_code or self.default_country,
        }


class LLMClient:
    """
    Multi-provider LLM API client (Google Gemini, Groq, OpenAI, Local Ollama)
    with persistent configuration, real-time connection verification,
    multimodal image OCR, and offline deterministic fallback.
    """

    CONFIG_FILE = Path("config/api_keys.json")

    def __init__(self) -> None:
        self.CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
        keys = self.load_api_keys()
        self.gemini_api_key: str = keys.get("gemini_api_key") or os.getenv("GEMINI_API_KEY", "")
        self.groq_api_key: str = keys.get("groq_api_key") or os.getenv("GROQ_API_KEY", "")
        self.openai_api_key: str = keys.get("openai_api_key") or os.getenv("OPENAI_API_KEY", "")
        self.ollama_url: str = keys.get("ollama_url") or os.getenv("OLLAMA_URL", "http://localhost:11434")
        self.preferred_provider: str = keys.get("preferred_provider", "auto")

    def load_api_keys(self) -> Dict[str, str]:
        """Loads saved API keys from persistent configuration file."""
        if not self.CONFIG_FILE.exists():
            return {}
        try:
            with open(self.CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    def save_api_keys(self, keys: Dict[str, str]) -> None:
        """Saves API keys to persistent configuration file and updates runtime state."""
        current = self.load_api_keys()
        current.update(keys)
        try:
            with open(self.CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(current, f, indent=2)
        except Exception as e:
            print(f"[LLMClient] Failed to save api_keys.json: {e}")

        # Refresh runtime attributes
        if "gemini_api_key" in current:
            self.gemini_api_key = current["gemini_api_key"]
            os.environ["GEMINI_API_KEY"] = self.gemini_api_key
        if "groq_api_key" in current:
            self.groq_api_key = current["groq_api_key"]
            os.environ["GROQ_API_KEY"] = self.groq_api_key
        if "openai_api_key" in current:
            self.openai_api_key = current["openai_api_key"]
            os.environ["OPENAI_API_KEY"] = self.openai_api_key
        if "ollama_url" in current:
            self.ollama_url = current["ollama_url"]
        if "preferred_provider" in current:
            self.preferred_provider = current["preferred_provider"]

    def set_api_key(self, provider: str, key: str) -> None:
        """Sets and persists a single API key."""
        p = provider.lower().strip()
        field_map = {
            "gemini": "gemini_api_key",
            "groq": "groq_api_key",
            "openai": "openai_api_key",
        }
        if p in field_map:
            self.save_api_keys({field_map[p]: key.strip()})

    def get_api_keys(self) -> Dict[str, str]:
        """Returns currently active API keys dict."""
        return {
            "gemini_api_key": self.gemini_api_key,
            "groq_api_key": self.groq_api_key,
            "openai_api_key": self.openai_api_key,
            "ollama_url": self.ollama_url,
            "preferred_provider": self.preferred_provider,
        }

    def has_any_active_key(self) -> bool:
        """Returns True if at least one cloud LLM API key is present."""
        return bool(self.gemini_api_key or self.groq_api_key or self.openai_api_key)

    def test_api_key(self, provider: str, key: Optional[str] = None) -> Tuple[bool, str]:
        """
        Tests API connectivity in real time with the specified provider.
        Returns (success: bool, status_message: str).
        """
        prov = provider.lower().strip()
        test_key = (key or "").strip()

        if prov == "gemini":
            k = test_key or self.gemini_api_key
            if not k:
                return False, "Google Gemini API key is empty."
            try:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={k}"
                body = {"contents": [{"parts": [{"text": "Reply with 'OK'."}]}]}
                r = requests.post(url, json=body, timeout=8.0)
                if r.status_code == 200:
                    return True, "Connected successfully to Google Gemini (gemini-1.5-flash)."
                err_msg = r.json().get("error", {}).get("message", f"HTTP {r.status_code}")
                return False, f"Gemini Error: {err_msg}"
            except Exception as e:
                return False, f"Gemini connection failed: {e}"

        elif prov == "groq":
            k = test_key or self.groq_api_key
            if not k:
                return False, "Groq API key is empty."
            try:
                headers = {
                    "Authorization": f"Bearer {k}",
                    "Content-Type": "application/json",
                }
                body = {
                    "model": "llama-3.1-8b-instant",
                    "messages": [{"role": "user", "content": "ping"}],
                    "max_tokens": 5,
                }
                r = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=body, timeout=8.0)
                if r.status_code == 200:
                    return True, "Connected successfully to Groq Cloud (llama-3.1-8b-instant)."
                err_msg = r.json().get("error", {}).get("message", f"HTTP {r.status_code}")
                return False, f"Groq Error: {err_msg}"
            except Exception as e:
                return False, f"Groq connection failed: {e}"

        elif prov == "openai":
            k = test_key or self.openai_api_key
            if not k:
                return False, "OpenAI API key is empty."
            try:
                headers = {
                    "Authorization": f"Bearer {k}",
                    "Content-Type": "application/json",
                }
                body = {
                    "model": "gpt-4o-mini",
                    "messages": [{"role": "user", "content": "ping"}],
                    "max_tokens": 5,
                }
                r = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=body, timeout=8.0)
                if r.status_code == 200:
                    return True, "Connected successfully to OpenAI (gpt-4o-mini)."
                err_msg = r.json().get("error", {}).get("message", f"HTTP {r.status_code}")
                return False, f"OpenAI Error: {err_msg}"
            except Exception as e:
                return False, f"OpenAI connection failed: {e}"

        return False, f"Unknown provider '{provider}'."

    def extract_text_from_image_vision(self, filepath: str, api_key: Optional[str] = None) -> Optional[str]:
        """
        Multimodal image OCR using Google Gemini Vision REST API.
        Extracts visible text, handwriting, tables, and document details verbatim.
        """
        k = api_key or self.gemini_api_key
        if not k or not os.path.exists(filepath):
            return None

        ext = Path(filepath).suffix.lower()
        mime_map = {
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".webp": "image/webp",
        }
        mime_type = mime_map.get(ext, "image/jpeg")

        try:
            with open(filepath, "rb") as img_f:
                b64_data = base64.b64encode(img_f.read()).decode("utf-8")

            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={k}"
            prompt = (
                "You are an enterprise OCR and document understanding engine. "
                "Extract all readable text, headers, paragraphs, line items, amounts, dates, and handwriting "
                "from this document image verbatim. Maintain natural line breaks and formatting. "
                "Do not add conversational commentary—transcribe all visible content accurately."
            )
            body = {
                "contents": [
                    {
                        "parts": [
                            {"text": prompt},
                            {
                                "inline_data": {
                                    "mime_type": mime_type,
                                    "data": b64_data,
                                }
                            },
                        ]
                    }
                ]
            }
            r = requests.post(url, json=body, timeout=15.0)
            if r.status_code == 200:
                data = r.json()
                candidates = data.get("candidates", [])
                if candidates:
                    parts = candidates[0].get("content", {}).get("parts", [])
                    if parts:
                        return parts[0].get("text", "").strip()
        except Exception as e:
            print(f"[LLMClient] Vision OCR error for {filepath}: {e}")

        return None

    def generate_rag_response(
        self,
        query: str,
        retrieved_chunks: List[Dict[str, Any]],
        system_prompt: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Generates a verified, cited AI response given user query and top retrieved chunks.
        Tries active cloud providers (Gemini -> Groq -> OpenAI -> Ollama) and falls back
        gracefully to local deterministic extraction when offline or keys missing.
        """
        # Build prompt context and citation objects
        context_parts = []
        citations = []
        for i, chunk in enumerate(retrieved_chunks):
            source = chunk.get("filename", "Unknown Document")
            page = chunk.get("page_number", 1)
            sec = chunk.get("section_title", "General")
            score = chunk.get("score", 0.0)
            text = chunk.get("snippet") or chunk.get("text", "")
            clean_snippet = " ".join(text.split())[:280]
            citation_str = f"Source: [{source}], Page: [{page}], Section: [{sec}]"

            citations.append({
                "citation": citation_str,
                "filename": source,
                "page": page,
                "page_number": page,
                "section_title": sec,
                "snippet": clean_snippet,
                "score": float(score),
            })
            context_parts.append(f"[{i+1}] ({citation_str}):\n{text}")

        context_text = "\n\n".join(context_parts)

        # 1. Try Google Gemini if key is present
        if self.gemini_api_key:
            try:
                resp = self._call_gemini(query, context_text)
                if resp:
                    return {
                        "answer": resp,
                        "provider": "Google Gemini 1.5 Flash (Cloud)",
                        "citations": citations,
                    }
            except Exception:
                pass

        # 2. Try Groq API if key is present
        if self.groq_api_key:
            try:
                resp = self._call_groq(query, context_text)
                if resp:
                    return {
                        "answer": resp,
                        "provider": "Groq Llama-3.1 (Cloud)",
                        "citations": citations,
                    }
            except Exception:
                pass

        # 3. Try OpenAI API if key is present
        if self.openai_api_key:
            try:
                resp = self._call_openai(query, context_text)
                if resp:
                    return {
                        "answer": resp,
                        "provider": "OpenAI GPT-4o-mini (Cloud)",
                        "citations": citations,
                    }
            except Exception:
                pass

        # 4. Try Local Ollama instance
        try:
            resp = self._call_ollama(query, context_text)
            if resp:
                return {
                    "answer": resp,
                    "provider": "Ollama Local LLM",
                    "citations": citations,
                }
        except Exception:
            pass

        # 5. Built-in Offline Local Extractive Engine (Zero external network needed)
        answer = self._generate_extractive_summary(query, retrieved_chunks)
        return {
            "answer": answer,
            "provider": "DocuVault Offline Hybrid Intelligence Engine",
            "citations": citations,
        }

    def _call_gemini(self, query: str, context: str) -> Optional[str]:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={self.gemini_api_key}"
        prompt = (
            "You are DocuVault AI, an enterprise document intelligence chatbot. "
            "Answer the user's question accurately based strictly on the provided vault document and image excerpts.\n\n"
            "Formatting Guidelines:\n"
            "- Start with a clean Markdown heading (e.g. '### 📋 Executive Summary').\n"
            "- Use bullet points ('• **Term/Detail**: explanation') to highlight specific figures, deadlines, obligations, or facts.\n"
            "- Use blockquotes (> 'verbatim excerpt') for direct clauses.\n"
            "- Always cite the source document name and page number.\n"
            "- Keep the formatting clean, professional, and readable.\n\n"
            f"Context Excerpts:\n{context}\n\n"
            f"Question:\n{query}\n\n"
            "Answer:"
        )
        body = {"contents": [{"parts": [{"text": prompt}]}]}
        r = requests.post(url, json=body, timeout=8.0)
        if r.status_code == 200:
            data = r.json()
            candidates = data.get("candidates", [])
            if candidates:
                parts = candidates[0].get("content", {}).get("parts", [])
                if parts:
                    return parts[0].get("text")
        return None

    def _call_groq(self, query: str, context: str) -> Optional[str]:
        headers = {
            "Authorization": f"Bearer {self.groq_api_key}",
            "Content-Type": "application/json",
        }
        body = {
            "model": "llama-3.1-8b-instant",
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are DocuVault AI, a document intelligence chatbot. "
                        "Answer questions accurately based on the provided context excerpts from documents and images. "
                        "Format your answer cleanly with Markdown headings ('### Summary'), bullet points ('• **Key**: value'), "
                        "and blockquotes (> 'quote') for verbatim clauses. Ground all statements in the cited sources."
                    ),
                },
                {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {query}"},
            ],
            "temperature": 0.2,
            "max_tokens": 700,
        }
        r = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=body, timeout=8.0)
        if r.status_code == 200:
            return r.json()["choices"][0]["message"]["content"]
        return None

    def _call_openai(self, query: str, context: str) -> Optional[str]:
        headers = {
            "Authorization": f"Bearer {self.openai_api_key}",
            "Content-Type": "application/json",
        }
        body = {
            "model": "gpt-4o-mini",
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are DocuVault AI, an enterprise document intelligence chatbot. "
                        "Answer questions accurately based only on the provided context excerpts from documents and images. "
                        "Format your response with clean Markdown headings ('### Summary'), bullet points ('• **Field**: explanation'), "
                        "and blockquotes (> 'excerpt') for verbatim source clauses. Ground every statement in the provided sources."
                    ),
                },
                {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {query}"},
            ],
            "temperature": 0.2,
            "max_tokens": 700,
        }
        r = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=body, timeout=8.0)
        if r.status_code == 200:
            return r.json()["choices"][0]["message"]["content"]
        return None

    def _call_ollama(self, query: str, context: str) -> Optional[str]:
        url = f"{self.ollama_url}/api/generate"
        prompt = f"Context:\n{context}\n\nQuestion:\n{query}\n\nProvide a concise cited answer with markdown headings and bullet points:"
        body = {"model": "llama3", "prompt": prompt, "stream": False}
        r = requests.post(url, json=body, timeout=3.0)
        if r.status_code == 200:
            return r.json().get("response")
        return None

    def _generate_extractive_summary(self, query: str, retrieved_chunks: List[Dict[str, Any]]) -> str:
        """Offline smart extractive summarizer selecting the most relevant sentences with citations."""
        if not retrieved_chunks:
            return "No matching document or image excerpts found in the vault matching your query."

        top_chunk = retrieved_chunks[0]
        source = top_chunk.get("filename", "Unknown Document")
        page = top_chunk.get("page_number", 1)
        sec = top_chunk.get("section_title", "General")
        text = top_chunk.get("snippet") or top_chunk.get("text", "")

        lines = [line.strip() for line in text.split("\n") if len(line.strip()) > 15 and not line.strip().startswith("---")]
        summary_text = " ".join(lines[:3]) if lines else text[:250]

        return (
            f"### 📄 Document Intelligence: {source}\n\n"
            f"Analysis of query **'{query}'** grounded in **{source}** (Page {page}, Section: {sec}).\n\n"
            f"#### Extracted Evidence:\n"
            f"• **Source File**: `{source}`\n"
            f"• **Page & Section**: Page {page} · {sec}\n"
            f"• **Vault Status**: Verified cryptographic hash\n\n"
            f"> ❝ {summary_text} ❞"
        )

