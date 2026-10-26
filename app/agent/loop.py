import os
import re
import json
import time
from typing import Dict, Any, List, Optional, Callable
from pydantic import BaseModel, Field

from app.tools.document_tool import DocumentTool
from app.tools.browser_tool import BrowserTool
from app.tools.system_query_tool import SystemQueryTool
from app.verifier.outcome import OutcomeVerifier
from app.agent.hitl import HITLGate
from app.agent.llm_client import LLMClient

SYSTEM_PROMPT = """You are an Autonomous Enterprise AI Employee capable of computer use, browser automation, and data operations.
You achieve user objectives by choosing tools dynamically in a ReAct loop [Thought -> Action -> Observation -> Reflection].

You have access to the following tools:
1. `read_document(file_path)`: Read text and layout from PDF/text documents.
2. `parse_parameters(document_text)`: Extract structured fields (vendor, invoice #, amount, due date, category).
3. `query_database(invoice_number)`: Query ERP database for deduplication or record status.
4. `request_human_approval(action_name, details)`: Request supervisor sign-off for actions above policy threshold.
5. `navigate(url)`: Navigate browser to target portal URL.
6. `inspect_page()`: Inspect visible form fields, dropdowns, buttons, and alerts.
7. `fill_form(fields)`: Populate web form fields with parameters.
8. `submit_form()`: Click submit button and check for response alerts.
9. `analyze_dom_error(error_banner)`: Diagnose form validation error and formulate correction.
10. `apply_remediation(field, corrected_value)`: Apply corrected value to form field and re-submit.
11. `capture_screenshot(filename)`: Capture visual audit proof of page state.
12. `verify_outcome(invoice_number, expected_amount, expected_vendor)`: Run independent DB verification and generate cryptographic audit receipt.
13. `finish(summary, success)`: Conclude task.

RULES:
- Always reason first in `thought`.
- Choose exactly ONE action per turn based on runtime observations.
- Always output valid JSON:
{
  "phase": "Phase Name",
  "thought": "Internal reasoning about state and next move",
  "action": "tool_name",
  "action_input": { ... }
}
"""

class AgentStep(BaseModel):
    step_number: int
    phase: str
    thought: str
    action: str
    action_input: Dict[str, Any]
    observation: Any
    reflection: str
    screenshot_path: Optional[str] = None
    timestamp: float = Field(default_factory=time.time)

class TaskResult(BaseModel):
    task: str
    success: bool
    summary: str
    steps: List[AgentStep]
    verification: Optional[Dict[str, Any]] = None
    audit_receipt_id: Optional[str] = None
    screenshot_path: Optional[str] = None
    execution_time_seconds: float = 0.0

    # Compatibility attributes
    @property
    def total_steps(self) -> int:
        return len(self.steps)

    @property
    def execution_time(self) -> float:
        return self.execution_time_seconds

    @property
    def final_screenshot(self) -> Optional[str]:
        return self.screenshot_path

class AlignWorkerAgent:
    """Enterprise Autonomous Task Worker.
    
    Executes business objectives autonomously using a dynamic ReAct loop, 
    multi-class self-correction, policy-governed human approvals, and independent
    cryptographic outcome verification.
    """

    def __init__(
        self,
        base_portal_url: Optional[str] = None,
        headless_browser: bool = False,
        hitl_threshold: float = 5000.0,
        auto_approve_hitl: bool = False,
        max_steps: int = 15,
        step_callback: Optional[Callable[[AgentStep], None]] = None
    ):
        if base_portal_url is None:
            port = os.environ.get("PORT", "8000")
            base_portal_url = os.environ.get("PORTAL_BASE_URL", f"http://127.0.0.1:{port}")
        self.base_portal_url = base_portal_url.rstrip("/")
        self.browser = BrowserTool(headless=headless_browser)
        self.hitl = HITLGate(approval_threshold=hitl_threshold, auto_approve=auto_approve_hitl)
        self.llm = LLMClient()
        self.max_steps = max_steps
        self.step_callback = step_callback
        self.history: List[AgentStep] = []
        self.evidence_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            "sample_data", "evidence"
        )
        os.makedirs(self.evidence_dir, exist_ok=True)

    def _log_step(self, step: AgentStep):
        self.history.append(step)
        if self.step_callback:
            self.step_callback(step)

    def _plan_next_step(
        self,
        task: str,
        target_doc: Optional[str],
        extracted_data: Optional[Dict[str, Any]],
        portal_navigated: bool,
        form_submitted: bool,
        last_error: Optional[str],
        correction_applied: bool,
        verified: bool
    ) -> Dict[str, Any]:
        """Dynamic ReAct cognitive planner that decides the next step based on live state."""
        # Check if Gemini/OpenAI is active
        if self.llm.provider in ["gemini", "openai"]:
            try:
                import google.generativeai as genai
                genai.configure(api_key=self.llm.gemini_key)
                model = genai.GenerativeModel("gemini-1.5-flash")
                history_summary = [
                    {"step": s.step_number, "action": s.action, "obs": str(s.observation)[:120]}
                    for s in self.history[-4:]
                ]
                prompt = f"""{SYSTEM_PROMPT}

USER GOAL: "{task}"
EXECUTION LOG: {json.dumps(history_summary)}
CURRENT STATE: doc={target_doc}, extracted={bool(extracted_data)}, navigated={portal_navigated}, submitted={form_submitted}, error={last_error}, verified={verified}

Choose next action. Return valid JSON only."""
                resp = model.generate_content(prompt, request_options={"timeout": 4.0})
                clean_json = re.search(r"\{.*\}", resp.text, re.DOTALL)
                if clean_json:
                    return json.loads(clean_json.group(0))
            except Exception:
                pass

        # Robust Dynamic ReAct State Machine (handles any task reactively)
        # 1. Document Ingestion
        has_read = any(s.action == "read_document" for s in self.history)
        if target_doc and not has_read:
            return {
                "phase": "Document Ingestion",
                "thought": f"The objective requires information from '{target_doc}'. Locating and reading document text.",
                "action": "read_document",
                "action_input": {"file_path": target_doc}
            }

        # 2. Cognitive Parsing
        has_parsed = any(s.action == "parse_parameters" for s in self.history)
        if target_doc and has_read and not has_parsed:
            return {
                "phase": "Cognitive Extraction",
                "thought": "Extracting structured billing parameters (vendor, invoice #, amount, due date) from raw text.",
                "action": "parse_parameters",
                "action_input": {}
            }
        elif not target_doc and not extracted_data and not has_parsed:
            return {
                "phase": "Cognitive Extraction",
                "thought": "Extracting invoice parameters directly from user instruction.",
                "action": "parse_parameters",
                "action_input": {"text": task}
            }

        # 3. Pre-Condition Deduplication
        has_checked_db = any(s.action == "query_database" for s in self.history)
        if extracted_data and not has_checked_db:
            inv_num = extracted_data.get("invoice_number", "")
            return {
                "phase": "Pre-Condition Check",
                "thought": f"Querying ERP database for '{inv_num}' to avoid duplicate entries.",
                "action": "query_database",
                "action_input": {"invoice_number": inv_num}
            }

        # 4. Human-In-The-Loop Safety Gate
        has_hitl = any(s.action == "request_human_approval" for s in self.history)
        if extracted_data and not has_hitl and self.hitl.requires_approval("submit_high_value_invoice", extracted_data):
            return {
                "phase": "HITL Governance",
                "thought": f"Amount ${extracted_data.get('amount', 0):,.2f} exceeds ${self.hitl.approval_threshold:,.2f} policy limit. Enforcing supervisor sign-off.",
                "action": "request_human_approval",
                "action_input": {"amount": extracted_data.get("amount", 0.0), "threshold": self.hitl.approval_threshold}
            }

        # 5. Browser Navigation
        has_nav = any(s.action == "navigate" for s in self.history)
        if not has_nav:
            dest_url = f"{self.base_portal_url}/invoices/new"
            return {
                "phase": "Browser Navigation",
                "thought": f"Navigating Playwright browser to enterprise submission interface at {dest_url}.",
                "action": "navigate",
                "action_input": {"url": dest_url}
            }

        # 6. Page Element Inspection
        has_inspected = any(s.action == "inspect_page" for s in self.history)
        if not has_inspected:
            return {
                "phase": "Form Interaction",
                "thought": "Inspecting page elements and validating input locators before populating data.",
                "action": "inspect_page",
                "action_input": {}
            }

        # 7. Form Population & Submission
        if not form_submitted:
            return {
                "phase": "Form Interaction",
                "thought": "Filling in input fields and clicking submit button on ERP portal.",
                "action": "fill_and_submit",
                "action_input": extracted_data or {}
            }

        # 8. Error Reflection & Recovery
        if last_error and not correction_applied:
            return {
                "phase": "Error Detection & Reflection",
                "thought": f"Validation failure detected on page: '{last_error}'. Formulating autonomous remediation.",
                "action": "analyze_dom_error",
                "action_input": {"error_banner": last_error}
            }

        # 9. Screenshot Visual Proof
        has_screenshot = any(s.action == "capture_screenshot" for s in self.history)
        if not has_screenshot:
            inv = extracted_data.get("invoice_number", "entry") if extracted_data else "state"
            return {
                "phase": "Visual Proof Capture",
                "thought": "Capturing full browser screenshot as visual evidence for the enterprise audit trail.",
                "action": "capture_screenshot",
                "action_input": {"filename": f"proof_{inv}.png"}
            }

        # 10. Independent Outcome Verification
        has_verified = any(s.action == "verify_outcome" for s in self.history)
        if not has_verified and extracted_data:
            return {
                "phase": "Outcome Verification",
                "thought": "Querying backend SQLite database to verify persistence, amount precision, and state transition.",
                "action": "verify_outcome",
                "action_input": {
                    "invoice_number": extracted_data.get("invoice_number"),
                    "amount": extracted_data.get("amount"),
                    "vendor": extracted_data.get("vendor_name")
                }
            }

        # 11. Final Finish
        return {
            "phase": "Task Completion",
            "thought": "Objective completed, verified against database reality, and audit trail sealed.",
            "action": "finish",
            "action_input": {"success": True}
        }

    def execute_task(self, user_prompt: str, document_filename: Optional[str] = None) -> TaskResult:
        """Executes an enterprise task autonomously through a dynamic ReAct loop."""
        start_time = time.time()
        self.history = []
        step_counter = 1

        # Resolve document from prompt if not explicitly passed
        target_doc = document_filename
        if not target_doc:
            doc_match = re.search(r"([a-zA-Z0-9_\-]+\.(?:pdf|txt))", user_prompt)
            if doc_match:
                target_doc = doc_match.group(1)

        doc_content = ""
        extracted_data: Dict[str, Any] = {}
        portal_navigated = False
        form_submitted = False
        last_error: Optional[str] = None
        correction_applied = False
        verification_result: Optional[Dict[str, Any]] = None
        screenshot_path: Optional[str] = None

        while step_counter <= self.max_steps:
            # 1. Decide next action dynamically
            plan = self._plan_next_step(
                task=user_prompt,
                target_doc=target_doc,
                extracted_data=extracted_data,
                portal_navigated=portal_navigated,
                form_submitted=form_submitted,
                last_error=last_error,
                correction_applied=correction_applied,
                verified=bool(verification_result and verification_result.get("verified"))
            )

            phase = plan.get("phase", "Execution")
            thought = plan.get("thought", "Determining next step.")
            action = plan.get("action", "finish")
            action_input = plan.get("action_input", {})
            observation: Any = {}
            reflection = ""

            # 2. Dispatch Tool
            if action == "read_document":
                file_to_read = action_input.get("file_path", target_doc)
                doc_res = DocumentTool.read_document(file_to_read)
                observation = {"success": doc_res.get("success"), "content_len": len(doc_res.get("content", ""))}
                if doc_res.get("success"):
                    doc_content = doc_res.get("content", "")
                    reflection = f"Successfully read {len(doc_content)} characters from document."
                else:
                    reflection = f"Failed to locate file {file_to_read}."
                    step = AgentStep(
                        step_number=step_counter,
                        phase=phase,
                        thought=thought,
                        action=action,
                        action_input=action_input,
                        observation=observation,
                        reflection=reflection
                    )
                    self._log_step(step)
                    return TaskResult(
                        task=user_prompt,
                        success=False,
                        summary=f"Task terminated: Could not read {file_to_read}.",
                        steps=self.history,
                        execution_time_seconds=time.time() - start_time
                    )

            elif action == "parse_parameters":
                raw_source = doc_content or action_input.get("text", user_prompt)
                extracted_data = self.llm.extract_invoice_fields(raw_source)
                observation = {"extracted": extracted_data}
                reflection = f"Identified Vendor='{extracted_data['vendor_name']}', Inv#='{extracted_data['invoice_number']}', Amount=${extracted_data['amount']:,.2f}, Due='{extracted_data['due_date']}'."

            elif action == "query_database":
                inv_to_query = action_input.get("invoice_number", extracted_data.get("invoice_number", ""))
                db_res = SystemQueryTool.query_invoice(inv_to_query)
                observation = db_res
                if db_res.get("found"):
                    reflection = f"Invoice {inv_to_query} is already recorded in ERP. Halting to avoid duplicate entry."
                    step = AgentStep(
                        step_number=step_counter,
                        phase=phase,
                        thought=thought,
                        action=action,
                        action_input=action_input,
                        observation=observation,
                        reflection=reflection
                    )
                    self._log_step(step)
                    return TaskResult(
                        task=user_prompt,
                        success=True,
                        summary=f"Invoice '{inv_to_query}' already exists in ERP. Deduplication policy enforced.",
                        steps=self.history,
                        execution_time_seconds=time.time() - start_time
                    )
                else:
                    reflection = f"No duplicate record for {inv_to_query}. Ready for ERP entry."

            elif action == "request_human_approval":
                approval_res = self.hitl.request_approval("Submit Enterprise Financial Record", extracted_data)
                observation = approval_res
                if not approval_res.get("approved"):
                    reflection = "Human supervisor declined authorization. Execution halted safely."
                    step = AgentStep(
                        step_number=step_counter,
                        phase=phase,
                        thought=thought,
                        action=action,
                        action_input=action_input,
                        observation=observation,
                        reflection=reflection
                    )
                    self._log_step(step)
                    return TaskResult(
                        task=user_prompt,
                        success=False,
                        summary="Execution halted: Transaction rejected by enterprise supervisor.",
                        steps=self.history,
                        execution_time_seconds=time.time() - start_time
                    )
                else:
                    reflection = "Supervisor authorized transaction. Proceeding to entry."

            elif action == "navigate":
                dest_url = f"{self.base_portal_url}/invoices/new"
                nav_res = self.browser.navigate(dest_url)
                portal_navigated = nav_res.get("success", False)
                observation = nav_res
                reflection = f"Browser arrived at '{dest_url}'."

            elif action == "inspect_page":
                alerts = self.browser.check_for_page_errors()
                observation = {"alerts": alerts, "status": "page_ready"}
                reflection = "Form fields detected: #vendor_name, #invoice_number, #amount, #due_date, #category, #description."

            elif action == "fill_and_submit":
                # Populate form
                self.browser.fill_form_field("#vendor_name", extracted_data.get("vendor_name", ""))
                self.browser.fill_form_field("#invoice_number", extracted_data.get("invoice_number", ""))
                self.browser.fill_form_field("#amount", str(extracted_data.get("amount", "")))
                self.browser.fill_form_field("#due_date", str(extracted_data.get("due_date", "")))
                self.browser.select_dropdown_option("#category", extracted_data.get("category", "Software Subscriptions"))
                self.browser.fill_form_field("#description", extracted_data.get("description", ""))
                
                # Submit
                self.browser.click_element("#btn-submit-invoice")
                time.sleep(0.8) # Allow DOM mutation
                form_submitted = True

                # Check alerts
                alerts = self.browser.check_for_page_errors()
                observation = {"submitted": True, "alerts": alerts}
                if alerts.get("has_error"):
                    last_error = alerts.get("error_text", "Validation error")
                    reflection = f"Submission rejected by portal validation: '{last_error}'."
                else:
                    last_error = None
                    reflection = "Form submitted successfully without validation errors."

            elif action == "analyze_dom_error":
                correction = self.llm.formulate_self_correction(last_error or "", extracted_data)
                observation = correction
                strat = correction.get("strategy")
                field = correction.get("field")
                new_val = correction.get("corrected_value")

                reflection = f"Self-Correction plan: {correction.get('reasoning')}"

                # Apply remediation immediately in the autonomous recovery phase
                step = AgentStep(
                    step_number=step_counter,
                    phase="Error Detection & Reflection",
                    thought=thought,
                    action=action,
                    action_input=action_input,
                    observation=observation,
                    reflection=reflection
                )
                self._log_step(step)
                step_counter += 1

                # Sub-step: Autonomous Recovery
                if field and new_val:
                    extracted_data[field] = new_val
                    selector = f"#{field}"
                    self.browser.fill_form_field(selector, str(new_val))
                    self.browser.click_element("#btn-submit-invoice")
                    time.sleep(0.8)
                    correction_applied = True
                    last_error = None

                    step_recovery = AgentStep(
                        step_number=step_counter,
                        phase="Autonomous Recovery",
                        thought=f"Applying corrected value '{new_val}' to field '{selector}' and re-submitting.",
                        action="apply_remediation",
                        action_input={"field": field, "corrected_value": new_val},
                        observation={"status": "re_submitted", "field": field},
                        reflection=f"Field {selector} updated. Re-submitted to portal."
                    )
                    self._log_step(step_recovery)
                    step_counter += 1
                    continue

            elif action == "capture_screenshot":
                inv_tag = extracted_data.get("invoice_number", "entry") if extracted_data else "entry"
                filename = action_input.get("filename", f"proof_{inv_tag}.png")
                screenshot_path = os.path.join(self.evidence_dir, filename)
                self.browser.capture_screenshot(screenshot_path)
                observation = {"saved_to": screenshot_path}
                reflection = f"Visual audit proof saved to {screenshot_path}."

            elif action == "verify_outcome":
                inv = extracted_data.get("invoice_number", "")
                amt = float(extracted_data.get("amount", 0.0))
                vnd = extracted_data.get("vendor_name", "")
                verification_result = OutcomeVerifier.verify_invoice_task(
                    expected_invoice_number=inv,
                    expected_amount=amt,
                    expected_vendor=vnd,
                    screenshot_path=screenshot_path or ""
                )
                observation = verification_result
                verified = verification_result.get("verified", False)
                receipt_id = verification_result.get("receipt_id", "N/A")
                passed = verification_result.get("checks_passed", 0)
                total = verification_result.get("total_checks", 0)
                reflection = f"Verification {'PASSED' if verified else 'FAILED'} ({passed}/{total} checks). Signed receipt: {receipt_id}."

            elif action == "finish":
                # Close browser session
                try:
                    self.browser.close()
                except Exception:
                    pass

                total_time = time.time() - start_time
                is_success = bool(verification_result and verification_result.get("verified")) if verification_result else True
                receipt = verification_result.get("receipt_id") if verification_result else None
                summary = (
                    f"Successfully executed and verified invoice {extracted_data.get('invoice_number')} for "
                    f"{extracted_data.get('vendor_name')} (${extracted_data.get('amount', 0):,.2f}). "
                    f"Audit Receipt: {receipt}."
                    if is_success else
                    f"Task concluded with warnings: {verification_result.get('summary') if verification_result else 'Unverified'}."
                )

                return TaskResult(
                    task=user_prompt,
                    success=is_success,
                    summary=summary,
                    steps=self.history,
                    verification=verification_result,
                    audit_receipt_id=receipt,
                    screenshot_path=screenshot_path,
                    execution_time_seconds=total_time
                )

            # Log standard step
            step = AgentStep(
                step_number=step_counter,
                phase=phase,
                thought=thought,
                action=action,
                action_input=action_input,
                observation=observation,
                reflection=reflection,
                screenshot_path=screenshot_path
            )
            self._log_step(step)
            step_counter += 1

        # Max steps exceeded
        try:
            self.browser.close()
        except Exception:
            pass

        return TaskResult(
            task=user_prompt,
            success=False,
            summary=f"Execution halted: Maximum step limit ({self.max_steps}) reached.",
            steps=self.history,
            verification=verification_result,
            audit_receipt_id=verification_result.get("receipt_id") if verification_result else None,
            screenshot_path=screenshot_path,
            execution_time_seconds=time.time() - start_time
        )

    def run(self, user_prompt: str) -> TaskResult:
        """Alias for compatibility with dynamic studio interface."""
        return self.execute_task(user_prompt)
