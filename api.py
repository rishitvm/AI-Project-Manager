from fastapi import FastAPI, Request
from pydantic import BaseModel
from typing import List
from datetime import datetime
from multi_agent_wrapper import build_multi_agent_graph
from transcript_analyzer import (
    extract_metadata_from_transcript,
    extract_tasks_from_transcript,
    save_tasks_to_csv
)
from jira_integration import (
    update_jira_from_csv,
    delete_task_from_jira,
    fetch_task_from_jira
)
from memory_manager import load_memory, save_memory
from chatbot import query_llm

app = FastAPI(title="AI Project Manager")

class Task(BaseModel):
    id: int
    giver: str
    assignee: str
    task: str
    deadline: str = ""
    deliverable: str = ""
    priority: str = "Medium"
    status: str = "In Progress"

class ProjectInfoUpdate(BaseModel):
    description: str
    start_date: str
    expected_end_date: str

class NotesUpdate(BaseModel):
    notes: List[str]

class QuestionRequest(BaseModel):
    question: str

@app.post("/extract-tasks")
async def api_extract_tasks(request: Request):
    body = await request.json()
    transcript = body.get("transcript", "").strip()
    if not transcript:
        return {"status": "error", "message": "Transcript is empty."}

    memory, metadata_updates = extract_metadata_from_transcript(transcript)
    tasks = extract_tasks_from_transcript(transcript)
    save_tasks_to_csv(tasks)

    return {
        "status": "success",
        "metadata_updates": metadata_updates,
        "tasks": tasks
    }

@app.post("/add-task")
async def api_add_task(request: Request):
    task = await request.json()
    memory = load_memory()

    if "tasks" not in memory:
        memory["tasks"] = []

    # Avoid duplicate IDs
    if any(t["id"] == task["id"] for t in memory["tasks"]):
        return {"status": "error", "message": f"Task with ID {task['id']} already exists."}

    memory["tasks"].append(task)
    memory["metadata"]["updated_at"] = datetime.utcnow().isoformat()
    save_memory(memory)

    return {"status": "success", "message": "Task added to memory successfully."}

@app.post("/update-task")
async def api_update_task(request: Request):
    updated_task = await request.json()
    memory = load_memory()

    updated = False
    for t in memory.get("tasks", []):
        if t["id"] == updated_task["id"]:
            t.update(updated_task)
            updated = True
            break

    if not updated:
        return {"status": "error", "message": f"No task found with ID {updated_task['id']}"}

    memory["metadata"]["updated_at"] = datetime.utcnow().isoformat()
    save_memory(memory)

    return {"status": "success", "message": "Task updated in memory successfully."}


@app.post("/save-tasks")
async def api_save_tasks(request: Request):
    data = await request.json()
    tasks = data if isinstance(data, list) else data.get("tasks", [])
    csv_filename = "approval.csv"
    save_tasks_to_csv(tasks, filename=csv_filename)

    jira_results = update_jira_from_csv(csv_filename)

    memory = load_memory()
    if "tasks" not in memory:
        memory["tasks"] = []

    existing_ids = {t["id"] for t in memory["tasks"]}
    for task in tasks:
        if task["id"] not in existing_ids:
            memory["tasks"].append(task)
        else:
            for mt in memory["tasks"]:
                if mt["id"] == task["id"]:
                    mt.update(task)

    memory["metadata"]["updated_at"] = datetime.utcnow().isoformat()
    save_memory(memory)

    return {
        "status": "success",
        "message": "Jira and memory both updated successfully!",
        "jira_results": jira_results
    }

@app.delete("/delete-task/{task_id}")
def api_delete_task(task_id: int):
    # Delete from Jira
    result = delete_task_from_jira(task_id)

    memory = load_memory()
    tasks_before = len(memory.get("tasks", []))
    memory["tasks"] = [t for t in memory.get("tasks", []) if t["id"] != task_id]
    tasks_after = len(memory["tasks"])

    if tasks_before != tasks_after:
        memory["metadata"]["updated_at"] = datetime.utcnow().isoformat()
        save_memory(memory)

    return {
        "status": "success",
        "message": f"{result}. Memory synced successfully.",
        "memory_deleted": tasks_before - tasks_after
    }

@app.get("/get-task/{task_id}")
def api_get_task(task_id: int):
    task = fetch_task_from_jira(task_id)
    if task:
        return {"status": "success", "task": task}
    else:
        return {"status": "error", "message": f"No task found with ID {task_id}"}
    
@app.get("/get-project-name")
def get_project_name():
    memory = load_memory()
    project_name = memory.get("project_name", "Unnamed Project")
    return {"project_name": project_name}

@app.post("/update-project-name")
def update_project_name(payload: dict):
    new_name = payload.get("project_name")
    if not new_name:
        return {"status": "error", "message": "Project name cannot be empty."}

    memory = load_memory()
    memory["project_name"] = new_name
    save_memory(memory)
    return {"status": "success", "message": f"Project name updated to '{new_name}'"}

@app.get("/get-project-details")
def get_project_details():
    """
    Fetch detailed project information from memory including:
    description, start_date, expected_end_date, and notes.
    """
    memory = load_memory()
    project_info = memory.get("project_info",{})
    if not project_info:
        return {"status": "error", "message": "No project information found."}
    return {
        "status": "success",
        "project_info": project_info
    }

@app.post("/update-project-info")
def update_project_info(info: ProjectInfoUpdate):
    memory = load_memory()
    if "project_info" not in memory:
        memory["project_info"] = {}

    memory["project_info"]["description"] = info.description
    memory["project_info"]["start_date"] = info.start_date
    memory["project_info"]["expected_end_date"] = info.expected_end_date
    memory["project_info"]["updated_at"] = datetime.utcnow().isoformat()

    save_memory(memory)
    return {"status": "success", "message": "Project information updated successfully."}

@app.post("/update-project-notes")
def update_project_notes(notes_update: NotesUpdate):
    memory = load_memory()
    if "project_info" not in memory:
        memory["project_info"] = {}

    memory["project_info"]["notes"] = notes_update.notes
    memory["project_info"]["updated_at"] = datetime.utcnow().isoformat()

    save_memory(memory)
    return {"status": "success", "message": "Notes updated successfully."}

@app.get("/get-project-details")
def get_project_details():
    memory = load_memory()
    project_info = memory.get("project_info", {})
    return {"status": "success", "project_info": project_info}

@app.get("/get-task-analysis")
def get_task_analysis():
    memory = load_memory()
    return {"tasks": memory["tasks"], "metadata": memory["metadata"]}

@app.post("/ask-question")
async def ask_question(req: QuestionRequest):
    memory = load_memory()
    response = query_llm(memory, req.question)
    return {"answer": response}

"""@app.post("/run-multi-agent")
async def run_multi_agent(request: Request):
    data = await request.json()
    transcript = data.get("transcript")
    graph = build_multi_agent_graph()
    result = graph.invoke({"transcript": transcript})
    return result"""
