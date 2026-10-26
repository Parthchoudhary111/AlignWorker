from typing import Dict, Any, Optional

class HITLGate:
    """Human-In-The-Loop (HITL) Safety & Approval Gateway.
    
    Ensures that high-risk, irreversible enterprise actions (such as high-value
    financial entries) require explicit human sign-off before execution.
    """

    def __init__(self, approval_threshold: float = 5000.0, auto_approve: bool = False):
        self.approval_threshold = approval_threshold
        self.auto_approve = auto_approve

    def requires_approval(self, action_type: str, details: Dict[str, Any]) -> bool:
        """Determines if the proposed action requires human sign-off."""
        if action_type in ["submit_high_value_invoice", "record_financial_liability"]:
            amount = float(details.get("amount", 0.0))
            if amount >= self.approval_threshold:
                return True
        return False

    def request_approval(self, action_name: str, details: Dict[str, Any]) -> Dict[str, Any]:
        """Prompts for supervisor approval or auto-approves if configured."""
        if self.auto_approve:
            return {
                "approved": True,
                "approver": "Supervisor (Auto-Authorized in Test Mode)",
                "reason": "Passed automated policy threshold."
            }

        amount = details.get("amount", 0.0)
        vendor = details.get("vendor_name", "Unknown")
        inv_num = details.get("invoice_number", "Unknown")

        print("\n" + "="*60)
        print("🚨 HUMAN-IN-THE-LOOP APPROVAL REQUIRED")
        print("="*60)
        print(f"Action:       {action_name}")
        print(f"Vendor:       {vendor}")
        print(f"Invoice #:    {inv_num}")
        print(f"Amount:       ${amount:,.2f} (Exceeds policy threshold of ${self.approval_threshold:,.2f})")
        print("="*60)

        response = input("Authorize this transaction to proceed? [y/N]: ").strip().lower()
        if response in ["y", "yes"]:
            return {
                "approved": True,
                "approver": "Enterprise Human Supervisor",
                "reason": "Authorized via interactive prompt."
            }
        else:
            return {
                "approved": False,
                "approver": "Enterprise Human Supervisor",
                "reason": "Rejected by human supervisor."
            }
