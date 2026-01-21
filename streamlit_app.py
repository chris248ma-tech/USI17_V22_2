"""
USI17 V22.2 Streamlit Interface - SIMPLIFIED
"""

import streamlit as st
import tempfile
from translator import USI17_Translator

# Password protection
def check_password():
    def password_entered():
        if st.session_state["password"] == "CKD2026USI17":
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.title("🔒 USI17 V22.2 Translation System")
        st.text_input("Enter Password", type="password", on_change=password_entered, key="password")
        return False
    elif not st.session_state["password_correct"]:
        st.title("🔒 USI17 V22.2 Translation System")
        st.text_input("Enter Password", type="password", on_change=password_entered, key="password")
        st.error("❌ Incorrect password")
        return False
    else:
        return True

if not check_password():
    st.stop()

# Main app
st.set_page_config(page_title="USI17 V22.2", page_icon="🌐", layout="wide")

st.title("🌐 USI17 V22.2 Translation System")
st.markdown("**535 terms | 276 agents | Multi-directional translation**")

# Language definitions
LANGUAGES = {
    'ja': 'Japanese', 'en': 'English', 'de': 'German', 'fr': 'French',
    'es': 'Spanish', 'pt': 'Portuguese', 'it': 'Italian', 
    'ko': 'Korean', 'cn': 'Chinese (CN)', 'tw': 'Chinese (TW)'
}

# Session state
if 'translator' not in st.session_state:
    st.session_state.translator = None
if 'initialized' not in st.session_state:
    st.session_state.initialized = False

# Sidebar
with st.sidebar:
    st.header("⚙️ Configuration")
    
    gemini_key = st.text_input("Gemini API Key", type="password")
    grok_key = st.text_input("Grok API Key", type="password")
    
    V22_2_file = st.file_uploader("Upload USI17_V22_2_MASTER.txt", type=['txt'])
    
    if st.button("🚀 Initialize", type="primary"):
        if not grok_key:
            st.error("❌ Grok API key required!")
        elif not V22_2_file:
            st.error("❌ V22.2 Master file required!")
        else:
            with tempfile.NamedTemporaryFile(delete=False, suffix='.txt', mode='w', encoding='utf-8') as tmp:
                tmp.write(V22_2_file.getvalue().decode('utf-8'))
                tmp_path = tmp.name
            
            try:
                st.session_state.translator = USI17_Translator(
                    grok_api_key=grok_key,
                    gemini_api_key=gemini_key if gemini_key else None,
                    master_path=tmp_path
                )
                st.session_state.initialized = True
                st.success("✅ V22.2 loaded!")
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")

# Main content
if not st.session_state.initialized:
    st.info("👈 Initialize the system using the sidebar")
else:
    col1, col2 = st.columns([1, 2])
    
    with col1:
        source_lang = st.selectbox("Source Language", options=list(LANGUAGES.keys()), 
                                   format_func=lambda x: LANGUAGES[x])
    
    with col2:
        target_lang = st.selectbox("Target Language", 
                                   options=[k for k in LANGUAGES.keys() if k != source_lang],
                                   format_func=lambda x: LANGUAGES[x])
    
    source_text = st.text_area(f"Source Text ({LANGUAGES[source_lang]})", height=150)
    
    if st.button("🚀 TRANSLATE", type="primary", disabled=not source_text):
        with st.spinner("Translating..."):
            try:
                result = st.session_state.translator.translate(
                    source_text=source_text,
                    source_lang=source_lang,
                    target_lang=target_lang
                )
                
                st.success("✅ Translation complete!")
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Model", result['model'])
                with col2:
                    st.metric("Cost", f"¥{result['cost_jpy']:.2f}")
                with col3:
                    st.metric("Tokens", f"{result['tokens_input']}+{result['tokens_output']}")
                
                st.subheader(f"📄 {LANGUAGES[target_lang]} Translation:")
                st.text_area("Translation", value=result['translation'], height=150, key='output')
                
            except Exception as e:
                st.error(f"❌ Translation failed: {str(e)}")
