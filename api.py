from fastapi import FastAPI
from pydantic import BaseModel
from typing import List
from transcript_analyzer import extract_data, save_to_csv
from jira_integration import update_jira_from_csv, delete_task_from_jira

app = FastAPI(title="AI Project Manager")

class Transcript(BaseModel):
    transcript: str

class Task(BaseModel):
    giver: str
    assignee: str
    task: str
    deadline: str = ""
    deliverable: str = ""
    priority: str = "Medium"
    status: str = "To Do"

@app.post("/extract-tasks")
def api_extract_tasks(data: Transcript):
    tasks = extract_data(data.transcript)
    return {"tasks": tasks}

@app.post("/save-tasks")
def api_save_tasks(tasks: List[dict]):
    csv_filename = "approval.csv"
    save_to_csv(tasks, filename=csv_filename)
    jira_results = update_jira_from_csv(csv_filename)
    return {
        "status": "success",
        "message": "CSV saved & Jira updated!",
        "jira_results": jira_results
    }

@app.delete("/delete-task/{task_id}")
def api_delete_task(task_id: int):
    result = delete_task_from_jira(task_id)
    return {"status": "success", "message": result}
