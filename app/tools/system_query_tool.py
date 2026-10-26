from typing import Dict, Any, Optional
from app.mock_portal.database import get_invoice_by_number, list_invoices

class SystemQueryTool:
    """Tool for querying the internal ERP database state directly."""

    @staticmethod
    def query_invoice(invoice_number: str) -> Dict[str, Any]:
        """Queries the ERP database for an invoice by its invoice number."""
        try:
            record = get_invoice_by_number(invoice_number.strip())
            if record:
                return {
                    "found": True,
                    "invoice": record
                }
            return {
                "found": False,
                "message": f"No invoice record found with number '{invoice_number}'."
            }
        except Exception as e:
            return {"found": False, "error": f"Database query failed: {str(e)}"}

    @staticmethod
    def get_system_summary() -> Dict[str, Any]:
        """Returns high-level statistics and recent entries from ERP."""
        try:
            invoices = list_invoices()
            return {
                "total_invoices": len(invoices),
                "recent_invoices": invoices[:5]
            }
        except Exception as e:
            return {"error": f"Failed to retrieve summary: {str(e)}"}
