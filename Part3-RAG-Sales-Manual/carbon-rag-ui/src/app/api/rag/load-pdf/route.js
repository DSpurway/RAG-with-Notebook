/**
 * Next.js API Route - Proxy for RAG Backend Load PDF
 * This allows the UI to use relative URLs and avoids CORS issues
 * The backend URL uses internal OpenShift service name
 */

export async function POST(request) {
  try {
    const body = await request.json();
    
    // Use internal OpenShift service name - no FQDN needed!
    const backendUrl = process.env.RAG_BACKEND_URL || 'http://rag-backend-opensearch:8080';
    
    console.log(`[Load PDF API] Fetching from: ${backendUrl}/api/load-pdf`);
    console.log(`[Load PDF API] Request body:`, body);
    
    const response = await fetch(`${backendUrl}/api/load-pdf`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(body),
      // 20 minute timeout for PDF processing (matches route timeout)
      signal: AbortSignal.timeout(1200000),
    });

    console.log(`[Load PDF API] Response status: ${response.status}`);
    const data = await response.json();
    console.log(`[Load PDF API] Response data:`, data);
    
    return Response.json(data, { status: response.status });
  } catch (error) {
    console.error('[Load PDF API] Error:', error);
    return Response.json(
      { error: error.message || 'Failed to load PDF' },
      { status: 500 }
    );
  }
}

// Made with Bob
