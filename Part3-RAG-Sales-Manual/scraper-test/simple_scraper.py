from flask import Flask, jsonify, request
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import traceback
import time

app = Flask(__name__)

def scrape_ibm_docs_simple(url):
    """
    Scrape IBM Docs page using simple requests + BeautifulSoup
    
    Note: This gets the initial HTML. For JavaScript-rendered content,
    we would need a headless browser, but those aren't available for ppc64le.
    
    Alternative: Use IBM's "Print" or "PDF" export feature which generates
    static HTML with all content rendered server-side.
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Linux ppc64le) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
        
        print(f"Fetching URL: {url}")
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Try to find content container
        content_div = soup.find('div', class_='ibmdocs-content-container')
        
        if not content_div:
            # Fallback to body
            content_div = soup.find('body')
        
        if not content_div:
            return {
                'success': False,
                'error': 'Could not find content',
                'html_length': len(response.content),
                'note': 'Page may require JavaScript rendering'
            }
        
        # Extract content
        title = soup.find('h1')
        paragraphs = content_div.find_all('p')
        headings = content_div.find_all(['h1', 'h2', 'h3', 'h4'])
        tables = content_div.find_all('table')
        lists = content_div.find_all(['ul', 'ol'])
        
        main_text = content_div.get_text(separator='\n', strip=True)
        
        # Extract sections
        sections = []
        for heading in headings[:20]:  # Limit to first 20 headings
            section = {
                'level': heading.name,
                'title': heading.get_text(strip=True),
                'content': []
            }
            
            current = heading.find_next_sibling()
            count = 0
            while current and current.name not in ['h1', 'h2', 'h3', 'h4'] and count < 10:
                if current.name in ['p', 'ul', 'ol', 'table']:
                    text = current.get_text(strip=True)
                    if text:
                        section['content'].append(text[:500])  # Limit content length
                current = current.find_next_sibling()
                count += 1
            
            if section['content']:
                sections.append(section)
        
        quality = calculate_quality(content_div)
        
        result = {
            'success': True,
            'method': 'Simple requests + BeautifulSoup (no JS rendering)',
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
                'html_length': len(response.content)
            },
            'sample_headings': [h.get_text(strip=True) for h in headings[:10]],
            'text_sample': main_text[:2000],
            'quality_score': quality,
            'sections_preview': sections[:5],
            'note': 'This scrapes initial HTML only. For full JS-rendered content, consider using IBM Docs PDF export feature.'
        }
        
        return result
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc(),
            'scraped_at': datetime.now().isoformat()
        }

def calculate_quality(content_div):
    """Calculate content quality score"""
    checks = {
        'has_paragraphs': len(content_div.find_all('p')) > 10,
        'has_headings': len(content_div.find_all(['h2', 'h3'])) > 5,
        'has_tables': len(content_div.find_all('table')) > 0,
        'has_lists': len(content_div.find_all(['ul', 'ol'])) > 0,
        'sufficient_content': len(content_div.get_text()) > 1000
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
        return "Excellent - Content extracted successfully"
    elif score >= 60:
        return "Good - Partial content extracted"
    elif score >= 40:
        return "Fair - Limited content, may need JS rendering"
    else:
        return "Poor - Page requires JavaScript rendering. Consider using IBM Docs PDF export."

@app.route('/scrape-e1180')
def scrape_e1180():
    """Scrape IBM Power E1180 Sales Manual"""
    url = "https://www.ibm.com/docs/en/announcements/family-908005-power-e1180-enterprise-server-9080-heu"
    result = scrape_ibm_docs_simple(url)
    
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
    
    result = scrape_ibm_docs_simple(url)
    
    if result['success']:
        return jsonify(result)
    else:
        return jsonify(result), 500

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'IBM Docs Simple Scraper',
        'method': 'requests + BeautifulSoup (no JS rendering)',
        'note': 'For full content, use IBM Docs PDF export feature',
        'timestamp': datetime.now().isoformat()
    })

@app.route('/')
def index():
    """API documentation"""
    return jsonify({
        'service': 'IBM Docs Simple Scraper',
        'version': '1.0.0',
        'method': 'requests + BeautifulSoup (no JavaScript rendering)',
        'limitation': 'JavaScript-rendered content not available on ppc64le',
        'recommendation': 'Use IBM Docs PDF export for complete content',
        'endpoints': {
            '/health': 'Health check',
            '/scrape-e1180': 'Test scrape E1180 Sales Manual',
            '/scrape?url=<url>': 'Scrape any IBM Docs URL'
        },
        'pdf_approach': {
            'description': 'IBM Docs pages have a "Save as PDF" button that generates complete content',
            'advantage': 'PDFs contain all rendered content without needing JavaScript',
            'implementation': 'Download PDF programmatically and extract text with PyPDF2'
        }
    })

if __name__ == '__main__':
    print("Starting IBM Docs Simple Scraper Service...")
    print("Note: This scraper gets initial HTML only (no JS rendering)")
    print("For complete content, consider using IBM Docs PDF export feature")
    app.run(host='0.0.0.0', port=8080, debug=False)

# Made with Bob