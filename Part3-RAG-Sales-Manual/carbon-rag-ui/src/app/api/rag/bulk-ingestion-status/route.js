/**
 * Next.js API Route - Get Bulk Ingestion Status
 * Polls the backend for current bulk ingestion progress
 */

export async function GET(request) {
  try {
    const backendUrl = process.env.RAG_BACKEND_URL || 'http://rag-backend-opensearch:8080';
    
    const response = await fetch(`${backendUrl}/api/bulk-ingestion-status`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });
    
    if (!response.ok) {
      throw new Error(`Backend returned ${response.status}`);
    }
    
    const data = await response.json();
    
    return Response.json(data, { status: 200 });
  } catch (error) {
    console.error('[Bulk Ingestion Status API] Error:', error);
    return Response.json(
      { 
        error: error.message || 'Failed to get bulk ingestion status',
        in_progress: false,
        current_server: null,
        completed: [],
        failed: [],
        total: 0,
        completed_count: 0,
        failed_count: 0
      },
      { status: 500 }
    );
  }
}

// Made with Bob