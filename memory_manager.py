from pymongo import MongoClient
from datetime import datetime

MONGO_URI = "your mongodb local host url"
DB_NAME = "ai_pm"
COLLECTION_NAME = "memory"

client = MongoClient(MONGO_URI)
db = client[DB_NAME]
collection = db[COLLECTION_NAME]

def load_memory():
    """Load the project memory from MongoDB."""
    memory = collection.find_one({"_id": "project_ai_pm"})
    if not memory:
        memory = {
            "_id": "project_ai_pm",
            "project_name": "",
            "project_info": {
                "description": "",
                "start_date": datetime.utcnow().strftime("%Y-%m-%d"),
                "expected_end_date": None,
                "notes": []
            },
            "team": [],
            "tasks": [],
            "context_notes": [],
            "metadata": {
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat(),
                "meeting_count": 0
            }
        }
        collection.insert_one(memory)
    return memory

def save_memory(memory):
    """Save updated memory back to MongoDB."""
    memory["metadata"]["updated_at"] = datetime.utcnow().isoformat()
    collection.replace_one({"_id": "project_ai_pm"}, memory, upsert=True)

def log_memory_status():
    memory = load_memory()
    print(f"Total tasks in memory: {len(memory.get('tasks', []))}")


if __name__ == "__main__":
    memory = load_memory()
    print("Memory Loaded:")
    print(memory)
