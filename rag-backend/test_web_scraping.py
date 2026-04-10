#!/usr/bin/env python3
"""
Test script for web scraping functionality
Tests loading IBM Docs pages into the vector database
"""

import requests
import json
import sys
import time

# Configuration
BACKEND_URL = "http://localhost:8080"
TEST_URL = "https://www.ibm.com/docs/en/announcements/power-s1014-9105-41b"
COLLECTION_NAME = "ibm_announcements"

def test_health():
    """Test backend health"""
    print("Testing backend health...")
    try:
        response = requests.get(f"{BACKEND_URL}/health", timeout=5)
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_scrape_single_url():
    """Test scraping a single IBM Docs URL"""
    print(f"\nTesting single URL scraping...")
    print(f"URL: {TEST_URL}")
    print(f"Collection: {COLLECTION_NAME}")
    
    try:
        payload = {
            "url": TEST_URL,
            "collection_name": COLLECTION_NAME
        }
        
        print("\nSending request...")
        response = requests.post(
            f"{BACKEND_URL}/api/load-url",
            json=payload,
            timeout=120
        )
        
        print(f"Status: {response.status_code}")
        result = response.json()
        print(f"Response: {json.dumps(result, indent=2)}")
        
        if response.status_code == 200 and result.get('success'):
            print("\n✓ Successfully loaded URL into vector database")
            print(f"  Title: {result.get('title')}")
            print(f"  Chunks: {result.get('chunks')}")
            print(f"  Collection: {result.get('collection')}")
            return True
        else:
            print(f"\n✗ Failed to load URL: {result.get('error')}")
            return False
            
    except Exception as e:
        print(f"\n✗ Error: {e}")
        return False

def test_search():
    """Test searching the loaded content"""
    print(f"\nTesting search in collection {COLLECTION_NAME}...")
    
    test_questions = [
        "What is the announcement about?",
        "What are the key features?",
        "When was this announced?"
    ]
    
    for question in test_questions:
        print(f"\nQuestion: {question}")
        try:
            payload = {
                "question": question,
                "collection_name": COLLECTION_NAME,
                "k": 3
            }
            
            response = requests.post(
                f"{BACKEND_URL}/api/search",
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"Found {result.get('count')} results")
                
                for i, doc in enumerate(result.get('results', [])[:2], 1):
                    print(f"\n  Result {i} (score: {doc.get('score', 0):.4f}):")
                    content = doc.get('content', '')
                    print(f"  {content[:200]}...")
            else:
                print(f"Search failed: {response.json()}")
                
        except Exception as e:
            print(f"Error: {e}")

def test_multiple_urls():
    """Test loading multiple IBM Docs URLs"""
    print("\nTesting multiple URL loading...")
    
    urls = [
        "https://www.ibm.com/docs/en/announcements/power-s1014-9105-41b",
        # Add more URLs here if needed
    ]
    
    try:
        payload = {
            "urls": urls,
            "collection_name": "ibm_docs_multi"
        }
        
        print(f"Loading {len(urls)} URLs...")
        response = requests.post(
            f"{BACKEND_URL}/api/load-multiple-urls",
            json=payload,
            timeout=180
        )
        
        print(f"Status: {response.status_code}")
        result = response.json()
        print(f"Response: {json.dumps(result, indent=2)}")
        
        if response.status_code == 200 and result.get('success'):
            print("\n✓ Successfully loaded multiple URLs")
            print(f"  Pages loaded: {result.get('pages_loaded')}")
            print(f"  Total chunks: {result.get('total_chunks')}")
            return True
        else:
            print(f"\n✗ Failed: {result.get('error')}")
            return False
            
    except Exception as e:
        print(f"\n✗ Error: {e}")
        return False

def list_collections():
    """List all collections"""
    print("\nListing all collections...")
    try:
        response = requests.get(f"{BACKEND_URL}/api/collections", timeout=10)
        if response.status_code == 200:
            result = response.json()
            collections = result.get('collections', [])
            print(f"Found {len(collections)} collections:")
            for col in collections:
                print(f"  - {col}")
            return True
        else:
            print(f"Failed: {response.json()}")
            return False
    except Exception as e:
        print(f"Error: {e}")
        return False

def main():
    """Run all tests"""
    print("=" * 60)
    print("Web Scraping Test Suite")
    print("=" * 60)
    
    # Test 1: Health check
    if not test_health():
        print("\n✗ Backend is not healthy. Please start the backend service.")
        sys.exit(1)
    
    print("\n" + "=" * 60)
    
    # Test 2: List existing collections
    list_collections()
    
    print("\n" + "=" * 60)
    
    # Test 3: Scrape single URL
    if test_scrape_single_url():
        # Wait a moment for indexing
        time.sleep(2)
        
        # Test 4: Search the loaded content
        test_search()
    
    print("\n" + "=" * 60)
    
    # Test 5: List collections again
    list_collections()
    
    print("\n" + "=" * 60)
    print("Tests complete!")
    print("=" * 60)

if __name__ == "__main__":
    main()

# Made with Bob
