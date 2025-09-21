import streamlit as st
import pandas as pd
import requests

BACKEND_URL = "http://127.0.0.1:8000"

st.title("AI Project Manager - Transcript Analyzer")

# ---------------- Transcript Upload & Extraction ---------------- #
uploaded_file = st.file_uploader("Upload Meeting Transcript (.txt)", type=["txt"])

if uploaded_file:
    transcript = uploaded_file.read().decode("utf-8")

    if st.button("Extract Tasks"):
        with st.spinner("Extracting tasks..."):
            response = requests.post(f"{BACKEND_URL}/extract-tasks", json={"transcript": transcript})
            if response.status_code == 200:
                tasks = response.json().get("tasks", [])
                if tasks:
                    st.session_state.df = pd.DataFrame(tasks)
                    st.success(f"{len(tasks)} tasks extracted!")
                else:
                    st.warning("No tasks found in transcript!")
            else:
                st.error("Failed to extract tasks.")

# ---------------- Extracted Tasks Editor ---------------- #
if "df" in st.session_state:
    st.subheader("Editable Extracted Tasks Table")

    if st.button("Add Row to Extracted Tasks"):
        st.session_state.df = pd.concat(
            [st.session_state.df, pd.DataFrame([{
                "id": "",
                "giver": "",
                "assignee": "",
                "task": "",
                "deadline": "",
                "deliverable": "",
                "priority": "Medium",
                "status": "To Do"
            }])],
            ignore_index=True
        )

    st.session_state.df = st.data_editor(
        st.session_state.df,
        use_container_width=True,
        key="task_editor"
    )

    st.subheader("Delete Rows (Extracted Tasks)")
    row_options = [f"{i} - {row['task'][:30]}" for i, row in st.session_state.df.iterrows()]
    rows_to_delete = st.multiselect("Select rows to delete", options=row_options, key="delete_extracted")

    if st.button("Delete Selected Extracted Rows"):
        indices_to_delete = [int(x.split(" - ")[0]) for x in rows_to_delete]
        st.session_state.df = st.session_state.df.drop(indices_to_delete).reset_index(drop=True)
        st.success(f"Deleted {len(indices_to_delete)} extracted row(s)")

    if st.button("Finalize & Save Extracted Tasks to Jira"):
        tasks_list = st.session_state.df.to_dict(orient="records")
        for task in tasks_list:
            if task.get("id") not in [None, ""]:
                task["id"] = int(float(task["id"]))
        resp = requests.post(f"{BACKEND_URL}/save-tasks", json=tasks_list)
        if resp.status_code == 200:
            data = resp.json()
            st.success(data["message"])
            with st.expander("Jira update log (Extracted Tasks)"):
                for r in data["jira_results"]:
                    st.write(r)
        else:
            st.error("Failed to save & update Jira.")


# ---------------- Manual Task Creation ---------------- #
st.subheader("Or Create Tasks Manually (No Transcript Needed)")

if "df_manual" not in st.session_state:
    st.session_state.df_manual = pd.DataFrame(columns=[
        "id", "giver", "assignee", "task", "deadline", "deliverable", "priority", "status"
    ])

if st.button("Add Empty Manual Task Row"):
    next_id = 1001 if st.session_state.df_manual.empty else int(st.session_state.df_manual["id"].max()) + 1
    st.session_state.df_manual = pd.concat(
        [st.session_state.df_manual, pd.DataFrame([{
            "id": next_id,
            "giver": "",
            "assignee": "",
            "task": "",
            "deadline": "",
            "deliverable": "",
            "priority": "Medium",
            "status": "In Progress"
        }])],
        ignore_index=True
    )

st.session_state.df_manual = st.data_editor(
    st.session_state.df_manual,
    use_container_width=True,
    key="manual_task_editor"
)

st.subheader("Delete Rows (Manual Tasks)")
row_options_manual = [f"{i} - {row['task'][:30]}" for i, row in st.session_state.df_manual.iterrows()]
rows_to_delete_manual = st.multiselect("Select rows to delete (Manual)", options=row_options_manual, key="delete_manual")

if st.button("Delete Selected Manual Rows"):
    indices_to_delete = [int(x.split(" - ")[0]) for x in rows_to_delete_manual]
    st.session_state.df_manual = st.session_state.df_manual.drop(indices_to_delete).reset_index(drop=True)
    st.success(f"Deleted {len(indices_to_delete)} manual row(s)")

if st.button("Finalize & Send Manual Tasks to Jira"):
    tasks_list = st.session_state.df_manual.to_dict(orient="records")
    resp = requests.post(f"{BACKEND_URL}/save-tasks", json=tasks_list)
    if resp.status_code == 200:
        data = resp.json()
        st.success(data["message"])
        with st.expander("Jira update log (Manual Tasks)"):
            for r in data["jira_results"]:
                st.write(r)
    else:
        st.error("Failed to save & update Jira.")

st.subheader("Delete Task from Jira by Task ID")
task_id_to_delete = st.text_input("Enter Task ID to delete (e.g., 1003)")

if st.button("Delete Task from Jira"):
    if task_id_to_delete.strip():
        resp = requests.delete(f"{BACKEND_URL}/delete-task/{task_id_to_delete}")
        if resp.status_code == 200:
            data = resp.json()
            st.success(data["message"])
        else:
            st.error("Failed to delete task from Jira.")
    else:
        st.warning("Please enter a Task ID.")

'''st.subheader("Fetch & Edit Task from Jira")
fetch_task_id = st.text_input("Enter Task ID to fetch", key="fetch_task_id")

if st.button("Fetch Task"):
    if fetch_task_id.strip():
        resp = requests.get(f"{BACKEND_URL}/get-task/{fetch_task_id}")
        if resp.status_code == 200:
            data = resp.json()
            if data["status"] == "success":
                st.session_state.fetched_df = pd.DataFrame([data["task"]])
                st.success(f"Task {fetch_task_id} fetched from Jira!")
            else:
                st.warning(data["message"])
        else:
            st.error("Failed to fetch task from Jira.")
    else:
        st.warning("Please enter a Task ID.")

if "fetched_df" in st.session_state:
    st.subheader("Edit Fetched Task Details")

    st.session_state.fetched_df = st.data_editor(
        st.session_state.fetched_df,
        use_container_width=True,
        key="fetched_task_editor"
    )

    if st.button("Update Jira with Edited Task"):
        tasks_list = st.session_state.fetched_df.to_dict(orient="records")
        resp = requests.post(f"{BACKEND_URL}/save-tasks", json=tasks_list)
        if resp.status_code == 200:
            data = resp.json()
            st.success(data["message"])
            with st.expander("Jira update log (Edited Task)"):
                for r in data["jira_results"]:
                    st.write(r)
        else:
            st.error("Failed to update Jira.")'''
