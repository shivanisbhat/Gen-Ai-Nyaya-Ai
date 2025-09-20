from app.services.free_embedder import embed_texts
from app.services.free_google_llm import free_google_llm
from app.services.vectordb import faiss_index
import numpy as np
import logging

logger = logging.getLogger(__name__)

LEGAL_SIMPLIFICATION_PROMPT = """You are NyayaAI, an AI assistant that helps people understand legal documents in simple, clear language.

TASK: Analyze the user's document and provide a plain-language explanation.

USER'S DOCUMENT:
{user_clause}

USER QUESTION: {query}

Note: If this appears to be a template with blank fields (___), explain what the template is for and what should be filled in.

Please provide a clear explanation using this format:

**What this document is:**
[Identify the type of document and its purpose]

**What this means in simple English:**
[Explain in everyday language, noting if it's a template to be filled]

**Key points to understand:**
[Important aspects, requirements, or implications]

**What you should know:**
[Risks, benefits, or things to watch for]

**Next steps:**
[What someone should do with this document]

Keep your explanation helpful, clear, and easy to understand."""
def detect_legal_document(text):
    """Detect if document is legal/government related"""
    legal_keywords = [
        'agreement', 'contract', 'terms', 'conditions', 'whereas', 'party', 'clause',
        'liability', 'indemnity', 'breach', 'terminate', 'jurisdiction', 'arbitration',
        
        'government', 'ministry', 'department', 'act', 'section', 'subsection',
        'regulation', 'rule', 'notification', 'circular', 'order', 'directive',
        'policy', 'guidelines', 'procedure', 'compliance', 'statutory', 'legal',
        
        'maharashtra', 'delhi', 'mumbai', 'kolkata', 'chennai', 'bangalore',
        'indian', 'india', 'rupees', 'crores', 'lakhs', 'gst', 'pan', 'aadhar',
        
        'tender', 'rfp', 'proposal', 'bid', 'procurement', 'purchase order',
        'invoice', 'receipt', 'certificate', 'license', 'permit', 'registration'
    ]
    
    text_lower = text.lower()
    legal_score = sum(1 for word in legal_keywords if word in text_lower)
    

    return legal_score >= 3

def generate_legal_answer(query: str, user_clause: dict, kb_hits: list) -> str:
    """Generate legal explanation using free Gemini model"""
    if free_google_llm is None:
        return "Error: Google AI not initialized. Please check your API key configuration."
    
    kb_info = ""
    if kb_hits:
        for i, hit in enumerate(kb_hits, 1):
            source_info = f"Reference {i} ({hit.get('act', 'Legal Document')})"
            text_preview = hit.get('text', '')[:350]  
            kb_info += f"{source_info}:\n{text_preview}...\n\n"
    else:
        kb_info = "No specific legal references found in knowledge base."
    

    prompt = LEGAL_SIMPLIFICATION_PROMPT.format(
        query=query,
        user_clause=user_clause.get('text', ''),
        kb_info=kb_info
    )
    
    return free_google_llm.generate_legal_explanation(prompt)

def retrieve_top_k_for_text(text: str, k=3, min_score=0.7):
    """Retrieve top-k similar documents from knowledge base"""
    if not text.strip():
        return []
    
    try:
        vec = embed_texts([text])
        results = faiss_index.search(vec, top_k=k)
        relevant_results = [r for r in results if r.get('score', 0) > min_score]
        return relevant_results[:k]
    except Exception as e:
        logger.error(f"Error in retrieval: {e}")
        return []

def build_and_run_rag(user_doc_clauses, query_text, k=3):
    """Enhanced RAG pipeline for legal/government documents only"""
    if not user_doc_clauses:
        return {"error": "No document clauses provided"}
    
    try:
        clause_texts = [c.get('text', '') for c in user_doc_clauses if c.get('text')]
        if not clause_texts:
            return {"error": "No valid text found in document clauses"}
        
        full_text = ' '.join(clause_texts)
        is_legal = detect_legal_document(full_text)
        
        if not is_legal:
            return {
                "error": "This document does not appear to be a legal or government document. NyayaAI is designed specifically for analyzing legal contracts, government policies, regulations, and official documents.",
                "suggestion": "Please upload a legal contract, government notification, policy document, or official regulation for analysis."
            }
        
        logger.info("Legal/government document detected - proceeding with analysis")
        
        clause_embs = embed_texts(clause_texts)
        q_emb = embed_texts([query_text])
        
        sims = (clause_embs @ q_emb.T).squeeze()
        if sims.ndim == 0:  # Single clause case
            best_idx = 0
        else:
            best_idx = int(np.argmax(sims))
        
        best_user_clause = user_doc_clauses[best_idx]
        
        kb_results = retrieve_top_k_for_text(query_text, k=k)
        
        ai_answer = generate_legal_answer(query_text, best_user_clause, kb_results)
        
        return {
            "answer": ai_answer,
            "user_clause": best_user_clause,
            "kb_hits": kb_results,
            "document_type": "legal",
            "sources": [f"{r.get('act', 'Legal Reference')} - {r.get('section', '')}" for r in kb_results],
            "model_used": "gemini-1.5-flash (free) - legal analysis"
        }
        
    except Exception as e:
        logger.error(f"Error in RAG pipeline: {e}")
        return {"error": f"Error processing request: {str(e)}"}