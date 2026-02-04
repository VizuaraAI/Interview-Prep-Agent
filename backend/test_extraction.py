from PyPDF2 import PdfReader

pdf_path = "/Users/rajat/Desktop/Vizuara RAG Demo Nutri Chatbot/Himanshu Kumar Resume - Himanshu Kumar.pdf"
reader = PdfReader(pdf_path)

# Extract first 500 characters to see the header format
text = ""
for page in reader.pages:
    text += page.extract_text() + "\n"

print("First 800 characters of extracted text:")
print("=" * 60)
print(text[:800])
print("=" * 60)
