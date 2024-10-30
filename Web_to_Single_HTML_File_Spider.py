import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import os
from langdetect import detect, LangDetectException
from collections import Counter
import xml.etree.ElementTree as ET
import hashlib

# List of file extensions to skip
SKIP_EXTENSIONS = {
    '.pdf', '.mp3', '.mp4', '.avi', '.mov', '.wmv', '.flv', '.wav',
    '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp',
    '.zip', '.rar', '.7z', '.tar', '.gz', '.exe', '.dmg', '.iso'
}

def is_valid_url(url, domain):
    parsed = urlparse(url)
    return bool(parsed.netloc) and parsed.netloc.endswith(domain)

def should_skip_url(url):
    parsed = urlparse(url)
    ext = os.path.splitext(parsed.path)[1].lower()
    return ext in SKIP_EXTENSIONS

def get_homepage_links(url, domain):
    """Get all unique content links from homepage"""
    visited = set()
    content_links = []
    
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html5lib')
        
        for link in soup.find_all('a', href=True):
            href = urljoin(url, link['href'])
            if is_valid_url(href, domain) and href not in visited and not should_skip_url(href):
                content_links.append(href)
                visited.add(href)
                
        return list(set(content_links))  # Remove any duplicates
    except Exception as e:
        print(f"Error processing homepage: {str(e)}")
        return []

def find_sitemap(domain):
    sitemap_urls = [
        f"https://{domain}/sitemap.xml",
        f"https://{domain}/sitemap_index.xml",
        f"https://{domain}/sitemap-index.xml",
        f"https://{domain}/sitemapindex.xml",
        f"https://{domain}/sitemap.php",
        f"https://{domain}/sitemap",
    ]

    for url in sitemap_urls:
        try:
            response = requests.get(url)
            if response.status_code == 200:
                return url
        except requests.RequestException:
            continue

    return None

def parse_sitemap(sitemap_url):
    response = requests.get(sitemap_url)
    root = ET.fromstring(response.content)

    # Namespace dictionary
    namespaces = {
        'sm': 'http://www.sitemaps.org/schemas/sitemap/0.9'
    }

    urls = []

    # Check if it's a sitemap index
    sitemaps = root.findall('.//sm:sitemap', namespaces)
    if sitemaps:
        print(f"Found a sitemap index with {len(sitemaps)} sitemaps")
        for sitemap in sitemaps:
            sitemap_loc = sitemap.find('sm:loc', namespaces)
            if sitemap_loc is not None:
                urls.extend(parse_sitemap(sitemap_loc.text))
    else:
        # It's a regular sitemap
        for url in root.findall('.//sm:url/sm:loc', namespaces):
            if not should_skip_url(url.text):
                urls.append(url.text)

    return urls

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

def create_sitemap(start_url, use_existing_sitemap=False, homepage_only=False, homepage_links=None):
    domain = urlparse(start_url).netloc
    visited = set()
    to_visit = homepage_links if homepage_only else [start_url]
    sitemap = []
    english_pages = []
    non_english_pages = 0
    skipped_files = 0
    content_hashes = set()

    if use_existing_sitemap and not homepage_only:
        sitemap_url = find_sitemap(domain)
        if sitemap_url:
            print(f"Using existing sitemap: {sitemap_url}")
            to_visit = parse_sitemap(sitemap_url)
            print(f"Found {len(to_visit)} URLs in sitemap (after filtering out multimedia files)")
        else:
            print("No sitemap found. Falling back to manual spidering.")

    while to_visit:
        current_url = to_visit.pop(0)
        if current_url in visited:
            continue

        visited.add(current_url)
        print(f"Mapping: {current_url}")

        if should_skip_url(current_url):
            print("Skipping file based on extension")
            skipped_files += 1
            continue

        try:
            response = requests.get(current_url, allow_redirects=True)
            content_type = response.headers.get('Content-Type', '').lower()
            
            if 'text/html' not in content_type:
                print(f"Skipping non-HTML content: {content_type}")
                skipped_files += 1
                continue

            soup = BeautifulSoup(response.text, 'html5lib')
            text = soup.get_text()

            if is_english(text):
                # Generate a hash of the page content
                content_hash = hashlib.md5(text.encode()).hexdigest()
                
                if content_hash not in content_hashes:
                    content_hashes.add(content_hash)
                    english_pages.append(current_url)
                    sitemap.append((current_url, soup))
                    print("Content is in English and unique. Adding to sitemap.")

                    if not use_existing_sitemap and not homepage_only:
                        for link in soup.find_all('a', href=True):
                            href = urljoin(current_url, link['href'])
                            if is_valid_url(href, domain) and href not in visited and not should_skip_url(href):
                                to_visit.append(href)
                else:
                    print("Duplicate content found. Skipping.")
            else:
                non_english_pages += 1
                print("Content is not in English. Skipping.")

        except Exception as e:
            print(f"Error processing {current_url}: {str(e)}")

    print(f"\nSitemap creation complete.")
    print(f"Total unique English pages to be saved: {len(english_pages)}")
    print(f"Total non-English pages skipped: {non_english_pages}")
    print(f"Total files skipped based on extension or content type: {skipped_files}")

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
    spider_type = input("Would you like to spider: \n1. The entire domain\n2. Only links from homepage\nEnter 1 or 2: ")
    
    domain = urlparse(start_url).netloc
    use_existing_sitemap = False
    
    if spider_type == "2":
        print(f"\nAnalyzing homepage: {start_url}")
        homepage_links = get_homepage_links(start_url, domain)
        print(f"Found {len(homepage_links)} unique content links on homepage")
        
        # Create artificial sitemap from homepage links
        sitemap = create_sitemap(start_url, use_existing_sitemap=False, homepage_only=True, homepage_links=homepage_links)
    else:
        sitemap_url = find_sitemap(urlparse(start_url).netloc)
        if sitemap_url:
            print(f"Sitemap found at: {sitemap_url}")
            use_sitemap = input("Would you like to use this sitemap instead of manually spidering the site? (y/n): ")
            use_existing_sitemap = use_sitemap.lower() == 'y'
        sitemap = create_sitemap(start_url, use_existing_sitemap)
    
    output_file = input("Enter the base filename to save the data (e.g., extracted_content): ")
    
    print("\nProcessing content...")
    process_content(sitemap, output_file)
    
    print("\nProcess complete.")

if __name__ == "__main__":
    main()
