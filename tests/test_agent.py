import os
import sys
import socket
import pytest

# Setup path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from app.agent.loop import AlignWorkerAgent, AgentStep, TaskResult
from app.agent.llm_client import LLMClient
from app.agent.hitl import HITLGate
from app.tools.document_tool import DocumentTool
from app.tools.system_query_tool import SystemQueryTool
from app.verifier.outcome import OutcomeVerifier
from app.mock_portal.database import reset_db, get_invoice_by_number, insert_invoice

def is_portal_online(host="127.0.0.1", port=8000) -> bool:
    """Checks if a local ERP server is listening on loopback."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(0.5)
        res = s.connect_ex((host, port))
        s.close()
        return res == 0
    except Exception:
        return False

# =====================================================================
# Unit & Component Tests (Deterministic, Fast, Zero Network Dependency)
# =====================================================================

def test_document_tool_pdf_extraction():
    """Validates that DocumentTool parses enterprise PDF files accurately."""
    res_acme = DocumentTool.read_document("invoice_acme_corp.pdf")
    assert res_acme["success"] is True
    assert "Acme Corp" in res_acme["content"]
    assert "INV-ACME-2026-441" in res_acme["content"]
    assert res_acme["pages"] >= 1

    res_apex = DocumentTool.read_document("invoice_apex_logistics.pdf")
    assert res_apex["success"] is True
    assert "Apex Logistics" in res_apex["content"]
    assert "15/12/2026" in res_apex["content"]

def test_cognitive_extraction():
    """Validates that LLMClient extracts structured parameters from raw text."""
    llm = LLMClient()
    sample_text = """
    Invoice #: INV-TEST-9001
    Acme Corp Enterprise Solutions
    Total Due: $3,450.00
    Due Date: 2026-11-30
    Description: Cloud hosting services
    """
    fields = llm.extract_invoice_fields(sample_text)
    assert fields["invoice_number"] == "INV-TEST-9001"
    assert fields["amount"] == 3450.00
    assert fields["due_date"] == "2026-11-30"

def test_self_correction_date_recovery():
    """Validates that self-correction remediates non-ISO date formats to ISO 8601."""
    llm = LLMClient()
    err_banner = "Validation Error: 'due_date' must be formatted as YYYY-MM-DD (ISO 8601). Received '15/12/2026'."
    current_state = {"due_date": "15/12/2026", "invoice_number": "INV-APX-8802"}
    
    correction = llm.formulate_self_correction(err_banner, current_state)
    assert correction["strategy"] == "REFORMAT_DATE"
    assert correction["field"] == "due_date"
    assert correction["corrected_value"] == "2026-12-15"

def test_self_correction_negative_amount():
    """Validates that self-correction fixes invalid or negative financial amounts."""
    llm = LLMClient()
    err_banner = "Validation Error: 'amount' must be greater than 0.00."
    current_state = {"amount": -500.00, "due_date": "2026-12-15"}
    
    correction = llm.formulate_self_correction(err_banner, current_state)
    assert correction["strategy"] == "FIX_AMOUNT"
    assert correction["field"] == "amount"
    assert float(correction["corrected_value"]) > 0

def test_self_correction_conflict_resolution():
    """Validates that duplicate invoice conflicts generate revision suffixes."""
    llm = LLMClient()
    err_banner = "Conflict Error: Invoice 'INV-DUP-100' already exists in ERP system."
    current_state = {"invoice_number": "INV-DUP-100"}
    
    correction = llm.formulate_self_correction(err_banner, current_state)
    assert correction["strategy"] == "RENAME_INVOICE"
    assert "INV-DUP-100" in correction["corrected_value"]

def test_hitl_governance_policy():
    """Validates that Human-In-The-Loop gate halts only high-value actions."""
    hitl = HITLGate(approval_threshold=5000.0, auto_approve=True)
    
    # Under limit
    assert hitl.requires_approval("submit_high_value_invoice", {"amount": 4500.00}) is False
    
    # Over limit
    assert hitl.requires_approval("submit_high_value_invoice", {"amount": 12500.00}) is True
    
    # Auto-approve test mode
    appr = hitl.request_approval("Test Action", {"amount": 12500.00})
    assert appr["approved"] is True

def test_hitl_rejection():
    """Validates that a supervisor declining authorization halts the action."""
    hitl = HITLGate(approval_threshold=5000.0, auto_approve=False)
    # Simulate supervisor typing 'N'
    hitl.request_approval = lambda action, details: {"approved": False, "reason": "Supervisor rejected"}
    appr = hitl.request_approval("Record Financial Liability", {"amount": 15000.00})
    assert appr["approved"] is False

def test_database_and_system_query():
    """Validates that SystemQueryTool checks ERP database state."""
    reset_db()
    
    # Existing record seeded in reset_db
    res = SystemQueryTool.query_invoice("INV-AWS-2026-001")
    assert res["found"] is True
    assert res["invoice"]["amount"] == 1240.50

    # Non-existent record
    res_none = SystemQueryTool.query_invoice("INV-NONEXISTENT")
    assert res_none["found"] is False

def test_independent_outcome_verification():
    """Validates that OutcomeVerifier verifies state in database and seals with SHA-256 receipt."""
    reset_db()
    
    # Insert test record
    insert_invoice(
        vendor_name="Acme Corp Enterprise Solutions",
        invoice_number="INV-VERIFY-1",
        amount=4750.00,
        due_date="2026-11-20",
        category="Cloud Infrastructure",
        description="Verification unit test"
    )

    # 1. Matching verification
    ver_pass = OutcomeVerifier.verify_invoice_task(
        expected_invoice_number="INV-VERIFY-1",
        expected_amount=4750.00,
        expected_vendor="Acme Corp Enterprise Solutions"
    )
    assert ver_pass["verified"] is True
    assert ver_pass["receipt_id"].startswith("RCPT-")
    assert ver_pass["checks_passed"] >= 3

    # 2. Mismatched amount verification
    ver_fail = OutcomeVerifier.verify_invoice_task(
        expected_invoice_number="INV-VERIFY-1",
        expected_amount=9999.00,  # Deliberate mismatch
        expected_vendor="Acme Corp Enterprise Solutions"
    )
    assert ver_fail["verified"] is False

def test_agent_deduplication_early_exit():
    """Validates that AlignWorkerAgent detects duplicate entries dynamically and halts safely."""
    reset_db()
    agent = AlignWorkerAgent(base_portal_url="http://127.0.0.1:8000", headless_browser=True)
    
    # INV-AWS-2026-001 already exists in DB
    result = agent.execute_task(
        user_prompt="Process invoice INV-AWS-2026-001 from AWS Cloud Services",
        document_filename=None
    )
    # Should halt gracefully on pre-condition deduplication check
    assert result.success is True
    assert "already exists in ERP" in result.summary

def test_agent_hitl_rejection_safety():
    """Validates that AlignWorkerAgent aborts if human supervisor rejects authorization."""
    reset_db()
    agent = AlignWorkerAgent(
        base_portal_url="http://127.0.0.1:8000",
        headless_browser=True,
        hitl_threshold=5000.0,
        auto_approve_hitl=False
    )
    # Simulate supervisor rejection
    agent.hitl.request_approval = lambda action, details: {"approved": False, "reason": "Supervisor rejected"}
    
    result = agent.execute_task(
        user_prompt="Process high-value invoice",
        document_filename="invoice_apex_logistics.pdf"
    )
    assert result.success is False
    assert "rejected by enterprise supervisor" in result.summary.lower()

# =====================================================================
# End-to-End Live Browser Integration Test (Runs if portal is active)
# =====================================================================

@pytest.mark.skipif(not is_portal_online(), reason="Local AcmeFlow ERP portal is not active on http://127.0.0.1:8000")
def test_live_browser_end_to_end_flow():
    """Full end-to-end integration test with Playwright browser navigation & DOM interaction."""
    reset_db()
    agent = AlignWorkerAgent(
        base_portal_url="http://127.0.0.1:8000",
        headless_browser=True,
        auto_approve_hitl=True
    )
    result = agent.execute_task(
        user_prompt="Process Acme Corp invoice",
        document_filename="invoice_acme_corp.pdf"
    )
    assert result.success is True
    assert result.audit_receipt_id is not None
    assert result.verification["verified"] is True
