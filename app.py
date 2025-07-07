import streamlit as st
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, scoped_session
import os
from dotenv import load_dotenv
from llm import summarize_db_output
from PIL import Image

# logo = Image.open("xenie_logo.png")  # Use your uploaded logo
# st.image(logo, width=150)

# Load environment variables from .env
env_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(dotenv_path=env_path)

DATABASE_URL = os.getenv('DATABASE_URL')

if not DATABASE_URL:
    raise ValueError("Please set DATABASE_URL environment variable in .env file")

# Replace postgresql with postgresql+psycopg2 for SQLAlchemy
DATABASE_URL = DATABASE_URL.replace('postgresql://', 'postgresql+psycopg2://', 1)

engine = create_engine(DATABASE_URL)
SessionLocal = scoped_session(
    sessionmaker(autocommit=False, autoflush=False, bind=engine)
)

def run_daily_summary():
    try:
        with open('daily_summary.sql', 'r') as f:
            sql = f.read()
        db = SessionLocal()
        result = db.execute(text(sql))
        columns = result.keys()
        rows = result.fetchall()
        db.close()
        return {'success': True, 'rows': rows, 'columns': columns}
    except Exception as e:
        return {'success': False, 'error': str(e)}

# Streamlit UI
st.set_page_config(page_title="Xenie: Retail Assistant Chat", layout="wide")
st.markdown("""
<style>
/* Set background for the whole app */
.stApp {
    background-color: #0B0023;
    color: #FFFFFF;
    font-family: 'Segoe UI', sans-serif;
}

/* Bubble for the user */
.user-bubble {
    background-color: #819ffc;
    color: #0B0023;
    padding: 10px 16px;
    border-radius: 16px 16px 16px 16px;
    margin-bottom: 8px;
    max-width: 85%;
    align-self: flex-end;
    margin-left: 15%;
}

/* Bubble for the assistant */
.xenie-bubble {
    background-color: #e0ecff;
    color: #0B0023;
    padding: 10px 16px;
    border-radius: 16px 16px 16px 16px;
    margin-bottom: 8px;
    max-width: 100%;
    align-self: flex-start;
}

/* Chat container layout */
.chat-container {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
    margin-bottom: 2rem;
}

/* Avatar for assistant */
.xenie-avatar {
    width: 32px;
    height: 32px;
    border-radius: 50%;
    background: #FEE440;
    color: #0B0023;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    font-weight: bold;
    margin-right: 8px;
}

/* Headings */
h1, h2, h3, h4 {
    color: #FFFFFF;
}

/* Optional: style sidebar if used */
.css-1d391kg {
    background-color: #0B0023 !important;
    color: white;
}

/* Fix dark mode table text */
thead, tbody, td, th {
    color: white !important;
}
</style>
""", unsafe_allow_html=True)

col1, col2 = st.columns([0.1, 0.9])  # Adjust widths as needed

with col1:
    st.image("xenie_logo.png", width=200)  # <-- Replace with your image file name

with col2:
    st.markdown("## Xenie: Your Retail Assistant")  # Markdown lets you style it more freely

DEFAULT_USER = os.getenv('DEFAULT_USER', 'User').replace("'", "")

# On app load, run daily summary and generate summary with LLM
if 'chat_history' not in st.session_state:
    with st.spinner('Preparing your summary...'):
        result = run_daily_summary()
        if result['success'] and result['rows']:
            # Try to extract the main summary dict from the first row/column
            db_output = result['rows'][0][0] if len(result['rows'][0]) == 1 else result['rows'][0]
            summary, action_items = summarize_db_output(db_output)
            summary = summary.replace("\n", "\n\n")
        else:
            summary = "Sorry, I couldn't fetch the summary right now."
            action_items = []
        #st.markdown(f"<small style='color:#f00'>DEBUG: summary={summary}</small>", unsafe_allow_html=True)
        #st.markdown(f"<small style='color:#f00'>DEBUG: action_items={action_items} (type={type(action_items)})</small>", unsafe_allow_html=True)
        greeting = f"Hello {DEFAULT_USER}! Here is a summary of yesterday's business performance:\n\n"
        st.session_state.chat_history = [
            {"role": "assistant", "content": f"{greeting}{summary}"}
        ]
        st.session_state.db_output = db_output
        if not isinstance(action_items, list):
            st.warning(f"action_items is not a list: {action_items} (type={type(action_items)})")
            st.session_state.action_items = []
        else:
            st.session_state.action_items = action_items

# Chat UI
# ─── Replace EVERYTHING from “# Chat UI” down to “# Render detailed data…” with this ───

# Streamlit’s native chat components automatically render Markdown inside bubbles
st.markdown('<div class="chat-container">', unsafe_allow_html=True)
for msg in st.session_state.chat_history:
    if msg['role'] == 'user':
        st.markdown(f'<div class="user-bubble">{msg["content"]}</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="xenie-bubble"><span class="xenie-avatar">X</span> {msg["content"]}</div>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

# --- ACTION BUTTONS BELOW XENIE BUBBLE ---
# Only show if last message is from assistant and action_items exist
if 'action_items' not in st.session_state:
    st.session_state.action_items = []

# Try to extract action items from the last assistant response (if available)
if st.session_state.chat_history and st.session_state.chat_history[-1]['role'] == 'assistant':
    # Attempt to get action items from the last response, else keep previous
    import ast
    last_response = st.session_state.chat_history[-1]['content']
    # If action items are present in session, use them; else, try to get from last_response
    if hasattr(st.session_state, 'last_action_items_response') and st.session_state.last_action_items_response == last_response:
        action_items = st.session_state.action_items
    else:
        # Fallback: try to parse a list from the response, or use session
        try:
            # If action items are stored in session, use them
            action_items = st.session_state.action_items
            if not action_items:
                # Try to extract a python list from the response (if present)
                import re
                match = re.search(r"\[(.*?)\]", last_response, re.DOTALL)
                if match:
                    action_items = ast.literal_eval("[" + match.group(1) + "]")
        except Exception:
            action_items = []
        st.session_state.action_items = action_items
        st.session_state.last_action_items_response = last_response
else:
    action_items = st.session_state.action_items

# Debug: Show action_items in the UI
#st.markdown(f"<small style='color:gray'>DEBUG action_items: {st.session_state.action_items}</small>", unsafe_allow_html=True)

st.markdown("""
<style>
/* target all Streamlit column buttons */
div[data-testid="stHorizontalBlock"] button[data-baseweb="button"] {
    background-color: #ff0000 !important; /* Red background */
    color: #222 !important;
    border-radius: 8px !important;
    border: 1px solid #ccc !important;
    font-weight: 600 !important;
    margin-bottom: 0.5rem !important;
}
div[data-testid="stHorizontalBlock"] button[data-baseweb="button"]:hover {
    background-color: #5a7be6 !important;
    color: #fff !important;
}
</style>
""", unsafe_allow_html=True)

# Ensure action_items is a list
if isinstance(action_items, str):
    import ast
    try:
        action_items = ast.literal_eval(action_items)
        if not isinstance(action_items, list):
            action_items = []
    except Exception:
        action_items = []

if action_items:
    st.markdown("""
    <style>
    .action-btn-row {
        display: flex;
        gap: 2rem;
        margin-bottom: 1.5rem;
        justify-content: flex-start;
    }
    .custom-red-btn {
        background-color: #ff0000;
        color: #fff;
        border: 1px solid #b30000;
        border-radius: 8px;
        font-weight: 600;
        padding: 0.5em 1.5em;
        margin: 0.5em 0;
        cursor: pointer;
        font-size: 1rem;
        transition: background 0.2s;
    }
    .custom-red-btn:hover {
        background-color: #cc0000;
    }
    </style>
    <div class="action-btn-row">
    """, unsafe_allow_html=True)
    for i, action in enumerate(action_items):
        button_id = f"custom_btn_{i}"
        # Use a unique form for each button to allow POST event
        st.markdown(f'''
            <form action="" method="post">
                <input type="hidden" name="action_item" value="{action}" />
                <button class="custom-red-btn" type="submit" name="{button_id}">{action}</button>
            </form>
        ''', unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)
    # Handle button click via query params
    import streamlit as st
    if "action_item" in st.query_params:
        st.session_state.user_input = st.query_params["action_item"][0]
        st.experimental_rerun()


def render_section(title, content, icon="📌"):
    with st.expander(f"{icon} {title}", expanded=False):
        if isinstance(content, dict):
            for key, value in content.items():
                st.write(f"**{key.replace('_', ' ').title()}**: {value}")
        elif isinstance(content, list):
            import pandas as pd
            df = pd.DataFrame(content)
            st.dataframe(df.style.hide(axis="index"))  # ✅ hides index column
        else:
            st.write(content)

# Now render your detailed sections as before…
db_output = st.session_state.get("db_output")



# Render detailed data dynamically (only if summary is a dict)
if isinstance(db_output, dict):
    for section, content in db_output.items():
        if content:  # Show only non-empty sections
            readable_title = section.replace("_", " ").title()
            render_section(readable_title, content)


# User input box (text or from button)
user_input = st.text_input("You:", value=st.session_state.get("user_input", ""), key="user_input", placeholder="Ask Xenie about your business...")
if user_input:
    st.session_state.chat_history.append({"role": "user", "content": user_input})
    with st.spinner("Xenie is typing..."):
        db_context = st.session_state.chat_history[0]['content'] if st.session_state.chat_history else ""
        summary, action_items = summarize_db_output(db_context, user_message=user_input)
    st.session_state.chat_history.append({"role": "assistant", "content": summary})
    st.session_state.action_items = action_items if isinstance(action_items, list) else []
    st.session_state.user_input = ""
    st.experimental_rerun()