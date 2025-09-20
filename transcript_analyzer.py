from dotenv import load_dotenv
from langchain_groq import ChatGroq
import json
import os
import csv

load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

with open("meet1.txt", "r", encoding="utf-8") as f:
    transcript = f.read()

llm = ChatGroq(
    model="llama-3.1-8b-instant",
    api_key=GROQ_API_KEY
)

def extract_data(transcript):
    prompt = f"""
    You are an AI Project Manager Assistant.
    Extract all tasks discussed in the meeting transcript below.

    For each task, return a JSON array with objects having these keys:
    - id (unique task number, starting from 1001, increment by 1 for each task)
    - giver (who assigned the task)
    - assignee (who will do the task)
    - task (what needs to be done)
    - deadline (if mentioned, else null)
    - deliverable (what should be produced)
    - priority (High / Medium / Low, infer from context)
    - status (choose only from these: "In Progress", "Done").
        Guidelines for status:
        * "In Progress" → if the assignee is expected to start/continue working on it or has a deadline.
        * "Done" → if it is explicitly mentioned as finished or completed.

    Meeting Transcript:
    {transcript}

    Return only valid JSON, no extra text or whitespaces anywhere in your response.
    """
    response = llm.invoke(prompt)
    tasks = json.loads(response.content)

    for i, task in enumerate(tasks, start=1001):
        task["id"] = i
    return tasks


def save_to_csv(tasks, filename="approval.csv"):
    if not tasks:
        print("No tasks discussed in meeting")
        return
    keys = ["id", "giver", "assignee", "task", "deadline", "deliverable", "priority", "status"]
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(tasks)
        print("CSV saved successfully !!")

#tasks = extract_data(transcript)
#save_to_csv(tasks)
