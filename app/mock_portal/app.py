import re
import os
import asyncio
from fastapi import FastAPI, Request, Form, status
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

from .database import list_invoices, get_invoice_by_number, insert_invoice, reset_db

app = FastAPI(title="AcmeFlow ERP Portal", version="1.0.0")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(BASE_DIR))
EVIDENCE_DIR = os.path.join(PROJECT_ROOT, "sample_data", "evidence")
os.makedirs(EVIDENCE_DIR, exist_ok=True)

templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))
app.mount("/static/evidence", StaticFiles(directory=EVIDENCE_DIR), name="evidence")

# Initialize DB on start
reset_db()

@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    invoices = list_invoices()
    return templates.TemplateResponse(request=request, name="index.html", context={"invoices": invoices})

@app.get("/agent", response_class=HTMLResponse)
async def agent_studio(request: Request):
    return templates.TemplateResponse(request=request, name="agent_studio.html", context={})

@app.get("/invoices", response_class=HTMLResponse)
async def view_invoices(request: Request):
    invoices = list_invoices()
    return templates.TemplateResponse(request=request, name="index.html", context={"invoices": invoices})

@app.get("/invoices/new", response_class=HTMLResponse)
@app.get("/invoices/new,", response_class=HTMLResponse)
@app.get("/invoices/new/", response_class=HTMLResponse)
async def new_invoice_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="new_invoice.html",
        context={
            "error_message": None,
            "success_message": None,
            "form_data": {}
        }
    )

@app.post("/invoices/new", response_class=HTMLResponse)
@app.post("/invoices/new,", response_class=HTMLResponse)
@app.post("/invoices/new/", response_class=HTMLResponse)
async def handle_new_invoice(
    request: Request,
    vendor_name: str = Form(...),
    invoice_number: str = Form(...),
    amount: float = Form(...),
    due_date: str = Form(...),
    category: str = Form(...),
    description: str = Form("")
):
    form_data = {
        "vendor_name": vendor_name,
        "invoice_number": invoice_number,
        "amount": amount,
        "due_date": due_date,
        "category": category,
        "description": description
    }

    # Strict Validation Rule 1: Date must be YYYY-MM-DD
    if not re.match(r"^\d{4}-\d{2}-\d{2}$", due_date.strip()):
        return templates.TemplateResponse(
            request=request,
            name="new_invoice.html",
            context={
                "error_message": f"Validation Error: 'due_date' must be formatted as YYYY-MM-DD (ISO 8601). Received '{due_date}'.",
                "success_message": None,
                "form_data": form_data
            },
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY
        )

    # Strict Validation Rule 2: Positive amount
    if amount <= 0:
        return templates.TemplateResponse(
            request=request,
            name="new_invoice.html",
            context={
                "error_message": "Validation Error: 'amount' must be greater than 0.00.",
                "success_message": None,
                "form_data": form_data
            },
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY
        )

    # Check for duplicate invoice number
    existing = get_invoice_by_number(invoice_number.strip())
    if existing:
        return templates.TemplateResponse(
            request=request,
            name="new_invoice.html",
            context={
                "error_message": f"Conflict Error: Invoice '{invoice_number}' already exists in ERP system.",
                "success_message": None,
                "form_data": form_data
            },
            status_code=status.HTTP_409_CONFLICT
        )

    # Insert record into database
    insert_invoice(
        vendor_name=vendor_name.strip(),
        invoice_number=invoice_number.strip(),
        amount=amount,
        due_date=due_date.strip(),
        category=category.strip(),
        description=description.strip()
    )

    return templates.TemplateResponse(
        request=request,
        name="new_invoice.html",
        context={
            "error_message": None,
            "success_message": f"Invoice {invoice_number} successfully registered in ERP! Record state is 'ENTERED'.",
            "form_data": {}
        }
    )

# --- REST APIs for Programmatic & Verification Use ---

@app.get("/api/invoices")
async def api_list_invoices():
    return {"invoices": list_invoices()}

@app.get("/api/invoices/{invoice_number}")
async def api_get_invoice(invoice_number: str):
    inv = get_invoice_by_number(invoice_number)
    if not inv:
        return JSONResponse(status_code=404, content={"error": "Invoice not found"})
    return {"invoice": inv}

@app.post("/api/reset")
async def api_reset_db():
    reset_db()
    return {"status": "ok", "message": "Database reset to initial state"}

@app.post("/api/agent/run")
async def api_run_agent(payload: dict):
    import importlib
    import app.agent.llm_client
    import app.agent.loop
    import app.agent.dynamic_agent
    importlib.reload(app.agent.llm_client)
    importlib.reload(app.agent.loop)
    importlib.reload(app.agent.dynamic_agent)
    from app.agent.dynamic_agent import DynamicAlignWorker

    prompt = payload.get("prompt", "").strip()
    
    # Run the worker in a thread to keep the async event loop responsive
    def run_worker():
        agent = DynamicAlignWorker(headless=True, max_steps=12)
        try:
            return agent.run(prompt)
        finally:
            try:
                agent.browser.close()
            except Exception:
                pass

    result = await asyncio.to_thread(run_worker)
    
    steps_data = [
        {
            "step_number": s.step_number,
            "thought": s.thought,
            "action": s.action,
            "action_input": s.action_input,
            "observation": s.observation
        }
        for s in result.steps
    ]
    screenshot_url = "/static/evidence/final_state.png" if os.path.exists(os.path.join(EVIDENCE_DIR, "final_state.png")) else None
    
    return {
        "success": result.success,
        "summary": result.summary,
        "total_steps": result.total_steps,
        "execution_time": result.execution_time,
        "steps": steps_data,
        "screenshot_url": screenshot_url
    }
