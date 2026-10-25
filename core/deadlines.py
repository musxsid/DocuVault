"""
DocuVault — Smart Deadline & Compliance Reminders Engine
Calculates upcoming and overdue statutory/contractual obligations,
applies working-day and holiday adjustments, and exports to CSV / iCalendar (.ics).
"""

import csv
import io
from datetime import date, datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
from backend.api_client import PublicHolidayClient


class DeadlineManager:
    """
    Manages statutory, contractual, and financial deadlines.
    Applies configurable holiday adjustments, tracks reminder intervals (7d, 3d, 1d),
    and exports formatted calendars.
    """

    def __init__(self, holiday_client: Optional[PublicHolidayClient] = None):
        self.holiday_client = holiday_client or PublicHolidayClient()
        self.adjust_holidays = True

    def evaluate_deadline(self, deadline: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluates a deadline record against the current date:
        - Calculates days remaining or overdue.
        - Checks if holiday adjustment should move the deadline.
        - Determines reminder notifications (7d, 3d, 1d).
        """
        result = dict(deadline)
        due_str = deadline.get("due_date", "")

        try:
            due_date = date.fromisoformat(due_str[:10])
        except Exception:
            due_date = date.today()

        today = date.today()

        # Check holiday & weekend adjustment
        adjusted_date = due_date
        was_adjusted = False
        shift_note = ""
        if self.adjust_holidays and self.holiday_client:
            try:
                adj = self.holiday_client.calculate_working_deadline(due_date)
                adjusted_date = date.fromisoformat(adj["working_deadline"])
                was_adjusted = adj.get("was_shifted", False)
                shift_note = adj.get("shift_reason", "")
            except Exception:
                pass

        days_left = (adjusted_date - today).days

        # Status categorization
        if days_left < 0:
            status = "Overdue"
            urgency = "Critical"
        elif days_left == 0:
            status = "Due Today"
            urgency = "Urgent"
        elif days_left <= 3:
            status = "Urgent (≤3 days)"
            urgency = "Urgent"
        elif days_left <= 7:
            status = "Upcoming (≤7 days)"
            urgency = "Medium"
        else:
            status = "On Track"
            urgency = "Normal"

        # Reminders trigger
        triggered_reminders = []
        for interval in [7, 3, 1]:
            if days_left == interval:
                triggered_reminders.append(f"{interval}-day reminder triggered")

        result["days_left"] = days_left
        result["computed_status"] = status
        result["urgency"] = urgency
        result["adjusted_due_date"] = adjusted_date.isoformat()
        result["was_holiday_adjusted"] = was_adjusted
        result["holiday_note"] = shift_note
        result["triggered_reminders"] = triggered_reminders

        return result

    @classmethod
    def export_csv(cls, deadlines: List[Dict[str, Any]]) -> str:
        """Exports deadlines list to CSV string."""
        output = io.StringIO()
        fieldnames = ["id", "title", "document", "category", "due_date", "priority", "status", "days_left", "notes"]
        writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for d in deadlines:
            writer.writerow(d)
        return output.getvalue()

    @classmethod
    def export_icalendar(cls, deadlines: List[Dict[str, Any]]) -> str:
        """Exports deadlines list to RFC 5545 iCalendar (.ics) string."""
        now_stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        lines = [
            "BEGIN:VCALENDAR",
            "VERSION:2.0",
            "PRODID:-//DocuVault AI//Document Deadlines//EN",
            "CALSCALE:GREGORIAN",
            "METHOD:PUBLISH",
        ]

        for d in deadlines:
            due_str = d.get("due_date", "")[:10].replace("-", "")
            d_id = d.get("id", "DL")
            title = d.get("title", "Document Deadline").replace("\n", " ")
            doc = d.get("document", "Document")
            notes = d.get("notes", "").replace("\n", " ")

            lines.extend([
                "BEGIN:VEVENT",
                f"UID:docuvault-{d_id}-{now_stamp}@docuvault.internal",
                f"DTSTAMP:{now_stamp}",
                f"DTSTART;VALUE=DATE:{due_str}",
                f"SUMMARY:{title}",
                f"DESCRIPTION:DocuVault Obligation: {title}\\nDocument: {doc}\\nNotes: {notes}",
                f"STATUS:CONFIRMED",
                f"PRIORITY:1" if d.get("priority") == "High" else "PRIORITY:5",
                "END:VEVENT",
            ])

        lines.append("END:VCALENDAR")
        return "\r\n".join(lines)
