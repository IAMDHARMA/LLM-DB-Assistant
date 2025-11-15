import streamlit as st
import requests

st.set_page_config(page_title="LLM DB Assistant", layout="wide")

API = st.text_input('Backend URL', value='http://localhost:8000')


st.title('💽 LLM DB Assistant — Demo')

# Initialize Session State
if "connection_name" not in st.session_state:
    st.session_state.connection_name = None

# -------------------------
# Sidebar — Connect DB
# -------------------------
with st.sidebar.expander('🔌 Connect Database'):
    name_input = st.text_input('Connection name', value='demo')

    dialect = st.selectbox('Dialect', ['sqlite', 'mysql', 'postgres'])

    config = {'name': name_input, 'dialect': dialect}

    if dialect == 'sqlite':
        config['sqlite_path'] = st.text_input('SQLite File Path', value='demo.db')
        config.update({'host': '', 'port': None, 'username': '', 'password': '', 'database': None})

    else:
        config['host'] = st.text_input('Host', value='localhost')
        config['port'] = st.number_input('Port', value=3306 if dialect == 'mysql' else 5432)
        config['username'] = st.text_input('Username')
        config['password'] = st.text_input('Password', type='password')
        config['database'] = st.text_input('Database name')
        config['sqlite_path'] = ''

    if st.button('Connect'):
        resp = requests.post(f"{API}/connect", json=config)
        st.write(resp.json())

        if resp.status_code == 200:
            # SAVE the connection name for future use
            st.session_state.connection_name = name_input
            st.success(f"Connected as: {name_input}")

# -------------------------
# Fetch Schema
# -------------------------
if st.button('Fetch Schema'):
    if not st.session_state.connection_name:
        st.error("❗ No connection selected. Please connect first.")
    else:
        r = requests.get(f"{API}/schema/{st.session_state.connection_name}")
        st.subheader("📂 Schema")
        st.json(r.json())

# -------------------------
# Natural Language Question
# -------------------------
question = st.text_area('Ask a question in natural language')

if st.button('Ask'):
    if not st.session_state.connection_name:
        st.error("❗ No connection selected. Please connect first.")
    else:
        payload = {
            "connection_name": st.session_state.connection_name,
            "question": question
        }

        resp = requests.post(f"{API}/ask", json=payload)

        if resp.status_code != 200:
            st.error(resp.text)
        else:
            data = resp.json()

            st.subheader("🧠 Generated SQL")
            st.code(data.get("sql", "SQL not returned by backend"))

            st.subheader("📊 Query Result")
            st.dataframe(data.get("rows", []))
