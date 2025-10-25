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

def preprocess_memory(memory):
    memory_text = []

    pi = memory.get("project_info", {})
    if pi.get("description"):
        memory_text.append(f"Project Description: {pi['description']}")
    if pi.get("start_date"):
        memory_text.append(f"Start Date: {pi['start_date']}")
    if pi.get("expected_end_date"):
        memory_text.append(f"Expected End Date: {pi['expected_end_date']}")
    if pi.get("notes"):
        memory_text.append("Project Notes: " + "; ".join(pi["notes"]))

    team = memory.get("team", [])
    if team:
        ts = []
        for m in team:
            if isinstance(m, dict):
                ts.append(f"{m.get('name','Unknown')} ({m.get('role','')})")
            else:
                ts.append(str(m))
        memory_text.append("Team Members: " + "; ".join(ts))

    tasks = memory.get("tasks", [])
    if tasks:
        tstr = []
        for t in tasks:
            desc = t.get("task","") or t.get("description","")
            assigned = t.get("assignee","") or t.get("assigned_to","")
            priority = t.get("priority","")
            status = t.get("status","")
            tstr.append(f"{desc} (Assigned: {assigned}, Priority: {priority}, Status: {status})")
        memory_text.append("Tasks: " + "; ".join(tstr))

    cn = memory.get("context_notes", [])
    if cn:
        memory_text.append("Context Notes: " + "; ".join(cn))

    memory_final = "\n".join(memory_text)
    return memory_final

def query_llm(memory, question):
    memory_preprocessed = preprocess_memory(memory)
    prompt = f"""
                You are an AI project assistant. Use the project memory below to answer the user's question concisely. 
                Provide short, actionable responses only. Do NOT include long explanations.

                Project Memory:
                {memory_preprocessed}

                User Question:
                {question}

                Answer briefly, in 1–3 sentences, focused only on actionable suggestions or factual info based on the memory. Do proper reasoning.
                Greet if user greets and only answer about the project when the question is about the project.
             """
    response = llm.invoke(prompt)
    return response.content

