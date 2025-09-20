"""
NyayaAI CLI - Command Line Interface for Legal Document Analysis
"""

import os
import sys
import json
import argparse
import requests
from pathlib import Path
from typing import Optional
import time

# Suppress Google warnings for cleaner CLI output
os.environ['GRPC_VERBOSITY'] = 'ERROR'
os.environ['GRPC_TRACE'] = ''

# Add project root to Python path
# cli.py is in legalRAG/ folder, app/ folder is also in legalRAG/
PROJECT_ROOT = Path(__file__).parent  # This is legalRAG/
sys.path.insert(0, str(PROJECT_ROOT))  # Add legalRAG/ to path so we can import app.services

try:
    from app.services.parser import extract_text_from_pdf, chunk_into_clauses
    from app.services.free_rag import build_and_run_rag
    from app.services.kb_indexer import rebuild_knowledge_base, get_kb_status
    from app.config import settings
    LOCAL_MODE = True
except ImportError:
    print("⚠️  Local modules not found. Using API mode only.")
    LOCAL_MODE = False

class NyayaAICLI:
    def __init__(self, api_base: str = "http://localhost:8000"):
        self.api_base = api_base
        self.session = requests.Session()
        
    def print_banner(self):
        """Print NyayaAI banner"""
        print("""
╔═══════════════════════════════════════════════════╗
║                    NyayaAI CLI                    ║
║           AI-Powered Legal Document Analysis      ║
║                     v2.0-free                     ║
╚═══════════════════════════════════════════════════╝
        """)

    def check_server_status(self) -> bool:
        """Check if the FastAPI server is running"""
        try:
            response = self.session.get(f"{self.api_base}/health", timeout=5)
            if response.status_code == 200:
                health_data = response.json()
                print(f"✅ Server is running")
                print(f"   - Google AI: {'✅' if health_data.get('google_ai_configured') else '❌'}")
                print(f"   - Embedding Model: {health_data.get('embedding_model', 'Unknown')}")
                print(f"   - LLM Model: {health_data.get('llm_model', 'Unknown')}")
                return True
            return False
        except Exception as e:
            print(f"❌ Server not accessible: {e}")
            return False

    def kb_status(self):
        """Show knowledge base status"""
        if LOCAL_MODE:
            status = get_kb_status()
            print(f"\n📚 Knowledge Base Status:")
            print(f"   - Folder: {status['kb_folder']}")
            print(f"   - PDF files: {status['pdf_files_count']}")
            print(f"   - Indexed chunks: {status['indexed_chunks']}")
            print(f"   - FAISS index: {'✅' if status['faiss_index_exists'] else '❌'}")
            
            if status['pdf_files']:
                print(f"\n📄 PDF Files:")
                for pdf in status['pdf_files']:
                    print(f"   - {pdf}")
        else:
            # API mode
            try:
                response = self.session.get(f"{self.api_base}/knowledge/status")
                status = response.json()
                print(f"\n📚 Knowledge Base Status:")
                print(f"   - PDF files: {status['pdf_files_count']}")
                print(f"   - Indexed chunks: {status['indexed_chunks']}")
                
                if status['pdf_files']:
                    print(f"\n📄 PDF Files:")
                    for pdf in status['pdf_files']:
                        print(f"   - {pdf}")
            except Exception as e:
                print(f"❌ Error getting KB status: {e}")

    def rebuild_kb(self):
        """Rebuild knowledge base"""
        print("🔄 Rebuilding knowledge base...")
        
        if LOCAL_MODE:
            result = rebuild_knowledge_base()
        else:
            try:
                response = self.session.post(f"{self.api_base}/knowledge/rebuild")
                result = response.json()
            except Exception as e:
                print(f"❌ Error rebuilding KB: {e}")
                return

        if result.get('status') == 'success':
            print(f"✅ Knowledge base rebuilt successfully!")
            print(f"   - Processed {result.get('total_files', 0)} files")
            print(f"   - Created {result.get('total_chunks', 0)} chunks")
            
            for file_info in result.get('processed_files', []):
                print(f"   - {file_info['file']}: {file_info['chunks']} chunks")
        else:
            print(f"❌ Error rebuilding knowledge base:")
            print(f"   {result.get('error', 'Unknown error')}")
            
            if 'errors' in result:
                for error in result['errors']:
                    print(f"   - {error}")

    def upload_document(self, pdf_path: str) -> Optional[int]:
        """Upload a PDF document"""
        if not os.path.exists(pdf_path):
            print(f"❌ File not found: {pdf_path}")
            return None
            
        print(f"📤 Uploading: {pdf_path}")
        
        try:
            with open(pdf_path, 'rb') as f:
                files = {'file': (os.path.basename(pdf_path), f, 'application/pdf')}
                response = self.session.post(f"{self.api_base}/doc/upload", files=files)
                
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Document uploaded successfully!")
                print(f"   - Doc ID: {data['doc_id']}")
                print(f"   - Chunks: {data['chunks']}")
                return data['doc_id']
            else:
                print(f"❌ Upload failed: {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ Error uploading document: {e}")
            return None

    def analyze_document(self, doc_id: int, query: str):
        """Analyze document with a query"""
        print(f"🤖 Analyzing document {doc_id}...")
        print(f"   Query: {query}")
        print("   Processing... (this may take a moment)")
        
        try:
            data = {'doc_id': doc_id, 'query': query}
            response = self.session.post(f"{self.api_base}/query", data=data)
            
            if response.status_code == 200:
                result = response.json()
                self.print_analysis_result(result)
            else:
                print(f"❌ Analysis failed: {response.text}")
                
        except Exception as e:
            print(f"❌ Error analyzing document: {e}")

    def analyze_local(self, pdf_path: str, query: str):
        """Analyze document locally without server"""
        if not LOCAL_MODE:
            print("❌ Local analysis not available. Use server mode.")
            return
            
        if not os.path.exists(pdf_path):
            print(f"❌ File not found: {pdf_path}")
            return
            
        print(f"📄 Processing: {pdf_path}")
        print(f"❓ Query: {query}")
        print("🤖 Analyzing locally... (this may take a moment)")
        
        try:
            # Extract and chunk text
            text = extract_text_from_pdf(pdf_path)
            chunks = chunk_into_clauses(text)
            print(f"   - Extracted {len(chunks)} chunks")
            
            # Run RAG analysis
            result = build_and_run_rag(chunks, query)
            self.print_analysis_result(result)
            
        except Exception as e:
            print(f"❌ Error in local analysis: {e}")

    def print_analysis_result(self, result: dict):
        """Print analysis result in a nice format"""
        print("\n" + "="*80)
        print("🏛️  NYAYAAI LEGAL ANALYSIS RESULT")
        print("="*80)
        
        if 'error' in result:
            print(f"❌ Error: {result['error']}")
            return
            
        # Print the AI answer
        print("\n🤖 AI EXPLANATION:")
        print("-" * 40)
        print(result.get('answer', 'No answer provided'))
        
        # Print the relevant clause
        if 'user_clause' in result:
            print(f"\n📋 ANALYZED CLAUSE:")
            print("-" * 40)
            clause_text = result['user_clause'].get('text', '')
            if len(clause_text) > 300:
                print(clause_text[:300] + "...")
            else:
                print(clause_text)
        
        # Print knowledge base hits
        if result.get('kb_hits'):
            print(f"\n📚 KNOWLEDGE BASE REFERENCES:")
            print("-" * 40)
            for i, hit in enumerate(result['kb_hits'], 1):
                print(f"{i}. {hit.get('act', 'Unknown')} - {hit.get('section', 'Unknown')}")
                print(f"   Score: {hit.get('score', 0):.3f}")
                
        # Print model used
        if 'model_used' in result:
            print(f"\n⚙️  Model: {result['model_used']}")
            
        print("="*80)

    def interactive_mode(self):
        """Interactive mode for easy document analysis"""
        self.print_banner()
        
        # Check server status
        server_running = self.check_server_status()
        
        if not server_running and not LOCAL_MODE:
            print("❌ Neither server nor local mode available. Please start the server or install dependencies.")
            return
            
        print("\n🎯 Interactive Mode - Choose an option:")
        print("1. 📚 Check knowledge base status")
        print("2. 🔄 Rebuild knowledge base") 
        print("3. 📤 Upload and analyze document")
        print("4. 📄 Analyze local PDF (no upload)")
        print("5. 🚪 Exit")
        
        while True:
            try:
                choice = input("\n👉 Enter choice (1-5): ").strip()
                
                if choice == '1':
                    self.kb_status()
                    
                elif choice == '2':
                    self.rebuild_kb()
                    
                elif choice == '3':
                    if not server_running:
                        print("❌ Server required for document upload")
                        continue
                        
                    pdf_path = input("📁 Enter PDF path: ").strip()
                    if pdf_path:
                        doc_id = self.upload_document(pdf_path)
                        if doc_id:
                            query = input("❓ Enter your question: ").strip()
                            if query:
                                self.analyze_document(doc_id, query)
                                
                elif choice == '4':
                    pdf_path = input("📁 Enter PDF path: ").strip()
                    if pdf_path:
                        query = input("❓ Enter your question: ").strip()
                        if query:
                            self.analyze_local(pdf_path, query)
                            
                elif choice == '5':
                    print("👋 Goodbye!")
                    break
                    
                else:
                    print("❌ Invalid choice. Please enter 1-5.")
                    
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"❌ Error: {e}")

def main():
    parser = argparse.ArgumentParser(description="NyayaAI CLI - Legal Document Analysis")
    parser.add_argument("--server", default="http://localhost:8000", help="API server URL")
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Status command
    status_parser = subparsers.add_parser('status', help='Check system status')
    
    # KB commands
    kb_parser = subparsers.add_parser('kb', help='Knowledge base operations')
    kb_subparsers = kb_parser.add_subparsers(dest='kb_action')
    kb_subparsers.add_parser('status', help='Show KB status')
    kb_subparsers.add_parser('rebuild', help='Rebuild KB from PDF files')
    
    # Upload command  
    upload_parser = subparsers.add_parser('upload', help='Upload PDF document')
    upload_parser.add_argument('pdf_path', help='Path to PDF file')
    
    # Query command
    query_parser = subparsers.add_parser('query', help='Query uploaded document')
    query_parser.add_argument('doc_id', type=int, help='Document ID from upload')
    query_parser.add_argument('query', help='Question to ask')
    
    # Analyze command (local)
    analyze_parser = subparsers.add_parser('analyze', help='Analyze PDF locally')
    analyze_parser.add_argument('pdf_path', help='Path to PDF file')
    analyze_parser.add_argument('query', help='Question to ask')
    
    # Interactive command
    subparsers.add_parser('interactive', help='Interactive mode')
    
    args = parser.parse_args()
    
    cli = NyayaAICLI(api_base=args.server)
    
    if not args.command or args.command == 'interactive':
        cli.interactive_mode()
        
    elif args.command == 'status':
        cli.print_banner()
        cli.check_server_status()
        cli.kb_status()
        
    elif args.command == 'kb':
        if args.kb_action == 'status':
            cli.kb_status()
        elif args.kb_action == 'rebuild':
            cli.rebuild_kb()
            
    elif args.command == 'upload':
        doc_id = cli.upload_document(args.pdf_path)
        if doc_id:
            print(f"✅ Use 'python cli.py query {doc_id} \"your question\"' to analyze")
            
    elif args.command == 'query':
        cli.analyze_document(args.doc_id, args.query)
        
    elif args.command == 'analyze':
        cli.analyze_local(args.pdf_path, args.query)

if __name__ == "__main__":
    main()