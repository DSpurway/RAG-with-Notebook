/**
 * Next.js API Route - Proxy for RAG Backend Collections
 * This allows the UI to use relative URLs and avoids CORS issues
 * The backend URL uses internal OpenShift service name
 */

export async function GET(request) {
  try {
    // Use internal OpenShift service name - no FQDN needed!
    const backendUrl = process.env.RAG_BACKEND_URL || 'http://rag-backend-opensearch:8080';
    
    console.log(`[Collections API] Fetching from: ${backendUrl}/api/collections`);
    
    const response = await fetch(`${backendUrl}/api/collections`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
      // 10 second timeout for collections list
      signal: AbortSignal.timeout(10000),
    });

    console.log(`[Collections API] Response status: ${response.status}`);
    const data = await response.json();
    console.log(`[Collections API] Response data:`, data);
    
    return Response.json(data, { status: response.status });
  } catch (error) {
    console.error('[Collections API] Error:', error);
    return Response.json(
      { error: error.message || 'Failed to get collections', collections: [] },
      { status: 500 }
    );
  }
}

// Made with Bob
