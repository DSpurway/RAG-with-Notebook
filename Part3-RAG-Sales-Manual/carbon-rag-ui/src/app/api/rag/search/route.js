/**
 * Next.js API Route - Proxy for RAG Backend Search
 * This allows the UI to use relative URLs and avoids CORS issues
 * The backend URL uses internal OpenShift service name
 */

export async function POST(request) {
  try {
    const body = await request.json();
    
    // Use internal OpenShift service name - no FQDN needed!
    const backendUrl = process.env.RAG_BACKEND_URL || 'http://rag-backend:8080';
    
    const response = await fetch(`${backendUrl}/api/search`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(body),
    });

    const data = await response.json();
    
    return Response.json(data, { status: response.status });
  } catch (error) {
    console.error('Search proxy error:', error);
    return Response.json(
      { error: error.message || 'Failed to search' },
      { status: 500 }
    );
  }
}

// Made with Bob
