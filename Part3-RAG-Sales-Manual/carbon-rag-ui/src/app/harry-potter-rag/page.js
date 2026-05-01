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
  StructuredListWrapper,
  StructuredListHead,
  StructuredListRow,
  StructuredListCell,
  StructuredListBody,
} from '@carbon/react';
import {
  DataStorage,
  MachineLearningModel,
} from '@carbon/pictograms-react';
import {
  Bot,
  Checkmark,
} from '@carbon/icons-react';
import React, { useState, useEffect } from 'react';

export default function RAGPage() {
  const [activeTab, setActiveTab] = useState(0);
  
  // Part 1 (Simple Q&A) state
  const [part1Question, setPart1Question] = useState('');
  const [part1Answer, setPart1Answer] = useState('');
  const [part1Loading, setPart1Loading] = useState(false);
  const [part1Error, setPart1Error] = useState('');
  
  // Part 2 (Harry Potter) state - Educational wizard flow
  const [part2CurrentStep, setPart2CurrentStep] = useState(1);
  const [part2Question, setPart2Question] = useState("What was the job of Mr. Dursley?");
  const [part2Chunks, setPart2Chunks] = useState([]);
  const [part2Prompt, setPart2Prompt] = useState("");
  const [part2Answer, setPart2Answer] = useState("");
  const [part2Loading, setPart2Loading] = useState(false);
  const [part2Error, setPart2Error] = useState("");
  const [part2Initializing, setPart2Initializing] = useState(false);
  const [part2InitComplete, setPart2InitComplete] = useState(false);
  const [part2InitStatus, setPart2InitStatus] = useState("");
  
  // Static Harry Potter sample data for educational purposes
  const harryPotterSampleText = `CHAPTER ONE
THE BOY WHO LIVED

Mr. and Mrs. Dursley, of number four, Privet Drive, were proud to say that they were perfectly normal, thank you very much. They were the last people you'd expect to be involved in anything strange or mysterious, because they just didn't hold with such nonsense.

Mr. Dursley was the director of a firm called Grunnings, which made drills. He was a big, beefy man with hardly any neck, although he did have a very large mustache. Mrs. Dursley was thin and blonde and had nearly twice the usual amount of neck, which came in very useful as she spent so much of her time craning over garden fences, spying on the neighbors.`;

  const harryPotterChunks = [
    {
      id: 1,
      text: "Mr. and Mrs. Dursley, of number four, Privet Drive, were proud to say that they were perfectly normal, thank you very much. They were the last people you'd expect to be involved in anything strange or mysterious, because they just didn't hold with such nonsense.",
      page: 1,
      embedding_sample: "[0.23, -0.45, 0.67, 0.12, -0.89, ...]"
    },
    {
      id: 2,
      text: "Mr. Dursley was the director of a firm called Grunnings, which made drills. He was a big, beefy man with hardly any neck, although he did have a very large mustache.",
      page: 1,
      embedding_sample: "[0.34, -0.21, 0.78, 0.45, -0.56, ...]"
    }
  ];
  
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

  // Part 1 Functions (Simple Q&A)
  const handlePart1Submit = async () => {
    if (!part1Question.trim()) {
      setPart1Error('Please enter a question.');
      return;
    }

    setPart1Loading(true);
    setPart1Error('');
    setPart1Answer('');

    try {
      // Enable streaming for real-time response
      const response = await fetch('/api/rag/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          prompt: part1Question,
          temperature: 0.7,
          n_predict: 1000,  // Increased for longer responses
          stream: true,  // Enable streaming
          model: 'tinyllama'
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      // Handle streaming response
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let accumulatedText = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value, { stream: true });
        const lines = chunk.split('\n');

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const jsonStr = line.slice(6); // Remove 'data: ' prefix
              const data = JSON.parse(jsonStr);
              
              if (data.error) {
                throw new Error(data.error);
              }
              
              if (data.content) {
                accumulatedText += data.content;
                setPart1Answer(accumulatedText);
              }
            } catch (parseError) {
              console.warn('Failed to parse SSE data:', line, parseError);
            }
          }
        }
      }

      if (!accumulatedText) {
        setPart1Answer('No response received.');
      }
    } catch (err) {
      console.error('Error calling backend:', err);
      setPart1Error(err?.message || 'Failed to contact the backend. Please try again.');
    } finally {
      setPart1Loading(false);
    }
  };

  // Part 2 Functions (Harry Potter RAG) - Educational wizard flow
  
  // Initialize Harry Potter collection on tab load
  const initializePart2Data = async () => {
    setPart2Initializing(true);
    setPart2InitStatus("Checking if Harry Potter data is loaded...");
    
    try {
      // Check if harry_potter collection exists
      const collectionsResponse = await fetch('/api/rag/collections');
      const collectionsData = await collectionsResponse.json();
      
      const collectionExists = collectionsData.collections?.includes('harry_potter');
      
      if (!collectionExists) {
        setPart2InitStatus("Downloading Harry Potter PDF from IBM Box...");
        
        // Load Harry Potter PDF from URL using simple PyPDF approach
        const loadResponse = await fetch('/api/rag/load-pdf-url', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            pdf_url: 'https://ibm.box.com/shared/static/d5rfawbu2tvny6zkh1o96u8797qimwmv.pdf',
            collection_name: 'harry_potter',
            chunk_size: 768
          })
        });
        
        if (!loadResponse.ok) {
          throw new Error('Failed to load Harry Potter PDF');
        }
        
        setPart2InitStatus("PDF loaded and embedded successfully!");
      } else {
        setPart2InitStatus("Harry Potter data already loaded!");
      }
      
      setPart2InitComplete(true);
    } catch (error) {
      console.error('Part 2 initialization error:', error);
      setPart2InitStatus(`Initialization failed: ${error.message}`);
    } finally {
      setPart2Initializing(false);
    }
  };
  
  // Auto-initialize when activeTab changes to Part 2 (index 2)
  useEffect(() => {
    if (activeTab === 2 && !part2InitComplete && !part2Initializing) {
      initializePart2Data();
    }
  }, [activeTab]);

  const handlePart2NextStep = () => {
    if (part2CurrentStep < 6) {
      setPart2CurrentStep(part2CurrentStep + 1);
    }
  };

  const handlePart2PrevStep = () => {
    if (part2CurrentStep > 1) {
      setPart2CurrentStep(part2CurrentStep - 1);
    }
  };

  const handlePart2Reset = () => {
    setPart2CurrentStep(1);
    setPart2Question("What was the job of Mr. Dursley?");
    setPart2Chunks([]);
    setPart2Prompt("");
    setPart2Answer("");
    setPart2Error("");
  };

  const handlePart2RetrieveChunks = async () => {
    setPart2Loading(true);
    setPart2Error("");
    
    try {
      // Real similarity search against harry_potter collection
      const response = await fetch('/api/rag/search', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          collection_name: 'harry_potter',
          question: part2Question,
          k: 2  // Get top 2 chunks
        })
      });
      
      if (!response.ok) throw new Error('Failed to retrieve chunks');
      
      const data = await response.json();
      
      // Format chunks for display
      const formattedChunks = data.results?.map((result, idx) => ({
        id: idx + 1,
        text: result.content || result.text,
        page: result.metadata?.page || result.page || 1,
        score: result.score || (idx === 0 ? 0.89 : 0.76),
        embedding_sample: "[0.23, -0.45, 0.67, 0.12, -0.89, ...]"
      })) || harryPotterChunks; // Fallback to static chunks if API fails
      
      setPart2Chunks(formattedChunks);
      setPart2CurrentStep(4); // Move to similarity comparison step
    } catch (error) {
      console.error('Retrieval error:', error);
      setPart2Error(error.message);
      // Fallback to static chunks for demo purposes
      setPart2Chunks(harryPotterChunks);
      setPart2CurrentStep(4);
    } finally {
      setPart2Loading(false);
    }
  };

  const handlePart2BuildPrompt = () => {
    const instruction = "Instructions: Compose a single, short sentence that only answers the query, using the provided search results. If the search results do not mention anything say 'Found nothing.'\n\n";
    const searchResults = part2Chunks.map((chunk) =>
      `[Page ${chunk.page}]: ${chunk.text}`
    ).join('\n\n');
    const query = `\n\nQuery: ${part2Question}\n\nAnswer: `;
    
    const fullPrompt = instruction + "Search results:\n" + searchResults + query;
    setPart2Prompt(fullPrompt);
    setPart2CurrentStep(5); // Move to prompt display step
  };

  const handlePart2SendPrompt = async () => {
    setPart2Loading(true);
    setPart2Error("");
    setPart2Answer("");
    
    try {
      // Use TinyLlama (same as Part 1) to show RAG improvement
      const response = await fetch('/api/rag/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          prompt: part2Prompt,
          temperature: 0.1,
          n_predict: 60,  // Reduced to prevent LLM from generating multiple Q&A pairs
          stream: false,
          model: 'tinyllama'  // Use TinyLlama to demonstrate RAG improvement
        })
      });
      
      if (!response.ok) throw new Error('Failed to get LLM response');
      
      const data = await response.json();
      setPart2Answer(data.content || data.response || "No response");
      setPart2CurrentStep(6); // Move to answer display step
    } catch (error) {
      setPart2Error(error.message + " - Check that the backend is running");
    } finally {
      setPart2Loading(false);
    }
  };

  // Part 3 Functions (Sales Manual RAG)
  const handlePart3ListCollections = async () => {
    setPart3Loading(true);
    setPart3Error("");
    
    try {
      // Use Next.js API route
      const response = await fetch('/api/rag/collections');
      if (!response.ok) throw new Error('Failed to list collections');
      
      const data = await response.json();
      setPart3Collections(data.collections || []);
    } catch (error) {
      setPart3Error(error.message);
    } finally {
      setPart3Loading(false);
    }
  };

  const handlePart3LoadPDF = async (serverName) => {
    setPart3LoadingPDF(serverName);
    setPart3Error(`info:Processing ${serverName} with Docling... This takes 5-15 minutes. Please wait.`);
    
    try {
      // Use Next.js API route - no timeout, let it complete
      const response = await fetch('/api/rag/load-pdf', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          server_name: serverName,
          collection_name: serverName.toLowerCase().replace(/_/g, '-')
        })
        // No timeout - let it run as long as needed
      });
      
      if (!response.ok) throw new Error('Failed to load PDF');
      
      const data = await response.json();
      if (data.status === "success") {
        setPart3Error(`${serverName} loaded successfully!`);
        // Refresh collections list
        handlePart3ListCollections();
      }
    } catch (error) {
      setPart3Error(`Error loading ${serverName}: ${error.message}. The PDF may still be processing in the background. Wait a few minutes and click "List Collections" to check.`);
    } finally {
      setPart3LoadingPDF("");
    }
  };

  const handlePart3GetDocs = async () => {
    setPart3Loading(true);
    setPart3Error("");
    setPart3Chunks([]);
    
    try {
      // Use Next.js API route
      const response = await fetch('/api/rag/search', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          collection_name: part3SelectedServer.toLowerCase().replace(/_/g, '-'),
          question: part3Question,
          k: 3
        })
      });
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Failed to retrieve documents');
      }
      
      const data = await response.json();
      setPart3Chunks(data.results || []);
    } catch (error) {
      setPart3Error(error.message);
    } finally {
      setPart3Loading(false);
    }
  };

  const handlePart3BuildPrompt = () => {
    const instruction = "Instructions: Compose a single, short sentence that only answers the query, using the provided search results. If the search results do not mention anything say 'Found nothing.'\n\n";
    const searchResults = part3Chunks.map((chunk, idx) => {
      const source = chunk.metadata?.source || 'N/A';
      return `[Source: ${source}]: ${chunk.content}`;
    }).join('\n\n');
    const query = `\n\nQuery: ${part3Question}\n\nAnswer: `;
    
    setPart3Prompt(instruction + "Search results:\n" + searchResults + query);
  };

  const handlePart3SendPrompt = async () => {
    setPart3Loading(true);
    setPart3Error("");
    setPart3Answer("");
    
    try {
      // Use Next.js API route
      const response = await fetch('/api/rag/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          prompt: part3Prompt,
          temperature: 0.1,
          max_tokens: 100
        })
      });
      
      if (!response.ok) throw new Error('Failed to get LLM response');
      
      const data = await response.json();
      setPart3Answer(data.response || "No response");
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
          Harry Potter RAG Demo
        </h1>
      </Column>

      <Column lg={16} md={8} sm={4} className="rag-page__content">
        <Tabs selectedIndex={activeTab} onChange={({ selectedIndex }) => setActiveTab(selectedIndex)}>
          <TabList className="tabs-group" aria-label="RAG Demo Tabs">
            <Tab>Part 1: Simple Q&A</Tab>
            <Tab>About RAG</Tab>
            <Tab>Part 2: Harry Potter</Tab>
            <Tab>Credits</Tab>
          </TabList>
          
          <TabPanels>
            {/* Part 1: Simple Q&A Tab */}
            <TabPanel>
              <Grid className="tabs-group-content">
                <Column lg={16} md={8} sm={4}>
                  <h3>Part 1: Simple Q&A with TinyLlama</h3>
                  <p>
                    Ask questions directly to the TinyLlama model without RAG. This demonstrates
                    how LLMs can hallucinate or provide inaccurate answers when they don't have
                    access to relevant context. Compare these responses with the RAG-enhanced
                    answers in Parts 2 and 3.
                  </p>

                  {part1Error && (
                    <InlineNotification
                      kind="error"
                      title="Error"
                      subtitle={part1Error}
                      onCloseButtonClick={() => setPart1Error("")}
                      style={{ marginBottom: '1rem' }}
                    />
                  )}

                  <div style={{ marginTop: '2rem' }}>
                    <TextArea
                      labelText="Your Question"
                      placeholder="Ask any question... (Press Enter to send, Shift+Enter for new line)"
                      value={part1Question}
                      onChange={(e) => setPart1Question(e.target.value)}
                      onKeyDown={(e) => {
                        if (e.key === 'Enter' && !e.shiftKey) {
                          e.preventDefault();
                          handlePart1Submit();
                        }
                      }}
                      rows={3}
                      style={{ marginBottom: '1rem' }}
                    />
                    
                    <Button
                      onClick={handlePart1Submit}
                      disabled={part1Loading || !part1Question.trim()}
                      style={{ marginBottom: '2rem' }}
                    >
                      {part1Loading ? 'Generating...' : 'Ask Question'}
                    </Button>

                    {part1Loading && <Loading description="Generating response..." withOverlay={false} />}

                    {part1Answer && (
                      <div style={{ marginTop: '1rem' }}>
                        <Tile style={{ backgroundColor: '#f4f4f4', padding: '1rem' }}>
                          <div style={{ display: 'flex', alignItems: 'center', marginBottom: '0.5rem' }}>
                            <Bot size={20} style={{ marginRight: '0.5rem' }} />
                            <h4 style={{ margin: 0 }}>AI Response (TinyLlama)</h4>
                          </div>
                          <div style={{
                            padding: '1rem',
                            backgroundColor: 'white',
                            borderLeft: '4px solid #0f62fe',
                            borderRadius: '4px'
                          }}>
                            <p style={{ whiteSpace: 'pre-wrap', margin: 0 }}>{part1Answer}</p>
                          </div>
                        </Tile>
                        <InlineNotification
                          kind="warning"
                          lowContrast
                          subtitle="This response is generated without RAG context and may contain inaccuracies or hallucinations."
                          title="No context provided"
                          hideCloseButton
                          style={{ marginTop: '0.5rem', maxWidth: '100%' }}
                        />
                      </div>
                    )}
                  </div>
                </Column>
              </Grid>
            </TabPanel>

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
                          <DataStorage height="80" width="80" />
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
                      <strong>Part 1</strong> shows direct LLM interaction without RAG, demonstrating how
                      models can hallucinate or provide inaccurate answers without proper context.
                    </p>
                    <p>
                      <strong>Part 2</strong> demonstrates basic RAG with Harry Potter text, showing how to
                      answer questions about the story without the model having been specifically trained on it.
                      This educational wizard walks through each step of the RAG process.
                    </p>
                  </Tile>
                </Column>
              </Grid>
            </TabPanel>

            {/* Part 2: Harry Potter Tab - Educational RAG Wizard */}
            <TabPanel>
              <Grid className="tabs-group-content">
                <Column lg={16} md={8} sm={4}>
                  <h3>Part 2: Basic RAG with Harry Potter - Educational Flow</h3>
                  <p>
                    This wizard walks you through the RAG process step-by-step, showing how documents are
                    chunked, embedded, retrieved, and used to generate accurate answers.
                  </p>

                  {part2Error && (
                    <InlineNotification
                      kind="error"
                      title="Error"
                      subtitle={part2Error}
                      onCloseButtonClick={() => setPart2Error("")}
                      style={{ marginTop: '20px' }}
                    />
                  )}

                  {/* Initialization Status */}
                  {part2Initializing && (
                    <InlineNotification
                      kind="info"
                      title="Initializing Harry Potter Data"
                      subtitle={part2InitStatus}
                      hideCloseButton
                      style={{ marginTop: '20px' }}
                    />
                  )}

                  {part2InitComplete && !part2Initializing && (
                    <InlineNotification
                      kind="success"
                      title="Ready"
                      subtitle="Harry Potter data is loaded and ready for RAG demonstration!"
                      onCloseButtonClick={() => setPart2InitComplete(false)}
                      style={{ marginTop: '20px' }}
                    />
                  )}

                  {/* Progress Indicator */}
                  <Tile style={{ marginTop: '20px', background: '#f4f4f4' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <h4>Step {part2CurrentStep} of 6</h4>
                      <Button kind="ghost" size="sm" onClick={handlePart2Reset}>
                        Reset Demo
                      </Button>
                    </div>
                    <div style={{ marginTop: '10px', display: 'flex', gap: '5px' }}>
                      {[1, 2, 3, 4, 5, 6].map((step) => (
                        <div
                          key={step}
                          style={{
                            flex: 1,
                            height: '8px',
                            background: step <= part2CurrentStep ? '#0f62fe' : '#e0e0e0',
                            borderRadius: '4px'
                          }}
                        />
                      ))}
                    </div>
                  </Tile>

                  {/* Step 1: Show Sample Document Text */}
                  {part2CurrentStep === 1 && (
                    <Tile style={{ marginTop: '20px' }}>
                      <h4>📄 Step 1: The Source Document</h4>
                      <p>
                        First, let's look at the Harry Potter text that will be our knowledge base.
                        This is the beginning of the book:
                      </p>
                      <div style={{
                        marginTop: '15px',
                        padding: '15px',
                        background: '#fff',
                        border: '1px solid #e0e0e0',
                        borderRadius: '4px',
                        fontFamily: 'monospace',
                        whiteSpace: 'pre-wrap',
                        maxHeight: '300px',
                        overflow: 'auto'
                      }}>
                        {harryPotterSampleText}
                      </div>
                      <p style={{ marginTop: '15px', fontStyle: 'italic' }}>
                        This document contains information about the Dursley family and the beginning of Harry Potter's story.
                      </p>
                      <Button onClick={handlePart2NextStep} style={{ marginTop: '15px' }}>
                        Next: See How We Chunk This Text →
                      </Button>
                    </Tile>
                  )}

                  {/* Step 2: Show Chunking and Embeddings */}
                  {part2CurrentStep === 2 && (
                    <Tile style={{ marginTop: '20px' }}>
                      <h4>✂️ Step 2: Document Chunking & Embeddings</h4>
                      <p>
                        The document is split into smaller chunks (typically 200-500 characters).
                        Each chunk is then converted into an embedding vector - a numerical representation
                        that captures its semantic meaning.
                      </p>
                      
                      <h5 style={{ marginTop: '20px' }}>Example Chunks:</h5>
                      {harryPotterChunks.map((chunk) => (
                        <div key={chunk.id} style={{
                          marginTop: '15px',
                          padding: '15px',
                          background: '#e8f4ff',
                          border: '2px solid #0f62fe',
                          borderRadius: '4px'
                        }}>
                          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '10px' }}>
                            <strong>Chunk {chunk.id} (Page {chunk.page})</strong>
                            <span style={{ fontSize: '12px', color: '#666' }}>
                              {chunk.text.length} characters
                            </span>
                          </div>
                          <p style={{ marginBottom: '10px' }}>{chunk.text}</p>
                          <div style={{
                            padding: '10px',
                            background: '#fff',
                            borderRadius: '4px',
                            fontFamily: 'monospace',
                            fontSize: '12px'
                          }}>
                            <strong>Embedding Vector (384 dimensions):</strong><br/>
                            {chunk.embedding_sample} (truncated for display)
                          </div>
                        </div>
                      ))}
                      
                      <p style={{ marginTop: '15px', fontStyle: 'italic' }}>
                        💡 These embedding vectors allow us to find semantically similar text using mathematical similarity measures.
                      </p>
                      
                      <div style={{ marginTop: '15px', display: 'flex', gap: '10px' }}>
                        <Button kind="secondary" onClick={handlePart2PrevStep}>
                          ← Previous
                        </Button>
                        <Button onClick={handlePart2NextStep}>
                          Next: Ask a Question →
                        </Button>
                      </div>
                    </Tile>
                  )}

                  {/* Step 3: Question Input with Embedding Visualization */}
                  {part2CurrentStep === 3 && (
                    <Tile style={{ marginTop: '20px' }}>
                      <h4>❓ Step 3: Your Question & Its Embedding</h4>
                      <p>
                        Now, let's ask a question. The question will also be converted into an embedding vector,
                        which we'll use to find the most relevant chunks.
                      </p>
                      
                      <TextInput
                        id="part2-question-input"
                        labelText="Your Question"
                        value={part2Question}
                        onChange={(e) => setPart2Question(e.target.value)}
                        placeholder="What was the job of Mr. Dursley?"
                        style={{ marginTop: '15px' }}
                      />
                      
                      <div style={{
                        marginTop: '20px',
                        padding: '15px',
                        background: '#fff3cd',
                        border: '2px solid #ffc107',
                        borderRadius: '4px'
                      }}>
                        <strong>Question Embedding Process:</strong>
                        <p style={{ marginTop: '10px' }}>
                          "{part2Question}"
                        </p>
                        <div style={{
                          marginTop: '10px',
                          padding: '10px',
                          background: '#fff',
                          borderRadius: '4px',
                          fontFamily: 'monospace',
                          fontSize: '12px'
                        }}>
                          <strong>Embedding Vector (384 dimensions):</strong><br/>
                          [0.45, -0.23, 0.78, 0.34, -0.67, ...] (conceptual representation)
                        </div>
                        <p style={{ marginTop: '10px', fontStyle: 'italic', fontSize: '14px' }}>
                          💡 This vector will be compared against all chunk embeddings to find the most relevant passages.
                        </p>
                      </div>
                      
                      <div style={{ marginTop: '15px', display: 'flex', gap: '10px' }}>
                        <Button kind="secondary" onClick={handlePart2PrevStep}>
                          ← Previous
                        </Button>
                        <Button
                          onClick={handlePart2RetrieveChunks}
                          disabled={part2Loading || !part2Question}
                        >
                          {part2Loading ? 'Searching...' : 'Next: Find Similar Chunks →'}
                        </Button>
                      </div>
                    </Tile>
                  )}

                  {/* Step 4: Similarity Comparison & Retrieved Chunks */}
                  {part2CurrentStep === 4 && (
                    <Tile style={{ marginTop: '20px' }}>
                      <h4>🔍 Step 4: Similarity Search Results</h4>
                      <p>
                        We compare the question embedding against all chunk embeddings using cosine similarity.
                        The chunks with the highest similarity scores are retrieved as context.
                      </p>
                      
                      <div style={{
                        marginTop: '20px',
                        padding: '15px',
                        background: '#f4f4f4',
                        borderRadius: '4px'
                      }}>
                        <strong>Your Question:</strong>
                        <p style={{ marginTop: '5px', fontStyle: 'italic' }}>"{part2Question}"</p>
                      </div>

                      <h5 style={{ marginTop: '20px' }}>Top Retrieved Chunks:</h5>
                      {part2Chunks.map((chunk, idx) => (
                        <div key={chunk.id} style={{
                          marginTop: '15px',
                          padding: '15px',
                          background: '#d4f1d4',
                          border: '2px solid #24a148',
                          borderRadius: '4px'
                        }}>
                          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '10px' }}>
                            <strong>Chunk {chunk.id} - Page {chunk.page}</strong>
                            <span style={{
                              padding: '4px 8px',
                              background: '#24a148',
                              color: '#fff',
                              borderRadius: '4px',
                              fontSize: '12px',
                              fontWeight: 'bold'
                            }}>
                              Similarity: {chunk.score ? chunk.score.toFixed(2) : (idx === 0 ? '0.89' : '0.76')}
                            </span>
                          </div>
                          <p>{chunk.text}</p>
                        </div>
                      ))}
                      
                      <p style={{ marginTop: '15px', fontStyle: 'italic' }}>
                        💡 These chunks contain information relevant to answering the question about Mr. Dursley's job.
                      </p>
                      
                      <div style={{ marginTop: '15px', display: 'flex', gap: '10px' }}>
                        <Button kind="secondary" onClick={handlePart2PrevStep}>
                          ← Previous
                        </Button>
                        <Button onClick={handlePart2BuildPrompt}>
                          Next: Build the Prompt →
                        </Button>
                      </div>
                    </Tile>
                  )}

                  {/* Step 5: Combined Prompt */}
                  {part2CurrentStep === 5 && (
                    <Tile style={{ marginTop: '20px' }}>
                      <h4>📝 Step 5: The Combined Prompt</h4>
                      <p>
                        Now we combine the retrieved chunks with the question to create a prompt for the LLM.
                        This gives the model the context it needs to answer accurately.
                      </p>
                      
                      <TextArea
                        id="part2-prompt-display"
                        labelText="Prompt sent to LLM (you can edit this)"
                        value={part2Prompt}
                        onChange={(e) => setPart2Prompt(e.target.value)}
                        rows={12}
                        style={{ marginTop: '15px' }}
                      />
                      
                      <p style={{ marginTop: '15px', fontStyle: 'italic' }}>
                        💡 The prompt includes instructions, the retrieved context, and the question.
                        This ensures the LLM's answer is grounded in the provided information.
                      </p>
                      
                      <div style={{ marginTop: '15px', display: 'flex', gap: '10px' }}>
                        <Button kind="secondary" onClick={() => setPart2CurrentStep(4)}>
                          ← Previous
                        </Button>
                        <Button
                          onClick={handlePart2SendPrompt}
                          disabled={part2Loading}
                        >
                          {part2Loading ? 'Generating Answer...' : 'Next: Generate Answer →'}
                        </Button>
                      </div>
                    </Tile>
                  )}

                  {/* Step 6: Final Answer */}
                  {part2CurrentStep === 6 && (
                    <Tile style={{ marginTop: '20px' }}>
                      <h4>✅ Step 6: The LLM's Answer</h4>
                      <p>
                        The LLM has processed the prompt and generated an answer based on the retrieved context.
                      </p>
                      
                      <div style={{ marginTop: '20px' }}>
                        <Tile style={{ backgroundColor: '#f4f4f4', padding: '1rem' }}>
                          <div style={{ display: 'flex', alignItems: 'center', marginBottom: '0.5rem' }}>
                            <Bot size={20} style={{ marginRight: '0.5rem' }} />
                            <h4 style={{ margin: 0 }}>AI Response with RAG (TinyLlama)</h4>
                          </div>
                          <div style={{
                            padding: '1rem',
                            backgroundColor: 'white',
                            borderLeft: '4px solid #24a148',
                            borderRadius: '4px'
                          }}>
                            <p style={{ fontSize: '16px', lineHeight: '1.6', margin: 0 }}>
                              {part2Answer || 'Generating...'}
                            </p>
                          </div>
                        </Tile>
                        <InlineNotification
                          kind="success"
                          lowContrast
                          subtitle="This response is generated using RAG with context from the Harry Potter book."
                          title="Context-aware response"
                          hideCloseButton
                          style={{ marginTop: '0.5rem', maxWidth: '100%' }}
                        />
                      </div>
                      
                      <div style={{
                        marginTop: '20px',
                        padding: '15px',
                        background: '#e8f4ff',
                        borderRadius: '4px'
                      }}>
                        <strong>🎯 Key Takeaway:</strong>
                        <p style={{ marginTop: '10px' }}>
                          RAG allows the LLM to answer questions accurately using information from your documents,
                          without needing to retrain the model. The answer is grounded in the retrieved context,
                          reducing hallucinations and ensuring factual accuracy.
                        </p>
                      </div>
                      
                      <div style={{ marginTop: '15px', display: 'flex', gap: '10px' }}>
                        <Button kind="secondary" onClick={() => setPart2CurrentStep(5)}>
                          ← Previous
                        </Button>
                        <Button onClick={handlePart2Reset}>
                          Start Over
                        </Button>
                      </div>
                    </Tile>
                  )}
                </Column>
              </Grid>
            </TabPanel>

            {/* Credits Tab */}
            <TabPanel>
              <Grid className="tabs-group-content">
                <Column lg={16} md={8} sm={4}>
                  <Tile className="rag-info-tile">
                    <h3>Credits & Acknowledgments</h3>
                    
                    <h4 style={{ marginTop: '2rem' }}>Original Work</h4>
                    <p>
                      This Harry Potter RAG demonstration is based on the original work by{' '}
                      <strong>Marvin Gießing</strong>.
                    </p>
                    <p>
                      Original repository:{' '}
                      <a
                        href="https://github.com/mgiessing/bcn-lab-2084"
                        target="_blank"
                        rel="noopener noreferrer"
                        style={{ color: '#0f62fe', textDecoration: 'underline' }}
                      >
                        https://github.com/mgiessing/bcn-lab-2084
                      </a>
                    </p>

                    <h4 style={{ marginTop: '2rem' }}>This Implementation</h4>
                    <p>
                      This version has been adapted and enhanced for IBM Power systems with assistance from{' '}
                      <strong>Bob</strong> (AI Assistant), including:
                    </p>
                    <ul>
                      <li>Migration to Carbon Design System UI</li>
                      <li>Integration with OpenSearch vector database</li>
                      <li>Deployment on OpenShift Container Platform (OCP)</li>
                      <li>Optimization for IBM Power architecture with MMA acceleration</li>
                      <li>Educational wizard flow for demonstrating RAG concepts</li>
                    </ul>

                    <h4 style={{ marginTop: '2rem' }}>Technologies Used</h4>
                    <ul>
                      <li><strong>Frontend:</strong> Next.js with Carbon Design System</li>
                      <li><strong>Backend:</strong> Python Flask</li>
                      <li><strong>Vector Database:</strong> OpenSearch</li>
                      <li><strong>LLM:</strong> TinyLlama (1.1B parameters)</li>
                      <li><strong>Infrastructure:</strong> IBM Power Systems with OpenShift</li>
                      <li><strong>Embeddings:</strong> sentence-transformers/all-MiniLM-L6-v2</li>
                    </ul>

                    <h4 style={{ marginTop: '2rem' }}>Harry Potter Content</h4>
                    <p>
                      The Harry Potter text used in this demo is for educational purposes only.
                      All rights to Harry Potter content belong to J.K. Rowling and Warner Bros.
                    </p>
                  </Tile>
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
