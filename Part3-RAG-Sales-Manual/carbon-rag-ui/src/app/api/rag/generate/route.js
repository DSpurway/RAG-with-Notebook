/**
 * Next.js API Route - Proxy for RAG Backend Generate
 * This allows the UI to use relative URLs and avoids CORS issues
 * The backend URL uses internal OpenShift service name
 * Supports both streaming and non-streaming responses
 */

export async function POST(request) {
  try {
    const body = await request.json();
    
    // Use internal OpenShift service name - no FQDN needed!
    const backendUrl = process.env.RAG_BACKEND_URL || 'http://rag-backend:8080';
    
    const response = await fetch(`${backendUrl}/api/generate`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(body),
    });

    // If streaming is requested, pass through the stream
    if (body.stream) {
      return new Response(response.body, {
        status: response.status,
        headers: {
          'Content-Type': 'text/event-stream',
          'Cache-Control': 'no-cache',
          'Connection': 'keep-alive',
        },
      });
    }

    // Non-streaming response
    const data = await response.json();
    return Response.json(data, { status: response.status });
  } catch (error) {
    console.error('Generate proxy error:', error);
    return Response.json(
      { error: error.message || 'Failed to generate' },
      { status: 500 }
    );
  }
}

// Made with Bob
