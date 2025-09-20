import streamlit as st
import pandas as pd
import requests

BACKEND_URL = "http://127.0.0.1:8000"

st.title("AI Project Manager - Transcript Analyzer")

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

if "df" in st.session_state:
    st.subheader("Editable Tasks Table")

    if st.button("Add Row"):
        st.session_state.df = pd.concat(
            [st.session_state.df, pd.DataFrame([{
                "giver": "",
                "assignee": "",
                "task": "",
                "deadline": "",
                "deliverable": "",
                "priority": "Medium"
            }])],
            ignore_index=True
        )

    st.session_state.df = st.data_editor(
        st.session_state.df,
        use_container_width=True,
        key="task_editor"
    )

    st.subheader("Delete Rows")
    row_options = [f"{i} - {row['task'][:30]}" for i, row in st.session_state.df.iterrows()]
    rows_to_delete = st.multiselect("Select rows to delete", options=row_options)

    if st.button("Delete Selected Rows"):
        indices_to_delete = [int(x.split(" - ")[0]) for x in rows_to_delete]
        st.session_state.df = st.session_state.df.drop(indices_to_delete).reset_index(drop=True)
        st.success(f"Deleted {len(indices_to_delete)} row(s)")

    if st.button("Finalize & Save CSV"):
        tasks_list = st.session_state.df.to_dict(orient="records")
        for task in tasks_list:
            if task.get("id") not in [None, ""]:
                task["id"] = int(float(task["id"]))
        resp = requests.post(f"{BACKEND_URL}/save-tasks", json=tasks_list)
        if resp.status_code == 200:
            data = resp.json()
            st.success(data["message"])
            with st.expander("Jira update log"):
                for r in data["jira_results"]:
                    st.write(r)
        else:
            st.error("Failed to save & update Jira.")



