# Web Scraping Feature for RAG Backend

## Overview

This feature extends the RAG backend to support loading content from dynamic web pages (specifically IBM Docs pages) into the vector database. Previously, only static PDF files could be loaded. Now you can scrape live documentation pages and keep your knowledge base up-to-date with the latest information.

## Problem Solved

**Before**: The RAG system could only work with static PDF files, which meant:
- Documentation could become outdated
- Manual PDF downloads were required
- No way to automatically update content when IBM Docs pages changed
- Announcements and updates were not accessible

**After**: The system can now:
- Scrape content directly from IBM Docs URLs
- Load multiple pages at once
- Keep the knowledge base current with live documentation
- Access IBM announcements and product updates directly

## Architecture

```
┌─────────────────────┐
│   IBM Docs Pages    │
│  (Live Web Content) │
└──────────┬──────────┘
           │
           │ HTTPS
           │
┌──────────▼──────────┐
│  IBMDocsScraper     │
│  (BeautifulSoup)    │
└──────────┬──────────┘
           │
           │ Parsed Content
           │
┌──────────▼──────────┐
│  LangChain Docs     │
│  (Text Splitter)    │
└──────────┬──────────┘
           │
           │ Chunks
           │
┌──────────▼──────────┐
│  Milvus Vector DB   │
│  (Embeddings)       │
└─────────────────────┘
```

## New Components

### 1. `web_scraper.py`

A dedicated module for web scraping with the following features:

- **IBMDocsScraper class**: Handles fetching and parsing IBM Docs pages
- **Smart content extraction**: Identifies main content areas and filters out navigation/headers
- **Metadata extraction**: Captures title, description, keywords, and publication dates
- **Error handling**: Graceful failure with detailed error messages
- **Multiple URL support**: Can scrape multiple pages in one operation

Key methods:
- `scrape_url(url)`: Scrape a single URL
- `scrape_multiple_urls(urls)`: Scrape multiple URLs
- `extract_main_content(html, url)`: Parse HTML and extract relevant content
- `create_langchain_documents(scraped_data)`: Convert to LangChain format

### 2. New API Endpoints

#### Load Single URL
```bash
POST /api/load-url
Content-Type: application/json

{
  "url": "https://www.ibm.com/docs/en/announcements/power-s1014-9105-41b",
  "collection_name": "ibm_announcements"
}
```

Response:
```json
{
  "success": true,
  "message": "Successfully loaded content from URL",
  "title": "IBM Power S1014 (9105-41B) announcement",
  "chunks": 15,
  "collection": "ibm_announcements",
  "url": "https://www.ibm.com/docs/en/announcements/power-s1014-9105-41b"
}
```

#### Load Multiple URLs
```bash
POST /api/load-multiple-urls
Content-Type: application/json

{
  "urls": [
    "https://www.ibm.com/docs/en/announcements/power-s1014-9105-41b",
    "https://www.ibm.com/docs/en/announcements/power-s1022-9105-22a"
  ],
  "collection_name": "ibm_announcements"
}
```

Response:
```json
{
  "success": true,
  "message": "Successfully loaded 2 URLs",
  "pages_loaded": 2,
  "total_chunks": 28,
  "collection": "ibm_announcements",
  "titles": [
    "IBM Power S1014 (9105-41B) announcement",
    "IBM Power S1022 (9105-22A) announcement"
  ]
}
```

## Dependencies Added

```
beautifulsoup4==4.12.2  # HTML parsing
lxml==5.1.0             # Fast XML/HTML parser
```

## Usage Examples

### Example 1: Load IBM Announcement Page

```python
import requests

# Load a single IBM announcement
response = requests.post(
    "http://localhost:8080/api/load-url",
    json={
        "url": "https://www.ibm.com/docs/en/announcements/power-s1014-9105-41b",
        "collection_name": "power_announcements"
    }
)

print(response.json())
```

### Example 2: Load Multiple Product Pages

```python
import requests

# Load multiple product documentation pages
urls = [
    "https://www.ibm.com/docs/en/announcements/power-s1014-9105-41b",
    "https://www.ibm.com/docs/en/announcements/power-s1022-9105-22a",
    "https://www.ibm.com/docs/en/announcements/power-s1024-9105-42a"
]

response = requests.post(
    "http://localhost:8080/api/load-multiple-urls",
    json={
        "urls": urls,
        "collection_name": "power_systems"
    }
)

print(f"Loaded {response.json()['pages_loaded']} pages")
```

### Example 3: Search Loaded Content

```python
import requests

# Search the loaded content
response = requests.post(
    "http://localhost:8080/api/search",
    json={
        "question": "What are the specifications of the Power S1014?",
        "collection_name": "power_announcements",
        "k": 3
    }
)

for result in response.json()['results']:
    print(f"Score: {result['score']}")
    print(f"Content: {result['content'][:200]}...")
    print()
```

## Testing

A comprehensive test script is provided: `test_web_scraping.py`

Run the tests:
```bash
cd rag-backend
python test_web_scraping.py
```

The test script will:
1. Check backend health
2. List existing collections
3. Scrape the IBM announcement page
4. Search the loaded content
5. Verify the results

## Content Extraction Strategy

The scraper uses a multi-strategy approach to extract content:

1. **Primary Strategy**: Look for IBM Docs-specific containers
   - `div.bx--content`
   - `main` element
   - `article` element

2. **Fallback Strategy**: Use generic content containers
   - `div.content`
   - `div#content`
   - `div.main-content`

3. **Last Resort**: Use `body` element with aggressive filtering

4. **Content Filtering**:
   - Remove navigation, headers, footers
   - Remove scripts and styles
   - Extract text from paragraphs, headings, lists, and tables
   - Filter out very short text snippets (<10 characters)

## Metadata Captured

For each scraped page, the following metadata is captured:

- `source`: Original URL
- `source_type`: "web_page"
- `description`: Meta description tag
- `keywords`: Meta keywords tag
- `publication_date`: DC.date meta tag (if available)
- `domain`: Domain name from URL

This metadata is stored with each chunk in the vector database and can be used for filtering searches.

## Error Handling

The scraper includes robust error handling:

- **Network errors**: Timeout, connection failures
- **HTTP errors**: 404, 500, etc.
- **Parsing errors**: Invalid HTML, missing content
- **Graceful degradation**: If one URL fails in a batch, others continue

All errors are logged with detailed messages for debugging.

## Performance Considerations

- **Request timeout**: 30 seconds per page (configurable)
- **Chunk size**: 768 characters with 100 character overlap
- **Concurrent requests**: Currently sequential (can be parallelized in future)
- **Memory usage**: Efficient streaming and chunking

## Limitations

1. **JavaScript-rendered content**: The scraper fetches static HTML only. Pages that require JavaScript execution may not work fully.
2. **Authentication**: Currently no support for pages requiring login.
3. **Rate limiting**: No built-in rate limiting (be respectful of IBM's servers).
4. **Dynamic content**: Content is captured at the time of scraping, not updated automatically.

## Future Enhancements

Potential improvements for future versions:

1. **Scheduled updates**: Automatically re-scrape pages on a schedule
2. **Change detection**: Only update chunks that have changed
3. **JavaScript rendering**: Use Selenium or Playwright for JS-heavy pages
4. **Authentication support**: Handle login-protected pages
5. **Rate limiting**: Built-in throttling for bulk operations
6. **Parallel scraping**: Concurrent requests for faster bulk loading
7. **Content versioning**: Track changes over time
8. **Sitemap support**: Automatically discover and scrape related pages

## Integration with Existing System

The web scraping feature integrates seamlessly with the existing RAG system:

- Uses the same vector database (Milvus)
- Uses the same embeddings model (all-MiniLM-L6-v2)
- Uses the same text splitter (CharacterTextSplitter)
- Compatible with existing search and generation endpoints
- Can be used alongside PDF loading

## Example Workflow

1. **Initial Load**: Load IBM announcement pages into a collection
   ```bash
   POST /api/load-url
   ```

2. **Search**: Query the loaded content
   ```bash
   POST /api/search
   ```

3. **Generate**: Use LLM to generate answers based on retrieved content
   ```bash
   POST /api/generate
   ```

4. **Update**: Re-scrape pages when announcements are updated
   ```bash
   POST /api/load-url  # Same URL, updates existing content
   ```

## Troubleshooting

### Issue: "Failed to scrape URL"
- Check that the URL is accessible
- Verify network connectivity
- Check backend logs for detailed error messages

### Issue: "No content extracted from page"
- The page structure may not match expected patterns
- Check if the page requires JavaScript
- Verify the page has actual content (not just navigation)

### Issue: "Request timed out"
- Increase timeout in `IBMDocsScraper(timeout=60)`
- Check network speed and stability

### Issue: "Collection not found" when searching
- Ensure you used the correct collection name
- List collections with `GET /api/collections`

## Security Considerations

- **URL validation**: Only scrape trusted domains (IBM Docs)
- **Content sanitization**: HTML is parsed and cleaned
- **No code execution**: Static content extraction only
- **Rate limiting**: Be respectful of source servers

## License

Same as parent project.

## Support

For issues or questions:
1. Check the backend logs for detailed error messages
2. Run the test script to verify functionality
3. Review this documentation for common issues