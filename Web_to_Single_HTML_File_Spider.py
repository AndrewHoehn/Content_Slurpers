import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import os
from langdetect import detect, LangDetectException
from collections import Counter
import mimetypes

def is_valid_url(url, domain):
    parsed = urlparse(url)
    return bool(parsed.netloc) and parsed.netloc.endswith(domain)

def is_multimedia_file(url, content_type):
    # Check file extension
    _, ext = os.path.splitext(urlparse(url).path)
    if ext.lower() in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.mp4', '.avi', '.mov', '.wmv', '.flv', '.mp3', '.wav']:
        return True
    
    # Check MIME type
    mime_type, _ = content_type.split(';', 1) if ';' in content_type else (content_type, None)
    return mime_type.strip().lower().startswith(('image/', 'video/', 'audio/'))

def extract_formatted_content(soup):
    # Remove script, style, and nav elements
    for element in soup(["script", "style", "nav"]):
        element.decompose()
    
    # Extract the main content
    main_content = soup.find('main') or soup.find('body')
    
    if main_content:
        # Preserve only specific tags
        allowed_tags = ['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'b', 'strong', 'i', 'em', 'table', 'tr', 'td', 'th']
        for tag in main_content.find_all(True):
            if tag.name not in allowed_tags:
                tag.unwrap()
    
        # Convert table to simple format
        for table in main_content.find_all('table'):
            new_table = soup.new_tag('table')
            for row in table.find_all('tr'):
                new_row = soup.new_tag('tr')
                for cell in row.find_all(['td', 'th']):
                    new_cell = soup.new_tag('td')
                    new_cell.string = cell.get_text(strip=True)
                    new_row.append(new_cell)
                new_table.append(new_row)
            table.replace_with(new_table)
        
        return main_content
    return None

def is_english(text):
    try:
        return detect(text) == 'en'
    except LangDetectException:
        return False

def save_chunks(content, base_filename, chunk_size=5*1024*1024):
    chunk_number = 1
    start = 0
    while start < len(content):
        end = start + chunk_size
        chunk = content[start:end]
        
        if end < len(content):
            # Find the last closing tag
            last_tag = chunk.rfind('>')
            if last_tag != -1:
                end = start + last_tag + 1
                chunk = content[start:end]
        
        filename = f"{base_filename}_{chunk_number}.html"
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(f"<html><body>{chunk}</body></html>")
        
        print(f"Chunk {chunk_number} saved to {filename}")
        print(f"File size: {os.path.getsize(filename) / 1024:.2f} KB")
        
        start = end
        chunk_number += 1

def create_sitemap(start_url):
    domain = urlparse(start_url).netloc
    visited = set()
    to_visit = [start_url]
    sitemap = []
    english_pages = []
    non_english_pages = 0
    skipped_multimedia = 0

    while to_visit:
        current_url = to_visit.pop(0)
        if current_url in visited:
            continue

        visited.add(current_url)
        print(f"Mapping: {current_url}")

        try:
            response = requests.get(current_url, allow_redirects=True)
            content_type = response.headers.get('Content-Type', '').lower()
            
            if is_multimedia_file(current_url, content_type):
                print("Skipping multimedia file")
                skipped_multimedia += 1
                continue

            if 'text/html' not in content_type:
                print(f"Skipping non-HTML content: {content_type}")
                skipped_multimedia += 1
                continue

            soup = BeautifulSoup(response.text, 'html5lib')
            text = soup.get_text()

            if is_english(text):
                english_pages.append(current_url)
                sitemap.append((current_url, soup))
                print("Content is in English. Adding to sitemap.")

                for link in soup.find_all('a', href=True):
                    href = urljoin(current_url, link['href'])
                    if is_valid_url(href, domain) and href not in visited:
                        to_visit.append(href)
            else:
                non_english_pages += 1
                print("Content is not in English. Skipping.")

        except Exception as e:
            print(f"Error processing {current_url}: {str(e)}")

    print(f"\nSitemap creation complete.")
    print(f"Total English pages to be saved: {len(english_pages)}")
    print(f"Total non-English pages skipped: {non_english_pages}")
    print(f"Total multimedia files skipped: {skipped_multimedia}")

    return sitemap

def remove_common_elements(contents):
    # Convert BeautifulSoup objects to strings for comparison
    string_contents = [str(content) for content in contents]
    
    # Count occurrences of each line across all pages
    line_counter = Counter()
    for content in string_contents:
        lines = content.split('\n')
        line_counter.update(lines)
    
    # Identify common lines (appearing in more than 50% of pages)
    total_pages = len(string_contents)
    common_lines = set(line for line, count in line_counter.items() if count > total_pages * 0.5)
    
    # Remove common lines from each page's content
    cleaned_contents = []
    for content in contents:
        cleaned_lines = [line for line in str(content).split('\n') if line not in common_lines]
        cleaned_content = '\n'.join(cleaned_lines)
        cleaned_contents.append(BeautifulSoup(cleaned_content, 'html.parser'))
    
    return cleaned_contents

def process_content(sitemap, output_file):
    all_content = []
    total_pages = len(sitemap)

    print("Extracting content from pages...")
    for i, (url, soup) in enumerate(sitemap, 1):
        content = extract_formatted_content(soup)
        if content:
            all_content.append(content)
        progress = (i / total_pages) * 100
        print(f"Extracted content from page {i} of {total_pages} ({progress:.2f}% complete)")

    print("\nRemoving common elements (like menus and footers)...")
    cleaned_content = remove_common_elements(all_content)

    print("Combining content...")
    combined_content = ''.join(str(content) for content in cleaned_content)

    print("Saving content...")
    save_chunks(combined_content, output_file)

def main():
    start_url = input("Enter the domain to spider (e.g., https://example.com): ")
    output_file = input("Enter the base filename to save the data (e.g., extracted_content): ")

    print("\nCreating sitemap...")
    sitemap = create_sitemap(start_url)

    print("\nProcessing content...")
    process_content(sitemap, output_file)

    print("\nProcess complete.")

if __name__ == "__main__":
    main()
