# Content_Slurpers
A set of python tools useful for spidering websites and PDFs for text that can be easily loaded into custom GPTs or other LLMs. 



# Web_to_Single_HTML_File_Spider.py

## Description

This Python-based tool is designed to spider a given domain, extract text-based content, and save it in a structured HTML format as a single HTML file. It's particularly useful for creating datasets for AI training, content analysis, or archiving purposes.

## Key Features

- **Domain Spidering**: Crawls an entire domain, creating a comprehensive sitemap.
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

## Installation

```bash
git clone https://github.com/yourusername/web-content-extractor.git
cd web-content-extractor
pip install -r requirements.txt
```

## Usage

```bash
python web_content_extractor.py
```

Follow the prompts to enter the target domain and desired output filename.

## Limitations

- Respects robots.txt by default
- May not handle JavaScript-rendered content
- Language detection may not be 100% accurate for very short texts


---

This description provides a comprehensive overview of the tool, its features, how it works, potential use cases, and how to set it up and use it. It also mentions some limitations and invites contributions, which are good practices for open-source projects on GitHub. Remember to replace "yourusername" with your actual GitHub username and adjust any other details as necessary.
