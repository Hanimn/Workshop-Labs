"""
CTI Web Interface - Streamlined web UI for Multi-language CTI Pipeline
Integrates Phase 1 (Ollama RAG) + Phase 2 (Multi-language) capabilities
"""
import logging
import json
import asyncio
from typing import Dict, List, Optional, Any
from pathlib import Path
import time
from datetime import datetime

from fastapi import FastAPI, HTTPException, UploadFile, File, Form, BackgroundTasks
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

# Import our Phase 2 components
from config.settings import get_config
from ..processing.language_detector import LanguageDetector
from ..processing.translator import TranslationService
from ..ingestion.multilang_processor import MultiLanguageProcessor, MultiLangDocument
from ..rag.multilang_query_processor import MultiLanguageQueryProcessor, MultiLangQuery, MultiLangResponse

logger = logging.getLogger(__name__)

# Pydantic Models for API
class ChatMessage(BaseModel):
    message: str
    language: Optional[str] = "auto"
    user_id: Optional[str] = "anonymous"

class ChatResponse(BaseModel):
    response: str
    original_language: str
    response_language: str
    confidence: float
    translation_needed: bool
    processing_time: float
    sources: List[Dict[str, Any]]

class DocumentUpload(BaseModel):
    filename: str
    content: str
    source: Optional[str] = "upload"

class DocumentProcessResult(BaseModel):
    document_id: str
    original_language: str
    confidence: float
    processing_status: str
    message: str

class LanguageDetectionResult(BaseModel):
    text: str
    language: str
    confidence: float
    alternatives: Optional[List[Dict[str, float]]] = None

class TranslationRequest(BaseModel):
    text: str
    source_language: Optional[str] = "auto"
    target_language: str = "en"

class TranslationResponse(BaseModel):
    original_text: str
    translated_text: str
    source_language: str
    target_language: str
    confidence: float
    service_used: str

class SystemStats(BaseModel):
    total_queries: int
    total_documents: int
    supported_languages: List[str]
    active_sessions: int
    uptime_seconds: float

class CTIWebInterface:
    """Main CTI Web Interface Application"""
    
    def __init__(self):
        self.config = get_config()
        
        # Initialize Phase 2 components
        self.language_detector = LanguageDetector()
        self.translator = TranslationService()
        self.document_processor = MultiLanguageProcessor()
        self.query_processor = MultiLanguageQueryProcessor()
        
        # FastAPI app
        self.app = FastAPI(
            title="CTI Multi-language Pipeline",
            description="Web interface for multi-language cyber threat intelligence processing",
            version="3.0.0"
        )
        
        # Add CORS middleware
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # Application state
        self.start_time = time.time()
        self.active_sessions = set()
        self.processed_documents = []
        self.query_history = []
        
        # Setup routes
        self._setup_routes()
        
    def _setup_routes(self):
        """Setup FastAPI routes"""
        
        @self.app.get("/", response_class=HTMLResponse)
        async def home():
            """Serve main interface"""
            return self._get_main_html()
        
        @self.app.post("/api/chat", response_model=ChatResponse)
        async def chat(message: ChatMessage):
            """Process chat message with multi-language support"""
            start_time = time.time()
            
            try:
                # Process query through Phase 2 pipeline
                processed_query = self.query_processor.process_query(
                    message.message, 
                    message.language if message.language != "auto" else None
                )
                
                # Mock RAG pipeline response (you can integrate with your actual RAG here)
                mock_response = await self._mock_rag_pipeline(processed_query.english_query)
                
                # Localize response if needed
                if processed_query.original_language != 'en':
                    try:
                        localized = self.query_processor.localize_response(
                            mock_response['response'],
                            processed_query.original_language
                        )
                        final_response = localized.localized_response
                        response_lang = localized.response_language
                    except Exception as e:
                        logger.warning(f"Response localization failed: {e}")
                        final_response = mock_response['response']
                        response_lang = 'en'
                else:
                    final_response = mock_response['response']
                    response_lang = 'en'
                
                processing_time = time.time() - start_time
                
                # Store in history
                self.query_history.append({
                    'timestamp': datetime.now().isoformat(),
                    'query': message.message,
                    'language': processed_query.original_language,
                    'response': final_response,
                    'processing_time': processing_time
                })
                
                return ChatResponse(
                    response=final_response,
                    original_language=processed_query.original_language,
                    response_language=response_lang,
                    confidence=processed_query.confidence,
                    translation_needed=processed_query.translation_needed,
                    processing_time=processing_time,
                    sources=mock_response['sources']
                )
                
            except Exception as e:
                logger.error(f"Chat processing error: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/api/detect-language", response_model=LanguageDetectionResult)
        async def detect_language(text: str = Form(...)):
            """Detect language of input text"""
            try:
                result = self.language_detector.detect_language(text)
                
                return LanguageDetectionResult(
                    text=text,
                    language=result.language,
                    confidence=result.confidence,
                    alternatives=[
                        {alt[0]: alt[1]} for alt in (result.alternatives or [])
                    ]
                )
            except Exception as e:
                logger.error(f"Language detection error: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/api/translate", response_model=TranslationResponse)
        async def translate_text(request: TranslationRequest):
            """Translate text between languages"""
            try:
                result = self.translator.translate_text(
                    request.text,
                    request.source_language,
                    request.target_language
                )
                
                return TranslationResponse(
                    original_text=result.original_text,
                    translated_text=result.translated_text,
                    source_language=result.source_language,
                    target_language=result.target_language,
                    confidence=result.confidence,
                    service_used=result.translation_service
                )
            except Exception as e:
                logger.error(f"Translation error: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/api/upload-document", response_model=DocumentProcessResult)
        async def upload_document(
            background_tasks: BackgroundTasks,
            file: UploadFile = File(...),
            source: str = Form("upload")
        ):
            """Upload and process CTI document"""
            try:
                # Read file content
                content = await file.read()
                
                # Try to parse as JSON (CTI documents are often JSON)
                try:
                    if file.filename.endswith('.json'):
                        document_data = json.loads(content.decode('utf-8'))
                    else:
                        # For other file types, create a simple document structure
                        document_data = {
                            'id': f"upload_{int(time.time())}",
                            'filename': file.filename,
                            'content': content.decode('utf-8'),
                            'upload_time': datetime.now().isoformat()
                        }
                except Exception as e:
                    logger.warning(f"File parsing error: {e}")
                    document_data = {
                        'id': f"upload_{int(time.time())}",
                        'filename': file.filename,
                        'content': str(content),
                        'upload_time': datetime.now().isoformat()
                    }
                
                # Process document in background
                background_tasks.add_task(
                    self._process_document_background,
                    document_data,
                    source
                )
                
                return DocumentProcessResult(
                    document_id=document_data.get('id', file.filename),
                    original_language="detecting...",
                    confidence=0.0,
                    processing_status="queued",
                    message="Document queued for processing"
                )
                
            except Exception as e:
                logger.error(f"Document upload error: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/api/documents")
        async def list_documents():
            """List processed documents"""
            return {
                'documents': self.processed_documents,
                'total': len(self.processed_documents)
            }
        
        @self.app.get("/api/stats", response_model=SystemStats)
        async def get_stats():
            """Get system statistics"""
            query_stats = self.query_processor.get_query_statistics()
            doc_stats = self.document_processor.get_processing_stats()
            
            return SystemStats(
                total_queries=query_stats.get('total_queries_processed', 0),
                total_documents=doc_stats.total_documents,
                supported_languages=self.config.multi_language.supported_languages,
                active_sessions=len(self.active_sessions),
                uptime_seconds=time.time() - self.start_time
            )
        
        @self.app.get("/api/history")
        async def get_history():
            """Get query history"""
            return {
                'history': self.query_history[-50:],  # Last 50 queries
                'total': len(self.query_history)
            }
    
    async def _mock_rag_pipeline(self, query: str) -> Dict[str, Any]:
        """Mock RAG pipeline response (replace with actual Ollama integration)"""
        
        # This is where you would integrate with your Ollama instance
        # For now, return a mock response based on common CTI queries
        
        mock_responses = {
            "apt29": "APT29 (Cozy Bear) is a sophisticated Russian cyber espionage group that primarily uses spear-phishing emails, living-off-the-land techniques, and advanced persistent threats. They commonly employ techniques like T1566.001 (spearphishing attachments) and T1055 (process injection).",
            "apt28": "APT28 (Fancy Bear) is a Russian military intelligence cyber unit that focuses on espionage and influence operations. They utilize zero-day exploits, custom malware, and social engineering techniques targeting government and military organizations.",
            "lazarus": "Lazarus Group is a North Korean state-sponsored group known for financially motivated attacks and espionage. They are responsible for major incidents like WannaCry and various cryptocurrency exchange attacks using sophisticated malware and social engineering.",
            "fin7": "FIN7 is a financially motivated threat group that targets point-of-sale systems and payment card data. They use spear-phishing, custom malware, and various evasion techniques to compromise retail and hospitality sectors."
        }
        
        query_lower = query.lower()
        response = "Based on the available threat intelligence, I can provide information about various threat actors and their techniques."
        
        for actor, description in mock_responses.items():
            if actor in query_lower:
                response = description
                break
        
        # Mock sources
        sources = [
            {
                'title': 'MITRE ATT&CK Framework',
                'url': 'https://attack.mitre.org/',
                'score': 0.95,
                'type': 'framework'
            },
            {
                'title': 'Threat Intelligence Report',
                'url': '#',
                'score': 0.88,
                'type': 'report'
            }
        ]
        
        return {
            'response': response,
            'sources': sources
        }
    
    async def _process_document_background(self, document_data: Dict, source: str):
        """Process document in background"""
        try:
            result = self.document_processor.process_document(document_data, source)
            
            # Store result
            self.processed_documents.append({
                'id': result.document_id,
                'original_language': result.original_language,
                'confidence': result.confidence,
                'source': result.source,
                'processing_timestamp': result.processing_timestamp,
                'status': 'completed'
            })
            
            logger.info(f"Document {result.document_id} processed successfully")
            
        except Exception as e:
            logger.error(f"Background document processing error: {e}")
            # Store error result
            self.processed_documents.append({
                'id': document_data.get('id', 'unknown'),
                'original_language': 'unknown',
                'confidence': 0.0,
                'source': source,
                'processing_timestamp': time.time(),
                'status': 'error',
                'error': str(e)
            })
    
    def _get_main_html(self) -> str:
        """Generate main HTML interface"""
        return '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CTI Multi-language Pipeline</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; padding: 20px; }
        .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 10px; margin-bottom: 30px; text-align: center; }
        .header h1 { font-size: 2.5em; margin-bottom: 10px; }
        .header p { font-size: 1.1em; opacity: 0.9; }
        .tabs { display: flex; margin-bottom: 20px; background: white; border-radius: 10px; overflow: hidden; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .tab { flex: 1; padding: 15px; text-align: center; cursor: pointer; background: white; border: none; font-size: 16px; transition: background 0.3s; }
        .tab:hover { background: #f0f0f0; }
        .tab.active { background: #667eea; color: white; }
        .tab-content { display: none; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .tab-content.active { display: block; }
        .chat-container { display: flex; flex-direction: column; height: 500px; }
        .chat-messages { flex: 1; border: 1px solid #ddd; border-radius: 10px; padding: 20px; margin-bottom: 20px; overflow-y: auto; background: #fafafa; }
        .message { margin-bottom: 15px; padding: 10px; border-radius: 10px; }
        .message.user { background: #e3f2fd; margin-left: 50px; }
        .message.assistant { background: #f1f8e9; margin-right: 50px; }
        .message-header { font-size: 0.9em; color: #666; margin-bottom: 5px; }
        .input-group { display: flex; gap: 10px; margin-bottom: 10px; }
        .input-group input, .input-group select, .input-group button { padding: 12px; border: 1px solid #ddd; border-radius: 5px; font-size: 16px; }
        .input-group input { flex: 1; }
        .input-group button { background: #667eea; color: white; cursor: pointer; min-width: 100px; }
        .input-group button:hover { background: #5a6fd8; }
        .upload-area { border: 2px dashed #ddd; border-radius: 10px; padding: 40px; text-align: center; margin-bottom: 20px; transition: border-color 0.3s; }
        .upload-area:hover { border-color: #667eea; }
        .upload-area.dragover { border-color: #667eea; background: #f0f4ff; }
        .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; }
        .stat-card { background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); text-align: center; }
        .stat-card h3 { color: #667eea; font-size: 2em; margin-bottom: 10px; }
        .language-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(150px, 1fr)); gap: 10px; margin: 20px 0; }
        .language-tag { background: #667eea; color: white; padding: 8px 12px; border-radius: 20px; text-align: center; font-size: 0.9em; }
        .loading { text-align: center; padding: 20px; color: #666; }
        .error { color: #d32f2f; background: #ffebee; padding: 10px; border-radius: 5px; margin: 10px 0; }
        .success { color: #2e7d32; background: #e8f5e8; padding: 10px; border-radius: 5px; margin: 10px 0; }
        .response-metadata { font-size: 0.9em; color: #666; margin-top: 10px; padding: 10px; background: #f5f5f5; border-radius: 5px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🌍 CTI Multi-language Pipeline</h1>
            <p>Phase 3: Web Interface for Multi-language Cyber Threat Intelligence</p>
            <p><strong>Powered by:</strong> Phase 1 (RAG + Ollama) + Phase 2 (Multi-language) + Phase 3 (Web UI)</p>
        </div>
        
        <div class="tabs">
            <button class="tab active" onclick="showTab('chat')">💬 Chat Interface</button>
            <button class="tab" onclick="showTab('upload')">📄 Document Processing</button>
            <button class="tab" onclick="showTab('translate')">🔄 Translation</button>
            <button class="tab" onclick="showTab('stats')">📊 Statistics</button>
        </div>
        
        <!-- Chat Tab -->
        <div id="chat" class="tab-content active">
            <h2>Multi-language CTI Chat</h2>
            <p>Ask questions about threat intelligence in any supported language!</p>
            
            <div class="chat-container">
                <div class="chat-messages" id="chatMessages">
                    <div class="message assistant">
                        <div class="message-header">🤖 Assistant</div>
                        <div>Welcome! I can help you with cyber threat intelligence queries in multiple languages. Try asking about APT groups, techniques, or upload CTI documents for analysis.</div>
                    </div>
                </div>
                
                <div class="input-group">
                    <select id="queryLanguage">
                        <option value="auto">Auto-detect</option>
                        <option value="en">English</option>
                        <option value="fr">French</option>
                        <option value="de">German</option>
                        <option value="es">Spanish</option>
                        <option value="ru">Russian</option>
                    </select>
                    <input type="text" id="chatInput" placeholder="Ask about threat intelligence..." onkeypress="if(event.key==='Enter') sendMessage()">
                    <button onclick="sendMessage()">Send</button>
                </div>
            </div>
        </div>
        
        <!-- Upload Tab -->
        <div id="upload" class="tab-content">
            <h2>Document Processing</h2>
            <p>Upload CTI documents in any supported language for automatic processing and analysis.</p>
            
            <div class="upload-area" id="uploadArea" ondrop="handleDrop(event)" ondragover="handleDragOver(event)" ondragleave="handleDragLeave(event)">
                <h3>📁 Drag & Drop CTI Documents</h3>
                <p>Or click to select files</p>
                <input type="file" id="fileInput" accept=".json,.txt,.pdf" style="display: none;" onchange="handleFileSelect(event)">
                <button onclick="document.getElementById('fileInput').click()">Select Files</button>
            </div>
            
            <div id="uploadStatus"></div>
            <div id="documentsList"></div>
        </div>
        
        <!-- Translate Tab -->
        <div id="translate" class="tab-content">
            <h2>Text Translation</h2>
            <p>Translate threat intelligence content between supported languages.</p>
            
            <div class="input-group">
                <select id="sourceLanguage">
                    <option value="auto">Auto-detect</option>
                    <option value="en">English</option>
                    <option value="fr">French</option>
                    <option value="de">German</option>
                    <option value="es">Spanish</option>
                    <option value="ru">Russian</option>
                </select>
                <select id="targetLanguage">
                    <option value="en">English</option>
                    <option value="fr">French</option>
                    <option value="de">German</option>
                    <option value="es">Spanish</option>
                    <option value="ru">Russian</option>
                </select>
                <button onclick="translateText()">Translate</button>
            </div>
            
            <textarea id="sourceText" placeholder="Enter text to translate..." rows="4" style="width: 100%; margin: 10px 0; padding: 12px; border: 1px solid #ddd; border-radius: 5px;"></textarea>
            
            <div id="translationResult"></div>
        </div>
        
        <!-- Stats Tab -->
        <div id="stats" class="tab-content">
            <h2>System Statistics</h2>
            <div id="statsContent" class="loading">Loading statistics...</div>
        </div>
    </div>

    <script>
        // Tab Management
        function showTab(tabName) {
            // Hide all tabs
            const tabs = document.querySelectorAll('.tab-content');
            tabs.forEach(tab => tab.classList.remove('active'));
            
            const buttons = document.querySelectorAll('.tab');
            buttons.forEach(button => button.classList.remove('active'));
            
            // Show selected tab
            document.getElementById(tabName).classList.add('active');
            event.target.classList.add('active');
            
            // Load data for specific tabs
            if (tabName === 'stats') {
                loadStats();
            }
        }
        
        // Chat Functions
        async function sendMessage() {
            const input = document.getElementById('chatInput');
            const language = document.getElementById('queryLanguage').value;
            const message = input.value.trim();
            
            if (!message) return;
            
            // Add user message
            addMessage('user', message, language);
            input.value = '';
            
            // Show loading
            const loadingId = addMessage('assistant', 'Processing your query...', 'en', true);
            
            try {
                const response = await fetch('/api/chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ message, language })
                });
                
                const data = await response.json();
                
                // Remove loading message
                document.getElementById(loadingId).remove();
                
                // Add response
                const responseText = data.response;
                const metadata = `Language: ${data.original_language} → ${data.response_language} | ` +
                              `Translation: ${data.translation_needed ? 'Yes' : 'No'} | ` +
                              `Confidence: ${data.confidence.toFixed(2)} | ` +
                              `Time: ${data.processing_time.toFixed(2)}s`;
                
                addMessage('assistant', responseText, data.response_language, false, metadata);
                
            } catch (error) {
                document.getElementById(loadingId).remove();
                addMessage('assistant', `Error: ${error.message}`, 'en');
            }
        }
        
        function addMessage(sender, text, language, isLoading = false, metadata = null) {
            const messagesContainer = document.getElementById('chatMessages');
            const messageDiv = document.createElement('div');
            const messageId = 'msg_' + Date.now();
            messageDiv.id = messageId;
            messageDiv.className = `message ${sender}`;
            
            let content = `<div class="message-header">${sender === 'user' ? '👤 You' : '🤖 Assistant'} (${language})</div>`;
            content += `<div>${text}</div>`;
            
            if (metadata) {
                content += `<div class="response-metadata">${metadata}</div>`;
            }
            
            messageDiv.innerHTML = content;
            messagesContainer.appendChild(messageDiv);
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
            
            return messageId;
        }
        
        // File Upload Functions
        function handleDragOver(event) {
            event.preventDefault();
            document.getElementById('uploadArea').classList.add('dragover');
        }
        
        function handleDragLeave(event) {
            document.getElementById('uploadArea').classList.remove('dragover');
        }
        
        function handleDrop(event) {
            event.preventDefault();
            document.getElementById('uploadArea').classList.remove('dragover');
            const files = event.dataTransfer.files;
            uploadFiles(files);
        }
        
        function handleFileSelect(event) {
            const files = event.target.files;
            uploadFiles(files);
        }
        
        async function uploadFiles(files) {
            const statusDiv = document.getElementById('uploadStatus');
            statusDiv.innerHTML = '';
            
            for (let file of files) {
                const formData = new FormData();
                formData.append('file', file);
                formData.append('source', 'web_upload');
                
                try {
                    statusDiv.innerHTML += `<div class="loading">Uploading ${file.name}...</div>`;
                    
                    const response = await fetch('/api/upload-document', {
                        method: 'POST',
                        body: formData
                    });
                    
                    const data = await response.json();
                    statusDiv.innerHTML += `<div class="success">✅ ${file.name} uploaded successfully (${data.document_id})</div>`;
                    
                } catch (error) {
                    statusDiv.innerHTML += `<div class="error">❌ Failed to upload ${file.name}: ${error.message}</div>`;
                }
            }
            
            // Refresh documents list
            setTimeout(loadDocuments, 1000);
        }
        
        async function loadDocuments() {
            try {
                const response = await fetch('/api/documents');
                const data = await response.json();
                
                const listDiv = document.getElementById('documentsList');
                listDiv.innerHTML = '<h3>Processed Documents</h3>';
                
                if (data.documents.length === 0) {
                    listDiv.innerHTML += '<p>No documents processed yet.</p>';
                    return;
                }
                
                data.documents.forEach(doc => {
                    const docDiv = document.createElement('div');
                    docDiv.className = 'stat-card';
                    docDiv.innerHTML = `
                        <h4>${doc.id}</h4>
                        <p>Language: ${doc.original_language}</p>
                        <p>Confidence: ${doc.confidence.toFixed(2)}</p>
                        <p>Status: ${doc.status}</p>
                    `;
                    listDiv.appendChild(docDiv);
                });
                
            } catch (error) {
                console.error('Failed to load documents:', error);
            }
        }
        
        // Translation Functions
        async function translateText() {
            const sourceText = document.getElementById('sourceText').value.trim();
            const sourceLanguage = document.getElementById('sourceLanguage').value;
            const targetLanguage = document.getElementById('targetLanguage').value;
            
            if (!sourceText) {
                alert('Please enter text to translate');
                return;
            }
            
            const resultDiv = document.getElementById('translationResult');
            resultDiv.innerHTML = '<div class="loading">Translating...</div>';
            
            try {
                const response = await fetch('/api/translate', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        text: sourceText,
                        source_language: sourceLanguage,
                        target_language: targetLanguage
                    })
                });
                
                const data = await response.json();
                
                resultDiv.innerHTML = `
                    <div class="stat-card">
                        <h3>Translation Result</h3>
                        <p><strong>Original (${data.source_language}):</strong> ${data.original_text}</p>
                        <p><strong>Translated (${data.target_language}):</strong> ${data.translated_text}</p>
                        <div class="response-metadata">
                            Service: ${data.service_used} | Confidence: ${data.confidence.toFixed(2)}
                        </div>
                    </div>
                `;
                
            } catch (error) {
                resultDiv.innerHTML = `<div class="error">Translation failed: ${error.message}</div>`;
            }
        }
        
        // Statistics Functions
        async function loadStats() {
            const statsDiv = document.getElementById('statsContent');
            
            try {
                const response = await fetch('/api/stats');
                const data = await response.json();
                
                const uptimeHours = (data.uptime_seconds / 3600).toFixed(1);
                
                statsDiv.innerHTML = `
                    <div class="stats-grid">
                        <div class="stat-card">
                            <h3>${data.total_queries}</h3>
                            <p>Total Queries</p>
                        </div>
                        <div class="stat-card">
                            <h3>${data.total_documents}</h3>
                            <p>Documents Processed</p>
                        </div>
                        <div class="stat-card">
                            <h3>${data.supported_languages.length}</h3>
                            <p>Supported Languages</p>
                        </div>
                        <div class="stat-card">
                            <h3>${uptimeHours}h</h3>
                            <p>System Uptime</p>
                        </div>
                    </div>
                    
                    <h3>Supported Languages</h3>
                    <div class="language-grid">
                        ${data.supported_languages.map(lang => `<div class="language-tag">${lang.toUpperCase()}</div>`).join('')}
                    </div>
                `;
                
            } catch (error) {
                statsDiv.innerHTML = `<div class="error">Failed to load statistics: ${error.message}</div>`;
            }
        }
        
        // Initialize
        document.addEventListener('DOMContentLoaded', function() {
            loadStats();
            loadDocuments();
        });
    </script>
</body>
</html>
        '''

def create_app():
    """Create and configure the CTI Web Interface"""
    interface = CTIWebInterface()
    return interface.app

def run_server(host: str = "0.0.0.0", port: int = 8000, debug: bool = True):
    """Run the CTI Web Interface server"""
    app = create_app()
    
    print("🌍 Starting CTI Multi-language Web Interface...")
    print(f"🔗 Access the interface at: http://localhost:{port}")
    print("📋 Features available:")
    print("   • Multi-language chat interface")
    print("   • Document upload and processing") 
    print("   • Text translation")
    print("   • System statistics")
    
    uvicorn.run(app, host=host, port=port, log_level="info" if debug else "warning")

if __name__ == "__main__":
    run_server()