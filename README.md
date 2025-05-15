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
- **Language Detection**: Identifies and extracts only English-language content using a multi-level approach:
  - URL pattern analysis to avoid unnecessary downloads
  - HTML language tags inspection 
  - Full content language detection (only when needed)
- **Real-time Progress Tracking**: Shows progress bars for all operations, with estimated completion times.
- **Multimedia Filtering**: Automatically detects and skips image, video, and audio files.
- **HTML Structure Preservation**: Maintains basic HTML formatting including headers, paragraphs, tables, and text emphasis.
- **Content De-duplication**: Removes common elements like menus and footers across pages.
- **Large Content Handling**: Splits large outputs into manageable chunks.

## How It Works

1. **User Input**: Prompts for the target domain and output filename.
2. **Sitemap Creation**: Spiders the domain, identifying English-language HTML pages using an optimized multi-level approach.
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
- Required libraries: 
  - requests
  - beautifulsoup4
  - html5lib
  - langdetect
  - tqdm (for progress bars)

## Installation

```bash
pip install requests beautifulsoup4 html5lib langdetect tqdm
```

## Usage

1. Run the script from the command line:
   ```
   python Web_to_Single_HTML_File_Spider.py
   ```
2. Enter the domain you want to spider (e.g., https://example.com).
3. Choose whether to spider the entire domain or just the homepage-linked content.
4. If a sitemap is found, decide whether to use it or manually spider the site.
5. Enter the filename for the output single-HTML file.

## Performance Optimization

This version includes significant performance improvements:
- **Optimized Language Detection**: Uses a cascade approach from fastest to most expensive checks
- **URL Pattern Pre-filtering**: Detects language from URL patterns before downloading content
- **HTML Tag Analysis**: Checks language tags before falling back to full content analysis
- **Progress Visualization**: Real-time progress tracking with ETA for all operations

## Limitations

- Respects robots.txt by default
- May not handle JavaScript-rendered content
- Language detection may not be 100% accurate for very short texts


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

