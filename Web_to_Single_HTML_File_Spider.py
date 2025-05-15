import hashlib
from concurrent.futures import ProcessPoolExecutor

import fasttext
FASTTEXT_MODEL = fasttext.load_model("lid.176.bin")

def is_english_fasttext(text):
    try:
        prediction = FASTTEXT_MODEL.predict(text.strip().replace("\n", " ")[:1000])
        return prediction[0][0] == "__label__en"
    except:
        return False

def content_hash(text):
    normalized = text.strip().lower()
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()

def analyze_page(page_data):
    url, text = page_data
    if not is_english_fasttext(text):
        return None
    h = content_hash(text)
    return (h, url, text)

def filter_unique_english_pages(page_contents):
    with ProcessPoolExecutor(max_workers=8) as executor:
        results = list(executor.map(analyze_page, page_contents))

    seen_hashes = set()
    unique_pages = []

    for result in results:
        if not result:
            continue
        h, url, text = result
        if h not in seen_hashes:
            seen_hashes.add(h)
            unique_pages.append((url, text))
    return unique_pages
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, parse_qs
import os
from langdetect import detect, LangDetectException
from collections import Counter
import xml.etree.ElementTree as ET
import hashlib
from tqdm import tqdm

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

def is_likely_english_url(url, domain):
    """
    Check if a URL is likely to point to English content based on URL patterns.
    Returns: 
        - True: URL is likely English
        - False: URL is likely non-English
        - None: Cannot determine from URL alone
    """
    parsed = urlparse(url)
    path = parsed.path.strip('/')
    path_parts = path.split('/')
    netloc_parts = parsed.netloc.split('.')
    
    # Check for language subdomain patterns (en.example.com, english.example.com)
    if netloc_parts[0] in ['en', 'eng', 'english']:
        return True
    elif netloc_parts[0] in ['es', 'fr', 'de', 'it', 'ru', 'zh', 'ja', 'ko', 'pt', 'ar', 'nl', 
                         'sv', 'da', 'no', 'fi', 'pl', 'tr', 'cs', 'hu', 'th', 'el', 'he', 
                         'id', 'vi', 'uk', 'hi', 'espanol', 'francais', 'deutsch']:
        return False
    
    # Check for language in path patterns (/en/, /en-us/, /english/)
    if path_parts and path_parts[0] in ['en', 'eng', 'english', 'en-us', 'en-gb', 'en-au', 'en-ca']:
        return True
    elif path_parts and path_parts[0] in ['es', 'fr', 'de', 'it', 'ru', 'zh', 'ja', 'ko', 'pt', 'ar', 'nl', 
                                      'sv', 'da', 'no', 'fi', 'pl', 'tr', 'cs', 'hu', 'th', 'el', 'he', 
                                      'id', 'vi', 'uk', 'hi', 'es-mx', 'fr-ca', 'pt-br']:
        return False
    
    # Check for language query parameters (?lang=en, ?locale=en_US)
    query_params = parse_qs(parsed.query)
    lang_params = query_params.get('lang', []) + query_params.get('locale', []) + query_params.get('language', [])
    
    for param in lang_params:
        param = param.lower()
        if param.startswith('en') or param == 'english':
            return True
        elif param in ['es', 'fr', 'de', 'it', 'ru', 'zh', 'ja', 'ko', 'pt', 'ar', 'nl', 
                   'sv', 'da', 'no', 'fi', 'pl', 'tr', 'cs', 'hu', 'th', 'el', 'he', 
                   'id', 'vi', 'uk', 'hi']:
            return False
    
    # If domain ends with country TLD that typically uses English
    english_tlds = ['.us', '.uk', '.ca', '.au', '.nz', '.ie', '.za']
    for tld in english_tlds:
        if parsed.netloc.endswith(tld):
            return True
    
    # Non-English country TLDs
    non_english_tlds = ['.mx', '.es', '.fr', '.de', '.it', '.ru', '.cn', '.jp', '.kr', '.br', '.pt', 
                     '.sa', '.nl', '.se', '.dk', '.no', '.fi', '.pl', '.tr', '.cz', '.hu', '.th', 
                     '.gr', '.il', '.id', '.vn', '.ua', '.in']
    for tld in non_english_tlds:
        if parsed.netloc.endswith(tld) and not parsed.netloc.endswith('.com' + tld):
            return False
    
    # Check for common patterns in file names
    if path:
        filename = path_parts[-1] if path_parts else ""
        if '-en.' in filename or '_en.' in filename or '-english.' in filename:
            return True
        elif any(f'-{lang}.' in filename or f'_{lang}.' in filename 
                for lang in ['es', 'fr', 'de', 'it', 'ru', 'zh', 'ja', 'ko', 'pt']):
            return False
            
    # Cannot determine from URL alone
    return None

def get_homepage_links(url, domain):
    """Get all unique content links from homepage"""
    visited = set()
    content_links = []
    
    try:
        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.text, 'html5lib')
        
        for link in soup.find_all('a', href=True):
            href = urljoin(url, link['href'])
            if is_valid_url(href, domain) and href not in visited and not should_skip_url(href):
                # Pre-filter URLs based on language patterns
                if is_likely_english_url(href, domain) is not False:
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
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                return url
        except requests.RequestException:
            continue

    return None

def parse_sitemap(sitemap_url):
    response = requests.get(sitemap_url, timeout=10)
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
                # Also check hreflang tags if they exist
                url_elem = url.getparent() if hasattr(url, 'getparent') else None
                if url_elem is not None:
                    hreflang_tags = url_elem.findall('.//sm:link', namespaces)
                    is_english_page = False
                    has_hreflang = len(hreflang_tags) > 0
                    
                    for hreflang in hreflang_tags:
                        if 'hreflang' in hreflang.attrib and hreflang.attrib['hreflang'].startswith('en'):
                            is_english_page = True
                            break
                    
                    # Only skip if we have hreflang tags and none are English
                    if has_hreflang and not is_english_page:
                        continue
                
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
    filtered_by_url = 0
    content_hashes = set()
    
    # Track language determination statistics
    url_pattern_detected_english = 0
    url_pattern_detected_non_english = 0
    content_detected_english = 0
    content_detected_non_english = 0
    html_tag_detected_english = 0
    html_tag_detected_non_english = 0

    if use_existing_sitemap and not homepage_only:
        sitemap_url = find_sitemap(domain)
        if sitemap_url:
            print(f"Using existing sitemap: {sitemap_url}")
            to_visit = parse_sitemap(sitemap_url)
            print(f"Found {len(to_visit)} URLs in sitemap (after filtering out multimedia files)")
            
            # Pre-filter URLs based on language patterns
            filtered_to_visit = []
            print("Pre-filtering URLs based on language patterns...")
            for url in tqdm(to_visit, desc="Filtering URLs", unit="url"):
                url_language = is_likely_english_url(url, domain)
                if url_language is False:  # URL is definitely not English
                    filtered_by_url += 1
                    continue
                filtered_to_visit.append(url)
            
            print(f"Filtered out {filtered_by_url} likely non-English URLs based on URL patterns")
            to_visit = filtered_to_visit
        else:
            print("No sitemap found. Falling back to manual spidering.")

    # Create a progress bar for the main processing loop
    total_urls = len(to_visit)
    print(f"\nProcessing {total_urls} URLs...")
    
    # Create progress bar
    pbar = tqdm(total=total_urls, desc="Processing pages", unit="page")
    processed_count = 0
    
    while to_visit:
        current_url = to_visit.pop(0)
        if current_url in visited:
            pbar.update(1)
            processed_count += 1
            continue

        visited.add(current_url)
        
        # Instead of printing each URL, update progress bar description occasionally
        if processed_count % 10 == 0:
            remaining = len(to_visit)
            pbar.set_description(f"Processing pages ({remaining} remaining)")
        
        if should_skip_url(current_url):
            # Update silent counter without verbose output
            skipped_files += 1
            pbar.update(1)
            processed_count += 1
            continue
            
        # Check URL pattern for language before downloading
        url_language = is_likely_english_url(current_url, domain)
        if url_language is False:  # URL is definitely not English
            non_english_pages += 1
            url_pattern_detected_non_english += 1
            filtered_by_url += 1
            pbar.update(1)
            processed_count += 1
            continue
        elif url_language is True:
            url_pattern_detected_english += 1

        try:
            response = requests.get(current_url, timeout=10, allow_redirects=True)
            content_type = response.headers.get('Content-Type', '').lower()
            
            if 'text/html' not in content_type:
                skipped_files += 1
                pbar.update(1)
                processed_count += 1
                continue

            soup = BeautifulSoup(response.text, 'html5lib')
            
            # Only check HTML language tags if URL pattern didn't definitively say it's English
            is_english_page = True  # Default to True if we already know from URL pattern
            
            if url_language is not True:  # If URL pattern didn't confirm English
                # Check for language meta tags
                html_lang = soup.find('html', attrs={'lang': True})
                meta_lang = soup.find('meta', attrs={'http-equiv': 'content-language'}) or \
                            soup.find('meta', attrs={'name': 'language'})
                            
                lang_value = None
                if html_lang and html_lang.get('lang'):
                    lang_value = html_lang.get('lang').lower().split('-')[0]
                elif meta_lang and meta_lang.get('content'):
                    lang_value = meta_lang.get('content').lower().split('-')[0]
                    
                if lang_value:
                    if lang_value != 'en':
                        non_english_pages += 1
                        html_tag_detected_non_english += 1
                        pbar.update(1)
                        processed_count += 1
                        continue
                    else:
                        html_tag_detected_english += 1
                        is_english_page = True
                else:
                    # Only perform content language detection if we couldn't determine from URL or HTML tags
                    text = soup.get_text()
                    if is_english(text):
                        content_detected_english += 1
                        is_english_page = True
                    else:
                        content_detected_non_english += 1
                        is_english_page = False
            
            if is_english_page:
                # Generate a hash of the page content to check for duplicates
                text = soup.get_text()
                content_hash = hashlib.md5(text.encode()).hexdigest()
                
                if content_hash not in content_hashes:
                    content_hashes.add(content_hash)
                    english_pages.append(current_url)
                    sitemap.append((current_url, soup))
                    
                    # If we're spidering and finding new links
                    if not use_existing_sitemap and not homepage_only:
                        new_links = []
                        for link in soup.find_all('a', href=True):
                            href = urljoin(current_url, link['href'])
                            if is_valid_url(href, domain) and href not in visited and not should_skip_url(href):
                                # Pre-filter new URLs
                                if is_likely_english_url(href, domain) is not False:
                                    new_links.append(href)
                        
                        # If we found new links, add them and update the progress bar total
                        if new_links:
                            to_visit.extend(new_links)
                            # Update the total in the progress bar
                            pbar.total += len(new_links)
                            total_urls += len(new_links)
                            pbar.refresh()
            else:
                non_english_pages += 1

        except Exception as e:
            # Just log errors to the progress bar's display
            pbar.write(f"Error processing {current_url}: {str(e)}")
        
        # Update progress bar
        pbar.update(1)
        processed_count += 1
    
    # Close the progress bar
    pbar.close()

    print(f"\nSitemap creation complete.")
    print(f"Total unique English pages to be saved: {len(english_pages)}")
    print(f"Total non-English pages skipped: {non_english_pages}")
    print(f"Total files skipped based on extension or content type: {skipped_files}")
    print(f"Total pages filtered by URL pattern before processing: {filtered_by_url}")
    print(f"\nLanguage Detection Statistics:")
    print(f"URLs detected as English by pattern: {url_pattern_detected_english}")
    print(f"URLs detected as non-English by pattern: {url_pattern_detected_non_english}")
    print(f"Pages detected as English by HTML/meta tags: {html_tag_detected_english}")
    print(f"Pages detected as non-English by HTML/meta tags: {html_tag_detected_non_english}")
    print(f"Pages requiring full content language detection: {content_detected_english + content_detected_non_english}")
    print(f"  - Confirmed English by content: {content_detected_english}")
    print(f"  - Determined non-English by content: {content_detected_non_english}")

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
    # Create progress bar for content extraction
    for i, (url, soup) in enumerate(tqdm(sitemap, desc="Extracting content", unit="page")):
        content = extract_formatted_content(soup)
        if content:
            all_content.append(content)
    
    print("\nRemoving common elements (like menus and footers)...")
    # We don't need a progress bar here since it's a single operation
    cleaned_content = remove_common_elements(all_content)

    print("Combining content...")
    combined_content = ''.join(str(content) for content in cleaned_content)

    print("Saving content...")
    save_chunks(combined_content, output_file)
    
    return len(all_content)
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
