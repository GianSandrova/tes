import streamlit as st
from retrieval.search import search_and_respond
from config import GROQ_API_KEY, GROQ_MODEL

# Inisialisasi state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "history" not in st.session_state:
    st.session_state.history = []

# Konfigurasi halaman
st.set_page_config(
    page_title="Chatbot Tafsir Al-Quran",
    page_icon="📖",
    layout="centered"
)

# Override complete streamlit theme with custom dark theme
st.markdown("""
<style>
    /* Reset all backgrounds to dark */
    html, body, div, header, footer, section, article, aside, nav {
        background-color: #121212 !important;
        color: #f0f0f0 !important;
    }
    
    /* Main background */
    .stApp, .main, .block-container, [data-testid="stAppViewContainer"] {
        background-color: #121212 !important;
        color: #f0f0f0 !important;
    }
    
    /* Header areas */
    .stHeader, header, [data-testid="stHeader"] {
        background-color: #121212 !important;
    }
    
    /* Sidebar - comprehensive selector targeting */
    [data-testid="stSidebar"], 
    [data-testid="stSidebarUserContent"],
    .css-1d391kg, .css-12oz5g7, .css-1oe6oti,
    .st-emotion-cache-1oe6oti, .st-emotion-cache-1d391kg,
    .st-emotion-cache-12oz5g7, .st-emotion-cache-1cypcdb,
    .st-emotion-cache-ue6h4q, .st-emotion-cache-5rimss {
        background-color: #1a1a1a !important;
        color: #f0f0f0 !important;
    }
    
    /* Sidebar expander */
    .st-emotion-cache-ch5dnh, [data-testid="collapsedControl"] {
        background-color: #1a1a1a !important;
        color: #f0f0f0 !important;
    }
    
    /* Force all sidebar contents dark */
    [data-testid="stSidebar"] * {
        background-color: #1a1a1a !important;
        color: #f0f0f0 !important;
    }
    
    /* Sidebar content styles */
    .sidebar .sidebar-content {
        background-color: #1a1a1a !important;
    }
    
    /* Input area styling - enhanced for better visibility */
    .stChatInput, [data-testid="stChatInput"],
    .stChatInput input, [data-testid="stChatInputTextArea"],
    .st-emotion-cache-10oheav, .st-emotion-cache-yfdjkx,
    .st-emotion-cache-w1wxsf, .st-emotion-cache-1q3a02i,
    .element-container .stTextInput input,
    [data-baseweb="input"] input, [data-baseweb="textarea"] textarea,
    .stTextArea textarea {
        background-color: #1e1e1e !important;
        color: #ffffff !important;
        border: 1px solid #444444 !important;
        border-radius: 25px !important;
        padding: 12px 15px !important;
        font-size: 15px !important;
        box-shadow: 0 2px 5px rgba(0, 0, 0, 0.3) !important;
    }
    
    /* Bottom container including input area */
    footer, .st-emotion-cache-17lntkn, .st-emotion-cache-7ym5gk,
    [data-testid="stFooter"], .stChatFloatingInputContainer,
    .streamlit-chat .stChatFloatingInputContainer,
    .st-emotion-cache-1r4qj4y, .st-emotion-cache-1kg1ch6 {
        background-color: #121212 !important;
        border-color: #3a3a3a !important;
        padding: 10px 5px !important;
    }
    
    /* Input container adjustments */
    .stChatInputContainer, [data-testid="stChatInputContainer"] {
        background-color: transparent !important;
        padding: 5px !important;
        max-width: 900px !important;
        margin: 0 auto !important;
    }
    
    /* Chat container */
    .stChatContainer, [data-testid="stChatContainer"], 
    .st-emotion-cache-1v04vpj, .st-emotion-cache-1n9bvj {
        background-color: #121212 !important;
    }
    
    /* Message styling */
    .assistant-message {
        background-color: #1a3447 !important;
        color: #f0f0f0 !important;
        padding: 1.2rem !important;
        border-radius: 0.5rem !important;
        margin: 0.8rem 0 !important;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.3) !important;
    }
    
    .user-message {
        background-color: #2e2e2e !important;
        color: #f0f0f0 !important;
        padding: 1.2rem !important;
        border-radius: 0.5rem !important;
        margin: 0.8rem 0 !important;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.3) !important;
    }
    
    .error-message {
        background-color: #6b1515 !important;
        color: #f0f0f0 !important;
        padding: 1.2rem !important;
        border-radius: 0.5rem !important;
        margin: 0.8rem 0 !important;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.3) !important;
    }
    
    /* Individual chat messages */
    .stChatMessage, [data-testid="stChatMessage"],
    .st-emotion-cache-4oy321, .st-emotion-cache-llzb55 {
        background-color: transparent !important;
    }
    
    /* Chat message avatar containers */
    .stChatMessageAvatar, [data-baseweb="avatar"],
    .st-emotion-cache-1p1nwyz, .st-emotion-cache-tvksg {
        background-color: #2a2a2a !important;
    }
    
    /* Typography */
    h1, h2, h3, h4, h5, h6 {
        color: #ffffff !important;
    }
    
    p, span, div, li, a {
        color: #f0f0f0 !important;
    }
    
    /* Links */
    a {
        color: #4da6ff !important;
    }
    
    /* Lists in Markdown */
    .stMarkdown ul li {
        color: #f0f0f0 !important;
    }
    
    /* Input field text */
    input, textarea, [contentEditable=true] {
        color: #ffffff !important;
        background-color: #2a2a2a !important;
    }
    
    /* Input field placeholder */
    ::placeholder {
        color: #aaaaaa !important;
        opacity: 0.8 !important;
    }
    
    /* Send button in chat - enhanced styling */
    button[kind="primaryFormSubmit"],
    .st-emotion-cache-13e17gk, .st-emotion-cache-7ym5gk,
    button[data-testid="stChatMessageSubmitButton"] {
        background-color: #1c3a5e !important;
        color: white !important;
        border-radius: 50% !important;
        width: 36px !important;
        height: 36px !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        box-shadow: 0 2px 5px rgba(0, 0, 0, 0.3) !important;
        margin-left: 8px !important;
    }
    
    /* Status widget */
    [data-testid="stStatusWidget"], 
    .st-emotion-cache-6q9sum, .st-emotion-cache-9qtgef {
        background-color: #121212 !important;
        color: #aaaaaa !important;
    }
    
    /* Force all dialog content to dark */
    .stDialog, dialog, [role="dialog"] {
        background-color: #1a1a1a !important;
        color: #f0f0f0 !important;
    }
    
    /* Force all tooltip content to dark */
    .stTooltipContent, [data-testid="stTooltipContent"] {
        background-color: #1a1a1a !important;
        color: #f0f0f0 !important;
    }
    
    /* Bottom input container */
    .stChatInputContainer {
        background-color: #121212 !important;
    }
    
    /* Streamlit main page top margin fix */
    .main > div:first-of-type {
        padding-top: 1rem !important;
    }
    
    /* Streamlit top header removal */
    header[data-testid="stHeader"] {
        display: none !important;
    }
    
    /* Clean input container with proper styling */
    .stChatFloatingInputContainer, .st-emotion-cache-8qqqw5,
    .streamlit-chat .stChatFloatingInputContainer,
    [data-testid="stChatFloatingInputContainer"] {
        background-color: #121212 !important;
        border-top: 1px solid #333333 !important;
        padding: 15px !important;
        display: flex !important;
        justify-content: center !important;
        align-items: center !important;
    }
    
    /* Input area wrapper */
    .stChatInput > div, [data-testid="stChatInput"] > div {
        background-color: transparent !important;
    }
    
    /* Input placeholder */
    .stChatInput input::placeholder, 
    [data-testid="stChatInputTextArea"]::placeholder {
        color: #aaaaaa !important;
        opacity: 0.7 !important;
    }
    
    /* Input field interaction states */
    .stChatInput input:focus, 
    [data-testid="stChatInputTextArea"]:focus {
        border-color: #4d90fe !important;
        box-shadow: 0 0 0 2px rgba(77, 144, 254, 0.3) !important;
        outline: none !important;
    }
    
    /* Make sure the scrollbars match theme */
    ::-webkit-scrollbar {
        width: 10px;
        height: 10px;
    }
    
    ::-webkit-scrollbar-track {
        background: #1a1a1a;
    }
    
    ::-webkit-scrollbar-thumb {
        background: #444444;
        border-radius: 5px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: #555555;
    }
    
    /* Bottom button area */
    .st-emotion-cache-16txtl3, .st-emotion-cache-r421ms {
        background-color: #1a1a1a !important;
    }
    
    /* Any white boxes that might pop up */
    .stAlert, .stException, .stWarning, .stError, .stInfo,
    [data-baseweb="notification"], [role="alert"] {
        background-color: #232323 !important;
        color: #f0f0f0 !important;
    }
</style>
""", unsafe_allow_html=True)

# Konten aplikasi
st.title(":blue_book: Chatbot Al-Quran")

with st.sidebar:
    st.header("Tentang Aplikasi")
    st.markdown("""
    Aplikasi chatbot ini membantu Anda memahami Al-Quran dengan:
    - Tafsir ayat berdasarkan referensi terpercaya
    - Terjemahan resmi Kemenag RI
    - Penjelasan kontekstual menggunakan AI
    """)
    
    st.markdown("**Contoh Pertanyaan:**")
    st.markdown("""
    - Jelaskan makna Surat Al-Fatihah ayat 1
    - Apa hukum riba dalam Islam?
    - Jelaskan tafsir Surat Al-Baqarah ayat 255
    """)

# Tampilkan riwayat chat
for message in st.session_state.messages:
    avatar = "💡" if message["role"] == "assistant" else "💭"
    css_class = "assistant-message" if message["role"] == "assistant" else "user-message"

    if message["role"] == "assistant" and message["content"].startswith("❌"):
        css_class = "error-message"
        avatar = "❌"

    with st.chat_message(message["role"], avatar=avatar):
        st.markdown(f'<div class="{css_class}">{message["content"]}</div>', unsafe_allow_html=True)

# Input chat
if prompt := st.chat_input("Masukkan pertanyaan Anda..."):
    st.session_state.messages.append({"role": "user", "content": prompt, "avatar": "💭"})

    with st.chat_message("user", avatar="💭"):
        st.markdown(f'<div class="user-message">{prompt}</div>', unsafe_allow_html=True)

    with st.spinner("🔍 Mencari jawaban..."):
        try:
            answer = search_and_respond(prompt)

            if answer.startswith("❌"):
                error_msg = answer.replace("❌", "").strip()
                with st.chat_message("assistant", avatar="❌"):
                    st.markdown(f'<div class="error-message">{error_msg}</div>', unsafe_allow_html=True)
                st.session_state.messages.append({"role": "assistant", "content": answer, "avatar": "❌"})
                st.stop()

            processed_answer = answer.replace('\n', '<br>')
            formatted_answer = f'<div class="assistant-message">{processed_answer}</div>'

            with st.chat_message("assistant", avatar="💡"):
                st.markdown(formatted_answer, unsafe_allow_html=True)

            st.session_state.messages.append({"role": "assistant", "content": answer, "avatar": "💡"})

            # Update history max 3
            st.session_state.history.append((prompt, answer))
            if len(st.session_state.history) > 3:
                st.session_state.history.pop(0)

        except Exception as e:
            error_msg = f"❌ Terjadi kesalahan sistem: {str(e)}"
            with st.chat_message("assistant", avatar="❌"):
                st.markdown(f'<div class="error-message">{error_msg}</div>', unsafe_allow_html=True)
            st.session_state.messages.append({"role": "assistant", "content": error_msg, "avatar": "❌"})