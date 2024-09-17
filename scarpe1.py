import os
from unstructured.partition.html import partition_html
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import json
from datetime import datetime
def scrape_url(url):
   response = requests.get(url)
   html_content = response.text
   elements = partition_html(text=html_content)
   return [element.text for element in elements if element.text.strip()]
def extract_links(url):
   response = requests.get(url)
   soup = BeautifulSoup(response.text, 'html.parser')
   return [urljoin(url, link.get('href')) for link in soup.find_all('a') if link.get('href')]
def scrape_website(main_url, output_folder):
   os.makedirs(output_folder, exist_ok=True)
   all_data = []
   links = extract_links(main_url)
   for link in links:
       try:
           content = scrape_url(link)
           all_data.append({
               "url": link,
               "content": content
           })
           print(f"Scraped: {link}")
       except Exception as e:
           print(f"Error scraping {link}: {str(e)}")
   # Generate a filename based on the current date and time
   timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
   filename = f"scraped_data_{timestamp}.json"
   file_path = os.path.join(output_folder, filename)
   # Write the scraped content to a JSON file
   with open(file_path, 'w', encoding='utf-8') as f:
       json.dump(all_data, f, ensure_ascii=False, indent=2)
   print(f"Scraped data saved to: {file_path}")
if __name__ == "__main__":
   main_url = "https://python.langchain.com/v0.2/docs/introduction/"
   output_folder = "scraped_data"
   scrape_website(main_url, output_folder)
