# 🎥 AlignWorker Demo Video Script (3-Minute Loom Walkthrough)

> **Goal**: In 3 minutes, show the hiring manager:
> 1. Real execution (not simulated).
> 2. Autonomous self-correction.
> 3. Human-In-The-Loop safety.
> 4. Independent outcome verification.

---

## ⏱️ Video Breakdown

### 0:00 - 0:35 | Introduction & Problem Framing
* **What to show**: Screen on VS Code and the project architecture diagram.
* **What to say**:
  > *"Hi everyone, I'm Parth. Here is my submission for the AI Engineering Intern role at CentrAlign AI: **AlignWorker**, an autonomous enterprise task worker. 
  > Instead of building another chatbot that merely suggests steps, I focused on what enterprise AI employees actually need: real computer execution via browser automation, autonomous recovery from unexpected validation errors, human governance on high-value actions, and independent outcome verification."*

---

### 0:35 - 1:30 | Scenario 1: Autonomous Execution & Browser Automation
* **What to show**: Run `python run_demo.py` and select **Option 1 (Standard Clean Invoice)**.
* **Screen action**: The Chromium browser opens automatically, navigates to `http://127.0.0.1:8000/invoices/new`, fills in `#vendor_name`, `#invoice_number`, `#amount`, `#due_date`, clicks submit, and captures a screenshot proof.
* **What to say**:
  > *"Let's run our first scenario. The user gives a natural language objective: 'Find the latest invoice from Acme Corp, extract the amount and due date, enter it into our internal system, and tell me once it is done.'
  > Notice the agent breaks this down: it parses the PDF document, checks the backend database to ensure no duplicate entry exists, spins up Playwright to navigate our internal ERP portal, fills in the fields, and submits.
  > Crucially, it doesn't assume success just because the button was clicked. Our independent OutcomeVerifier queries the SQLite database, validates the amount precision to the cent, confirms the record state is 'ENTERED', and generates a signed audit receipt."*

---

### 1:30 - 2:25 | Scenario 2: Autonomous Self-Correction & Recovery
* **What to show**: Run Option 2 (Apex Logistics with European date format `15/12/2026`).
* **Screen action**: Form submits $\to$ Red error banner appears: *"Validation Error: 'due_date' must be formatted as YYYY-MM-DD"* $\to$ Agent logs: *"Error Detection & Reflection: Reformatted from 15/12/2026 to 2026-12-15"* $\to$ Form re-submits successfully $\to$ Green success banner.
* **What to say**:
  > *"Now for the most important test of reliability: what happens when things go wrong? In this second scenario, our invoice contains an edge case: a European date format '15/12/2026', but our ERP portal strictly requires ISO 8601 'YYYY-MM-DD'.
  > When submitted, the portal throws a 422 validation alert. A naive agent would crash or loop infinitely. AlignWorker's reflection module scrapes the DOM alert, identifies the format mismatch, reformats the date to '2026-12-15', and re-submits within the same session. As you can see, it autonomously recovered and verified the outcome."*

---

### 2:25 - 3:00 | Governance (HITL) & Summary
* **What to show**: Show Scenario 3 (terminal prompting for supervisor approval) or show the Streamlit Dashboard (`streamlit run app/ui/dashboard.py`).
* **What to say**:
  > *"Finally, we implemented enterprise Human-In-The-Loop governance: for any transaction above $5,000, the agent pauses and requests supervisor sign-off.
  > The entire system is built with modular Python, Playwright, FastAPI, and Pydantic, covered by an automated pytest test suite.
  > Thank you for reviewing my project, and I look forward to walking through the architecture in the technical interview!"*
