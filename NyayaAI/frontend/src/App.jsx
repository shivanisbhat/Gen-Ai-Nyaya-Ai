import { useState, useRef, useEffect } from 'react'
import * as pdfjsLib from 'pdfjs-dist'
import './App.css'

pdfjsLib.GlobalWorkerOptions.workerSrc = `//cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js`

function App() {
  const [fileName, setFileName] = useState('Select a document to upload')
  const [showResults, setShowResults] = useState(false)
  const [showQnaAnswer, setShowQnaAnswer] = useState(false)
  const [showChat, setShowChat] = useState(false)
  const [messages, setMessages] = useState([])
  const [userInput, setUserInput] = useState('')
  const [extractedText, setExtractedText] = useState('')
  const [isProcessing, setIsProcessing] = useState(false)
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [uploadedDocId, setUploadedDocId] = useState(null)
  const [analysisResult, setAnalysisResult] = useState(null)
  const [serverStatus, setServerStatus] = useState('unknown')
  const messagesEndRef = useRef(null)

  const API_BASE = 'http://localhost:8000'

  useEffect(() => {
    checkServerStatus()
  }, [])

  const checkServerStatus = async () => {
    try {
      const response = await fetch(`${API_BASE}/health`)
      if (response.ok) {
        const data = await response.json()
        setServerStatus('connected')
        console.log('Server status:', data)
      } else {
        setServerStatus('error')
      }
    } catch (error) {
      setServerStatus('disconnected')
      console.error(' Server not reachable:', error)
    }
  }

  const extractTextFromPDF = async (file) => {
    setIsProcessing(true)
    try {
      const arrayBuffer = await file.arrayBuffer()
      const pdf = await pdfjsLib.getDocument({ data: arrayBuffer }).promise
      let fullText = ''
      console.log(`📄 PDF Info: ${pdf.numPages} pages found`)
      
      for (let pageNum = 1; pageNum <= pdf.numPages; pageNum++) {
        console.log(`📖 Processing page ${pageNum}...`)
        const page = await pdf.getPage(pageNum)
        const textContent = await page.getTextContent()
        
        const pageText = textContent.items
          .map(item => {
            let text = item.str
            if (item.hasEOL) {
              text += '\n'
            }
            return text
          })
          .join(' ')
          .replace(/\s+/g, ' ') 
          .trim()
        
        fullText += `\n=== PAGE ${pageNum} ===\n${pageText}\n`
        console.log(`Page ${pageNum} extracted: ${pageText.length} characters`)
      }
      
      console.log('🔍 FULL EXTRACTED TEXT:')
      console.log('=' .repeat(50))
      const chunkSize = 1000
      for (let i = 0; i < fullText.length; i += chunkSize) {
        const chunk = fullText.substring(i, i + chunkSize)
        console.log(`📝 Chunk ${Math.floor(i/chunkSize) + 1}:`, chunk)
      }
      console.log('=' .repeat(50))
      console.log(`📊 Total extracted text length: ${fullText.length} characters`)
      
      setExtractedText(fullText)
      return fullText
    } catch (error) {
      console.error(' Error extracting PDF text:', error)
      alert('Error reading PDF file. Please try again.')
      return null
    } finally {
      setIsProcessing(false)
    }
  }

  const uploadPDFToServer = async (file) => {
    try {
      const formData = new FormData()
      formData.append('file', file)
      
      const response = await fetch(`${API_BASE}/doc/upload`, {
        method: 'POST',
        body: formData
      })
      
      if (response.ok) {
        const data = await response.json()
        console.log('Document uploaded:', data)
        return data.doc_id
      } else {
        const error = await response.text()
        console.error(' Upload failed:', error)
        throw new Error('Upload failed')
      }
    } catch (error) {
      console.error(' Error uploading document:', error)
      throw error
    }
  }

  const queryRAGSystem = async (docId, query) => {
    try {
      const formData = new FormData()
      formData.append('doc_id', docId.toString())
      formData.append('query', query)
      
      const response = await fetch(`${API_BASE}/query`, {
        method: 'POST',
        body: formData
      })
      
      if (response.ok) {
        const data = await response.json()
        console.log('RAG Analysis result:', data)
        return data
      } else {
        const error = await response.text()
        console.error(' Query failed:', error)
        throw new Error('Query failed')
      }
    } catch (error) {
      console.error(' Error querying RAG system:', error)
      throw error
    }
  }

  const handleFileChange = async (event) => {
    const file = event.target.files[0]
    if (file) {
      setFileName(file.name)
      // Check if it's a PDF file
      if (file.type === 'application/pdf') {
        console.log('PDF file detected, extracting text...')
        await extractTextFromPDF(file)
        
        // Upload to server for RAG processing
        if (serverStatus === 'connected') {
          try {
            const docId = await uploadPDFToServer(file)
            setUploadedDocId(docId)
            console.log('Document ready for analysis with ID:', docId)
          } catch (error) {
            console.error(' Failed to upload document:', error)
            alert('Failed to upload document to server. You can still view the extracted text.')
          }
        }
      } else {
        console.log('Non-PDF file selected:', file.name)
        alert('Please select a PDF file for AI analysis')
      }
    } else {
      setFileName('Select a document to upload')
      setExtractedText('')
      setUploadedDocId(null)
    }
  }

  const handleAnalyzeClick = () => {
    if (fileName !== 'Select a document to upload') {
      if (extractedText) {
        console.log('Analysis starting with extracted text:', extractedText.substring(0, 200) + '...')
        setShowResults(true)
      } else {
        alert('Please wait for the document to be processed')
      }
    } else {
      alert('Please select a document first')
    }
  }

  const handleAskClick = () => {
    setShowQnaAnswer(true)
  }

  const handleChatClick = () => {
    setShowChat(true)
  }

  const handleSendMessage = async (e) => {
    if (e) e.preventDefault()
    if (!userInput.trim()) return
    
    const newMessage = { text: userInput, sender: 'user' }
    setMessages(prev => [...prev, newMessage])
    const currentInput = userInput
    setUserInput('')
    
    if (uploadedDocId && serverStatus === 'connected') {
      setIsAnalyzing(true)
      try {
        const result = await queryRAGSystem(uploadedDocId, currentInput)
        
        const aiResponse = {
          text: result.answer || `Based on the document "${fileName}", I apologize but I couldn't generate a proper response. Please try rephrasing your question.`,
          sender: 'ai'
        }
        
        setMessages(prev => [...prev, aiResponse])
        setAnalysisResult(result)
        
      } catch (error) {
        const errorResponse = {
          text: 'Sorry, I encountered an error while processing your question. Please try again.',
          sender: 'ai'
        }
        setMessages(prev => [...prev, errorResponse])
      } finally {
        setIsAnalyzing(false)
      }
    } else {
      setTimeout(() => {
        const aiResponse = {
          text: `Based on the document "${fileName}", this is a response using the extracted text. The document contains ${extractedText.length} characters of text. ${uploadedDocId ? '' : 'Note: AI analysis requires server connection.'}`,
          sender: 'ai'
        }
        setMessages(prev => [...prev, aiResponse])
      }, 1000)
    }
  }

  const handleKeyPress = (e) => {
    if (e.key === 'Enter') {
      e.preventDefault()
      handleSendMessage()
    }
  }

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  return (
    <>
      <div className="container my-5">
        <div style={{maxWidth: '896px'}} className="mx-auto">
          <header className="text-center mb-5">
            <h1 className="display-5 fw-bold text-primary">NyayaAI</h1>
            <p className="lead text-muted">Simplifying your legal documents, clause by clause.</p>
            <p className="text-muted">Aapke kanooni dastavezon ko saral banaye.</p>
            
            <div className="mt-3">
              <span className={`badge ${
                serverStatus === 'connected' ? 'bg-success' : 
                serverStatus === 'error' ? 'bg-danger' : 'bg-warning'
              }`}>
                Server: {
                  serverStatus === 'connected' ? 'Connected' : 
                  serverStatus === 'error' ? 'Error' : 'Checking...'
                }
              </span>
              {uploadedDocId && (
                <span className="badge bg-info ms-2">Doc ID: {uploadedDocId}</span>
              )}
            </div>
          </header>
          
          <div className="card p-4 shadow-sm mb-5">
            <div className="row g-3 align-items-center">
              <div className="col-lg">
                <label htmlFor="doc-upload" className="upload-box w-100 p-4 rounded-3 text-center">
                  <i className="bi bi-cloud-arrow-up-fill fs-1 text-secondary"></i>
                  <span id="fileName" className="d-block mt-2 text-muted">
                    {isProcessing ? 'Processing PDF...' : fileName}
                  </span>
                  {isProcessing && (
                    <div className="spinner-border spinner-border-sm mt-2" role="status">
                      <span className="visually-hidden">Loading...</span>
                    </div>
                  )}
                </label>
                <input
                  id="doc-upload"
                  type="file"
                  className="d-none"
                  accept=".pdf,.txt,.doc,.docx"
                  onChange={handleFileChange}
                />
              </div>
              <div className="col-lg-auto">
                <select id="analysis-lang" className="form-select form-select-lg">
                  <option>English</option>
                  <option value="hi">Hindi (हिन्दी)</option>
                  <option value="ta">Tamil (தமிழ்)</option>
                </select>
              </div>
              <div className="col-lg-auto">
                <button
                  id="analyzeBtn"
                  className="btn btn-primary btn-lg w-100"
                  onClick={handleAnalyzeClick}
                  disabled={isProcessing}
                >
                  {isProcessing ? 'Processing...' : 'Analyse Document'}
                </button>
              </div>
            </div>
          </div>

          {extractedText && (
            <div className="card mb-4">
              <div className="card-header d-flex justify-content-between align-items-center">
                <h6 className="mb-0">Extracted Text ({extractedText.length} characters)</h6>
                <button
                  className="btn btn-sm btn-outline-secondary"
                  onClick={() => {
                    console.log('📋 Full extracted text copied to console:')
                    console.log(extractedText)
                    navigator.clipboard.writeText(extractedText)
                      .then(() => alert('Text copied to clipboard!'))
                      .catch(() => alert('Could not copy to clipboard'))
                  }}
                >
                  Copy Full Text
                </button>
              </div>
              <div className="card-body">
                <div className="mb-2">
                  <small className="text-muted">Preview (first 1000 characters):</small>
                </div>
                <pre className="small text-muted border p-2 rounded" style={{
                  whiteSpace: 'pre-wrap',
                  maxHeight: '300px',
                  overflowY: 'auto',
                  backgroundColor: '#f8f9fa'
                }}>
                  {extractedText.substring(0, 1000)}
                  {extractedText.length > 1000 && '\n\n... (click "Copy Full Text" to see complete content)'}
                </pre>
                <div className="mt-2">
                  <small className="text-info">
                    💡 Check browser console for full text with better formatting
                  </small>
                  {uploadedDocId && (
                    <div className="mt-1">
                      <small className="text-success">
                        Document uploaded to server - Ready for AI analysis!
                      </small>
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}

          {showResults && (
            <div className="card shadow-sm mb-4">
              <div className="card-header">
                <h5 className="mb-0">Document Analysis Results</h5>
              </div>
              <div className="card-body">
                <div className="row mb-3">
                  <div className="col-md-6">
                    <h6>Document Summary</h6>
                    <p className="text-muted">
                      Analysis of {fileName} has been completed.
                      Extracted {extractedText.length} characters of text.
                      {uploadedDocId ? ' Ready for AI-powered analysis.' : ' Local processing only.'}
                    </p>
                  </div>
                  <div className="col-md-6">
                    <h6>Key Findings</h6>
                    <ul className="list-unstyled text-muted">
                      <li>• Contract type identified</li>
                      <li>• Key clauses extracted</li>
                      <li>• {uploadedDocId ? 'AI analysis available' : 'Server required for AI analysis'}</li>
                      <li>• Simplified explanations {uploadedDocId ? 'ready' : 'pending server connection'}</li>
                    </ul>
                  </div>
                </div>
                <div className="d-flex gap-2">
                  <button className="btn btn-success" onClick={handleChatClick}>
                    <i className="bi bi-chat-dots"></i> Start Chat
                  </button>
                  <button className="btn btn-outline-primary" onClick={handleAskClick}>
                    <i className="bi bi-question-circle"></i> Ask Questions
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* Q&A section */}
          {showQnaAnswer && (
            <div className="card shadow-sm mb-4">
              <div className="card-header">
                <h5 className="mb-0">Quick Q&A about {fileName}</h5>
              </div>
              <div className="card-body">
                <div className="mb-3">
                  <h6>Common Questions:</h6>
                  <div className="list-group">
                    <button 
                      className="list-group-item list-group-item-action"
                      onClick={() => {
                        setUserInput('What are the key terms and conditions?')
                        setShowChat(true)
                      }}
                    >
                      What are the key terms and conditions?
                    </button>
                    <button 
                      className="list-group-item list-group-item-action"
                      onClick={() => {
                        setUserInput('What are the payment terms?')
                        setShowChat(true)
                      }}
                    >
                      What are the payment terms?
                    </button>
                    <button 
                      className="list-group-item list-group-item-action"
                      onClick={() => {
                        setUserInput('What are the cancellation clauses?')
                        setShowChat(true)
                      }}
                    >
                      What are the cancellation clauses?
                    </button>
                    <button 
                      className="list-group-item list-group-item-action"
                      onClick={() => {
                        setUserInput('Are there any hidden fees or charges?')
                        setShowChat(true)
                      }}
                    >
                      Are there any hidden fees or charges?
                    </button>
                  </div>
                </div>
                <div className="text-center">
                  <button className="btn btn-primary" onClick={handleChatClick}>
                    Switch to Interactive Chat
                  </button>
                </div>
              </div>
            </div>
          )}

          {showChat && (
            <div className="card shadow-sm chat-container">
              <div className="card-header text-center fw-bold d-flex justify-content-between align-items-center">
                <span>Chat about: {fileName}</span>
                {uploadedDocId && (
                  <small className="text-success">AI-Powered</small>
                )}
              </div>
              <div className="messages-container d-flex flex-column">
                {messages.length === 0 && (
                  <div className="text-center text-muted py-4">
                    <p>Start by asking a question about your document!</p>
                    {uploadedDocId && (
                      <small>Try: "What are the key terms in this contract?"</small>
                    )}
                  </div>
                )}
                
                {messages.map((msg, index) => (
                  <div key={index} className={`message ${msg.sender}-message`}>
                    {msg.text}
                  </div>
                ))}
                
                {isAnalyzing && (
                  <div className="message ai-message">
                    <div className="d-flex align-items-center">
                      <div className="spinner-border spinner-border-sm me-2" role="status">
                        <span className="visually-hidden">Loading...</span>
                      </div>
                      Analyzing your question...
                    </div>
                  </div>
                )}
                
                <div ref={messagesEndRef} />
              </div>
              <div className="chat-input-area">
                <form onSubmit={handleSendMessage}>
                  <div className="input-group">
                    <input
                      type="text"
                      className="form-control form-control-lg"
                      placeholder={uploadedDocId ? "Ask a question..." : "Ask a question (AI analysis requires server connection)"}
                      value={userInput}
                      onChange={(e) => setUserInput(e.target.value)}
                      onKeyPress={handleKeyPress}
                      disabled={isAnalyzing}
                    />
                    <button 
                      className="btn btn-primary" 
                      type="submit"
                      disabled={isAnalyzing || !userInput.trim()}
                    >
                      {isAnalyzing ? 'Sending...' : 'Send'}
                    </button>
                  </div>
                </form>
              </div>
            </div>
          )}

          {analysisResult && (
            <div className="card shadow-sm mt-4">
              <div className="card-header">
                <h5 className="mb-0">🏛️ Latest AI Analysis</h5>
              </div>
              <div className="card-body">
                <div className="mb-3">
                  <h6 className="text-primary">AI Explanation:</h6>
                  <div className="alert alert-info">
                    <div style={{whiteSpace: 'pre-line'}}>
                      {analysisResult.answer}
                    </div>
                  </div>
                </div>

                {analysisResult.user_clause && (
                  <div className="mb-3">
                    <h6 className="text-primary">Analyzed Clause:</h6>
                    <div className="alert alert-light">
                      <small>
                        {analysisResult.user_clause.text?.substring(0, 300)}
                        {analysisResult.user_clause.text?.length > 300 && '...'}
                      </small>
                    </div>
                  </div>
                )}

                {analysisResult.kb_hits && analysisResult.kb_hits.length > 0 && (
                  <div className="mb-3">
                    <h6 className="text-primary">📚 Knowledge Base References:</h6>
                    {analysisResult.kb_hits.map((hit, index) => (
                      <div key={index} className="alert alert-warning py-2">
                        <small>
                          <strong>{hit.act || 'Legal Reference'} - {hit.section || 'Unknown Section'}</strong><br/>
                          Relevance Score: {(hit.score || 0).toFixed(3)}
                        </small>
                      </div>
                    ))}
                  </div>
                )}

                {analysisResult.model_used && (
                  <div className="text-muted">
                    <small>⚙️ Analysis powered by: {analysisResult.model_used}</small>
                  </div>
                )}
              </div>
            </div>
          )}

          <div className="alert alert-warning mt-5" role="alert">
            <h4 className="alert-heading">Important Disclaimer</h4>
            <p>This analysis is generated by an AI model and is for informational purposes only. It is not a substitute for professional legal advice. Always consult a qualified legal professional for any legal matters.</p>
          </div>
        </div>
      </div>
    </>
  )
}

export default App