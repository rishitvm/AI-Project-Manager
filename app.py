import streamlit as st
import pandas as pd
import requests
from datetime import datetime
import matplotlib.pyplot as plt

BACKEND_URL = "http://127.0.0.1:8000"


page = st.sidebar.radio("Navigate", ["AutoPM", "Project Details"])

if page == "Project Details":
    
    try:
        resp = requests.get(f"{BACKEND_URL}/get-project-details", timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            if data.get("status") == "success":
                updated_at = data["project_info"].get("updated_at", "N/A")
            else:
                updated_at = "N/A"
        else:
            updated_at = "N/A"
    except Exception:
        updated_at = "N/A"

    if "project_name" not in st.session_state:
        try:
            resp = requests.get(f"{BACKEND_URL}/get-project-name", timeout=5)
            st.session_state.project_name = resp.json().get("project_name", "Unnamed Project") if resp.status_code == 200 else "Unnamed Project"
        except Exception:
            st.session_state.project_name = "Unnamed Project"
    try:
        resp = requests.get(f"{BACKEND_URL}/get-project-name", timeout=5)
        project_name = resp.json().get("project_name", "Unnamed Project") if resp.status_code == 200 else "Unnamed Project"
    except Exception:
        project_name = "Unnamed Project"

    # Display project name
    col1, col2 = st.columns([0.8, 0.2])
    with col1:
        st.markdown(f"<h1 style='text-align: left; color: #1E88E5;'>{st.session_state.project_name}</h1>", unsafe_allow_html=True)
    with col2:
        if st.button("✏️", key="edit_project_name_btn"):
            st.session_state.edit_project_name = True

    # Editable project name
    if st.session_state.get("edit_project_name", False):
        new_name = st.text_input("Enter new project name", value=st.session_state.project_name)
        if st.button("💾 Save Name", key="save_project_name_btn"):
            try:
                resp = requests.post(f"{BACKEND_URL}/update-project-name", json={"project_name": new_name}, timeout=5)
                data = resp.json()
                if resp.status_code == 200 and data.get("status") == "success":
                    st.session_state.project_name = new_name
                    st.session_state.edit_project_name = False
                    st.success("Project name updated successfully!")
                else:
                    st.error(data.get("message", "Failed to update project name."))
            except Exception as e:
                st.error(f"Error updating project name: {e}")


    # ----------------- Initialize States -----------------
    if "show_project_info" not in st.session_state:
        st.session_state.show_project_info = False
    if "edit_project_info" not in st.session_state:
        st.session_state.edit_project_info = False
    if "edit_notes" not in st.session_state:
        st.session_state.edit_notes = False
    if "project_data" not in st.session_state:
        st.session_state.project_data = {
            "description": "",
            "start_date": "",
            "expected_end_date": "",
            "notes": []
        }

    # ----------------- Toggle Project Info -----------------
    def toggle_project_info():
        st.session_state.show_project_info = not st.session_state.show_project_info
        # Fetch data from backend only once
        if st.session_state.show_project_info and st.session_state.project_data["description"] == "":
            try:
                resp = requests.get(f"{BACKEND_URL}/get-project-details")
                if resp.status_code == 200:
                    data = resp.json()
                    if data.get("status") == "success":
                        info = data["project_info"]
                        st.session_state.project_data["description"] = info.get("description", "")
                        st.session_state.project_data["start_date"] = info.get("start_date", "")
                        st.session_state.project_data["expected_end_date"] = info.get("expected_end_date", "")
                        st.session_state.project_data["notes"] = info.get("notes", [])
                    else:
                        st.warning(data.get("message", "Failed to fetch project info"))
                else:
                    st.error("Failed to fetch project information from backend.")
            except Exception as e:
                st.error(f"Error fetching project info: {e}")

    st.button("Close Info" if st.session_state.show_project_info else "View Project Info", on_click=toggle_project_info)

    # ----------------- Project Info & Notes -----------------
    if st.session_state.show_project_info:
        # ----- Project Info -----
        with st.expander("Project Information", expanded=True):
            col1, col2 = st.columns([0.9, 0.1])
            with col2:
                if st.button("✏️", key="edit_proj"):
                    st.session_state.edit_project_info = not st.session_state.edit_project_info

            if st.session_state.edit_project_info:
                st.session_state.project_data["description"] = st.text_area(
                    "Description", st.session_state.project_data["description"], key="desc_edit"
                )
                st.session_state.project_data["start_date"] = st.text_input(
                    "Start Date", st.session_state.project_data["start_date"], key="start_edit"
                )
                st.session_state.project_data["expected_end_date"] = st.text_input(
                    "Expected End Date", st.session_state.project_data["expected_end_date"], key="end_edit"
                )

                # ✅ Move Save button outside column block to avoid rerun issues
                save_clicked = st.button("💾 Save Project Info", key="save_proj_btn")
                if save_clicked:
                    payload = {
                        "description": st.session_state.project_data["description"] or "",
                        "start_date": st.session_state.project_data["start_date"] or "",
                        "expected_end_date": st.session_state.project_data["expected_end_date"] or ""
                    }
                    try:
                        resp = requests.post(
                            f"{BACKEND_URL}/update-project-info",
                            json=payload,
                            timeout=5
                        )
                        data = resp.json()
                        if resp.status_code == 200 and data.get("status") == "success":
                            st.session_state.edit_project_info = False
                            st.success(data.get("message", "Project Information updated successfully!"))
                        else:
                            st.error(data.get("message", "Failed to update project info."))
                    except Exception as e:
                        st.error(f"Error updating project info: {e}")
            else:
                st.markdown(f"**Description:** {st.session_state.project_data['description']}")
                st.markdown(f"**Start Date:** {st.session_state.project_data['start_date']}")
                st.markdown(f"**Expected End Date:** {st.session_state.project_data['expected_end_date']}")

        # ----- Notes -----
        # (kept unchanged, works fine)
        with st.expander("Notes", expanded=False):
            col1, col2 = st.columns([0.9, 0.1])
            with col2:
                if st.button("✏️", key="edit_notes_btn"):
                    st.session_state.edit_notes = not st.session_state.edit_notes

            notes = st.session_state.project_data.get("notes", [])

            if st.session_state.edit_notes:
                notes_text = "\n".join(notes)
                notes_text = st.text_area("Edit Notes (each line is a note)", notes_text, key="notes_edit")
                if st.button("💾 Save Notes", key="save_notes_btn"):
                    updated_notes = [n.strip() for n in notes_text.split("\n") if n.strip()]
                    st.session_state.project_data["notes"] = updated_notes
                    try:
                        resp = requests.post(
                            f"{BACKEND_URL}/update-project-notes",
                            json={"notes": updated_notes},
                            timeout=5
                        )
                        data = resp.json()
                        if resp.status_code == 200 and data.get("status") == "success":
                            st.session_state.edit_notes = False
                            st.success(data.get("message", "Notes updated successfully!"))
                        else:
                            st.error(data.get("message", "Failed to update notes."))
                    except Exception as e:
                        st.error(f"Error updating notes: {e}")
            else:
                for i, note in enumerate(notes, 1):
                    st.markdown(f"{i}. {note}")

    st.markdown("---")
    # Fetch tasks for analysis
    try:
        resp = requests.get(f"{BACKEND_URL}/get-task-analysis")
        if resp.status_code == 200:
            data = resp.json()
            tasks = pd.DataFrame(data["tasks"])
        else:
            st.error("Failed to fetch tasks.")
            tasks = pd.DataFrame()
    except Exception as e:
        st.error(f"Error fetching data: {e}")
        tasks = pd.DataFrame()

    if not tasks.empty:
        # --- Convert deadline to datetime ---
        tasks["deadline_dt"] = pd.to_datetime(tasks["deadline"], errors="coerce")

        # --- Project-Level Analysis ---
        st.subheader("Project-Level Analysis")

        # --- Layout with two columns ---
        col1, col2 = st.columns(2)

        # Left Column: Textual Info
        with col1:
            st.markdown("**Task Priority Counts:**")
            counts = tasks["priority"].value_counts().reindex(["High", "Medium", "Low"], fill_value=0)
            for p in ["High", "Medium", "Low"]:
                st.markdown(f"{p}: {counts.get(p,0)}")

            # Upcoming task
            upcoming = tasks[tasks["status"] != "Done"].sort_values("deadline_dt").head(1)
            if not upcoming.empty:
                st.markdown(
                    f"**Next Upcoming Task:** {upcoming.iloc[0]['task']} "
                    f"(Deadline: {upcoming.iloc[0]['deadline']}, Assigned to: {upcoming.iloc[0]['assignee']}, Priority: {upcoming.iloc[0]['priority']})"
                )
            else:
                st.markdown("**Next Upcoming Task:** None")

            # Latest completed task
            completed = tasks[tasks["status"] == "Done"].sort_values("deadline_dt", ascending=False)
            if not completed.empty:
                st.markdown(
                    f"**Latest Completed Task:** {completed.iloc[0]['task']} "
                    f"(Completed on: {completed.iloc[0]['deadline']}, Assigned to: {completed.iloc[0]['assignee']}, Priority: {completed.iloc[0]['priority']})"
                )
            else:
                st.markdown("**Latest Completed Task:** None")

        # Right Column: Pie Chart by Priority
        with col2:
            st.markdown("**Task Priority Pie Chart:**")
            priority_counts = tasks["priority"].value_counts().reindex(["High", "Medium", "Low"], fill_value=0)
            fig, ax = plt.subplots()
            ax.pie(priority_counts, labels=priority_counts.index, autopct="%1.1f%%", colors=["#FF4C4C", "#FFA500", "#4CAF50"])
            ax.set_title("Tasks by Priority")
            st.pyplot(fig)

        st.markdown("---")

        # --- Employee-Level Analysis (unchanged) ---
        st.subheader("Employee-Level Analysis")
        employees = tasks["assignee"].unique().tolist()
        selected_emp = st.selectbox("Select Employee", options=["All"] + employees)

        if selected_emp != "All":
            emp_tasks = tasks[tasks["assignee"] == selected_emp]
        else:
            emp_tasks = tasks

        # Priority counts
        st.markdown(f"**Priority Counts for {selected_emp}:**")
        emp_counts = emp_tasks["priority"].value_counts().reindex(["High", "Medium", "Low"], fill_value=0)
        for p in ["High", "Medium", "Low"]:
            st.markdown(f"{p}: {emp_counts.get(p,0)}")

        # Upcoming deliverables
        upcoming_deliv = emp_tasks[emp_tasks["status"] != "Done"].sort_values("deadline_dt")[["task", "deliverable", "deadline", "priority"]]
        st.markdown(f"**Upcoming Deliverables for {selected_emp}:**")
        st.dataframe(upcoming_deliv)
    else:
        st.info("No tasks found.")

elif page == "AutoPM":

    st.title("AI Project Manager (AutoPM)")
    st.write("")
    st.write("")


    # ---------------- Transcript Upload & Extraction ---------------- #
    uploaded_file = st.file_uploader("Upload Meeting Transcript (.txt)", type=["txt"])

    if uploaded_file:
        transcript = uploaded_file.read().decode("utf-8")

        if st.button("Extract Tasks", key="extract_tasks_btn"):
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

    st.markdown("<hr style='height:5px;border:none;color:#333;background-color:#333;'>", unsafe_allow_html=True)

    # ---------------- Extracted Tasks Editor ---------------- #
    if "df" in st.session_state:
        st.subheader("Extracted Tasks")

        if st.button("Add Row", key="add_extracted_row"):
            st.session_state.df = pd.concat(
                [st.session_state.df, pd.DataFrame([{
                    "id": "",
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

        st.session_state.df = st.data_editor(
            st.session_state.df,
            use_container_width=True,
            key="task_editor"
        )

        # Delete rows
        row_options = [f"{i} - {row['task'][:30]}" for i, row in st.session_state.df.iterrows()]
        rows_to_delete = st.multiselect("Select rows to delete", options=row_options, key="delete_extracted")

        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("Delete", key="delete_extracted_btn"):
                indices_to_delete = [int(x.split(" - ")[0]) for x in rows_to_delete]
                st.session_state.df = st.session_state.df.drop(indices_to_delete).reset_index(drop=True)
                st.success(f"Deleted {len(indices_to_delete)} extracted row(s)")
        with col2:
            if st.button("Finalize to Jira", key="finalize_extracted_btn"):
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
    st.subheader("Create Manual Tasks")

    if "df_manual" not in st.session_state:
        st.session_state.df_manual = pd.DataFrame(columns=[
            "id", "giver", "assignee", "task", "deadline", "deliverable", "priority", "status"
        ])

    if st.button("Add Row", key="add_manual_row"):
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

    # ---------------- Manual Task Deletion ---------------- #
    if not st.session_state.df_manual.empty:
        st.subheader("Delete Rows (Manual Tasks)")

        row_options_manual = [f"{i} - {row['task'][:30]}" for i, row in st.session_state.df_manual.iterrows()]
        rows_to_delete_manual = st.multiselect("Select rows to delete", options=row_options_manual, key="delete_manual")

        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("Delete", key="delete_manual_btn"):
                indices_to_delete = [int(x.split(" - ")[0]) for x in rows_to_delete_manual]
                st.session_state.df_manual = st.session_state.df_manual.drop(indices_to_delete).reset_index(drop=True)
                # Also delete from memory via API
                for idx in indices_to_delete:
                    task_id = int(st.session_state.df_manual.iloc[idx]["id"])
                    requests.delete(f"{BACKEND_URL}/delete-task/{task_id}")
                st.success(f"Deleted {len(indices_to_delete)} manual row(s) and memory synced")
        with col2:
            if st.button("Finalize to Jira", key="finalize_manual_btn"):
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

    # ---------------- Delete Task from Jira ---------------- #
    st.subheader("Delete Task from Jira")
    task_id_to_delete = st.text_input("Enter Task ID to delete")

    if st.button("Delete Task", key="delete_task_btn"):
        if task_id_to_delete.strip():
            resp = requests.delete(f"{BACKEND_URL}/delete-task/{task_id_to_delete}")
            if resp.status_code == 200:
                data = resp.json()
                st.success(data["message"])
            else:
                st.error("Failed to delete task from Jira.")
        else:
            st.warning("Please enter a Task ID.")

    # ---------------- Update Task from Jira ---------------- #
    st.subheader("Update Task from Jira")
    fetch_task_id = st.text_input("Enter Task ID to fetch", key="fetch_task_id")

    if st.button("Fetch Task", key="fetch_task_btn"):
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
        st.subheader("Edit Task Details")
        st.session_state.fetched_df = st.data_editor(
            st.session_state.fetched_df,
            use_container_width=True,
            key="fetched_task_editor"
        )

        if st.button("Update Jira", key="update_jira_btn"):
            tasks_list = st.session_state.fetched_df.to_dict(orient="records")
            resp = requests.post(f"{BACKEND_URL}/save-tasks", json=tasks_list)
            if resp.status_code == 200:
                data = resp.json()
                st.success(data["message"])
                with st.expander("Jira update log (Edited Task)"):
                    for r in data["jira_results"]:
                        st.write(r)
            else:
                st.error("Failed to update Jira.")



# Chatbot Interaction
if 'show_chatbot' not in st.session_state:
    st.session_state.show_chatbot = False
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'input_key' not in st.session_state:
    st.session_state.input_key = 0

if st.sidebar.button("💬 Ask AI", key="ask_ai_btn"):
    st.session_state.show_chatbot = not st.session_state.show_chatbot

if st.session_state.show_chatbot:
    @st.dialog("🤖 AI Assistant", width="large")
    def show_chatbot():
        if st.button("🗑️ Clear Chat", key="clear_chat_btn"):
            st.session_state.chat_history = []
            st.rerun()

        chat_container = st.container(height = 250)
        with chat_container:
            if len(st.session_state.chat_history) == 0:
                st.info("👋 Hello! How can I help you today?")
            else:
                for msg in st.session_state.chat_history:
                    if msg['role'] == 'user':
                        col1, col2 = st.columns([0.3, 0.7])
                        with col2:
                            with st.chat_message("user"):
                                st.write(msg['content'])
                    else:
                        with st.chat_message("assistant"):
                            st.write(msg['content'])

        st.markdown("---")
        col_input, col_send = st.columns([0.85, 0.15])

        with col_input:
            user_input = st.text_area(
                "Type a message...",
                value="",
                height=70,
                placeholder="Ask me anything...",
                key=f"chat_input_field_{st.session_state.input_key}",
                label_visibility="collapsed"
            )

        with col_send:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("Send", key="send_btn", use_container_width=True, type="primary"):
                if user_input.strip():
                    st.session_state.chat_history.append({
                        'role': 'user',
                        'content': user_input
                    })

                    try:
                        resp = requests.post(f"{BACKEND_URL}/ask-question", json={"question": user_input})
                        if resp.status_code == 200:
                            bot_response = resp.json().get("answer", "No response from AI.")
                        else:
                            bot_response = f"Error: {resp.status_code}"
                    except Exception as e:
                        bot_response = f"Error connecting to API: {e}"

                    st.session_state.chat_history.append({
                        'role': 'assistant',
                        'content': bot_response
                    })

                    st.session_state.input_key += 1
                    st.rerun()
            
    show_chatbot()
