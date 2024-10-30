# Content_Slurpers
A set of python tools useful for spidering websites and PDFs for text that can be easily loaded into custom GPTs or other LLMs. 

## Why? 
Tools like custom GPTs can be tremendously useful, but it's difficult to fill them with relevant data when that data comes from websites, and PDF files.  This set of tools can be used to: 

1) Spider a website for all its text content, and save that text content into a single HTML file that's (relatively) free of duplicate content.
2) Spider a website for all of its PDF files, and download those to your local machine.
3) Process all those individual PDF documents and convert them into a single text file that attempts to preserve useful formatting.

By using these together, you can get reasonably small files that can be uploaded to a custom GPT or other AI tool, to use for a variety of purposes. 



# Web_to_Single_HTML_File_Spider.py

## Description

This Python-based tool is designed to spider a given domain, extract text-based content, and save it in a structured HTML format as a single HTML file. It's particularly useful for creating datasets for AI training, content analysis, or archiving purposes.

## Key Features

- **Domain Spidering**: Crawls an entire domain, creating a comprehensive sitemap.
- **Homepage-Linked Content Spidering**: Allows the user to choose to only spider and download pages linked from the homepage, instead of the entire content of the domain. 
- **Language Detection**: Identifies and extracts only English-language content.
- **Multimedia Filtering**: Automatically detects and skips image, video, and audio files.
- **HTML Structure Preservation**: Maintains basic HTML formatting including headers, paragraphs, tables, and text emphasis.
- **Content De-duplication**: Removes common elements like menus and footers across pages.
- **Large Content Handling**: Splits large outputs into manageable chunks.

## How It Works

1. **User Input**: Prompts for the target domain and output filename.
2. **Sitemap Creation**: Spiders the domain, identifying English-language HTML pages.
3. **Content Extraction**: Processes each page, preserving essential HTML structure.
4. **De-duplication**: Removes common elements across pages to focus on unique content.
5. **Content Saving**: Combines processed content and saves it, splitting into chunks if necessary.

## Use Cases

- Creating datasets for natural language processing (NLP) models
- Web content analysis and research
- Website archiving
- SEO analysis
- Content migration

## Requirements

- Python 3.x
- Required libraries: requests, beautifulsoup4, html5lib, langdetect

## Usage

1. Run the script from the command line.
2. Enter the domain you want to spider.
3. Enter the filename for the output single-HTML file. 

## Limitations

- Respects robots.txt by default
- May not handle JavaScript-rendered content
- Language detection may not be 100% accurate for very short texts


# Single_Domain_PDF_Scraper.py

This Python script is a web crawler designed to spider an entire domain and download all unique PDF files found within it. It operates in two distinct phases: spidering and downloading, providing a comprehensive solution for bulk PDF retrieval from websites.

## Features

- **Domain-wide Spidering**: Crawls an entire domain, following internal links to discover all accessible pages.
- **PDF URL Extraction**: Identifies and collects URLs of all PDF files encountered during the spidering process.
- **Duplicate Detection**: Uses MD5 hashing to avoid downloading duplicate PDFs, even if they have different filenames.
- **Two-Phase Operation**: 
  1. Spiders the domain to collect all PDF URLs.
  2. Downloads unique PDFs in a separate phase.
- **Progress Tracking**: Provides detailed progress updates during both spidering and downloading phases.
- **User-Friendly**: Prompts for domain URL and save location, making it easy to use for various domains.
- **Error Handling**: Gracefully handles exceptions to ensure the script continues running even if individual page access fails.

## Usage

1. Run the script.
2. Enter the URL of the domain you wish to spider when prompted.
3. Choose to either spider the entire domain, or just the homepage-linked URLs
4. Specify the folder where you want to save the downloaded PDFs.
5. The script will first spider the domain, then download unique PDFs.

## Output

- Console updates on spidering progress.
- Detailed download progress, including counts and percentages.
- Final summary of PDFs found and downloaded.

## Requirements

- Python 3.x
- Libraries: requests, beautifulsoup4

## Ethical Considerations

This tool is intended for legitimate use cases such as archiving, research, or personal use. Always ensure you have the right to download content from the target domain and adhere to the website's terms of service and robots.txt file.

# PDF_Text_Converter.py

This tool turns a directory full of PDFs (and sub-directories) into a single text file, while trying to preserve some formatting. 

## Features

- Recursively searches through directories to find all PDF files
- Extracts text from PDF files while attempting to preserve basic formatting
- Combines extracted text from multiple PDFs into a single output
- Automatically splits output into multiple files if it exceeds 5MB
- Handles errors gracefully, continuing processing even if individual PDFs fail

## Requirements

- Python 3.x
- PyPDF2 library

## Usage

1. Run the script from the command line.
2. Enter the local directory path you want to spider for PDFs
3. Enter your desired output filename.

The script will then process all PDFs in the specified directory and its subdirectories, saving the extracted text to the specified output file (or multiple files if the output exceeds 5MB).

## Output

- If the total extracted text is 5MB or less, it will be saved to a single file with the name you specify.
- If the total extracted text exceeds 5MB, it will be split into multiple files, each 5MB or less. The files will be named like this: `output_1.txt`, `output_2.txt`, etc. (assuming you named the output file "output.txt").

## Limitations

- The quality of text extraction can vary depending on the PDF structure and content. Some PDFs, especially those with complex layouts or scanned images, may not extract perfectly.
- Very large directories with numerous PDFs may take a significant amount of time to process.

