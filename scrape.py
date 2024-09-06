from bs4 import BeautifulSoup
from fpdf import FPDF
import pandas as pd
import requests
import re
from urllib.parse import urljoin

def clean_text(text):
    text = re.sub(r'\s+', ' ', text)  
    text = re.sub(r'[^\x00-\x7F]+', ' ', text)  
    text = text.strip()
    return text

# extract tables 
def extract_tables_from_html(html_content):
    soup = BeautifulSoup(html_content, "html.parser")
    tables = soup.find_all("table")
    table_data = []

    for table in tables:
        headers = [th.text.strip() for th in table.find_all("th")]
        rows = []
        for row in table.find_all("tr"):
            cells = [cell.text.strip() for cell in row.find_all(["td", "th"])]
            if cells:
                rows.append(cells)
        # Create a DataFrame for each table
        if headers and rows:
            df = pd.DataFrame(rows, columns=headers)
        else:
            df = pd.DataFrame(rows)
        table_data.append(df)
    
    return table_data

#  format tables as text
def format_tables_for_pdf(tables):
    formatted_tables = ""
    for i, table in enumerate(tables):
        formatted_tables += f"\nTable {i + 1}:\n"
        formatted_tables += table.to_string(index=False) + "\n\n"
    return formatted_tables

# recursively extract URLs 
def extract_urls_from_html(html_content, base_url=""):
    soup = BeautifulSoup(html_content, "html.parser")
    urls = set()

    # Helper function to recursively find URLs in tags and their children
    def find_urls_recursively(tag, base_url):
        # Check 'href' in <a> tag attributes
        if tag.name == 'a' and tag.has_attr('href'):
            href = tag['href']
            # Convert relative URLs to absolute
            full_url = urljoin(base_url, href)
            if full_url.startswith('http'):
                urls.add(full_url)
        for child in tag.find_all(True):  # True finds all tags
            find_urls_recursively(child, base_url)
    find_urls_recursively(soup, base_url)
    return list(urls)

def fetch_content_with_bs4(url, base_url="", crawled_urls=set()):
    if url in crawled_urls:
        return None

    try:
        response = requests.get(url)
        response.raise_for_status()  
        soup = BeautifulSoup(response.content, "html.parser")
    except Exception as e:
        print(f"Failed to load content from {url}: {e}")
        return None

    crawled_urls.add(url)  
    content_dict = {"URL": url, "Content": ""}  
    tables = []
    cleaned_text = clean_text(soup.get_text(strip=True))
    content_dict["Content"] += cleaned_text + "\n\n"

    
    tables = extract_tables_from_html(soup.prettify())
    if tables:
        formatted_tables = format_tables_for_pdf(tables)
        content_dict["Content"] += formatted_tables
    links = extract_urls_from_html(response.content.decode(), base_url)
    for link in links:
        linked_content = fetch_content_with_bs4(link, base_url, crawled_urls)
        if linked_content:
            content_dict["Content"] += "\n\n" + linked_content["Content"]  
    
    return content_dict

#pdf content
def save_content_to_pdf(content_list, filename):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    #title
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, 'Crawled Web Content with BeautifulSoup', ln=True, align='C')
    pdf.ln(10)
    
    pdf.set_font("Arial", size=12)
  
    for content_dict in content_list:
        url = content_dict["URL"]
        body = content_dict["Content"]
        
        pdf.set_font("Arial", 'B', 12)
        pdf.multi_cell(0, 10, f'URL: {url}')
        pdf.ln(5)
        
        pdf.set_font("Arial", size=10)
        pdf.multi_cell(0, 10, body)
        pdf.ln(10)
    pdf.output(filename)
    print(f"Content saved to {filename}")

base_url = "https://codelibrary.amlegal.com/"  
content_list = []

initial_content = fetch_content_with_bs4(base_url, base_url)
if initial_content:
    content_list.append(initial_content)

if content_list:
    save_content_to_pdf(content_list, "structured_content_bs4.pdf")
