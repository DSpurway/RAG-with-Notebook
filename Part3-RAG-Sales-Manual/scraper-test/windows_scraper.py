"""
IBM Docs Scraper for Windows (x86_64)
Runs locally on your laptop and sends scraped content to Power backend
"""

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import time
import json
import requests
from datetime import datetime
import argparse

def create_driver():
    """Create a headless Chrome WebDriver (auto-downloads ChromeDriver if needed)"""
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    
    # Use webdriver-manager to auto-download correct ChromeDriver version
    service = ChromeService(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    driver.set_page_load_timeout(60)
    
    return driver

def scrape_ibm_docs(url, wait_time=10):
    """
    Scrape IBM Docs page using Selenium + Chrome
    
    Args:
        url: IBM Docs page URL
        wait_time: Seconds to wait for JavaScript rendering
    
    Returns:
        dict: Scraped content and metadata
    """
    driver = None
    try:
        print(f"Creating Chrome driver...")
        driver = create_driver()
        
        # Load the page
        print(f"Loading URL: {url}")
        driver.get(url)
        
        # Wait for main content to load
        print("Waiting for content to render...")
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CLASS_NAME, "ibmdocs-content-container"))
        )
        
        # Additional wait for JavaScript to complete
        print(f"Waiting {wait_time} seconds for JavaScript...")
        time.sleep(wait_time)
        
        # Get the fully rendered HTML
        html = driver.page_source
        
        # Parse with BeautifulSoup
        soup = BeautifulSoup(html, 'html.parser')
        
        # Extract main content container
        content_div = soup.find('div', class_='ibmdocs-content-container')
        
        if not content_div:
            return {
                'success': False,
                'error': 'Could not find ibmdocs-content-container',
                'html_length': len(html)
            }
        
        # Extract structured content
        title = soup.find('h1')
        paragraphs = content_div.find_all('p')
        headings = content_div.find_all(['h1', 'h2', 'h3', 'h4'])
        tables = content_div.find_all('table')
        lists = content_div.find_all(['ul', 'ol'])
        
        # Get all text content
        main_text = content_div.get_text(separator='\n', strip=True)
        
        # Extract sections with structure
        sections = []
        for heading in headings:
            section = {
                'level': heading.name,
                'title': heading.get_text(strip=True),
                'content': []
            }
            
            # Get content until next heading
            current = heading.find_next_sibling()
            while current and current.name not in ['h1', 'h2', 'h3', 'h4']:
                if current.name in ['p', 'ul', 'ol', 'table']:
                    section['content'].append(current.get_text(strip=True))
                current = current.find_next_sibling()
            
            sections.append(section)
        
        result = {
            'success': True,
            'method': 'Selenium + Chrome (Windows x86_64)',
            'url': url,
            'scraped_at': datetime.now().isoformat(),
            'page_title': title.get_text(strip=True) if title else None,
            'stats': {
                'paragraphs': len(paragraphs),
                'headings': len(headings),
                'tables': len(tables),
                'lists': len(lists),
                'sections': len(sections),
                'total_text_length': len(main_text),
                'html_length': len(html)
            },
            'sample_headings': [h.get_text(strip=True) for h in headings[:10]],
            'text_sample': main_text[:2000],
            'quality_score': calculate_quality(content_div),
            'sections': sections,  # Full sections for RAG processing
            'full_text': main_text  # Complete text content
        }
        
        print(f"\n✅ Scraping successful!")
        print(f"   Title: {result['page_title']}")
        print(f"   Sections: {len(sections)}")
        print(f"   Quality Score: {result['quality_score']['score']}%")
        print(f"   Recommendation: {result['quality_score']['recommendation']}")
        
        return result
        
    except Exception as e:
        print(f"\n❌ Scraping failed: {str(e)}")
        return {
            'success': False,
            'error': str(e),
            'scraped_at': datetime.now().isoformat()
        }
    
    finally:
        if driver:
            driver.quit()

def calculate_quality(content_div):
    """Calculate content quality score"""
    checks = {
        'has_paragraphs': len(content_div.find_all('p')) > 10,
        'has_headings': len(content_div.find_all(['h2', 'h3'])) > 5,
        'has_tables': len(content_div.find_all('table')) > 0,
        'has_lists': len(content_div.find_all(['ul', 'ol'])) > 0,
        'sufficient_content': len(content_div.get_text()) > 5000
    }
    score = sum(checks.values()) / len(checks) * 100
    return {
        'score': score,
        'checks': checks,
        'recommendation': get_recommendation(score)
    }

def get_recommendation(score):
    """Get recommendation based on quality score"""
    if score >= 80:
        return "Excellent - Ready for RAG processing"
    elif score >= 60:
        return "Good - Usable for RAG with minor adjustments"
    else:
        return "Poor - May need additional processing"

def send_to_backend(scraped_data, backend_url, server_model=None):
    """Send scraped content to Power backend for RAG processing"""
    try:
        # Add server_model to scraped data if provided
        if server_model:
            scraped_data['server_model'] = server_model
            print(f"\nSending data to backend: {backend_url} (server: {server_model})")
        else:
            print(f"\nSending data to backend: {backend_url}")
        
        response = requests.post(
            f"{backend_url}/ingest-scraped-content",
            json=scraped_data,
            timeout=30
        )
        
        if response.status_code == 200:
            print("✅ Data sent successfully to backend")
            return response.json()
        else:
            print(f"❌ Backend returned error: {response.status_code}")
            print(f"   Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Failed to send to backend: {str(e)}")
        return None

def save_to_file(scraped_data, filename):
    """Save scraped content to JSON file"""
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(scraped_data, f, indent=2, ensure_ascii=False)
        print(f"✅ Saved to {filename}")
    except Exception as e:
        print(f"❌ Failed to save file: {str(e)}")

def main():
    parser = argparse.ArgumentParser(description='Scrape IBM Docs pages from Windows')
    parser.add_argument('url', help='IBM Docs URL to scrape')
    parser.add_argument('--wait', type=int, default=10, help='Wait time for JavaScript (seconds)')
    parser.add_argument('--backend', help='Backend URL to send scraped data')
    parser.add_argument('--output', help='Output JSON file path')
    parser.add_argument('--server-model', help='Server model (e.g., E1180) for collection naming')
    
    args = parser.parse_args()
    
    # Validate URL
    if 'ibm.com/docs' not in args.url:
        print("❌ Error: URL must be from ibm.com/docs domain")
        return
    
    print("=" * 80)
    print("IBM Docs Scraper (Windows x86_64)")
    if args.server_model:
        print(f"Server Model: {args.server_model}")
    print("=" * 80)
    
    # Scrape the page
    result = scrape_ibm_docs(args.url, wait_time=args.wait)
    
    if not result['success']:
        print(f"\n❌ Scraping failed: {result.get('error', 'Unknown error')}")
        return
    
    # Save to file if requested
    if args.output:
        save_to_file(result, args.output)
    
    # Send to backend if requested
    if args.backend:
        backend_result = send_to_backend(result, args.backend, server_model=args.server_model)
        if backend_result:
            print(f"Backend response: {json.dumps(backend_result, indent=2)}")
    
    print("\n" + "=" * 80)
    print("Scraping complete!")
    print("=" * 80)

if __name__ == '__main__':
    # Example usage if run without arguments
    import sys
    if len(sys.argv) == 1:
        print("IBM Docs Scraper for Windows")
        print("\nUsage:")
        print("  python windows_scraper.py <url> [options]")
        print("\nOptions:")
        print("  --wait <seconds>     Wait time for JavaScript (default: 10)")
        print("  --backend <url>      Send scraped data to backend")
        print("  --output <file>      Save to JSON file")
        print("\nExamples:")
        print("  # Scrape E1180 Sales Manual")
        print('  python windows_scraper.py "https://www.ibm.com/docs/en/announcements/family-908005-power-e1180-enterprise-server-9080-heu"')
        print("\n  # Scrape and save to file")
        print('  python windows_scraper.py "https://www.ibm.com/docs/..." --output e1180.json')
        print("\n  # Scrape and send to backend")
        print('  python windows_scraper.py "https://www.ibm.com/docs/..." --backend http://rag-backend-route.apps.cluster')
        print("\n  # Scrape with longer wait time")
        print('  python windows_scraper.py "https://www.ibm.com/docs/..." --wait 15')
    else:
        main()

# Made with Bob
