from pypdf import PdfReader
import pandas as pd
import streamlit as st

# Extracts text from pdfs
def txt_extract(file):
    pdf = PdfReader(file)
    for page in pdf.pages:
        txt = page.extract_text() or ""
        return txt

r = txt_extract("ghjhgjhg.pdf")
print(r)