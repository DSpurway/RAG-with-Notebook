/**
 * Next.js API Route - Bulk Ingestion of All Sales Manuals
 * Triggers ingestion of all 26 IBM Power server Sales Manuals
 * This is a long-running operation that will take several hours
 */

// IBM Power server configuration - Same as in sales-manual/page.js
const IBM_POWER_SERVERS = [
  // POWER11 Servers
  { model: "E1180", name: "IBM Power E1180", processor: "POWER11" },
  { model: "E1150", name: "IBM Power E1150", processor: "POWER11" },
  { model: "S1122", name: "IBM Power S1122", processor: "POWER11" },
  { model: "S1124", name: "IBM Power S1124", processor: "POWER11" },
  // POWER10 Servers
  { model: "E1080", name: "IBM Power E1080", processor: "POWER10" },
  { model: "E1050", name: "IBM Power E1050", processor: "POWER10" },
  { model: "L1022", name: "IBM Power L1022", processor: "POWER10" },
  { model: "L1024", name: "IBM Power L1024", processor: "POWER10" },
  { model: "S1012", name: "IBM Power S1012", processor: "POWER10" },
  { model: "S1014", name: "IBM Power S1014", processor: "POWER10" },
  { model: "S1022", name: "IBM Power S1022", processor: "POWER10" },
  { model: "S1024", name: "IBM Power S1024", processor: "POWER10" },
  // POWER9 Servers
  { model: "E980", name: "IBM Power System E980", processor: "POWER9" },
  { model: "E950", name: "IBM Power System E950", processor: "POWER9" },
  { model: "H922", name: "IBM Power System H922", processor: "POWER9" },
  { model: "H924", name: "IBM Power System H924", processor: "POWER9" },
  { model: "IC922", name: "IBM Power System IC922", processor: "POWER9" },
  { model: "L922", name: "IBM Power System L922", processor: "POWER9" },
  { model: "LC921", name: "IBM Power System LC921", processor: "POWER9" },
  { model: "LC922", name: "IBM Power System LC922", processor: "POWER9" },
  { model: "S914", name: "IBM Power System S914", processor: "POWER9" },
  { model: "S914-G", name: "IBM Power System S914", processor: "POWER9" },
  { model: "S922", name: "IBM Power System S922", processor: "POWER9" },
  { model: "S922-G", name: "IBM Power System S922", processor: "POWER9" },
  { model: "S924", name: "IBM Power System S924", processor: "POWER9" },
  { model: "S924-G", name: "IBM Power System S924", processor: "POWER9" },
];

export async function POST(request) {
  try {
    const backendUrl = process.env.RAG_BACKEND_URL || 'http://rag-backend-opensearch:8080';
    
    console.log(`[Bulk Ingestion API] Starting bulk ingestion of ${IBM_POWER_SERVERS.length} servers`);
    
    // Initialize the backend bulk ingestion state
    try {
      const initResponse = await fetch(`${backendUrl}/api/init-bulk-ingestion`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ total: IBM_POWER_SERVERS.length }),
      });
      
      if (!initResponse.ok) {
        console.warn('[Bulk Ingestion API] Failed to initialize backend state, continuing anyway');
      }
    } catch (err) {
      console.warn('[Bulk Ingestion API] Error initializing backend state:', err);
    }
    
    // Start the bulk ingestion process
    // Note: This will trigger the Windows scraper for each server sequentially
    // The backend will handle the actual scraping and ingestion
    
    const results = {
      total: IBM_POWER_SERVERS.length,
      started: [],
      failed: [],
      message: `Bulk ingestion started for ${IBM_POWER_SERVERS.length} servers. This will take several hours.`
    };
    
    // Trigger ingestion for each server
    // We'll do this asynchronously and return immediately
    // The backend will handle the long-running process
    
    for (const server of IBM_POWER_SERVERS) {
      try {
        console.log(`[Bulk Ingestion API] Triggering ingestion for ${server.model}`);
        
        // Call the backend to trigger scraping for this server
        // The backend will call the Windows scraper
        const response = await fetch(`${backendUrl}/api/ingest-sales-manual`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            server_model: server.model,
            server_name: server.name,
            processor: server.processor
          }),
          // 5 minute timeout per server
          signal: AbortSignal.timeout(300000),
        });
        
        if (response.ok) {
          results.started.push(server.model);
          console.log(`[Bulk Ingestion API] Successfully started ingestion for ${server.model}`);
        } else {
          const errorData = await response.json().catch(() => ({ error: 'Unknown error' }));
          results.failed.push({ model: server.model, error: errorData.error || 'Failed to start' });
          console.error(`[Bulk Ingestion API] Failed to start ingestion for ${server.model}:`, errorData);
        }
      } catch (error) {
        results.failed.push({ model: server.model, error: error.message });
        console.error(`[Bulk Ingestion API] Error triggering ingestion for ${server.model}:`, error);
      }
    }
    
    console.log(`[Bulk Ingestion API] Bulk ingestion complete. Started: ${results.started.length}, Failed: ${results.failed.length}`);
    
    return Response.json(results, { status: 200 });
  } catch (error) {
    console.error('[Bulk Ingestion API] Error:', error);
    return Response.json(
      { 
        error: error.message || 'Failed to start bulk ingestion',
        total: IBM_POWER_SERVERS.length,
        started: [],
        failed: []
      },
      { status: 500 }
    );
  }
}

// Made with Bob