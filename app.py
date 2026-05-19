import streamlit as st
import json
import os
import requests
from authlib.integrations.requests_client import OAuth2Session

# -------------------------------
# GOOGLE OAUTH CONFIG
# -------------------------------
CLIENT_ID = "14988331281-eh2p1s4f5n9fn852b8gqhjcdvcac6lgn.apps.googleusercontent.com"
CLIENT_SECRET = "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"
REDIRECT_URI = "http://localhost:8501"

AUTHORIZATION_ENDPOINT = "https://accounts.google.com/o/oauth2/auth"
TOKEN_ENDPOINT = "https://oauth2.googleapis.com/token"
USER_INFO = "https://www.googleapis.com/oauth2/v1/userinfo"

# -------------------------------
# FILE HANDLING
# -------------------------------
TASK_FILE = "tasks.json"

def load_tasks():
    if not os.path.exists(TASK_FILE):
        return []
    with open(TASK_FILE, "r") as f:
        return json.load(f)

def save_tasks(tasks):
    with open(TASK_FILE, "w") as f:
        json.dump(tasks, f, indent=4)

# -------------------------------
# SESSION STATE INIT
# -------------------------------
if "user" not in st.session_state:
    st.session_state.user = None

if "message" not in st.session_state:
    st.session_state.message = None

if "task_title" not in st.session_state:
    st.session_state.task_title = ""

if "priority" not in st.session_state:
    st.session_state.priority = "High"

if "clear_form" not in st.session_state:
    st.session_state.clear_form = False

if "active_tab" not in st.session_state:
    st.session_state.active_tab = "create"

# -------------------------------
# GOOGLE LOGIN (UI IMPROVED ONLY)
# -------------------------------
def login():
    st.title("📝 TaskManager Kovai.Co")

    # ✨ NEW UI (ONLY ADDITION)
    st.markdown("### 👋 Welcome to TaskManager Kovai.Co")
    st.write("Manage your tasks efficiently and stay productive.")
    st.info("Please sign in using your Google account to continue.")

    oauth = OAuth2Session(
        CLIENT_ID,
        CLIENT_SECRET,
        redirect_uri=REDIRECT_URI,
        scope="openid email profile"
    )

    if "auth_url" not in st.session_state:
        auth_url, state = oauth.create_authorization_url(AUTHORIZATION_ENDPOINT)
        st.session_state.auth_url = auth_url
        st.session_state.state = state

    # 🔥 Styled button instead of plain link
    st.markdown(
        f"""
        <a href="{st.session_state.auth_url}" target="_self">
            <button style="
                background-color:#4285F4;
                color:white;
                padding:10px 20px;
                border:none;
                border-radius:6px;
                font-size:16px;
                cursor:pointer;">
                🔐 Sign in with Google
            </button>
        </a>
        """,
        unsafe_allow_html=True
    )

    query_params = st.query_params

    if "code" in query_params:
        try:
            token = oauth.fetch_token(
                TOKEN_ENDPOINT,
                code=query_params["code"]
            )

            resp = requests.get(
                USER_INFO,
                headers={"Authorization": f"Bearer {token['access_token']}"}
            )

            user_info = resp.json()
            email = user_info.get("email")

            if email:
                st.session_state.user = email
                st.session_state.message = f"✅ Logged in as {email}"

                st.query_params.clear()
                st.rerun()

        except Exception:
            st.error("Login failed. Try again.")

# -------------------------------
# MAIN APP (UNCHANGED)
# -------------------------------
def main_app():
    st.title("📝 TaskManager Kovai.co")

    if st.session_state.message:
        st.success(st.session_state.message)
        st.session_state.message = None

    if st.button("Logout"):
        st.session_state.user = None
        st.rerun()

    st.write(f"Logged in as: {st.session_state.user}")

    tasks = load_tasks()

    for t in tasks:
        if "priority" not in t:
            t["priority"] = "Low"

    selected_tab = st.radio(
        "Navigation",
        ["➕ Create Task", "📋 View Tasks"],
        horizontal=True,
        index=0 if st.session_state.active_tab == "create" else 1
    )

    if selected_tab == "➕ Create Task":
        st.session_state.active_tab = "create"

        st.subheader("Create a New Task")

        if st.session_state.clear_form:
            st.session_state.task_title = ""
            st.session_state.priority = "High"
            st.session_state.clear_form = False

        task_title = st.text_input("Task Title", key="task_title")

        priority = st.selectbox(
            "Priority",
            ["High", "Medium", "Low"],
            key="priority"
        )

        if st.button("Add Task"):
            if task_title:
                tasks.append({
                    "user": st.session_state.user,
                    "title": task_title,
                    "status": "Planned",
                    "priority": priority
                })
                save_tasks(tasks)

                st.session_state.message = "✅ Task added successfully!"
                st.session_state.clear_form = True
                st.rerun()
            else:
                st.warning("Please enter task title")

    elif selected_tab == "📋 View Tasks":
        st.session_state.active_tab = "view"

        st.subheader("Your Tasks")

        priority_order = {"High": 1, "Medium": 2, "Low": 3}

        user_tasks = sorted(
            [t for t in tasks if t["user"] == st.session_state.user],
            key=lambda x: priority_order.get(x.get("priority", "Low"), 3)
        )

        if not user_tasks:
            st.info("No tasks yet")
        else:
            for i, task in enumerate(user_tasks):

                priority = task.get("priority", "Low")

                if priority == "High":
                    color = "#ff0000"
                elif priority == "Medium":
                    color = "#ff8c00"
                else:
                    color = "#ffd700"

                if task["status"] == "Complete":
                    display = f"<s style='color:green'>{task['title']}</s>"
                else:
                    display = f"<span style='color:{color}; font-weight:bold'>{task['title']}</span>"

                st.markdown(display, unsafe_allow_html=True)

                st.write(f"Priority: {priority}")
                st.write(f"Status: {task['status']}")

                new_status = st.selectbox(
                    "Update Status",
                    ["Planned", "In Progress", "Complete"],
                    index=["Planned", "In Progress", "Complete"].index(task["status"]),
                    key=f"status_{i}"
                )

                col1, col2 = st.columns(2)

                with col1:
                    if st.button("Update", key=f"update_{i}"):
                        for t in tasks:
                            if t == task:
                                t["status"] = new_status
                        save_tasks(tasks)

                        st.session_state.message = "✅ Status updated!"
                        st.session_state.active_tab = "view"
                        st.rerun()

                with col2:
                    if st.button("Delete", key=f"delete_{i}"):
                        st.session_state[f"confirm_{i}"] = True

                if st.session_state.get(f"confirm_{i}", False):
                    st.warning("Confirm delete?")

                    c1, c2 = st.columns(2)

                    with c1:
                        if st.button("Yes", key=f"yes_{i}"):
                            tasks.remove(task)
                            save_tasks(tasks)

                            st.session_state.message = "🗑️ Task deleted!"
                            st.session_state.active_tab = "view"
                            st.rerun()

                    with c2:
                        if st.button("Cancel", key=f"no_{i}"):
                            st.session_state[f"confirm_{i}"] = False
                            st.rerun()

                st.write("---")

# -------------------------------
# ROUTING
# -------------------------------
if st.session_state.user:
    main_app()
else:
    login()