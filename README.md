# AlignWorker — Autonomous Enterprise AI Task Worker

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Playwright](https://img.shields.io/badge/browser-Playwright-green.svg)](https://playwright.dev/)
[![FastAPI](https://img.shields.io/badge/framework-FastAPI-teal.svg)](https://fastapi.tiangolo.com/)
[![Render](https://img.shields.io/badge/Render-Live%20Demo-brightgreen.svg)](https://alignworker.onrender.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> **Submission for CentrAlign AI — AI Engineering Intern Role**  
> An autonomous AI employee prototype capable of understanding high-level business goals, executing multi-step browser & document tasks, recovering from unexpected validation errors, enforcing human governance, and independently verifying completion outcomes.
>
> 🌐 **Live Web Demo**: [https://alignworker.onrender.com/](https://alignworker.onrender.com/)  
> ⚡ **Agent Studio**: [https://alignworker.onrender.com/agent](https://alignworker.onrender.com/agent)

---

## 📑 Table of Contents
1. [Core Capabilities & Highlights](#-core-capabilities--highlights)
2. [Architecture Overview](#-architecture-overview)
3. [Quickstart & Demo Walkthrough](#-quickstart--demo-walkthrough)
4. [Key Technical & Design Decisions](#-key-technical--design-decisions)
5. [Evaluation Criteria Mapping](#-evaluation-criteria-mapping)
6. [Known Limitations](#-known-limitations)
7. [What We Would Build Next](#-what-we-would-build-next)
8. [Assumptions Made](#-assumptions-made)
9. [Tech Stack & Dependencies](#-tech-stack--dependencies)

---

## 🌟 Core Capabilities & Highlights

Most agent demos simply run sequential scripts or print simulated actions. **AlignWorker executes real work**:

* 🧠 **Autonomous ReAct Loop**: Decomposes high-level natural language requests into dynamic `[Thought -> Action -> Observation -> Reflection]` sequences.
* 🌐 **Real Browser Execution**: Uses Playwright to navigate a live enterprise ERP portal, handle forms, interact with inputs, and capture state.
* 🔄 **Self-Correction & Error Recovery**: When a submission is rejected by the portal (e.g., malformed European date format `15/12/2026`), the agent inspects the DOM error banner, deduces the root cause, reformats the payload to ISO `2026-12-15`, and retries autonomously.
* 🛡️ **Human-In-The-Loop (HITL) Governance**: Policy-driven guardrails automatically halt the agent and prompt an enterprise supervisor before committing high-risk actions (e.g., transactions $> \$5,000$).
* 🔍 **Independent Outcome Verification**: Post-action verification queries the backend ERP database, confirms matching amounts and status (`ENTERED`), and generates a signed **Audit Receipt** with visual screenshot evidence.
* ⚡ **Model-Agnostic & Zero-Setup Run**: Works seamlessly with Google Gemini API, OpenAI, or an onboard deterministic cognitive engine (allows immediate evaluation without requiring API keys).

---

## 🏗️ Architecture Overview

```
                                  [ User Request ]
                                         │
                                         ▼
                      ┌───────────────────────────────────────┐
                      │           AlignWorker Core            │
                      │   (Dynamic State Machine & ReAct)     │
                      └──────────────────┬────────────────────┘
                                         │
        ┌────────────────────────────────┼────────────────────────────────┐
        ▼                                ▼                                ▼
 ┌───────────────┐               ┌───────────────┐                ┌───────────────┐
 │ DocumentTool  │               │  BrowserTool  │                │SystemQueryTool│
 │  (PDF Parser) │               │  (Playwright) │                │(DB / API State│
 └───────────────┘               └───────┬───────┘                └───────┬───────┘
                                         │                                │
                                         ▼                                ▼
                            ┌────────────────────────┐        ┌───────────────────────┐
                            │    AcmeFlow ERP Portal │◄───────┤    OutcomeVerifier    │
                            │   (FastAPI + SQLite)   │        │ (Independent Checker) │
                            └────────────────────────┘        └───────────┬───────────┘
                                                                          │
                                                                          ▼
                                                                [ Signed Audit Receipt ]
```

### Component Breakdown
* `app/agent/loop.py`: The central ReAct state machine orchestrating tool dispatch, observation analysis, and recovery.
* `app/tools/browser_tool.py`: Playwright controller managing browser lifecycle, form interaction, error banner detection, and screenshot proofing.
* `app/tools/document_tool.py`: Document ingestion tool reading raw PDFs and text invoices.
* `app/verifier/outcome.py`: Independent post-condition checker cross-referencing database reality with the source document.
* `app/agent/hitl.py`: Risk-tiered gatekeeper enforcing human sign-offs on high-value actions.
* `app/mock_portal/`: A self-contained, realistic enterprise ERP portal (`AcmeFlow ERP`) with SQLite persistence and form validation rules.

---

## 🚀 Quickstart & Demo Walkthrough

### 1. Installation
Clone the repository and install dependencies:
```bash
git clone https://github.com/Parthchoudhary111/AlignWorker.git
cd AlignWorker

# Create virtual environment (recommended)
python -m venv venv
venv\Scripts\activate  # On Windows

# Install packages
pip install -r requirements.txt
playwright install chromium
```

### 2. Run the Interactive CLI Demo (Headed Browser)
Launch the demo runner:
```bash
python run_demo.py
```
This automatically starts the local ERP server, opens a **live Chromium browser window** on your desktop, and lets you pick from 3 evaluation scenarios:
1. **Standard Clean Invoice** (Acme Corp `$4,750.00`): Full extraction, browser entry, deduplication check, and audit verification.
2. **Self-Correction & Recovery** (Apex Logistics `$12,450.00` with European date format): Demonstrates error banner detection, cognitive reflection, and autonomous re-submission.
3. **High-Value Transaction (HITL)**: Interactive supervisor approval prompt before financial commitment.

### 3. Run the Autonomous CyberDeck Web Studio
Alternatively, launch the native web console:
```bash
python -m uvicorn app.mock_portal.app:app --port 8000
```
Then navigate to:
* **Neural Agent Studio:** [http://127.0.0.1:8000/agent](http://127.0.0.1:8000/agent) — Natural language prompt dispatch, real-time ReAct trace cards, live optical telemetry (Chromium feed), and preset chips.
* **ERP Accounting Ledger:** [http://127.0.0.1:8000/](http://127.0.0.1:8000/) — Auto-refreshing database view.

### 4. Run the Automated Test Suite
```bash
pytest tests/ -v
```

### 5. Cloud Deployment (Docker, Render, Railway)
AlignWorker includes a production-ready `Dockerfile`, `render.yaml`, and `railway.json` for seamless deployment to cloud platforms with Playwright headless support:
* **Live Hosted Instance on Render:** [https://alignworker.onrender.com/](https://alignworker.onrender.com/) (Agent Studio: [/agent](https://alignworker.onrender.com/agent))
* Full step-by-step instructions in [DEPLOYMENT.md](DEPLOYMENT.md).


---

## 💡 Key Technical & Design Decisions

1. **Lightweight Custom ReAct Loop vs. Heavy Frameworks**:
   * *Decision*: Avoided monolithic frameworks like LangChain/CrewAI in favor of a clean, typed 180-line state machine.
   * *Rationale*: In enterprise production, framework abstractions obscure execution state, complicate custom retry logic, and introduce flaky prompt templates. A custom loop guarantees complete transparency and deterministic error boundaries.

2. **Decoupled Independent Verification Layer**:
   * *Decision*: Verification does not rely on the agent's self-reported success or HTTP status codes.
   * *Rationale*: Real enterprise systems fail silently (e.g. 200 OK returned on validation warnings). `OutcomeVerifier` acts as an external auditor, directly inspecting the SQLite state and verifying field-by-field accuracy.

3. **Deterministic Fallback Cognitive Engine**:
   * *Decision*: Included an intelligent heuristic extraction layer alongside Gemini/OpenAI API integrations.
   * *Rationale*: Evaluators shouldn't have their test experience blocked by missing environment variables or API quota limits.

---

## 🎯 Evaluation Criteria Mapping

| Criterion | How AlignWorker Addresses It |
| :--- | :--- |
| **Autonomy** | Translates a single natural language goal into dynamic step execution without step-by-step handholding. |
| **Execution** | Uses real browser automation (Playwright) typing into inputs and clicking buttons on an active web application. |
| **Reliability** | Catches DOM validation alerts, diagnoses format mismatches, and successfully recovers within the same session. |
| **Verification** | Generates an SHA-256 cryptographic **Audit Receipt** with database checks and visual screenshot proof. |
| **Generalization** | Tool interfaces and the ReAct engine are domain-agnostic; easily adaptable to customer onboarding or vendor registration. |
| **Engineering Quality** | Modular design, strict Pydantic schemas, isolated database layer, and comprehensive pytest coverage. |
| **Product Thinking** | Implements Human-In-The-Loop safety gates for high-value transactions—essential for enterprise adoption. |

---

## ⚠️ Known Limitations
* **Form Structure Adaptability**: Currently tuned for web forms with standard DOM inputs; heavily obfuscated canvas-based interfaces would require coordinate-based vision models.
* **Synchronous Execution**: Currently runs synchronously; enterprise production would benefit from an asynchronous message queue (e.g., Celery / Temporal).
* **Multi-Tab Orchestration**: Browser tool manages a single active tab per workflow.

---

## 🔮 What We Would Build Next
1. **Multi-Modal Vision Inspection**: Incorporate vision-based screen understanding (e.g., Gemini 1.5 Flash Vision) for interacting with legacy remote desktops / Citrix interfaces.
2. **Dynamic Workflow Learning**: Allow the agent to record a human demonstration once, compile it into an executable policy graph, and execute it thereafter.
3. **Enterprise RBAC & Auth**: Integration with Okta / SSO for scoped worker permissions and token rotation.
4. **Distributed Execution Cluster**: Containerized browser nodes running on Kubernetes with session replay videos for compliance audits.

---

## 📌 Assumptions Made
* The enterprise portal operates over HTTP/HTTPS with recognizable DOM input elements.
* Dates should follow ISO 8601 (`YYYY-MM-DD`) standards for database persistence.
* Financial transactions above `$5,000.00` require enterprise human supervisor authorization.

---

## 🛠️ Tech Stack & Dependencies
* **Core Language**: Python 3.11+
* **Browser Automation**: Playwright (Chromium)
* **Enterprise Mock Service**: FastAPI, Uvicorn, Jinja2, SQLite
* **Document Processing**: PyPDF, ReportLab
* **Type Validation & Schemas**: Pydantic v2
* **UI & Observability**: Streamlit, Rich Console
* **Test Suite**: Pytest
