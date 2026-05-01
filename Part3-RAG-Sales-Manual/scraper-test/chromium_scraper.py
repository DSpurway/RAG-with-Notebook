from flask import Flask, jsonify, request
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import time
from datetime import datetime
import traceback

app = Flask(__name__)

def create_driver():
    """Create a headless Chromium WebDriver using ppc64le community build"""
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--disable-software-rasterizer')
    options.add_argument('--disable-extensions')
    # ungoogled-chromium-browser binary location
    options.binary_location = '/usr/bin/chromium-browser'
    
    # ChromeDriver from EPEL
    service = Service('/usr/bin/chromedriver')
    driver = webdriver.Chrome(service=service, options=options)
    driver.set_page_load_timeout(60)
    
    return driver

def scrape_ibm_docs(url, wait_time=10):
    """
    Scrape IBM Docs page using Selenium + Chromium (ppc64le community build)
    
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
        
        # Wait for main content to load
        print("Waiting for content to render...")
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CLASS_NAME, "ibmdocs-content-container"))
        )
        
        # Additional wait for JavaScript to complete
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
            'method': 'Selenium + Chromium ppc64le (community build)',
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
            'sections_preview': sections[:3]  # First 3 sections
        }
        
        return result
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc(),
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

@app.route('/scrape-e1180')
def scrape_e1180():
    """Scrape IBM Power E1180 Sales Manual"""
    url = "https://www.ibm.com/docs/en/announcements/family-908005-power-e1180-enterprise-server-9080-heu"
    
    wait_time = request.args.get('wait', default=10, type=int)
    
    result = scrape_ibm_docs(url, wait_time=wait_time)
    
    if result['success']:
        return jsonify(result)
    else:
        return jsonify(result), 500

@app.route('/scrape')
def scrape_custom():
    """Scrape any IBM Docs URL"""
    url = request.args.get('url')
    
    if not url:
        return jsonify({
            'success': False,
            'error': 'Missing required parameter: url',
            'usage': '/scrape?url=https://www.ibm.com/docs/...'
        }), 400
    
    if 'ibm.com/docs' not in url:
        return jsonify({
            'success': False,
            'error': 'URL must be from ibm.com/docs domain'
        }), 400
    
    wait_time = request.args.get('wait', default=10, type=int)
    
    result = scrape_ibm_docs(url, wait_time=wait_time)
    
    if result['success']:
        return jsonify(result)
    else:
        return jsonify(result), 500

@app.route('/extract-content')
def extract_content():
    """Extract full structured content from IBM Docs page"""
    url = request.args.get('url')
    
    if not url:
        return jsonify({
            'success': False,
            'error': 'Missing required parameter: url'
        }), 400
    
    driver = None
    try:
        driver = create_driver()
        driver.get(url)
        
        # Wait for content
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CLASS_NAME, "ibmdocs-content-container"))
        )
        time.sleep(10)
        
        html = driver.page_source
        soup = BeautifulSoup(html, 'html.parser')
        content_div = soup.find('div', class_='ibmdocs-content-container')
        
        if not content_div:
            return jsonify({'success': False, 'error': 'Content not found'}), 500
        
        # Extract all sections with full content
        sections = []
        current_section = None
        
        for element in content_div.find_all(['h1', 'h2', 'h3', 'h4', 'p', 'ul', 'ol', 'table']):
            if element.name in ['h1', 'h2', 'h3', 'h4']:
                if current_section:
                    sections.append(current_section)
                current_section = {
                    'level': element.name,
                    'title': element.get_text(strip=True),
                    'content': []
                }
            elif current_section:
                text = element.get_text(strip=True)
                if text:
                    current_section['content'].append({
                        'type': element.name,
                        'text': text
                    })
        
        if current_section:
            sections.append(current_section)
        
        return jsonify({
            'success': True,
            'url': url,
            'sections': sections,
            'total_sections': len(sections)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500
    
    finally:
        if driver:
            driver.quit()

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'IBM Docs Chromium Scraper (ppc64le)',
        'chromium_version': 'ungoogled-chromium v84.0.4147.125',
        'source': 'https://gitlab.com/chromium-ppc64le/chromium-ppc64le',
        'timestamp': datetime.now().isoformat()
    })

@app.route('/')
def index():
    """API documentation"""
    return jsonify({
        'service': 'IBM Docs Chromium Scraper',
        'version': '1.0.0',
        'method': 'Selenium + ungoogled-chromium ppc64le',
        'chromium_source': 'https://gitlab.com/chromium-ppc64le/chromium-ppc64le',
        'endpoints': {
            '/health': 'Health check',
            '/scrape-e1180': 'Scrape E1180 Sales Manual (test endpoint)',
            '/scrape?url=<url>&wait=<seconds>': 'Scrape any IBM Docs URL',
            '/extract-content?url=<url>': 'Extract full structured content'
        },
        'examples': {
            'test_e1180': '/scrape-e1180',
            'custom_url': '/scrape?url=https://www.ibm.com/docs/en/announcements/...',
            'with_wait': '/scrape?url=https://www.ibm.com/docs/...&wait=15',
            'full_content': '/extract-content?url=https://www.ibm.com/docs/...'
        }
    })

if __name__ == '__main__':
    print("Starting IBM Docs Chromium Scraper Service...")
    print("Using ungoogled-chromium v84.0.4147.125 (ppc64le)")
    print("Source: https://gitlab.com/chromium-ppc64le/chromium-ppc64le")
    app.run(host='0.0.0.0', port=8080, debug=False)

# Made with Bob