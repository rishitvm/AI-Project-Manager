from dotenv import load_dotenv
from langchain_groq import ChatGroq
import json
import csv
import os
from memory_manager import load_memory, save_memory

load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

llm = ChatGroq(
    model="llama-3.1-8b-instant",
    api_key=GROQ_API_KEY
)

def merge_memory_with_transcript(transcript):
    memory = load_memory()
    context_text = ""

    if memory.get("project_name") or memory.get("project_info", {}).get("description"):
        context_text += "Project Info:\n"
        context_text += f"Title: {memory.get('project_name','')}\n"
        context_text += f"Description: {memory.get('project_info',{}).get('description','')}\n\n"

    if memory.get("tasks"):
        context_text += "Existing tasks:\n"
        for t in memory["tasks"]:
            context_text += f"{t.get('id','')} - {t.get('task','')} (Giver: {t.get('giver','')}, Assignee: {t.get('assignee','')}, Deadline: {t.get('deadline','')}, Priority: {t.get('priority','')}, Status: {t.get('status','')}, Deliverable: {t.get('deliverable','')})\n"

    if memory.get("team"):
        context_text += "Team members:\n"
        for member in memory["team"]:
            context_text += f"- {member}\n"

    context_text += "\nCurrent Meeting Transcript:\n" + transcript
    return memory, context_text


def extract_metadata_from_transcript(transcript):
    memory, _ = merge_memory_with_transcript(transcript)
    prompt = f"""
            You are an AI Project Manager Assistant.
            From the transcript below, extract updates for:
            - Project title (only if explicitly mentioned)
            - Project description (frame based on discussed tasks)
            - Team members (use full names exactly as in past memory; do not add duplicates; get new members if they are not in the memory)
            - Context notes (any other info not related to tasks)

            Important rules:
            1. Always use full names as they appear in existing memory. Do NOT create shortened or partial names.
            2. Only add new members to 'team_add' if they are not already in memory.
            3. Only remove members if explicitly mentioned.
            4. Ensure task assignments match the correct person from memory context if multiple people share first names.
            5. Use only the **full names** from the existing team members list: {memory.get("team")}
            6. If a first name appears that matches multiple team members, infer the correct one by **comparing the new task with their past similar tasks** (task domain similarity).
            7. Detect any new team member introductions or role updates

            Return JSON in this exact format:
            {{
                "project_name": "...",
                "project_info": {{
                    "description": "...",
                    "notes": ["..."]
                }},
                "team_add": ["..."],
                "team_remove": ["..."]
            }}

            Transcript:
            {transcript}

            Existing Team Members: {memory.get("team")}

            Please give ONLY the JSON, properly formatted, no extra spaces or characters.
            """

    response = llm.invoke(prompt)
    metadata_updates = json.loads(response.content)

    if metadata_updates.get("project_name"):
        memory["project_name"] = metadata_updates["project_name"]

    if metadata_updates.get("project_info", {}).get("description"):
        memory["project_info"]["description"] = metadata_updates["project_info"]["description"]

    if metadata_updates.get("project_info", {}).get("notes"):
        memory["project_info"]["notes"].extend(metadata_updates["project_info"]["notes"])

    if metadata_updates.get("team_add"):
        for member in metadata_updates["team_add"]:
            if member not in memory["team"]:
                memory["team"].append(member)

    if metadata_updates.get("team_remove"):
        memory["team"] = [m for m in memory["team"] if m not in metadata_updates["team_remove"]]

    memory["metadata"]["meeting_count"] += 1
    save_memory(memory)
    return memory, metadata_updates


def extract_tasks_from_transcript(transcript):
    memory, prompt_text = merge_memory_with_transcript(transcript)

    prompt = f"""
        You are an AI Project Manager Assistant.
        Extract all tasks discussed in the meeting transcript below.

        For each task, return a JSON array with objects having these keys:
        - id (unique task number, starting from 1001, increment by 1 for each task)
        - giver (who assigned the task; always use full names from existing memory)
        - assignee (who will do the task; always use full names and map them according to then tasks similarity from existing memory)
        - task (what needs to be done)
        - deadline (if mentioned, else null)
        - deliverable (what should be produced)
        - priority (High / Medium / Low; infer from context)
        - status (choose only from these: "In Progress", "Done")
            Guidelines for status:
            * "In Progress" → if assignee is expected to start/continue or has a deadline
            * "Done" → if explicitly mentioned as finished

        Important rules:
        1. Map all names (giver and assignee) to their full names from the existing memory context.
        2. Do not create new or shortened names.
        3. If a first name appears that matches multiple team members, infer the correct one by **comparing the new task with their past similar tasks** (task domain similarity).

        Meeting Transcript + Context:
        {prompt_text}

        Existing Team Members: {memory.get("team")}

        Return ONLY valid JSON, properly formatted, no extra text or whitespace.
        """


    response = llm.invoke(prompt)
    tasks = json.loads(response.content)
    return tasks


def save_tasks_to_csv(tasks, filename="approval.csv"):
    if not tasks:
        print("No tasks discussed in meeting")
        return
    keys = ["id", "giver", "assignee", "task", "deadline", "deliverable", "priority", "status"]
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(tasks)


'''if __name__ == "__main__":
    transcript_text = """
            Manager: Continuing from last meeting, we have a new task. 

Rajesh, I want you to implement the database based on the schema sketch we discussed previously. Ensure all tables and relationships are correctly set up.

Please complete this by next week.

            """

    memory, metadata_updates = extract_metadata_from_transcript(transcript_text)
    tasks = extract_tasks_from_transcript(transcript_text)
    save_tasks_to_csv(tasks)

    print("Updated Memory Metadata:", metadata_updates)
    print("Extracted Tasks:", tasks)'''
