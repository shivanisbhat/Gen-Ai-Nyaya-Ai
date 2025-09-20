import os
import json
from app.services.parser import extract_text_from_pdf, chunk_into_clauses
from app.services.free_embedder import embed_texts
from app.services.vectordb import faiss_index
from app.config import settings
import logging

logger = logging.getLogger(__name__)

def index_pdf_knowledge_base(kb_folder: str = None):
    """Index all PDFs in the knowledge base folder"""
    if kb_folder is None:
        kb_folder = os.path.join(settings.DATA_DIR, "kb")
    
    if not os.path.exists(kb_folder):
        os.makedirs(kb_folder, exist_ok=True)
        return {"error": f"Created folder: {kb_folder}. Please add PDF files to it."}
    
    pdf_files = [f for f in os.listdir(kb_folder) if f.lower().endswith('.pdf')]
    if not pdf_files:
        return {"warning": f"No PDF files found in {kb_folder}. Please add legal PDF documents."}
    
    total_chunks = 0
    processed_files = []
    errors = []
    
    for pdf_file in pdf_files:
        try:
            pdf_path = os.path.join(kb_folder, pdf_file)
            print(f"📄 Processing: {pdf_file}")
            
            # Extract text and chunk
            text = extract_text_from_pdf(pdf_path)
            if not text.strip():
                errors.append(f"{pdf_file}: No text extracted")
                continue
                
            chunks = chunk_into_clauses(text)
            if not chunks:
                errors.append(f"{pdf_file}: No chunks created")
                continue
            
            # Generate embeddings using FREE model
            texts = [c["text"] for c in chunks if c.get("text")]
            if not texts:
                errors.append(f"{pdf_file}: No valid text in chunks")
                continue
                
            embeddings = embed_texts(texts)
            
            # Create metadata for each chunk
            act_name = pdf_file.replace('.pdf', '').replace('_', ' ').title()
            metadatas = []
            for i, chunk in enumerate(chunks):
                if not chunk.get("text"):
                    continue
                metadata = {
                    "id": f"{act_name}_{i}",
                    "act": act_name,
                    "section": f"sec_{i}",
                    "text": chunk["text"],
                    "source": "KB",
                    "filename": pdf_file,
                    "chunk_id": chunk.get("id", f"chunk_{i}")
                }
                metadatas.append(metadata)
            
            # Add to FAISS index
            faiss_index.add(embeddings, metadatas)
            
            total_chunks += len(chunks)
            processed_files.append({"file": pdf_file, "chunks": len(chunks)})
            print(f"✅ {pdf_file}: {len(chunks)} chunks")
            
        except Exception as e:
            error_msg = f"{pdf_file}: {str(e)}"
            errors.append(error_msg)
            logger.error(f"Error processing {pdf_file}: {e}")
            continue
    
    result = {
        "status": "success" if processed_files else "error",
        "processed_files": processed_files,
        "total_chunks": total_chunks,
        "total_files": len(processed_files)
    }
    
    if errors:
        result["errors"] = errors
    
    print(f"📊 Indexing complete: {len(processed_files)} files, {total_chunks} total chunks")
    return result

def rebuild_knowledge_base():
    """Clear existing index and rebuild from PDF folder"""
    print("🔄 Rebuilding knowledge base...")
    faiss_index.create()  # Reset index
    result = index_pdf_knowledge_base()
    faiss_index.save()
    return result

def get_kb_status():
    """Get status of knowledge base"""
    kb_folder = os.path.join(settings.DATA_DIR, "kb")
    pdf_files = []
    
    if os.path.exists(kb_folder):
        pdf_files = [f for f in os.listdir(kb_folder) if f.lower().endswith('.pdf')]
    
    indexed_count = len(faiss_index.metadata) if faiss_index.metadata else 0
    
    return {
        "kb_folder": kb_folder,
        "pdf_files_count": len(pdf_files),
        "pdf_files": pdf_files,
        "indexed_chunks": indexed_count,
        "faiss_index_exists": faiss_index.index is not None,
        "embedding_model": settings.EMBEDDING_MODEL,
        "llm_model": settings.LLM_MODEL
    }