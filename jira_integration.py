import csv
import os
from dotenv import load_dotenv
from jira import JIRA

load_dotenv()

JIRA_EMAIL = os.getenv("JIRA_EMAIL")
JIRA_API_TOKEN = os.getenv("JIRA_API_TOKEN")
JIRA_URL = os.getenv("JIRA_URL")
JIRA_PROJECT_KEY = os.getenv("JIRA_PROJECT_KEY")

priority_map = {"High": "High", "Medium": "Medium", "Low": "Low"}

def update_jira_from_csv(filename):
    jira = JIRA(
        server=JIRA_URL,
        basic_auth=(JIRA_EMAIL, JIRA_API_TOKEN)
    )
    if not os.path.exists(filename):
        return ["CSV file not found"]

    results = []

    with open(filename, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        tasks = [row for row in reader]

    for task in tasks:
        task_id = task["id"]
        summary = f"[{task_id}] {task['task']}"
        description = (
            f"*Task ID:* {task_id}\n"
            f"*Giver:* {task['giver']}\n"
            f"*Assignee (from transcript):* {task['assignee']}\n"
            f"*Deliverable:* {task['deliverable']}\n"
            f"*Deadline:* {task['deadline']}\n"
            f"*Priority:* {task['priority']}\n"
            f"*Status (from transcript):* {task['status']}\n"
        )

        jql = f'project = {JIRA_PROJECT_KEY} AND labels = "taskid_{task_id}"'
        existing_issues = jira.search_issues(jql)

        if existing_issues:
            issue = existing_issues[0]
            issue.update(
                summary=summary,
                description=description,
                priority={"name": priority_map.get(task["priority"], "Medium")},
                fields={"labels": [f"taskid_{task_id}"]}
            )
            results.append(f"♻️ Updated {issue.key} → {summary}")
        else:
            issue_dict = {
                "project": {"key": JIRA_PROJECT_KEY},
                "summary": summary,
                "description": description,
                "issuetype": {"name": "Task"},
                "assignee": {"emailAddress": "manthena.rishit2022@vitstudent.ac.in"},
                "priority": {"name": priority_map.get(task["priority"], "Medium")},
                "labels": [f"taskid_{task_id}"]
            }
            issue = jira.create_issue(fields=issue_dict)
            results.append(f"✅ Created {issue.key} → {summary}")

        desired_status = task["status"].lower()
        transitions = jira.transitions(issue)
        transition_id = None

        for t in transitions:
            if t["name"].lower() == desired_status:
                transition_id = t["id"]
                break

        if transition_id:
            jira.transition_issue(issue, transition_id)
            results.append(f"   ↪ Status moved to {task['status']}")
        else:
            results.append(f"   ⚠️ Could not set status for {issue.key} (maybe already correct)")

    return results

'''x = update_jira_from_csv("approval.csv")
for y in x:
    print(y)'''