'use client';
import {
  Breadcrumb,
  BreadcrumbItem,
  Button,
  Tabs,
  Tab,
  TabList,
  TabPanels,
  TabPanel,
  Grid,
  Column,
  TextArea,
  Tile,
  Loading,
  InlineNotification,
  DataTable,
  TableContainer,
  Table,
  TableHead,
  TableRow,
  TableHeader,
  TableBody,
  TableCell,
  Tag,
  OverflowMenu,
  OverflowMenuItem,
  Modal,
  TextInput,
  ProgressBar,
} from '@carbon/react';
import {
  Checkmark,
  WarningAlt,
  Renew,
  View,
  TrashCan,
} from '@carbon/icons-react';
import React, { useState, useEffect } from 'react';

// IBM Power server configuration - Ordered by processor generation (POWER11, POWER10, POWER9)
const IBM_POWER_SERVERS = [
  // POWER11 Servers (4 servers)
  { model: "E1180", name: "IBM Power E1180", mtm: "9080-HEU", processor: "POWER11", url: "https://www.ibm.com/docs/en/announcements/family-908005-power-e1180-enterprise-server-9080-heu", category: "Enterprise" },
  { model: "E1150", name: "IBM Power E1150", mtm: "9043-MRU", processor: "POWER11", url: "https://www.ibm.com/docs/en/announcements/family-904302-power-e1150-enterprise-midrange-technology-based-server-9043-mru", category: "Enterprise" },
  { model: "S1122", name: "IBM Power S1122", mtm: "9824-22A", processor: "POWER11", url: "https://www.ibm.com/docs/en/announcements/family-982401-power-s1122-9824-22a", category: "Scale-out" },
  { model: "S1124", name: "IBM Power S1124", mtm: "9824-42A", processor: "POWER11", url: "https://www.ibm.com/docs/en/announcements/family-982402-power-s1124-9824-42a", category: "Scale-out" },
  // POWER10 Servers (8 servers)
  { model: "E1080", name: "IBM Power E1080", mtm: "9080-HEX", processor: "POWER10", url: "https://www.ibm.com/docs/en/announcements/power-e1080-enterprise-server", category: "Enterprise" },
  { model: "E1050", name: "IBM Power E1050", mtm: "9043-MRX", processor: "POWER10", url: "https://www.ibm.com/docs/en/announcements/power-e1050-enterprise-midrange-technology-based-server", category: "Enterprise" },
  { model: "L1022", name: "IBM Power L1022", mtm: "9786-22H", processor: "POWER10", url: "https://www.ibm.com/docs/en/announcements/power-l1022-9786-22h", category: "Linux-only" },
  { model: "L1024", name: "IBM Power L1024", mtm: "9786-42H", processor: "POWER10", url: "https://www.ibm.com/docs/en/announcements/power-l1024-9786-42h", category: "Linux-only" },
  { model: "S1012", name: "IBM Power S1012", mtm: "9028-21B", processor: "POWER10", url: "https://www.ibm.com/docs/en/announcements/family-9028-01-power-s1012", category: "Scale-out" },
  { model: "S1014", name: "IBM Power S1014", mtm: "9105-41B", processor: "POWER10", url: "https://www.ibm.com/docs/en/announcements/power-s1014-9105-41b", category: "Scale-out" },
  { model: "S1022", name: "IBM Power S1022", mtm: "9105-22A", processor: "POWER10", url: "https://www.ibm.com/docs/en/announcements/power-s1022-9105-22a", category: "Scale-out" },
  { model: "S1024", name: "IBM Power S1024", mtm: "9105-42A", processor: "POWER10", url: "https://www.ibm.com/docs/en/announcements/power-s1024-9105-42a", category: "Scale-out" },
  // POWER9 Servers (14 servers)
  { model: "E980", name: "IBM Power System E980", mtm: "9080-M9S", processor: "POWER9", url: "https://www.ibm.com/docs/en/announcements/power-system-e980-9080-m9s", category: "Enterprise" },
  { model: "E950", name: "IBM Power System E950", mtm: "9040-MR9", processor: "POWER9", url: "https://www.ibm.com/docs/en/announcements/power-system-e950-9040-mr9", category: "Enterprise" },
  { model: "H922", name: "IBM Power System H922", mtm: "9223-22S", processor: "POWER9", url: "https://www.ibm.com/docs/en/announcements/power-system-h922-9223-22s-2023-10-24", category: "High-performance" },
  { model: "H924", name: "IBM Power System H924", mtm: "9223-42S", processor: "POWER9", url: "https://www.ibm.com/docs/en/announcements/power-system-h924-9223-42s-2023-10-24", category: "High-performance" },
  { model: "IC922", name: "IBM Power System IC922", mtm: "9183-22X", processor: "POWER9", url: "https://www.ibm.com/docs/en/announcements/power-system-ic922-9183-22x-2021-12-14", category: "Intensive-compute" },
  { model: "L922", name: "IBM Power System L922", mtm: "9008-22L", processor: "POWER9", url: "https://www.ibm.com/docs/en/announcements/power-system-l922-9008-22l", category: "Linux-only" },
  { model: "LC921", name: "IBM Power System LC921", mtm: "9006-12P", processor: "POWER9", url: "https://www.ibm.com/docs/en/announcements/power-systems-lc921-9006-12p", category: "Linux-only" },
  { model: "LC922", name: "IBM Power System LC922", mtm: "9006-22P", processor: "POWER9", url: "https://www.ibm.com/docs/en/announcements/power-system-lc922-9006-22p", category: "Linux-only" },
  { model: "S914", name: "IBM Power System S914", mtm: "9009-41A", processor: "POWER9", url: "https://www.ibm.com/docs/en/announcements/power-system-s914-9009-41a", category: "Scale-out" },
  { model: "S914-G", name: "IBM Power System S914", mtm: "9009-41G", processor: "POWER9", url: "https://www.ibm.com/docs/en/announcements/power-system-s914-9009-41g-2023-10-24", category: "Scale-out" },
  { model: "S922", name: "IBM Power System S922", mtm: "9009-22A", processor: "POWER9", url: "https://www.ibm.com/docs/en/announcements/power-system-s922-9009-22a", category: "Scale-out" },
  { model: "S922-G", name: "IBM Power System S922", mtm: "9009-22G", processor: "POWER9", url: "https://www.ibm.com/docs/en/announcements/power-system-s922-9009-22g", category: "Scale-out" },
  { model: "S924", name: "IBM Power System S924", mtm: "9009-42A", processor: "POWER9", url: "https://www.ibm.com/docs/en/announcements/power-system-s924-9009-42a", category: "Scale-out" },
  { model: "S924-G", name: "IBM Power System S924", mtm: "9009-42G", processor: "POWER9", url: "https://www.ibm.com/docs/en/announcements/power-system-s924-9009-42g", category: "Scale-out" },
];

export default function SalesManualPage() {
  const [activeTab, setActiveTab] = useState(0);
  
  // Server management state
  const [servers, setServers] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [selectedServer, setSelectedServer] = useState(null);
  const [showDetailsModal, setShowDetailsModal] = useState(false);
  
  // Bulk ingestion progress state
  const [bulkIngestionInProgress, setBulkIngestionInProgress] = useState(false);
  const [bulkIngestionStatus, setBulkIngestionStatus] = useState(null);
  
  // Query state
  const [queryText, setQueryText] = useState('');
  const [queryResults, setQueryResults] = useState(null);
  const [queryLoading, setQueryLoading] = useState(false);

  // Load server status on mount
  useEffect(() => {
    loadServerStatus();
  }, []);

  const loadServerStatus = async () => {
    setLoading(true);
    setError('');
    
    try {
      // Get collections from backend
      const response = await fetch('/api/rag/collections');
      if (!response.ok) throw new Error('Failed to load collections');
      
      const data = await response.json();
      const collections = data.collections || [];
      
      // Match servers with their indexed status
      // Each server has its own collection: power_e1180, power_e1150, etc.
      const serversWithStatus = IBM_POWER_SERVERS.map(server => {
        const collectionName = `power_${server.model.toLowerCase().replace(/-/g, '_')}`;
        const isIndexed = collections.includes(collectionName);
        
        return {
          ...server,
          collectionName: collectionName,
          status: isIndexed ? 'indexed' : 'not-indexed',
          lastUpdated: isIndexed ? new Date().toISOString() : null,
          contentHash: null, // Will be populated when we implement hash checking
          documentCount: isIndexed ? '?' : 0
        };
      });
      
      setServers(serversWithStatus);
    } catch (err) {
      console.error('Error loading server status:', err);
      setError(err.message);
      // Initialize with default status
      setServers(IBM_POWER_SERVERS.map(s => ({
        ...s,
        collectionName: `power_${s.model.toLowerCase().replace(/-/g, '_')}`,
        status: 'unknown',
        lastUpdated: null,
        contentHash: null,
        documentCount: 0
      })));
    } finally {
      setLoading(false);
    }
  };

  // Poll bulk ingestion status
  const pollBulkIngestionStatus = async () => {
    try {
      // Call through Next.js API route, not directly to backend
      const response = await fetch('/api/rag/bulk-ingestion-status');
      
      if (!response.ok) {
        console.error('Failed to fetch bulk ingestion status');
        return;
      }
      
      const status = await response.json();
      setBulkIngestionStatus(status);
      
      // If still in progress, continue polling
      if (status.in_progress) {
        setTimeout(pollBulkIngestionStatus, 10000); // Poll every 10 seconds
      } else {
        // Ingestion complete
        setBulkIngestionInProgress(false);
        setLoading(false);
        
        // Show completion message
        if (status.failed_count > 0) {
          setError(`Bulk ingestion completed with errors. ${status.completed_count} succeeded, ${status.failed_count} failed.`);
        } else {
          setError(`Bulk ingestion completed successfully! All ${status.completed_count} servers indexed.`);
        }
        
        // Reload server status
        await loadServerStatus();
      }
    } catch (err) {
      console.error('Error polling bulk ingestion status:', err);
    }
  };

  const handleLoadAllDocuments = async () => {
    setLoading(true);
    setBulkIngestionInProgress(true);
    setBulkIngestionStatus(null);
    setError('Starting bulk ingestion of all 26 servers... This will take several hours.');
    
    try {
      // Call bulk ingest endpoint
      const response = await fetch('/api/rag/ingest-all-sales-manuals', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
      });
      
      if (!response.ok) throw new Error('Failed to start bulk ingestion');
      
      const data = await response.json();
      setError(`Bulk ingestion started! Processing ${data.total} servers.`);
      
      // Start polling for progress
      setTimeout(pollBulkIngestionStatus, 5000); // Start polling after 5 seconds
    } catch (err) {
      setError(`Error starting bulk ingestion: ${err.message}`);
      setLoading(false);
      setBulkIngestionInProgress(false);
    }
  };

  const handleIngestServer = async (server) => {
    setLoading(true);
    setError(`Ingesting ${server.model}... This may take 5-10 minutes.`);
    
    try {
      // Call scraper endpoint (would need to be implemented)
      const response = await fetch('/api/rag/ingest-sales-manual', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          url: server.url,
          model: server.model,
          name: server.name,
          mtm: server.mtm
        })
      });
      
      if (!response.ok) throw new Error('Failed to ingest server documentation');
      
      const data = await response.json();
      setError(`${server.model} ingested successfully! ${data.documentCount} documents indexed.`);
      
      // Reload server status
      await loadServerStatus();
    } catch (err) {
      setError(`Error ingesting ${server.model}: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleCheckForUpdates = async (server) => {
    setLoading(true);
    setError(`Checking ${server.model} for updates...`);
    
    try {
      // Calculate hash of current Sales Manual page
      const response = await fetch('/api/rag/check-updates', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          url: server.url,
          currentHash: server.contentHash
        })
      });
      
      if (!response.ok) throw new Error('Failed to check for updates');
      
      const data = await response.json();
      if (data.hasUpdates) {
        setError(`${server.model} has updates available! Re-ingest to get latest content.`);
      } else {
        setError(`${server.model} is up to date.`);
      }
    } catch (err) {
      setError(`Error checking updates for ${server.model}: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleViewDetails = (server) => {
    setSelectedServer(server);
    setShowDetailsModal(true);
  };

  const handleQuery = async () => {
    if (!queryText.trim()) return;
    
    setQueryLoading(true);
    setError('');
    
    try {
      const response = await fetch('/api/rag/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          collection_name: 'ibm_docs',
          prompt: queryText,
          top_k: 3
        })
      });
      
      if (!response.ok) throw new Error('Failed to query');
      
      const data = await response.json();
      setQueryResults(data);
    } catch (err) {
      setError(`Query error: ${err.message}`);
    } finally {
      setQueryLoading(false);
    }
  };

  // DataTable headers
  const headers = [
    { key: 'model', header: 'Model' },
    { key: 'name', header: 'Server Name' },
    { key: 'mtm', header: 'MTM' },
    { key: 'processor', header: 'Processor' },
    { key: 'category', header: 'Category' },
    { key: 'status', header: 'Status' },
    { key: 'documentCount', header: 'Docs' },
    { key: 'actions', header: 'Actions' },
  ];

  // Format rows for DataTable
  const rows = servers.map((server, idx) => ({
    id: `${idx}`,
    model: server.model,
    name: server.name,
    mtm: server.mtm,
    processor: server.processor,
    category: server.category,
    status: server.status,
    documentCount: server.documentCount,
    actions: server,
  }));

  return (
    <Grid className="rag-page" fullWidth>
      <Column lg={16} md={8} sm={4} className="rag-page__banner">
        <Breadcrumb noTrailingSlash>
          <BreadcrumbItem href="/">Home</BreadcrumbItem>
          <BreadcrumbItem href="/sales-manual">Sales Manual RAG</BreadcrumbItem>
        </Breadcrumb>
        <h1 className="rag-page__heading">IBM Power Sales Manual RAG</h1>
      </Column>
      
      <Column lg={16} md={8} sm={4} className="rag-page__content">
        <Tabs selectedIndex={activeTab} onChange={({ selectedIndex }) => setActiveTab(selectedIndex)}>
          <TabList aria-label="Sales Manual tabs" contained>
            <Tab>Manage Source Documents</Tab>
            <Tab>Query Documentation</Tab>
          </TabList>
          
          <TabPanels>
            {/* Tab 1: Manage Servers */}
            <TabPanel>
              <Grid>
                <Column lg={16}>
                  <Tile className="tile-spacing">
                    <h3>IBM Power Server Documentation Management</h3>
                    <p style={{ marginBottom: '1rem' }}>
                      Manage Sales Manual documentation for 26 IBM Power servers (POWER9, POWER10, POWER11).
                      Each server's documentation is scraped from IBM Docs and indexed for RAG queries.
                    </p>
                    
                    {error && (
                      <InlineNotification
                        kind={error.startsWith('Error') || error.startsWith('Failed') ? 'error' : 'info'}
                        title={error.startsWith('Error') ? 'Error' : 'Status'}
                        subtitle={error}
                        onCloseButtonClick={() => setError('')}
                        style={{ marginBottom: '1rem' }}
                      />
                    )}
                    
                    {/* Bulk Ingestion Progress */}
                    {bulkIngestionInProgress && bulkIngestionStatus && (
                      <Tile style={{ marginBottom: '1rem', backgroundColor: '#e0e0e0' }}>
                        <h4 style={{ marginBottom: '0.5rem' }}>Bulk Ingestion Progress</h4>
                        <p style={{ marginBottom: '0.5rem' }}>
                          <strong>Current Server:</strong> {bulkIngestionStatus.current_server || 'Starting...'}
                        </p>
                        <p style={{ marginBottom: '0.5rem' }}>
                          <strong>Progress:</strong> {bulkIngestionStatus.completed_count} of {bulkIngestionStatus.total} completed
                          {bulkIngestionStatus.failed_count > 0 && ` (${bulkIngestionStatus.failed_count} failed)`}
                        </p>
                        <ProgressBar
                          label="Ingestion Progress"
                          value={bulkIngestionStatus.completed_count}
                          max={bulkIngestionStatus.total}
                          helperText={`${Math.round((bulkIngestionStatus.completed_count / bulkIngestionStatus.total) * 100)}% complete`}
                        />
                        {bulkIngestionStatus.completed && bulkIngestionStatus.completed.length > 0 && (
                          <details style={{ marginTop: '1rem' }}>
                            <summary style={{ cursor: 'pointer', fontWeight: 'bold' }}>
                              Completed Servers ({bulkIngestionStatus.completed.length})
                            </summary>
                            <div style={{ marginTop: '0.5rem', fontSize: '0.875rem' }}>
                              {bulkIngestionStatus.completed.join(', ')}
                            </div>
                          </details>
                        )}
                        {bulkIngestionStatus.failed && bulkIngestionStatus.failed.length > 0 && (
                          <details style={{ marginTop: '0.5rem' }}>
                            <summary style={{ cursor: 'pointer', fontWeight: 'bold', color: '#da1e28' }}>
                              Failed Servers ({bulkIngestionStatus.failed.length})
                            </summary>
                            <div style={{ marginTop: '0.5rem', fontSize: '0.875rem', color: '#da1e28' }}>
                              {bulkIngestionStatus.failed.join(', ')}
                            </div>
                          </details>
                        )}
                      </Tile>
                    )}
                    
                    <div style={{ display: 'flex', gap: '1rem', marginBottom: '1rem' }}>
                      <Button
                        onClick={loadServerStatus}
                        disabled={loading || bulkIngestionInProgress}
                      >
                        {loading ? 'Loading...' : 'Refresh Status'}
                      </Button>
                      <Button
                        kind="primary"
                        onClick={handleLoadAllDocuments}
                        disabled={loading || bulkIngestionInProgress}
                      >
                        {bulkIngestionInProgress ? 'Ingestion in Progress...' : 'Load All Documents'}
                      </Button>
                    </div>
                    
                    <DataTable rows={rows} headers={headers}>
                      {({ rows, headers, getTableProps, getHeaderProps, getRowProps }) => (
                        <TableContainer>
                          <Table {...getTableProps()}>
                            <TableHead>
                              <TableRow>
                                {headers.map((header) => (
                                  <TableHeader key={header.key} {...getHeaderProps({ header })}>
                                    {header.header}
                                  </TableHeader>
                                ))}
                              </TableRow>
                            </TableHead>
                            <TableBody>
                              {rows.map((row) => {
                                const server = servers[parseInt(row.id)];
                                return (
                                  <TableRow key={row.id} {...getRowProps({ row })}>
                                    {row.cells.map((cell) => {
                                      if (cell.info.header === 'status') {
                                        return (
                                          <TableCell key={cell.id}>
                                            {server.status === 'indexed' && (
                                              <Tag type="green" renderIcon={Checkmark}>Indexed</Tag>
                                            )}
                                            {server.status === 'not-indexed' && (
                                              <Tag type="gray">Not Indexed</Tag>
                                            )}
                                            {server.status === 'unknown' && (
                                              <Tag type="red" renderIcon={WarningAlt}>Unknown</Tag>
                                            )}
                                          </TableCell>
                                        );
                                      }
                                      if (cell.info.header === 'actions') {
                                        return (
                                          <TableCell key={cell.id}>
                                            <OverflowMenu size="sm" flipped>
                                              <OverflowMenuItem
                                                itemText="View Details"
                                                onClick={() => handleViewDetails(server)}
                                              />
                                              <OverflowMenuItem
                                                itemText={server.status === 'indexed' ? 'Re-ingest' : 'Ingest'}
                                                onClick={() => handleIngestServer(server)}
                                                disabled={loading}
                                              />
                                              {server.status === 'indexed' && (
                                                <OverflowMenuItem
                                                  itemText="Check for Updates"
                                                  onClick={() => handleCheckForUpdates(server)}
                                                  disabled={loading}
                                                />
                                              )}
                                            </OverflowMenu>
                                          </TableCell>
                                        );
                                      }
                                      return <TableCell key={cell.id}>{cell.value}</TableCell>;
                                    })}
                                  </TableRow>
                                );
                              })}
                            </TableBody>
                          </Table>
                        </TableContainer>
                      )}
                    </DataTable>
                  </Tile>
                </Column>
              </Grid>
            </TabPanel>
            
            {/* Tab 2: Query Documentation */}
            <TabPanel>
              <Grid>
                <Column lg={16}>
                  <Tile className="tile-spacing">
                    <h3>Query IBM Power Documentation</h3>
                    <p style={{ marginBottom: '1rem' }}>
                      Ask questions about IBM Power servers. The system will search indexed Sales Manuals
                      and provide answers using the Granite LLM.
                    </p>
                    
                    <TextArea
                      labelText="Your Question"
                      placeholder="e.g., What are the key features of the IBM Power E1180?"
                      value={queryText}
                      onChange={(e) => setQueryText(e.target.value)}
                      rows={3}
                      style={{ marginBottom: '1rem' }}
                    />
                    
                    <Button
                      onClick={handleQuery}
                      disabled={queryLoading || !queryText.trim()}
                    >
                      {queryLoading ? 'Querying...' : 'Ask Question'}
                    </Button>
                    
                    {queryResults && (
                      <div style={{ marginTop: '2rem' }}>
                        <h4>Answer:</h4>
                        <Tile style={{ marginTop: '1rem', backgroundColor: '#f4f4f4' }}>
                          <p>{queryResults.content || queryResults.answer}</p>
                        </Tile>
                        
                        {queryResults.sources && (
                          <div style={{ marginTop: '1rem' }}>
                            <h5>Sources:</h5>
                            {queryResults.sources.map((source, idx) => (
                              <Tile key={idx} style={{ marginTop: '0.5rem', fontSize: '0.875rem' }}>
                                {source}
                              </Tile>
                            ))}
                          </div>
                        )}
                      </div>
                    )}
                  </Tile>
                </Column>
              </Grid>
            </TabPanel>
          </TabPanels>
        </Tabs>
      </Column>
      
      {/* Server Details Modal */}
      <Modal
        open={showDetailsModal}
        onRequestClose={() => setShowDetailsModal(false)}
        modalHeading={selectedServer ? `${selectedServer.model} Details` : 'Server Details'}
        passiveModal
      >
        {selectedServer && (
          <div>
            <p><strong>Full Name:</strong> {selectedServer.name}</p>
            <p><strong>MTM:</strong> {selectedServer.mtm}</p>
            <p><strong>Processor:</strong> {selectedServer.processor}</p>
            <p><strong>Category:</strong> {selectedServer.category}</p>
            <p><strong>Status:</strong> {selectedServer.status}</p>
            <p><strong>Document Count:</strong> {selectedServer.documentCount}</p>
            <p><strong>Last Updated:</strong> {selectedServer.lastUpdated || 'Never'}</p>
            <p><strong>Content Hash:</strong> {selectedServer.contentHash || 'Not calculated'}</p>
            <p><strong>Sales Manual URL:</strong></p>
            <a href={selectedServer.url} target="_blank" rel="noopener noreferrer" style={{ wordBreak: 'break-all', fontSize: '0.875rem' }}>
              {selectedServer.url}
            </a>
          </div>
        )}
      </Modal>
    </Grid>
  );
}

// Made with Bob
