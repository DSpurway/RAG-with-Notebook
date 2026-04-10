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
  Select,
  SelectItem,
  TextInput,
} from '@carbon/react';
import {
  DataStorage,
  MachineLearningModel,
  Search,
  DocumentBlank,
} from '@carbon/pictograms-react';
import React, { useState, useEffect } from 'react';

export default function RAGPage() {
  const [activeTab, setActiveTab] = useState(0);
  
  // Part 2 (Harry Potter) state
  const [part2Question, setPart2Question] = useState("What was the job of Mr. Dursley?");
  const [part2Chunks, setPart2Chunks] = useState([]);
  const [part2Prompt, setPart2Prompt] = useState("");
  const [part2Answer, setPart2Answer] = useState("");
  const [part2Loading, setPart2Loading] = useState(false);
  const [part2Error, setPart2Error] = useState("");
  
  // Part 3 (Sales Manual) state
  const [part3Collections, setPart3Collections] = useState([]);
  const [part3SelectedServer, setPart3SelectedServer] = useState("IBM_Power_S1012");
  const [part3Question, setPart3Question] = useState("How many dual-chip processor modules in the server?");
  const [part3Chunks, setPart3Chunks] = useState([]);
  const [part3Prompt, setPart3Prompt] = useState("");
  const [part3Answer, setPart3Answer] = useState("");
  const [part3Loading, setPart3Loading] = useState(false);
  const [part3Error, setPart3Error] = useState("");
  const [part3LoadingPDF, setPart3LoadingPDF] = useState("");

  // Configuration - these should be set via environment variables
  const config = {
    milvusHost: process.env.NEXT_PUBLIC_MILVUS_HOST || 'milvus-service',
    milvusPort: process.env.NEXT_PUBLIC_MILVUS_PORT || '19530',
    llamaHost: process.env.NEXT_PUBLIC_LLAMA_HOST || 'llama-service',
    llamaPort: process.env.NEXT_PUBLIC_LLAMA_PORT || '8080',
    // Part 3 service URLs
    listCollectionsUrl: process.env.NEXT_PUBLIC_LIST_COLLECTIONS_URL || 'http://localhost:8080',
    dropCollectionUrl: process.env.NEXT_PUBLIC_DROP_COLLECTION_URL || 'http://localhost:8080',
    loaderUrl: process.env.NEXT_PUBLIC_LOADER_URL || 'http://localhost:8080',
    getDocsUrl: process.env.NEXT_PUBLIC_GET_DOCS_URL || 'http://localhost:8080',
    promptLlmUrl: process.env.NEXT_PUBLIC_PROMPT_LLM_URL || 'http://localhost:8080',
  };

  // Part 2 Functions (Harry Potter RAG)
  const handlePart2GetDocs = async () => {
    setPart2Loading(true);
    setPart2Error("");
    setPart2Chunks([]);
    
    try {
      // This would call your Part 2 RAG service
      // For now, showing the structure
      const response = await fetch(`http://${config.milvusHost}:${config.milvusPort}/search`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          collection: 'demo',
          question: part2Question,
          k: 3
        })
      });
      
      if (!response.ok) throw new Error('Failed to retrieve documents');
      
      const data = await response.json();
      setPart2Chunks(data.chunks || []);
    } catch (error) {
      setPart2Error(error.message);
    } finally {
      setPart2Loading(false);
    }
  };

  const handlePart2BuildPrompt = () => {
    const instruction = "Instructions: Compose a single, short sentence that only answers the query, using the provided search results. If the search results do not mention anything say 'Found nothing.'\n\n";
    const searchResults = part2Chunks.map((chunk, idx) => 
      `[Page ${chunk.page}]: ${chunk.content}`
    ).join('\n\n');
    const query = `\n\nQuery: ${part2Question}\n\nAnswer: `;
    
    setPart2Prompt(instruction + "Search results:\n" + searchResults + query);
  };

  const handlePart2SendPrompt = async () => {
    setPart2Loading(true);
    setPart2Error("");
    setPart2Answer("");
    
    try {
      const response = await fetch(`http://${config.llamaHost}:${config.llamaPort}/completion`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          prompt: part2Prompt,
          temperature: 0.1,
          n_predict: 100,
          stream: false
        })
      });
      
      if (!response.ok) throw new Error('Failed to get LLM response');
      
      const data = await response.json();
      setPart2Answer(data.content || "No response");
    } catch (error) {
      setPart2Error(error.message + " - Check pod logs for details");
    } finally {
      setPart2Loading(false);
    }
  };

  // Part 3 Functions (Sales Manual RAG)
  const handlePart3ListCollections = async () => {
    setPart3Loading(true);
    setPart3Error("");
    
    try {
      const response = await fetch(`${config.listCollectionsUrl}/`);
      if (!response.ok) throw new Error('Failed to list collections');
      
      const data = await response.json();
      setPart3Collections(data.result || []);
    } catch (error) {
      setPart3Error(error.message);
    } finally {
      setPart3Loading(false);
    }
  };

  const handlePart3LoadPDF = async (serverName) => {
    setPart3LoadingPDF(serverName);
    setPart3Error("");
    
    try {
      const response = await fetch(`${config.loaderUrl}/?Server_Name=${serverName}`, {
        signal: AbortSignal.timeout(500000)
      });
      
      if (!response.ok) throw new Error('Failed to load PDF');
      
      const data = await response.json();
      if (data.result === "Success") {
        setPart3Error(`${serverName} loaded successfully!`);
      }
    } catch (error) {
      setPart3Error(`Error loading ${serverName}: ${error.message}. Check pod logs.`);
    } finally {
      setPart3LoadingPDF("");
    }
  };

  const handlePart3GetDocs = async () => {
    setPart3Loading(true);
    setPart3Error("");
    setPart3Chunks([]);
    
    try {
      const response = await fetch(
        `${config.getDocsUrl}/?Server_Name=${part3SelectedServer}&Question="${part3Question}"`
      );
      
      if (!response.ok) throw new Error('Failed to retrieve documents');
      
      const data = await response.json();
      // Parse the chunks from the response
      if (data.docs) {
        const parsed = JSON.parse(data.docs);
        setPart3Chunks(parsed || []);
      }
    } catch (error) {
      setPart3Error(error.message);
    } finally {
      setPart3Loading(false);
    }
  };

  const handlePart3BuildPrompt = () => {
    const instruction = "Instructions: Compose a single, short sentence that only answers the query, using the provided search results. If the search results do not mention anything say 'Found nothing.'\n\n";
    const searchResults = part3Chunks.map((chunk, idx) => 
      `Chunk ${idx + 1}: ${chunk[0]?.page_content || ''}`
    ).join('\n\n');
    const query = `\n\nQuery: ${part3Question}\n\nAnswer: `;
    
    setPart3Prompt(instruction + "Search results:\n" + searchResults + query);
  };

  const handlePart3SendPrompt = async () => {
    setPart3Loading(true);
    setPart3Error("");
    setPart3Answer("");
    
    try {
      const response = await fetch(config.promptLlmUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(part3Prompt)
      });
      
      if (!response.ok) throw new Error('Failed to get LLM response');
      
      const data = await response.json();
      setPart3Answer(data.answer || "No response");
    } catch (error) {
      setPart3Error(error.message + " - Check rag-prompt-llm pod logs");
    } finally {
      setPart3Loading(false);
    }
  };

  return (
    <Grid className="rag-page" fullWidth>
      <Column lg={16} md={8} sm={4} className="rag-page__banner">
        <Breadcrumb noTrailingSlash aria-label="Page navigation">
          <BreadcrumbItem>
            <a href="/">Home</a>
          </BreadcrumbItem>
        </Breadcrumb>
        <h1 className="rag-page__heading">
          Retrieval Augmented Generation (RAG) on IBM Power
        </h1>
      </Column>

      <Column lg={16} md={8} sm={4} className="rag-page__content">
        <Tabs selectedIndex={activeTab} onChange={({ selectedIndex }) => setActiveTab(selectedIndex)}>
          <TabList className="tabs-group" aria-label="RAG Demo Tabs">
            <Tab>About RAG</Tab>
            <Tab>Part 2: Harry Potter</Tab>
            <Tab>Part 3: Sales Manuals</Tab>
          </TabList>
          
          <TabPanels>
            {/* About Tab */}
            <TabPanel>
              <Grid className="tabs-group-content">
                <Column lg={16} md={8} sm={4}>
                  <Tile className="rag-info-tile">
                    <h3>What is Retrieval Augmented Generation (RAG)?</h3>
                    <p>
                      RAG is a technique that enhances Large Language Models (LLMs) by providing them with 
                      relevant context from your own documents. Instead of relying solely on the model's 
                      training data, RAG retrieves pertinent information from a knowledge base and includes 
                      it in the prompt.
                    </p>
                    
                    <h4>The RAG Process:</h4>
                    <Grid>
                      <Column lg={5} md={4} sm={4}>
                        <div style={{ textAlign: 'center', padding: '20px' }}>
                          <DataStorage height="80" width="80" />
                          <h5>1. Index Documents</h5>
                          <p>Load documents into a vector database</p>
                        </div>
                      </Column>
                      <Column lg={5} md={4} sm={4}>
                        <div style={{ textAlign: 'center', padding: '20px' }}>
                          <Search height="80" width="80" />
                          <h5>2. Retrieve Context</h5>
                          <p>Find relevant passages for your question</p>
                        </div>
                      </Column>
                      <Column lg={6} md={4} sm={4}>
                        <div style={{ textAlign: 'center', padding: '20px' }}>
                          <MachineLearningModel height="80" width="80" />
                          <h5>3. Generate Answer</h5>
                          <p>LLM uses context to provide accurate response</p>
                        </div>
                      </Column>
                    </Grid>

                    <h4>Why RAG on IBM Power?</h4>
                    <ul>
                      <li><strong>Data Sovereignty:</strong> Your data stays within your infrastructure</li>
                      <li><strong>No Retraining Needed:</strong> Update knowledge base without retraining models</li>
                      <li><strong>Cost Effective:</strong> Use smaller models with better results</li>
                      <li><strong>Reduced Hallucinations:</strong> Answers grounded in your documents</li>
                      <li><strong>MMA Acceleration:</strong> IBM Power's Matrix Math Accelerator speeds up inference</li>
                    </ul>

                    <h4>This Demo:</h4>
                    <p>
                      <strong>Part 2</strong> demonstrates basic RAG with Harry Potter text, showing how to 
                      answer questions about the story without the model having been specifically trained on it.
                    </p>
                    <p>
                      <strong>Part 3</strong> shows enterprise RAG with IBM Power Sales Manuals, demonstrating 
                      how to extract technical specifications from product documentation.
                    </p>
                  </Tile>
                </Column>
              </Grid>
            </TabPanel>

            {/* Part 2: Harry Potter Tab */}
            <TabPanel>
              <Grid className="tabs-group-content">
                <Column lg={16} md={8} sm={4}>
                  <h3>Part 2: Basic RAG with Harry Potter</h3>
                  <p>
                    This demonstrates RAG using the Harry Potter book. The text has been loaded into 
                    a Milvus vector database, and we can query it to answer questions about the story.
                  </p>

                  {part2Error && (
                    <InlineNotification
                      kind={part2Error.includes('successfully') ? 'success' : 'error'}
                      title={part2Error.includes('successfully') ? 'Success' : 'Error'}
                      subtitle={part2Error}
                      onCloseButtonClick={() => setPart2Error("")}
                    />
                  )}

                  <Tile style={{ marginTop: '20px' }}>
                    <h4>Step 1: Ask a Question</h4>
                    <TextInput
                      id="part2-question"
                      labelText="Question about Harry Potter"
                      value={part2Question}
                      onChange={(e) => setPart2Question(e.target.value)}
                      placeholder="What was the job of Mr. Dursley?"
                    />
                    <Button 
                      onClick={handlePart2GetDocs}
                      disabled={part2Loading || !part2Question}
                      style={{ marginTop: '10px' }}
                    >
                      {part2Loading ? 'Retrieving...' : 'Retrieve Relevant Passages'}
                    </Button>
                  </Tile>

                  {part2Chunks.length > 0 && (
                    <Tile style={{ marginTop: '20px' }}>
                      <h4>Step 2: Review Retrieved Passages</h4>
                      {part2Chunks.map((chunk, idx) => (
                        <div key={idx} style={{ marginBottom: '15px', padding: '10px', background: '#f4f4f4' }}>
                          <strong>Page {chunk.page}:</strong>
                          <p>{chunk.content}</p>
                        </div>
                      ))}
                      <Button onClick={handlePart2BuildPrompt} style={{ marginTop: '10px' }}>
                        Build Prompt
                      </Button>
                    </Tile>
                  )}

                  {part2Prompt && (
                    <Tile style={{ marginTop: '20px' }}>
                      <h4>Step 3: Review and Send Prompt to LLM</h4>
                      <TextArea
                        id="part2-prompt"
                        labelText="Prompt (editable)"
                        value={part2Prompt}
                        onChange={(e) => setPart2Prompt(e.target.value)}
                        rows={10}
                      />
                      <Button 
                        onClick={handlePart2SendPrompt}
                        disabled={part2Loading}
                        style={{ marginTop: '10px' }}
                      >
                        {part2Loading ? 'Generating...' : 'Send to LLM'}
                      </Button>
                    </Tile>
                  )}

                  {part2Answer && (
                    <Tile style={{ marginTop: '20px', background: '#d4f1d4' }}>
                      <h4>Answer:</h4>
                      <p style={{ fontSize: '16px', fontWeight: 'bold' }}>{part2Answer}</p>
                    </Tile>
                  )}
                </Column>
              </Grid>
            </TabPanel>

            {/* Part 3: Sales Manuals Tab */}
            <TabPanel>
              <Grid className="tabs-group-content">
                <Column lg={16} md={8} sm={4}>
                  <h3>Part 3: Enterprise RAG with Sales Manuals</h3>
                  <p>
                    This demonstrates RAG with IBM Power Sales Manual PDFs. Load the manuals, 
                    then query them for technical specifications.
                  </p>

                  {part3Error && (
                    <InlineNotification
                      kind={part3Error.includes('successfully') ? 'success' : 'error'}
                      title={part3Error.includes('successfully') ? 'Success' : 'Error'}
                      subtitle={part3Error}
                      onCloseButtonClick={() => setPart3Error("")}
                    />
                  )}

                  <Tile style={{ marginTop: '20px' }}>
                    <h4>Step 1: Load Sales Manuals</h4>
                    <p>Click to load IBM Power server sales manuals into the vector database:</p>
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '10px', marginTop: '10px' }}>
                      {['IBM_Power_S1012', 'IBM_Power_S1014', 'IBM_Power_S1022', 'IBM_Power_S1022s', 'IBM_Power_S1024'].map(server => (
                        <Button
                          key={server}
                          onClick={() => handlePart3LoadPDF(server)}
                          disabled={part3LoadingPDF === server}
                          size="sm"
                        >
                          {part3LoadingPDF === server ? 'Loading...' : server.replace('_', ' ')}
                        </Button>
                      ))}
                    </div>
                    <Button 
                      onClick={handlePart3ListCollections}
                      kind="tertiary"
                      size="sm"
                      style={{ marginTop: '10px' }}
                    >
                      List Collections
                    </Button>
                    {part3Collections.length > 0 && (
                      <p style={{ marginTop: '10px' }}>
                        <strong>Collections:</strong> {part3Collections.join(', ')}
                      </p>
                    )}
                  </Tile>

                  <Tile style={{ marginTop: '20px' }}>
                    <h4>Step 2: Query Sales Manuals</h4>
                    <Select
                      id="part3-server"
                      labelText="Select Server"
                      value={part3SelectedServer}
                      onChange={(e) => setPart3SelectedServer(e.target.value)}
                    >
                      <SelectItem value="IBM_Power_S1012" text="IBM Power S1012" />
                      <SelectItem value="IBM_Power_S1014" text="IBM Power S1014" />
                      <SelectItem value="IBM_Power_S1022" text="IBM Power S1022" />
                      <SelectItem value="IBM_Power_S1022s" text="IBM Power S1022s" />
                      <SelectItem value="IBM_Power_S1024" text="IBM Power S1024" />
                    </Select>
                    <TextInput
                      id="part3-question"
                      labelText="Question"
                      value={part3Question}
                      onChange={(e) => setPart3Question(e.target.value)}
                      placeholder="How many dual-chip processor modules in the server?"
                      style={{ marginTop: '10px' }}
                    />
                    <Button 
                      onClick={handlePart3GetDocs}
                      disabled={part3Loading}
                      style={{ marginTop: '10px' }}
                    >
                      {part3Loading ? 'Retrieving...' : 'Retrieve Relevant Passages'}
                    </Button>
                  </Tile>

                  {part3Chunks.length > 0 && (
                    <Tile style={{ marginTop: '20px' }}>
                      <h4>Step 3: Review Retrieved Passages</h4>
                      {part3Chunks.map((chunk, idx) => (
                        <div key={idx} style={{ marginBottom: '15px', padding: '10px', background: '#f4f4f4' }}>
                          <strong>Chunk {idx + 1}:</strong>
                          <p>{chunk[0]?.page_content || 'No content'}</p>
                        </div>
                      ))}
                      <Button onClick={handlePart3BuildPrompt} style={{ marginTop: '10px' }}>
                        Build Prompt
                      </Button>
                    </Tile>
                  )}

                  {part3Prompt && (
                    <Tile style={{ marginTop: '20px' }}>
                      <h4>Step 4: Review and Send Prompt to LLM</h4>
                      <TextArea
                        id="part3-prompt"
                        labelText="Prompt (editable)"
                        value={part3Prompt}
                        onChange={(e) => setPart3Prompt(e.target.value)}
                        rows={10}
                      />
                      <Button 
                        onClick={handlePart3SendPrompt}
                        disabled={part3Loading}
                        style={{ marginTop: '10px' }}
                      >
                        {part3Loading ? 'Generating...' : 'Send to LLM'}
                      </Button>
                    </Tile>
                  )}

                  {part3Answer && (
                    <Tile style={{ marginTop: '20px', background: '#d4f1d4' }}>
                      <h4>Answer:</h4>
                      <p style={{ fontSize: '16px', fontWeight: 'bold' }}>{part3Answer}</p>
                    </Tile>
                  )}
                </Column>
              </Grid>
            </TabPanel>
          </TabPanels>
        </Tabs>
      </Column>
    </Grid>
  );
}

// Made with Bob
