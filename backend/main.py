#!/usr/bin/env python3
"""
Unified GovTech Backend API
===========================

This unified backend combines:
1. SQL-First Data Retrieval Workflow (from GovTech-main)
2. Multi-Agent Legal RAG System (from GovTech)

Features:
- General chatbot with Gemini AI
- Legal document analysis with multi-agent system
- Court document generation
- Vector search with Qdrant
- Google Gemini integration

Author: AI Assistant
Version: 3.0.0 (Unified - Gemini Only)
Last Updated: 2025
"""

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import logging
import os
import sys
from datetime import datetime
from dotenv import load_dotenv
import google.generativeai as genai

# Add backend and legal module to path
backend_dir = os.path.dirname(os.path.abspath(__file__))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)
legal_dir = os.path.join(backend_dir, 'legal')
if legal_dir not in sys.path:
    sys.path.insert(0, legal_dir)

# Import web search
from .web_search import BraveSearchClient, create_web_search_context

# Import legal RAG system components
try:
    from .legal.orchestrator import AgentOrchestrator, WorkflowState, WorkflowStatus
    from .legal.vector_store import EnhancedQdrantVectorStore
    from .legal.gemini_client import EnhancedGeminiClient
    from .legal.pdf_processor import AdvancedPDFProcessor
    LEGAL_SYSTEM_AVAILABLE = True
except ImportError as e:
    logging.warning(f"Legal system modules not available: {e}")
    LEGAL_SYSTEM_AVAILABLE = False

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================================================
# PYDANTIC MODELS
# ============================================================================

class ChatRequest(BaseModel):
    """Request model for chat endpoint"""
    message: str
    conversation_history: Optional[List[Dict[str, str]]] = []
    web_search_enabled: Optional[bool] = False

class ChatResponse(BaseModel):
    """Response model for chat endpoint"""
    answer: str
    sources: Optional[List[Dict[str, Any]]] = []
    timestamp: str

class LegalAnalysisRequest(BaseModel):
    """Request model for legal analysis"""
    narrative: str
    petition: str

class LegalAnalysisResponse(BaseModel):
    """Response model for legal analysis"""
    status: str
    workflow_state: Optional[Dict[str, Any]] = None
    results: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    services: Dict[str, str]
    timestamp: str

# ============================================================================
# GLOBAL STATE
# ============================================================================

class AppState:
    """Global application state"""
    def __init__(self):
        self.gemini_client: Optional[Any] = None
        self.vector_store: Optional[Any] = None
        self.legal_orchestrator: Optional[Any] = None
        self.legal_vector_store: Optional[Any] = None
        self.legal_gemini_client: Optional[Any] = None
        self.brave_search_client: Optional[Any] = None

app_state = AppState()

# ============================================================================
# STARTUP/SHUTDOWN HANDLERS
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize services on startup"""
    logger.info("🚀 Starting Unified GovTech Backend...")

    # Initialize Google Gemini
    gemini_api_key = os.getenv('GEMINI_API_KEY')
    if gemini_api_key:
        model_name = os.getenv('GEMINI_MODEL', 'gemini-3.6-flash')
        app_state.gemini_client = genai.GenerativeModel(model_name)
        logger.info(f"✅ Google Gemini initialized ({model_name})")
    else:
        logger.warning("⚠️ Gemini API key not found")
        raise ValueError("GEMINI_API_KEY is required")

    # Initialize Brave Search
    brave_api_key = os.getenv('BRAVE_API_KEY')
    if brave_api_key:
        try:
            app_state.brave_search_client = BraveSearchClient(brave_api_key)
            logger.info("✅ Brave Search initialized")
        except Exception as e:
            logger.warning(f"⚠️ Failed to initialize Brave Search: {e}")
    else:
        logger.warning("⚠️ Brave API key not found - web search disabled")

    # Initialize Legal RAG System
    if LEGAL_SYSTEM_AVAILABLE:
        try:
            qdrant_url = os.getenv('QDRANT_URL')
            qdrant_api_key = os.getenv('QDRANT_API_KEY')

            if qdrant_url and qdrant_api_key:
                # Initialize legal vector store
                app_state.legal_vector_store = EnhancedQdrantVectorStore(
                    url=qdrant_url,
                    api_key=qdrant_api_key,
                    collection_name=os.getenv('QDRANT_COLLECTION_NAME', 'kpk_local_govt_act_2013')
                )
                logger.info("✅ Legal vector store initialized")

                # Initialize legal Gemini client
                if gemini_api_key:
                    app_state.legal_gemini_client = EnhancedGeminiClient(gemini_api_key)
                    logger.info("✅ Legal Gemini client initialized")

                # Initialize orchestrator
                if app_state.legal_vector_store and app_state.legal_gemini_client:
                    app_state.legal_orchestrator = AgentOrchestrator(
                        vector_store=app_state.legal_vector_store,
                        gemini_client=app_state.legal_gemini_client
                    )
                    logger.info("✅ Legal orchestrator initialized")
            else:
                logger.warning("⚠️ Qdrant configuration not found")
        except Exception as e:
            logger.error(f"❌ Failed to initialize legal system: {e}")

    logger.info("✅ Unified GovTech Backend ready!")

    yield

    # Cleanup on shutdown
    logger.info("🛑 Shutting down Unified GovTech Backend...")

# ============================================================================
# FASTAPI APP
# ============================================================================

app = FastAPI(
    title="Unified GovTech Backend API",
    description="Combined chatbot and legal RAG system",
    version="3.0.0",
    lifespan=lifespan
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# API ENDPOINTS - GENERAL CHATBOT
# ============================================================================

@app.get("/", tags=["General"])
async def root():
    """Root endpoint"""
    return {
        "service": "Unified GovTech Backend API",
        "version": "3.0.0",
        "features": [
            "General Chatbot with SQL + Web Search",
            "Legal Document Analysis (Multi-Agent RAG)",
            "Court Document Generation",
            "Vector Search"
        ],
        "endpoints": {
            "chat": "/chat",
            "legal_analysis": "/legal/analyze",
            "legal_qa": "/legal/qa",
            "health": "/health"
        }
    }

@app.get("/health", response_model=HealthResponse, tags=["General"])
async def health_check():
    """Health check endpoint"""
    services = {
        "gemini": "available" if app_state.gemini_client else "unavailable",
        "web_search": "available" if app_state.brave_search_client else "unavailable",
        "legal_system": "available" if LEGAL_SYSTEM_AVAILABLE and app_state.legal_orchestrator else "unavailable",
        "vector_store": "available" if app_state.legal_vector_store else "unavailable"
    }

    return HealthResponse(
        status="healthy",
        services=services,
        timestamp=datetime.now().isoformat()
    )

@app.post("/chat", response_model=ChatResponse, tags=["Chat"])
async def chat(request: ChatRequest):
    """
    General chat endpoint with Gemini AI
    Supports conversation history and web search
    """
    if not app_state.gemini_client:
        raise HTTPException(status_code=503, detail="Gemini service unavailable")

    try:
        # Build conversation context
        conversation_context = "You are GovTech, an AI assistant for the Government of KPK Performance Management & Reforms Unit. Provide helpful, accurate information about government services, policies, and initiatives.\n\n"

        # Handle web search if enabled
        search_results = []
        if request.web_search_enabled and app_state.brave_search_client:
            try:
                logger.info(f"Performing web search for: {request.message}")
                search_results = app_state.brave_search_client.search_and_format(
                    request.message,
                    count=5
                )

                if search_results:
                    web_context = create_web_search_context(request.message, search_results)
                    conversation_context += f"\n{web_context}\n"
                    conversation_context += "Please use the above web search results to inform your response when relevant.\n\n"
                    logger.info(f"Found {len(search_results)} web search results")
            except Exception as e:
                logger.error(f"Web search error: {e}")
                # Continue without web search if it fails

        # Add conversation history
        for msg in request.conversation_history[-10:]:  # Last 10 messages
            role = msg.get("role", "user")
            content = msg.get("content", "")
            conversation_context += f"{role.capitalize()}: {content}\n"

        # Add current message
        conversation_context += f"User: {request.message}\nAssistant:"

        # Generate response with Gemini
        response = app_state.gemini_client.generate_content(
            conversation_context,
            generation_config=genai.types.GenerationConfig(
                temperature=0.7,
                max_output_tokens=1500,
            )
        )

        answer = response.text

        # Format sources from web search
        sources = [
            {
                "title": result.get("title", ""),
                "url": result.get("url", ""),
                "description": result.get("description", ""),
                "type": "web_search"
            }
            for result in search_results
        ]

        return ChatResponse(
            answer=answer,
            sources=sources,
            timestamp=datetime.now().isoformat()
        )

    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=f"Chat processing failed: {str(e)}")

# ============================================================================
# API ENDPOINTS - LEGAL RAG SYSTEM
# ============================================================================

@app.post("/legal/analyze", response_model=LegalAnalysisResponse, tags=["Legal"])
async def legal_analyze(request: LegalAnalysisRequest):
    """
    Multi-agent legal analysis endpoint
    Analyzes narrative and petition to provide comprehensive legal commentary
    """
    if not LEGAL_SYSTEM_AVAILABLE or not app_state.legal_orchestrator:
        raise HTTPException(status_code=503, detail="Legal analysis system unavailable")

    try:
        # Run multi-agent workflow
        workflow_state = app_state.legal_orchestrator.execute_workflow(
            narrative=request.narrative,
            petition=request.petition
        )

        # Extract results
        results = {
            "status": workflow_state.status.value,
            "processed_data": workflow_state.processed_data,
            "case_analysis": workflow_state.case_analysis,
            "law_retrieval": workflow_state.law_retrieval,
            "commentary": workflow_state.commentary,
            "execution_log": workflow_state.execution_log,
            "errors": workflow_state.errors,
            "warnings": workflow_state.warnings
        }

        return LegalAnalysisResponse(
            status="success",
            workflow_state=workflow_state.to_dict(),
            results=results
        )

    except Exception as e:
        logger.error(f"Legal analysis error: {e}")
        return LegalAnalysisResponse(
            status="error",
            error=str(e)
        )

@app.post("/legal/qa", response_model=ChatResponse, tags=["Legal"])
async def legal_qa(request: ChatRequest):
    """
    Legal Q&A endpoint
    Answers questions about KPK Local Government Act 2013
    """
    if not app_state.legal_vector_store or not app_state.legal_gemini_client:
        raise HTTPException(status_code=503, detail="Legal Q&A system unavailable")

    try:
        # Search legal corpus
        search_results = app_state.legal_vector_store.smart_search(request.message, limit=5)

        if not search_results:
            return ChatResponse(
                answer="I couldn't find relevant information in the KPK Local Government Act 2013. Please try rephrasing your question.",
                sources=[],
                timestamp=datetime.now().isoformat()
            )

        # Generate response
        answer = app_state.legal_gemini_client.generate_response(request.message, search_results)

        # Format sources
        sources = [
            {
                "text": result.get("text", ""),
                "metadata": result.get("metadata", {}),
                "score": result.get("score", 0)
            }
            for result in search_results
        ]

        return ChatResponse(
            answer=answer,
            sources=sources,
            timestamp=datetime.now().isoformat()
        )

    except Exception as e:
        logger.error(f"Legal Q&A error: {e}")
        raise HTTPException(status_code=500, detail=f"Legal Q&A failed: {str(e)}")

@app.post("/legal/load-corpus", tags=["Legal"])
async def load_legal_corpus():
    """
    Load legal corpus from PDF
    Processes and indexes the KPK Local Government Act 2013
    """
    if not app_state.legal_vector_store:
        raise HTTPException(status_code=503, detail="Vector store unavailable")

    try:
        pdf_path = os.path.join(os.path.dirname(__file__), "..", "docs", "THE_KHYBER_PAKHTUNKHWA_LOCAL_GOVERNMENT_ACT_2013.pdf")

        if not os.path.exists(pdf_path):
            raise HTTPException(status_code=404, detail="Legal PDF not found")

        # Process PDF
        processor = AdvancedPDFProcessor()
        chunks_with_metadata, structure = processor.process_pdf_section_scoped(pdf_path)

        # Add to vector store
        app_state.legal_vector_store.add_documents_with_metadata(chunks_with_metadata)

        return {
            "status": "success",
            "message": "Legal corpus loaded successfully",
            "chunks_processed": len(chunks_with_metadata),
            "structure": structure
        }

    except Exception as e:
        logger.error(f"Load corpus error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to load corpus: {str(e)}")

# ============================================================================
# RUN SERVER
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="127.0.0.1",  # localhost only - accessible via port 5173 proxy
        port=8000,
        reload=True,
        log_level="info"
    )
