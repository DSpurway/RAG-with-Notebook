"""
Windows Scraper Service - Flask API for IBM Docs Scraping
Runs on Windows laptop (x86_64) and provides HTTP API for the RAG backend
"""

from flask import Flask, jsonify, request
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
from datetime import datetime
import traceback

app = Flask(__name__)

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
        driver = create_driver()
        
        # Load the page
        print(f"Loading URL: {url}")
        driver.get(url)
        
        # Wait for content to be present
        print("Waiting for content to render...")
        try:
            WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
        except Exception as e:
            print(f"Warning: Timeout waiting for body tag: {e}")
        
        # Additional wait for JavaScript
        print(f"Waiting {wait_time} seconds for JavaScript...")
        time.sleep(wait_time)
        
        # Get page source
        page_source = driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')
        
        # Extract title
        title_tag = soup.find('title')
        page_title = title_tag.get_text().strip() if title_tag else "Unknown Title"
        
        # Remove script and style elements
        for script in soup(["script", "style", "nav", "header", "footer"]):
            script.decompose()
        
        # Extract structured content
        sections = []
        
        # Find main content area
        main_content = soup.find('main') or soup.find('article') or soup.find('body')
        
        if main_content:
            # Extract headings and their content
            for heading in main_content.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
                section = {
                    'heading': heading.get_text().strip(),
                    'level': heading.name,
                    'content': []
                }
                
                # Get content until next heading
                for sibling in heading.find_next_siblings():
                    if sibling.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                        break
                    
                    if sibling.name == 'p':
                        text = sibling.get_text().strip()
                        if text:
                            section['content'].append({'type': 'paragraph', 'text': text})
                    
                    elif sibling.name in ['ul', 'ol']:
                        items = [li.get_text().strip() for li in sibling.find_all('li')]
                        if items:
                            section['content'].append({'type': 'list', 'items': items})
                    
                    elif sibling.name == 'table':
                        rows = []
                        for tr in sibling.find_all('tr'):
                            cells = [td.get_text().strip() for td in tr.find_all(['td', 'th'])]
                            if cells:
                                rows.append(cells)
                        if rows:
                            section['content'].append({'type': 'table', 'rows': rows})
                
                if section['content']:
                    sections.append(section)
        
        # Get full text
        full_text = main_content.get_text(separator='\n', strip=True) if main_content else ""
        
        # Calculate statistics
        paragraphs = len(soup.find_all('p'))
        headings = len(soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']))
        tables = len(soup.find_all('table'))
        lists = len(soup.find_all(['ul', 'ol']))
        
        # Quality score
        quality_checks = {
            'has_paragraphs': paragraphs > 10,
            'has_headings': headings > 5,
            'has_tables': tables > 0,
            'has_lists': lists > 0,
            'has_content': len(full_text) > 5000
        }
        
        quality_score = sum(quality_checks.values()) / len(quality_checks) * 100
        
        if quality_score >= 80:
            recommendation = "Excellent - Ready for RAG processing"
        elif quality_score >= 60:
            recommendation = "Good - Usable with minor adjustments"
        else:
            recommendation = "Poor - May need additional processing"
        
        result = {
            'success': True,
            'method': 'Selenium + Chrome (Windows x86_64)',
            'url': url,
            'scraped_at': datetime.now().isoformat(),
            'page_title': page_title,
            'stats': {
                'paragraphs': paragraphs,
                'headings': headings,
                'tables': tables,
                'lists': lists,
                'sections': len(sections),
                'total_text_length': len(full_text)
            },
            'quality_score': {
                'score': quality_score,
                'checks': quality_checks,
                'recommendation': recommendation
            },
            'sections': sections,
            'full_text': full_text
        }
        
        print(f"\n✅ Scraping successful!")
        print(f"   Title: {page_title}")
        print(f"   Sections: {len(sections)}")
        print(f"   Quality Score: {quality_score:.0f}%")
        print(f"   Recommendation: {recommendation}\n")
        
        return result
        
    except Exception as e:
        error_msg = f"Error scraping {url}: {str(e)}"
        print(f"\n❌ {error_msg}")
        traceback.print_exc()
        return {
            'success': False,
            'error': error_msg,
            'traceback': traceback.format_exc()
        }
    
    finally:
        if driver:
            driver.quit()

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'Windows Scraper Service',
        'method': 'Selenium + Chrome (Windows x86_64)'
    })

@app.route('/')
def index():
    """Service information"""
    return jsonify({
        'service': 'Windows Scraper Service',
        'version': '1.0',
        'method': 'Selenium + Chrome (Windows x86_64)',
        'endpoints': {
            '/health': 'Health check',
            '/scrape': 'Scrape IBM Docs page (GET with ?url=... parameter)',
            '/scrape-e1180': 'Scrape E1180 Sales Manual (example)'
        },
        'usage': {
            'scrape': 'GET /scrape?url=https://www.ibm.com/docs/...',
            'with_wait': 'GET /scrape?url=...&wait=15'
        }
    })

@app.route('/scrape')
def scrape_custom():
    """Scrape a custom IBM Docs URL"""
    url = request.args.get('url')
    if not url:
        return jsonify({
            'success': False,
            'error': 'Missing required parameter: url',
            'usage': 'GET /scrape?url=https://www.ibm.com/docs/...'
        }), 400
    
    wait_time = int(request.args.get('wait', 10))
    
    print(f"\n📥 Received scrape request:")
    print(f"   URL: {url}")
    print(f"   Wait time: {wait_time}s\n")
    
    result = scrape_ibm_docs(url, wait_time)
    
    if result['success']:
        return jsonify(result)
    else:
        return jsonify(result), 500

@app.route('/scrape-e1180')
def scrape_e1180():
    """Example: Scrape E1180 Sales Manual"""
    url = "https://www.ibm.com/docs/en/announcements/family-908005-power-e1180-enterprise-server-9080-heu"
    print(f"\n📥 Scraping E1180 Sales Manual...")
    result = scrape_ibm_docs(url)
    
    if result['success']:
        return jsonify(result)
    else:
@app.route('/scrape-e1180-preview')
def scrape_e1180_preview():
    """Example: Scrape E1180 and show formatted preview"""
    url = "https://www.ibm.com/docs/en/announcements/family-908005-power-e1180-enterprise-server-9080-heu"
    print(f"\n📥 Scraping E1180 Sales Manual (Preview)...")
    result = scrape_ibm_docs(url)
    
    if result['success']:
        # Return HTML with formatted text
        full_text = result.get('full_text', '')
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>{result.get('page_title', 'Preview')}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }}
                h1 {{ color: #0f62fe; }}
                pre {{ background: #f4f4f4; padding: 20px; border-radius: 5px; white-space: pre-wrap; }}
                .stats {{ background: #e8f4ff; padding: 15px; border-radius: 5px; margin: 20px 0; }}
            </style>
        </head>
        <body>
            <h1>{result.get('page_title', 'Scraped Content')}</h1>
            <div class="stats">
                <strong>Quality Score:</strong> {result['quality_score']['score']:.0f}% - {result['quality_score']['recommendation']}<br>
                <strong>Sections:</strong> {result['stats']['sections']}<br>
                <strong>Text Length:</strong> {result['stats']['total_text_length']:,} characters
            </div>
            <h2>Full Text Content:</h2>
            <pre>{full_text}</pre>
        </body>
        </html>
        """
        return html
    else:
        return jsonify(result), 500

        return jsonify(result), 500

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))
    
    print("=" * 80)
    print("IBM Docs Scraper Service")
    print("=" * 80)
    print("Method: Selenium + Chrome")
    print(f"Port: {port}")
    print("Endpoints:")
    print("  - GET /health - Health check")
    print("  - GET /scrape?url=... - Scrape IBM Docs page")
    print("  - GET /scrape-e1180 - Example: Scrape E1180")
    print("=" * 80)
    print()
    
    app.run(host='0.0.0.0', port=port, debug=False)

# Made with Bob
