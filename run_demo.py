import os
import sys
import time
import threading

# Ensure UTF-8 output encoding on Windows consoles
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

import uvicorn
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from app.agent.loop import AlignWorkerAgent, AgentStep
from app.mock_portal.database import reset_db

console = Console()

def start_mock_server():
    """Runs the mock portal FastAPI server in a background daemon thread."""
    from app.mock_portal.app import app
    config = uvicorn.Config(app, host="127.0.0.1", port=8000, log_level="warning")
    server = uvicorn.Server(config)
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    time.sleep(1.5) # Allow server to bind

def print_step_callback(step: AgentStep):
    """Real-time formatted streaming output for each agent decision."""
    phase_colors = {
        "Document Ingestion": "cyan",
        "Cognitive Extraction": "magenta",
        "Pre-Condition Check": "blue",
        "HITL Governance": "yellow",
        "Browser Navigation": "green",
        "Form Interaction": "green",
        "Error Detection & Reflection": "bright_red",
        "Autonomous Recovery": "bright_cyan",
        "Visual Proof Capture": "cyan",
        "Outcome Verification": "bold white on green",
        "Task Completion": "bold green"
    }
    color = phase_colors.get(step.phase, "white")
    
    console.print(f"\n[bold {color}]▶ [Step {step.step_number}] {step.phase}[/bold {color}]")
    console.print(f"  [bold]Thought:[/bold] {step.thought}")
    console.print(f"  [bold]Action:[/bold] [italic]{step.action}[/italic]({step.action_input})")
    
    # Trim observation if too verbose
    obs_summary = str(step.observation)
    if len(obs_summary) > 160:
        obs_summary = obs_summary[:160] + "..."
    console.print(f"  [bold]Observation:[/bold] {obs_summary}")
    console.print(f"  [bold]Reflection:[/bold] [dim]{step.reflection}[/dim]")

def main():
    console.clear()
    banner = """
    ╔═══════════════════════════════════════════════════════════════╗
    ║                     AlignWorker Engine                        ║
    ║        Autonomous Enterprise Task Worker & ReAct Agent        ║
    ╚═══════════════════════════════════════════════════════════════╝
    """
    console.print(Panel(banner, style="bold cyan", border_style="cyan"))

    console.print("[dim]1. Starting background AcmeFlow ERP server at http://127.0.0.1:8000...[/dim]")
    start_mock_server()
    reset_db()
    console.print("[bold green]✓ ERP Server active & initialized.[/bold green]\n")

    table = Table(title="Select Evaluation Scenario", show_header=True, header_style="bold magenta")
    table.add_column("Option", style="cyan", width=8)
    table.add_column("Scenario Name", style="bold white", width=32)
    table.add_column("Key Capabilities Evaluated", style="dim")
    table.add_row("1", "Standard Clean Invoice", "Document parsing, Browser automation, Deduplication, Verification")
    table.add_row("2", "Edge-Case Self-Correction", "Non-standard date, Portal rejection, Error reflection, Auto-recovery")
    table.add_row("3", "High-Value Transaction (HITL)", "Amount > $5k, Policy trigger, Human-in-the-loop supervisor approval")
    console.print(table)

    choice = input("\nEnter scenario (1, 2, or 3) [default: 1]: ").strip() or "1"

    if choice == "1":
        task_prompt = "Find the latest invoice from Acme Corp, extract the amount and due date, enter it into our internal system, and tell me once it is done."
        doc_file = "invoice_acme_corp.pdf"
        auto_approve = True
    elif choice == "2":
        task_prompt = "Process the pending invoice from Apex Logistics, submit it through the ERP form, handle any validation errors, and verify completion."
        doc_file = "invoice_apex_logistics.pdf"
        auto_approve = True
    else:
        task_prompt = "Process high-value advisory invoice from Apex Logistics with supervisor authorization."
        doc_file = "invoice_apex_logistics.pdf"
        auto_approve = False # Will trigger live interactive prompt!

    console.print(f"\n[bold yellow]Target Task:[/bold yellow] {task_prompt}")
    console.print(f"[bold yellow]Source File:[/bold yellow] sample_data/{doc_file}\n")
    console.print("[dim]Launching autonomous execution loop... (Headed Chromium browser will open)[/dim]")

    # Run agent
    agent = AlignWorkerAgent(
        base_portal_url="http://127.0.0.1:8000",
        headless_browser=False, # Opens real Chromium so reviewer can see it work!
        hitl_threshold=5000.0,
        auto_approve_hitl=auto_approve,
        step_callback=print_step_callback
    )

    result = agent.execute_task(user_prompt=task_prompt, document_filename=doc_file)

    # Print Result Summary Panel
    console.print("\n")
    if result.success:
        ver_checks = result.verification.get("checks", []) if result.verification else []
        summary_text = (
            f"[bold green]✔ TASK COMPLETED & VERIFIED[/bold green]\n\n"
            f"[bold]Summary:[/bold] {result.summary}\n"
            f"[bold]Audit Receipt ID:[/bold] {result.audit_receipt_id}\n"
            f"[bold]Checks Passed:[/bold] {result.verification.get('checks_passed')}/{result.verification.get('total_checks')}\n"
            f"[bold]Total Execution Time:[/bold] {result.execution_time_seconds:.2f} seconds\n"
            f"[bold]Visual Proof:[/bold] {result.screenshot_path}"
        )
        console.print(Panel(summary_text, title="Execution & Audit Report", border_style="green"))
    else:
        console.print(Panel(f"[bold red]✘ TASK FAILED / HALTED[/bold red]\n\n{result.summary}", border_style="red"))

if __name__ == "__main__":
    main()
