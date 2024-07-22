import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

def get_domain(url):
    return urlparse(url).netloc

def download_pdf(url, folder):
    try:
        response = requests.get(url, stream=True)
        if response.status_code == 200 and response.headers['Content-Type'] == 'application/pdf':
            filename = os.path.join(folder, url.split('/')[-1])
            total_size = int(response.headers.get('content-length', 0))
            block_size = 1024  # 1 KB
            downloaded = 0

            with open(filename, 'wb') as f:
                for data in response.iter_content(block_size):
                    size = f.write(data)
                    downloaded += size
                    if total_size > 0:
                        percent = int(50 * downloaded / total_size)
                        mb_downloaded = downloaded / (1024 * 1024)
                        mb_total = total_size / (1024 * 1024)
                        print(f"\rDownloading {filename}: [{'#' * percent}{'.' * (50-percent)}] {percent*2}% ({mb_downloaded:.2f}MB / {mb_total:.2f}MB)", end='', flush=True)
            print()  # New line after download completes
            print(f"Downloaded: {filename}")
        else:
            print(f"Failed to download: {url}")
    except Exception as e:
        print(f"Error downloading {url}: {e}")

def spider_for_pdfs(start_url, output_folder):
    domain = get_domain(start_url)
    visited = set()
    to_visit = [start_url]

    while to_visit:
        current_url = to_visit.pop(0)
        if current_url in visited:
            continue

        print(f"Visiting: {current_url}")
        visited.add(current_url)

        try:
            response = requests.get(current_url)
            soup = BeautifulSoup(response.text, 'html.parser')

            # Check for PDF links
            for link in soup.find_all('a', href=True):
                href = urljoin(current_url, link['href'])
                if href.lower().endswith('.pdf'):
                    download_pdf(href, output_folder)
                elif get_domain(href) == domain and href not in visited:
                    to_visit.append(href)
        except Exception as e:
            print(f"Error processing {current_url}: {e}")

if __name__ == "__main__":
    start_url = "https://flotron.com"  # Replace with your target domain
    output_folder = "downloaded_pdfs"  # Folder to save the PDFs
    
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    
    spider_for_pdfs(start_url, output_folder)