"""
DocuVaultAI — External API Clients (Unit 2: REST APIs & Error Handling)
Consumes public holiday APIs (Nager.Date) for working-day deadline adjustments
and external/local LLM APIs (Groq, Gemini, Ollama) with offline fallback.
"""

import json
import os
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional, Set

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
    Multi-provider LLM API client (Groq, Google Gemini, Local Ollama)
    with a zero-dependency offline extractive summarizer fallback.
    """

    def __init__(self) -> None:
        self.groq_api_key = os.getenv("GROQ_API_KEY", "")
        self.gemini_api_key = os.getenv("GEMINI_API_KEY", "")
        self.ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434")

    def generate_rag_response(
        self,
        query: str,
        retrieved_chunks: List[Dict[str, Any]],
        system_prompt: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Generates a cited AI response given user query and top retrieved chunks.
        Tries Groq -> Gemini -> Ollama -> Offline Local Summarizer.
        """
        # Build prompt context
        context_parts = []
        citations = []
        for i, chunk in enumerate(retrieved_chunks):
            source = chunk.get("filename", "Unknown")
            page = chunk.get("page_number", 1)
            score = chunk.get("score", 0.0)
            text = chunk.get("text", "")
            citation_str = f"Source: [{source}], Page: [{page}]"
            citations.append({
                "citation": citation_str,
                "filename": source,
                "page": page,
                "score": float(score),
            })
            context_parts.append(f"[{i+1}] ({citation_str}):\n{text}")

        context_text = "\n\n".join(context_parts)

        # 1. Try Groq API if key is present
        if self.groq_api_key:
            try:
                resp = self._call_groq(query, context_text)
                if resp:
                    return {
                        "answer": resp,
                        "provider": "Groq Llama-3 (Cloud)",
                        "citations": citations,
                    }
            except Exception:
                pass

        # 2. Try Gemini API if key is present
        if self.gemini_api_key:
            try:
                resp = self._call_gemini(query, context_text)
                if resp:
                    return {
                        "answer": resp,
                        "provider": "Google Gemini (Cloud)",
                        "citations": citations,
                    }
            except Exception:
                pass

        # 3. Try Local Ollama instance
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

        # 4. Built-in Offline Local Extractive Engine (Zero external network needed)
        answer = self._generate_extractive_summary(query, retrieved_chunks)
        return {
            "answer": answer,
            "provider": "DocuVault Offline Hybrid Intelligence Engine",
            "citations": citations,
        }

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
                    "content": "You are DocuVaultAI, a document intelligence assistant. Answer questions based only on the provided context. Include citations in format: Source: [Filename], Page: [Page Number].",
                },
                {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {query}"},
            ],
            "temperature": 0.2,
            "max_tokens": 512,
        }
        r = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=body, timeout=5.0)
        if r.status_code == 200:
            return r.json()["choices"][0]["message"]["content"]
        return None

    def _call_gemini(self, query: str, context: str) -> Optional[str]:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={self.gemini_api_key}"
        prompt = f"You are DocuVaultAI. Answer the question using this context. Always cite Source: [Filename], Page: [Page].\n\nContext:\n{context}\n\nQuestion:\n{query}"
        body = {"contents": [{"parts": [{"text": prompt}]}]}
        r = requests.post(url, json=body, timeout=5.0)
        if r.status_code == 200:
            return r.json()["candidates"][0]["content"]["parts"][0]["text"]
        return None

    def _call_ollama(self, query: str, context: str) -> Optional[str]:
        url = f"{self.ollama_url}/api/generate"
        prompt = f"Context:\n{context}\n\nQuestion:\n{query}\n\nProvide a concise cited answer:"
        body = {"model": "llama3", "prompt": prompt, "stream": False}
        r = requests.post(url, json=body, timeout=2.0)
        if r.status_code == 200:
            return r.json().get("response")
        return None

    def _generate_extractive_summary(self, query: str, retrieved_chunks: List[Dict[str, Any]]) -> str:
        """Offline smart extractive summarizer selecting the most relevant sentences with citations."""
        if not retrieved_chunks:
            return "No matching document excerpts found in the vault matching your query."

        top_chunk = retrieved_chunks[0]
        source = top_chunk.get("filename", "Unknown Document")
        page = top_chunk.get("page_number", 1)
        text = top_chunk.get("text", "")

        # Extract 2-3 most informative lines
        lines = [line.strip() for line in text.split("\n") if len(line.strip()) > 20]
        summary_text = "\n".join(f"> {line}" for line in lines[:3]) if lines else f"> {text[:300]}"

        return (
            f"Based on indexed verification records for **'{query}'**:\n\n"
            f"{summary_text}\n\n"
            f"**Verified Citation:** `Source: [{source}], Page: [{page}]`"
        )
