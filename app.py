import streamlit as st
from html import escape
import re
from retrieval.search import search_and_respond
from config import GROQ_API_KEY, GROQ_MODEL

# Fungsi tambahan untuk konversi Markdown ke HTML
def markdown_to_html(text):
    text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)
    text = re.sub(r'\*(.*?)\*', r'<i>\1</i>', text)
    return text

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
    
    /* 🔧 PERBAIKAN INPUT CHAT - Menghilangkan double border */
    /* Container utama untuk input chat */
    .stChatFloatingInputContainer,
    [data-testid="stChatFloatingInputContainer"],
    .st-emotion-cache-1r4qj4y,
    .st-emotion-cache-1kg1ch6,
    .st-emotion-cache-8qqqw5 {
        background-color: #121212 !important;
        border-top: 1px solid #333333 !important;
        padding: 10px !important;
    }
    
    /* Input container wrapper - HILANGKAN BORDER GANDA */
    .stChatInputContainer,
    [data-testid="stChatInputContainer"],
    .stChatInput,
    [data-testid="stChatInput"] {
        background-color: transparent !important;
        max-width: 900px !important;
        margin: 0 auto !important;
        border: none !important;
        box-shadow: none !important;
        outline: none !important;
    }
    
    /* Div pembungkus input - HILANGKAN SEMUA BORDER */
    .stChatInput > div,
    [data-testid="stChatInput"] > div,
    .stChatInput > div > div,
    [data-testid="stChatInput"] > div > div,
    .stChatInput div[data-baseweb="base-input"],
    [data-testid="stChatInput"] div[data-baseweb="base-input"] {
        background-color: transparent !important;
        border: none !important;
        box-shadow: none !important;
        outline: none !important;
    }
    
    /* Input field itu sendiri - SINGLE BORDER SAJA */
    .stChatInput input,
    [data-testid="stChatInputTextArea"],
    .stChatInput textarea,
    input[data-testid="stChatInputTextArea"],
    .st-emotion-cache-10oheav input,
    .st-emotion-cache-yfdjkx input,
    .st-emotion-cache-w1wxsf input,
    .st-emotion-cache-1q3a02i input,
    [data-baseweb="input"] input,
    [data-baseweb="textarea"] textarea {
        background-color: #2a2a2a !important;
        color: #ffffff !important;
        border: 1px solid #444444 !important;
        border-radius: 25px !important;
        padding: 12px 50px 12px 15px !important;
        font-size: 15px !important;
        box-shadow: none !important;
        outline: none !important;
        caret-color: white !important;
    }
    
    /* Input placeholder */
    .stChatInput input::placeholder,
    [data-testid="stChatInputTextArea"]::placeholder,
    input::placeholder,
    textarea::placeholder {
        color: #aaaaaa !important;
        opacity: 0.7 !important;
    }
    
    /* Input focus state */
    .stChatInput input:focus,
    [data-testid="stChatInputTextArea"]:focus,
    input:focus,
    textarea:focus {
        border-color: #5a5a5a !important;
        box-shadow: 0 0 0 1px #5a5a5a !important;
        outline: none !important;
        background-color: #2a2a2a !important;
    }
    
    /* Bottom footer area */
    footer, 
    .st-emotion-cache-17lntkn, 
    .st-emotion-cache-7ym5gk,
    [data-testid="stFooter"] {
        background-color: #121212 !important;
        border-color: #3a3a3a !important;
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
        overflow-wrap: break-word !important;
        word-break: break-word !important;
        white-space: pre-wrap !important;
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
    
    /* Send button in chat - enhanced styling */
    button[kind="primaryFormSubmit"],
    .st-emotion-cache-13e17gk,
    button[data-testid="stChatMessageSubmitButton"],
    button[aria-label="Send message"] {
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
        border: none !important;
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
    
    /* Streamlit main page top margin fix */
    .main > div:first-of-type {
        padding-top: 1rem !important;
    }
    
    /* Streamlit top header removal */
    header[data-testid="stHeader"] {
        display: none !important;
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
        background-color: #121212 !important;
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

            # ⬇️ Konversi ke HTML dengan bold/italic support
            escaped_answer = escape(answer)
            html_answer = markdown_to_html(escaped_answer).replace('\n', '<br>')
            formatted_answer = f'<div class="assistant-message">{html_answer}</div>'

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