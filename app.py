import streamlit as st
import google.generativeai as genai
import PyPDF2
import datetime

# Load API key securely from Streamlit secrets
API_KEY = st.secrets["API_KEY"]
genai.configure(api_key=API_KEY)

st.set_page_config(page_title="AI PDF Summarizer", page_icon="🤖")

# Improved, readable CSS – light background with dark text
st.markdown("""
<style>
    .stApp { background-color: #fafafa; }
    h1, h2, h3, h4, h5, h6, p, .stMarkdown { color: #111111 !important; }
    .stButton>button { background-color: #4CAF50; color: white; border-radius: 8px; }
    .stTextInput>div>div>input { border-radius: 10px; background-color: white; color: black; }
    .stSelectbox label, .stFileUploader label { color: #111111; }
    .stProgress > div > div { background-color: #4CAF50; }
</style>
""", unsafe_allow_html=True)

st.title("📄 AI PDF Summarizer")
st.write("Upload one or more PDFs – get summaries, ask questions, and download results!")

model_options = {
    "Fast & Light": "models/gemini-3.1-flash-lite-preview",
    "Balanced": "models/gemini-3.1-pro-preview",
    "Experimental (Audio)": "models/gemini-2.5-flash-native-audio-preview-12-2025"
}
selected_model_name = st.selectbox("Choose AI model", list(model_options.keys()))
selected_model = model_options[selected_model_name]
model = genai.GenerativeModel(selected_model)

uploaded_files = st.file_uploader("Choose PDF files", type="pdf", accept_multiple_files=True)

def summarize_long_text(text, model, max_chunk=30000):
    chunks = [text[i:i+max_chunk] for i in range(0, len(text), max_chunk)]
    if len(chunks) == 1:
        prompt = f"Summarize the following document in 3-5 bullet points:\n\n{text[:max_chunk]}"
        return model.generate_content(prompt).text
    else:
        chunk_summaries = []
        for i, chunk in enumerate(chunks):
            prompt = f"Summarize this part (part {i+1}/{len(chunks)}) in 3-5 bullet points:\n\n{chunk}"
            chunk_summaries.append(model.generate_content(prompt).text)
        combined = "\n\n".join(chunk_summaries)
        final_prompt = f"Combine these part-summaries into one coherent summary (5–8 bullet points):\n\n{combined}"
        return model.generate_content(final_prompt).text

if uploaded_files:
    for uploaded_file in uploaded_files:
        st.divider()
        st.subheader(f"📁 {uploaded_file.name}")
        with st.spinner(f"Reading {uploaded_file.name}..."):
            pdf_reader = PyPDF2.PdfReader(uploaded_file)
            text = ""
            progress_bar = st.progress(0)
            for i, page in enumerate(pdf_reader.pages):
                page_text = page.extract_text()
                if page_text:
                    text += page_text
                progress_bar.progress((i + 1) / len(pdf_reader.pages))
            progress_bar.empty()
        if not text.strip():
            st.error("No text could be extracted from this PDF. It might be a scanned image or empty.")
            continue
        st.success(f"✅ Loaded {len(text)} characters")
        try:
            with st.spinner("Generating summary..."):
                summary = summarize_long_text(text, model)
            st.subheader("📌 Summary")
            st.write(summary)
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_filename = uploaded_file.name.replace(".pdf", "")[:30]
            download_filename = f"{safe_filename}_summary_{timestamp}.txt"
            st.download_button(
                label="📥 Download Summary",
                data=summary,
                file_name=download_filename,
                mime="text/plain",
                key=f"download_{uploaded_file.name}"
            )
            with st.expander("❓ Ask a question about this document"):
                question = st.text_input("Your question", key=f"q_{uploaded_file.name}")
                if question:
                    with st.spinner("Thinking..."):
                        q_text = text[:30000]
                        q_prompt = f"Based on the document, answer concisely:\n\n{q_text}\n\nQuestion: {question}"
                        answer = model.generate_content(q_prompt).text
                        st.write("**Answer:**", answer)
        except Exception as e:
            st.error(f"Error: {e}")
else:
    st.info("👆 Upload one or more PDF files to begin.")
