import contextvars
import threading
import uuid
import json
from fastapi import FastAPI, Request, BackgroundTasks
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from pathlib import Path

# Application specific imports
from main import run_pipeline
from logger import current_run_id, run_logs

app = FastAPI(title="Startup Evaluator Web")

# Setup templates and static files
BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")

# In-memory store for evaluation states
evaluations = {}

class EvaluationRequest(BaseModel):
    idea: str

def execute_pipeline(idea: str, run_id: str):
    """Run the pipeline inside a copied context so ContextVar is visible to the log handler."""
    def _run():
        # Set the run_id inside this thread's context copy
        current_run_id.set(run_id)
        try:
            state = run_pipeline(idea, run_id=run_id)
            evaluations[run_id] = {
                "status": state.status,
                "report_path": state.report_path,
                "error": state.error
            }
        except Exception as e:
            evaluations[run_id] = {
                "status": "failed",
                "report_path": None,
                "error": str(e)
            }

    # Copy context from the calling thread and run inside it
    ctx = contextvars.copy_context()
    ctx.run(_run)

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")

@app.post("/api/evaluate")
async def evaluate(req: EvaluationRequest, background_tasks: BackgroundTasks):
    run_id = str(uuid.uuid4())[:8]
    evaluations[run_id] = {
        "status": "running",
        "report_path": None,
        "error": None
    }
    
    # Run the pipeline in a separate thread so it doesn't block the event loop
    thread = threading.Thread(target=execute_pipeline, args=(req.idea, run_id))
    thread.start()
    
    return {"run_id": run_id}

@app.get("/api/status/{run_id}")
async def get_status(run_id: str):
    if run_id not in evaluations:
        return JSONResponse(status_code=404, content={"error": "Run not found"})
        
    state = evaluations[run_id]
    logs = run_logs.get(run_id, [])
    
    report_content = None
    if state["status"] == "completed" and state["report_path"]:
        report_path = Path(state["report_path"])
        if report_path.exists():
            with open(report_path, "r", encoding="utf-8") as f:
                report_content = f.read()
                
    return {
        "status": state["status"],
        "error": state["error"],
        "logs": logs,
        "report": report_content
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
