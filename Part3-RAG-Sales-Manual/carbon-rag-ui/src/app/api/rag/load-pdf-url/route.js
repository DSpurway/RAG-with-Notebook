import { NextResponse } from 'next/server';

export async function POST(request) {
  try {
    const body = await request.json();
    const { pdf_url, collection_name } = body;

    if (!pdf_url || !collection_name) {
      return NextResponse.json(
        { error: 'Missing required fields: pdf_url and collection_name' },
        { status: 400 }
      );
    }

    console.log(`[API] Loading PDF from URL: ${pdf_url} into collection: ${collection_name}`);

    // Forward request to backend
    const backendUrl = 'http://rag-backend:8080/api/load-pdf-url';
    
    const response = await fetch(backendUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        pdf_url,
        collection_name,
      }),
    });

    const data = await response.json();

    if (!response.ok) {
      console.error(`[API] Backend error: ${response.status}`, data);
      return NextResponse.json(
        { error: data.error || 'Failed to load PDF' },
        { status: response.status }
      );
    }

    console.log(`[API] Successfully loaded PDF: ${data.message}`);
    return NextResponse.json(data);

  } catch (error) {
    console.error('[API] Error loading PDF:', error);
    return NextResponse.json(
      { error: error.message || 'Internal server error' },
      { status: 500 }
    );
  }
}

// Made with Bob
