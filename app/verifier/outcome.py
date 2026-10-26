import json
import os
import hashlib
from datetime import datetime
from typing import Dict, Any, List

from app.tools.system_query_tool import SystemQueryTool

class OutcomeVerifier:
    """Independent verification engine that checks post-conditions against enterprise reality."""

    @staticmethod
    def verify_invoice_task(
        expected_invoice_number: str,
        expected_amount: float,
        expected_vendor: str,
        screenshot_path: str = ""
    ) -> Dict[str, Any]:
        """Performs multi-point independent verification."""
        verification_steps: List[Dict[str, Any]] = []
        is_fully_verified = True

        # Check 1: Record existence in backend DB
        db_result = SystemQueryTool.query_invoice(expected_invoice_number)
        if not db_result.get("found"):
            verification_steps.append({
                "check": "Database Record Existence",
                "status": "FAILED",
                "message": f"Record '{expected_invoice_number}' does not exist in database."
            })
            return {
                "verified": False,
                "summary": "Outcome verification failed: Invoice record was not found in ERP database.",
                "checks": verification_steps
            }

        verification_steps.append({
            "check": "Database Record Existence",
            "status": "PASSED",
            "message": f"Found record in database (ID: {db_result['invoice']['id']})."
        })

        rec = db_result["invoice"]

        # Check 2: Amount precision match
        actual_amount = float(rec["amount"])
        if abs(actual_amount - expected_amount) < 0.01:
            verification_steps.append({
                "check": "Financial Amount Consistency",
                "status": "PASSED",
                "expected": expected_amount,
                "actual": actual_amount
            })
        else:
            is_fully_verified = False
            verification_steps.append({
                "check": "Financial Amount Consistency",
                "status": "FAILED",
                "expected": expected_amount,
                "actual": actual_amount,
                "difference": abs(actual_amount - expected_amount)
            })

        # Check 3: State / Workflow status
        if rec["status"] in ["ENTERED", "PENDING_APPROVAL", "APPROVED"]:
            verification_steps.append({
                "check": "ERP Workflow Status",
                "status": "PASSED",
                "current_status": rec["status"]
            })
        else:
            is_fully_verified = False
            verification_steps.append({
                "check": "ERP Workflow Status",
                "status": "FAILED",
                "current_status": rec["status"]
            })

        # Check 4: Evidence artifact check
        has_screenshot = bool(screenshot_path and os.path.exists(screenshot_path))
        verification_steps.append({
            "check": "Visual Audit Proof Captured",
            "status": "PASSED" if has_screenshot else "WARNING",
            "artifact": screenshot_path if has_screenshot else "None provided"
        })

        # Generate cryptographic audit checksum
        payload_str = f"{rec['invoice_number']}|{rec['amount']}|{rec['vendor_name']}|{rec['created_at']}"
        audit_hash = hashlib.sha256(payload_str.encode()).hexdigest()[:16]

        audit_receipt = {
            "verified": is_fully_verified,
            "receipt_id": f"RCPT-{audit_hash.upper()}",
            "verified_at": datetime.utcnow().isoformat() + "Z",
            "target_entity": expected_invoice_number,
            "checks_passed": sum(1 for c in verification_steps if c["status"] == "PASSED"),
            "total_checks": len(verification_steps),
            "checks": verification_steps,
            "system_record": rec,
            "evidence": {
                "screenshot": screenshot_path,
                "audit_hash": audit_hash
            }
        }

        return audit_receipt
