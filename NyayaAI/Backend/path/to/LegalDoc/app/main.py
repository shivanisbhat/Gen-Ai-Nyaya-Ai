from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import os
import uuid
import json
import logging
from app.services.parser import extract_text_from_pdf, chunk_into_clauses
from app.services.free_rag import build_and_run_rag  # Updated import
from app.services.kb_indexer import rebuild_knowledge_base, get_kb_status
from app.services.storage import SessionLocal, UserDoc
from app.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="NyayaAI - Free AI-Powered Legal Document Assistant", 
    description="Understand legal documents in simple English using free Google AI",
    version="2.0-free"
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000","http://localhost:5173","http://127.0.0.1:5173","https://gen-ai-nyaya-ai-1.onrender.com" ],  # React dev server
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

os.makedirs(settings.DATA_DIR, exist_ok=True)
os.makedirs(os.path.join(settings.DATA_DIR, "kb"), exist_ok=True)

@app.get("/")
async def root():
    return {
        "message": "🏛️ NyayaAI is ready! Upload legal documents to get AI-powered explanations.", 
        "version": "2.0-free-google-ai",
        "features": [
            "📄 PDF document analysis",
            "🤖 AI-powered explanations in simple English", 
            "⚖️ Legal risk assessment",
            "📚 Knowledge base comparison",
            "💸 Completely free to use"
        ]
    }

@app.get("/health")
async def health():
    try:
        from app.services.free_google_llm import free_google_llm
        from app.services.free_embedder import _model
        
        status = {
            "status": "healthy",
            "google_ai_configured": free_google_llm is not None,
            "embedding_model_loaded": _model is not None,
            "embedding_model": settings.EMBEDDING_MODEL,
            "llm_model": settings.LLM_MODEL,
            "cost": "FREE"
        }
        return status
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")

@app.post("/knowledge/rebuild")
async def rebuild_kb():
    """Build knowledge base from PDFs in data/kb/ folder"""
    try:
        result = rebuild_knowledge_base()
        return result
    except Exception as e:
        logger.error(f"Error rebuilding KB: {e}")
        raise HTTPException(status_code=500, detail=f"Error rebuilding knowledge base: {str(e)}")

@app.get("/knowledge/status")
async def kb_status():
    """Get status of knowledge base"""
    return get_kb_status()

@app.post("/doc/upload")
async def upload_user_doc(file: UploadFile = File(...)):
    """Upload user's contract/document for analysis"""
    try:
        if not file.filename.lower().endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Only PDF files are supported")
        
        file_id = str(uuid.uuid4())
        path = os.path.join(settings.DATA_DIR, f"user_{file_id}_{file.filename}")
        
        with open(path, "wb") as f:
            f.write(await file.read())
        
        text = extract_text_from_pdf(path)
        if not text.strip():
            raise HTTPException(status_code=400, detail="Could not extract text from PDF")
        
        chunks = chunk_into_clauses(text)
        if not chunks:
            raise HTTPException(status_code=400, detail="Could not create chunks from document")
        
        db = SessionLocal()
        try:
            doc = UserDoc(filename=file.filename, path=path, meta=json.dumps(chunks))
            db.add(doc)
            db.commit()
            db.refresh(doc)
            
            return {
                "doc_id": doc.id,
                "filename": file.filename,
                "chunks": len(chunks),
                "message": "📄 Document uploaded and processed successfully! Ready for AI analysis."
            }
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Error uploading document: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing document: {str(e)}")

@app.post("/query")
async def analyze_document(doc_id: int = Form(...), query: str = Form(...)):
    """🤖 Analyze user's document with FREE AI-powered explanations"""
    try:
        db = SessionLocal()
        try:
            doc = db.query(UserDoc).filter(UserDoc.id == doc_id).first()
            if not doc:
                raise HTTPException(status_code=404, detail="Document not found")
            
            chunks = json.loads(doc.meta)
            
            # Use the enhanced RAG pipeline with FREE Google AI
            result = build_and_run_rag(chunks, query)
            
            if "error" in result:
                raise HTTPException(status_code=500, detail=result["error"])
            
            return result
        finally:
            db.close()
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing document: {e}")
        raise HTTPException(status_code=500, detail=f"Error analyzing document: {str(e)}")

@app.get("/docs")
async def list_user_docs():
    """List all uploaded user documents"""
    db = SessionLocal()
    try:
        docs = db.query(UserDoc).all()
        return [{"id": d.id, "filename": d.filename} for d in docs]
    finally:
        db.close()

@app.delete("/docs/{doc_id}")
async def delete_user_doc(doc_id: int):
    """Delete a user document"""
    db = SessionLocal()
    try:
        doc = db.query(UserDoc).filter(UserDoc.id == doc_id).first()
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")
        
        if os.path.exists(doc.path):
            os.remove(doc.path)
        
        db.delete(doc)
        db.commit()
        
        return {"message": f"🗑️ Document {doc.filename} deleted successfully"}
    finally:
        db.close()
