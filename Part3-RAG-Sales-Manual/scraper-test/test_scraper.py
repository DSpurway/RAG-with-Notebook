from flask import Flask, jsonify
import requests
from bs4 import BeautifulSoup
from requests_html import HTMLSession
from datetime import datetime

app = Flask(__name__)

@app.route('/test-e1180')
def test_e1180():
    """Test scraping E1180 Sales Manual"""
    url = "https://www.ibm.com/docs/en/announcements/family-908005-power-e1180-enterprise-server-9080-heu"
    
    # Add headers to avoid 403 Forbidden
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extract key information
        title = soup.find('h1')
        paragraphs = soup.find_all('p')
        headings = soup.find_all(['h2', 'h3'])
        tables = soup.find_all('table')
        
        # Get main text content
        main_text = soup.get_text(separator='\n', strip=True)
        
        result = {
            'success': True,
            'url': url,
            'tested_at': datetime.now().isoformat(),
            'status_code': response.status_code,
            'content_length': len(response.content),
            'title': title.text.strip() if title else None,
            'stats': {
                'paragraphs': len(paragraphs),
                'headings': len(headings),
                'tables': len(tables),
                'total_text_length': len(main_text)
            },
            'sample_headings': [h.text.strip() for h in headings[:5]],
            'text_sample': main_text[:1000],
            'quality_score': calculate_quality(soup),
            'recommendation': get_recommendation(soup)
        }
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'tested_at': datetime.now().isoformat()
        }), 500

def calculate_quality(soup):
    """Calculate content quality score"""
    checks = {
        'has_title': bool(soup.find('h1')),
        'has_paragraphs': len(soup.find_all('p')) > 10,
        'has_tables': len(soup.find_all('table')) > 0,
        'has_lists': len(soup.find_all(['ul', 'ol'])) > 0,
        'sufficient_content': len(soup.get_text()) > 5000
    }
    return sum(checks.values()) / len(checks) * 100

def get_recommendation(soup):
    """Get recommendation based on content quality"""
    score = calculate_quality(soup)
    if score > 80:
        return "Excellent - BeautifulSoup is sufficient"
    elif score > 60:
        return "Good - BeautifulSoup works, may need minor enhancements"
    else:
        return "Poor - May need JavaScript rendering (requests-html)"

@app.route('/test-e1180-js')
def test_e1180_js():
    """Test scraping E1180 Sales Manual with JavaScript rendering"""
    url = "https://www.ibm.com/docs/en/announcements/family-908005-power-e1180-enterprise-server-9080-heu"
    
    try:
        session = HTMLSession()
        response = session.get(url, timeout=30)
        
        # Render JavaScript (wait for page to load)
        response.html.render(timeout=20, sleep=2)
        
        # Parse with BeautifulSoup
        soup = BeautifulSoup(response.html.html, 'html.parser')
        
        # Extract key information
        title = soup.find('h1')
        paragraphs = soup.find_all('p')
        headings = soup.find_all(['h2', 'h3'])
        tables = soup.find_all('table')
        
        # Get main text content
        main_text = soup.get_text(separator='\n', strip=True)
        
        result = {
            'success': True,
            'method': 'requests-html (JavaScript rendering)',
            'url': url,
            'tested_at': datetime.now().isoformat(),
            'status_code': response.status_code,
            'content_length': len(response.html.html),
            'title': title.text.strip() if title else None,
            'stats': {
                'paragraphs': len(paragraphs),
                'headings': len(headings),
                'tables': len(tables),
                'total_text_length': len(main_text)
            },
            'sample_headings': [h.text.strip() for h in headings[:5]],
            'text_sample': main_text[:1000],
            'quality_score': calculate_quality(soup),
            'recommendation': get_recommendation(soup)
        }
        
        session.close()
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'method': 'requests-html (JavaScript rendering)',
            'error': str(e),
            'tested_at': datetime.now().isoformat()
        }), 500

@app.route('/health')
def health():
    return jsonify({'status': 'healthy'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)

# Made with Bob
