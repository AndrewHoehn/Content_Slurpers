import os
import PyPDF2
import re

def extract_text_from_pdf(pdf_path):
    with open(pdf_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        text = ''
        for page in reader.pages:
            text += page.extract_text() + '\n\n'
    return text

def process_text(text, pdf_path):
    text = re.sub(r'\n\s*\n', '\n\n', text)
    text = text.replace('\r\n', '\n')
    text = f"{'=' * 80}\n{os.path.basename(pdf_path)}\n{'=' * 80}\n\n{text}\n\n"
    return text

def spider_directory(directory):
    all_text = ""
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.lower().endswith('.pdf'):
                pdf_path = os.path.join(root, file)
                print(f"Processing: {pdf_path}")
                
                try:
                    pdf_text = extract_text_from_pdf(pdf_path)
                    processed_text = process_text(pdf_text, pdf_path)
                    all_text += processed_text
                except Exception as e:
                    print(f"Error processing {pdf_path}: {str(e)}")
    
    return all_text

def save_text_to_file(text, output_file, max_size_mb=5):
    max_size_bytes = max_size_mb * 1024 * 1024
    text_bytes = text.encode('utf-8')
    total_chunks = -(-len(text_bytes) // max_size_bytes)  # Ceiling division
    
    for i in range(total_chunks):
        chunk_start = i * max_size_bytes
        chunk_end = (i + 1) * max_size_bytes
        chunk = text_bytes[chunk_start:chunk_end].decode('utf-8', errors='ignore')
        
        if total_chunks > 1:
            chunk_file = f"{os.path.splitext(output_file)[0]}_{i+1}{os.path.splitext(output_file)[1]}"
        else:
            chunk_file = output_file
        
        with open(chunk_file, 'w', encoding='utf-8') as file:
            file.write(chunk)
        
        print(f"Chunk {i+1} saved to {chunk_file}")

if __name__ == "__main__":
    directory_to_spider = input("Enter the directory path to spider for PDFs: ")
    output_file = input("Enter the output file name (e.g., output.txt): ")
    
    combined_text = spider_directory(directory_to_spider)
    save_text_to_file(combined_text, output_file)
    
    print(f"Text extraction complete. Output saved to {output_file} (and possibly additional numbered files)")