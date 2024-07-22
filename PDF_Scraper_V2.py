import os
import requests
import hashlib
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup

def get_file_hash(content):
    file_hash = hashlib.md5()
    file_hash.update(content)
    return file_hash.hexdigest()

def spider_domain(url):
    visited = set()
    to_visit = [url]
    pdf_urls = set()

    while to_visit:
        current_url = to_visit.pop(0)
        if current_url in visited:
            continue

        print(f"Visiting: {current_url}")
        visited.add(current_url)

        try:
            response = requests.get(current_url)
            soup = BeautifulSoup(response.text, 'html.parser')

            for link in soup.find_all('a'):
                href = link.get('href')
                if href:
                    full_url = urljoin(current_url, href)
                    if urlparse(full_url).netloc == urlparse(url).netloc:
                        if full_url.lower().endswith('.pdf'):
                            pdf_urls.add(full_url)
                        elif full_url not in visited:
                            to_visit.append(full_url)

        except Exception as e:
            print(f"Error processing {current_url}: {str(e)}")

    return pdf_urls

def download_pdfs(pdf_urls, folder):
    downloaded_hashes = set()
    total_pdfs = len(pdf_urls)
    downloaded_count = 0

    for i, pdf_url in enumerate(pdf_urls, 1):
        try:
            response = requests.get(pdf_url)
            content = response.content
            file_hash = get_file_hash(content)

            if file_hash not in downloaded_hashes:
                filename = os.path.join(folder, pdf_url.split('/')[-1])
                with open(filename, 'wb') as f:
                    f.write(content)
                downloaded_hashes.add(file_hash)
                downloaded_count += 1
                print(f"Downloaded ({downloaded_count}/{total_pdfs}, {downloaded_count/total_pdfs:.1%}): {filename}")
            else:
                print(f"Skipped duplicate ({i}/{total_pdfs}, {i/total_pdfs:.1%}): {pdf_url}")

        except Exception as e:
            print(f"Error downloading {pdf_url}: {str(e)}")

        print(f"Progress: {i}/{total_pdfs} ({i/total_pdfs:.1%}) PDFs processed")

    return downloaded_count

if __name__ == "__main__":
    domain_url = input("Enter the URL of the domain to spider: ")
    save_folder = input("Enter the name of the folder to save PDFs: ")

    if not os.path.exists(save_folder):
        os.makedirs(save_folder)

    print("\nStep 1: Spidering the domain...")
    pdf_urls = spider_domain(domain_url)
    print(f"\nSpidering completed. Found {len(pdf_urls)} unique PDF URLs.")

    print("\nStep 2: Downloading PDFs...")
    downloaded_count = download_pdfs(pdf_urls, save_folder)

    print(f"\nDownload completed. Downloaded {downloaded_count} unique PDFs out of {len(pdf_urls)} found.")
    print(f"Download efficiency: {downloaded_count/len(pdf_urls):.1%}")