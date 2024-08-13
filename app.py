import streamlit as st
from transformers import MarianMTModel, MarianTokenizer
import fitz  # PyMuPDF
import os

# Load translation model and tokenizer
model_name = 'Helsinki-NLP/opus-mt-en-de'
tokenizer = MarianTokenizer.from_pretrained(model_name)
model = MarianMTModel.from_pretrained(model_name)

# Function to extract text and formatting from PDF
def extract_text_and_format(file_path):
    document = fitz.open(file_path)
    pages = []
    for page_num in range(len(document)):
        page = document.load_page(page_num)
        blocks = page.get_text("dict", flags=11)["blocks"]
        pages.append(blocks)
    return pages

# Function to translate text
def translate_text(text, tokenizer, model):
    tokenized = tokenizer([text], return_tensors='pt', padding=True)
    translated_tokens = model.generate(**tokenized, max_length=512)
    translated_text = tokenizer.decode(translated_tokens[0], skip_special_tokens=True)
    return translated_text

# Function to normalize color
def normalize_color(color):
    if isinstance(color, (tuple, list)):
        return tuple(c / 255.0 if c > 1 else c for c in color)
    return color / 255.0 if color > 1 else color

# Function to create translated PDF
def create_translated_pdf(original_file_path, translated_data, output_file_path):
    document = fitz.open(original_file_path)
    new_document = fitz.open()
    for page_num in range(len(document)):
        page = document.load_page(page_num)
        new_page = new_document.new_page(width=page.rect.width, height=page.rect.height)
        for block in translated_data[page_num]:
            if block["type"] == 0:
                for line in block["lines"]:
                    for span in line["spans"]:
                        fontname = "helv"
                        fontsize = span.get("size")
                        color = span.get("color")
                        if fontsize:
                            new_page.insert_text(
                                fitz.Point(span["bbox"][0], span["bbox"][1]),
                                span["text"],
                                fontname=fontname,
                                fontsize=fontsize,
                                color=normalize_color(color)
                            )
    new_document.save(output_file_path)

# Streamlit app
st.title("PDF Translation App")

uploaded_file = st.file_uploader("Choose a PDF file", type="pdf")

if uploaded_file is not None:
    with open("uploaded_file.pdf", "wb") as f:
        f.write(uploaded_file.getbuffer())

    st.write("Translating PDF...")
    extracted_data = extract_text_and_format("uploaded_file.pdf")

    translated_data = []
    for page in extracted_data:
        translated_page = []
        for block in page:
            if block["type"] == 0:
                for line in block["lines"]:
                    for span in line["spans"]:
                        span["text"] = translate_text(span["text"], tokenizer, model)
            translated_page.append(block)
        translated_data.append(translated_page)

    output_pdf_path = 'translated_pdf.pdf'
    create_translated_pdf("uploaded_file.pdf", translated_data, output_pdf_path)

    with open(output_pdf_path, "rb") as f:
        st.download_button(
            label="Download Translated PDF",
            data=f,
            file_name=output_pdf_path,
            mime="application/pdf"
        )

    # Clean up uploaded file after processing
    os.remove("uploaded_file.pdf")
