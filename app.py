import streamlit as st
from pathlib import Path
import tempfile

from converter import convert_docx_to_pdf, convert_pdf_to_docx

st.set_page_config(page_title="ResConv – Resume Converter", page_icon="📄")

st.title("📄 ResConv – Resume Converter")
st.write("Upload a **DOCX** or **PDF** resume and convert it instantly.")

uploaded = st.file_uploader("Upload your resume", type=["pdf", "docx"])

if uploaded:
    src_suffix = Path(uploaded.name).suffix.lower()
    target_ext = ".pdf" if src_suffix == ".docx" else ".docx"

    st.info(f"Detected **{src_suffix[1:].upper()}** → convert to **{target_ext[1:].upper()}**")

    if st.button("Convert"):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)

            # Save uploaded file
            src_path = tmpdir / uploaded.name
            src_path.write_bytes(uploaded.getvalue())

            # Output file path
            out_path = src_path.with_suffix(target_ext)

            # Run conversion using your converter.py logic
            if target_ext == ".pdf":
                convert_docx_to_pdf(src_path, out_path)
            else:
                convert_pdf_to_docx(src_path, out_path)

            # Read converted file
            result_data = out_path.read_bytes()

        st.success("✅ Conversion complete!")
        st.download_button(
            "Download converted file",
            result_data,
            file_name=out_path.name,
        )
