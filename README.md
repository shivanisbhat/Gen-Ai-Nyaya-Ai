# NyayaAI - AI-Powered Legal Document Assistant

NyayaAI is an intelligent legal document analysis system that simplifies complex legal language into plain English. Upload PDFs, get instant analysis with risk assessment, contract comparison, and actionable advice using free Google Gemini AI.

## Features

- **📄 PDF Document Analysis** - Extract and analyze text from legal documents
- **🤖 AI-Powered Explanations** - Get plain-language explanations using Google Gemini
- **⚖️ Legal Risk Assessment** - Identify potential risks and concerns in contracts
- **📚 Knowledge Base Integration** - Compare against Indian legal acts and precedents
- **🔍 Document Type Detection** - Automatically detects legal documents, resumes, or general content
- **💬 Interactive Chat Interface** - Ask questions about your documents in real-time
- **🆓 Completely Free** - Uses free Google Gemini API

## Tech Stack

**Backend:**
- FastAPI (Python web framework)
- Google Gemini 1.5 Flash (Free LLM)
- Sentence Transformers (Free embeddings)
- FAISS (Vector database)
- SQLite (Document storage)
- PDF Plumber (Text extraction)

**Frontend:**
- React.js
- Bootstrap 5
- PDF.js (Client-side PDF processing)

## Installation

### Prerequisites
- Python 3.8+
- Node.js 16+
- Google API Key (free from Google AI Studio)

### Backend Setup

1. Clone the repository:
```bash
git clone https://github.com/your-username/nyayaai.git
cd nyayaai
```

2. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
export GOOGLE_API_KEY="your_google_api_key_here"
```

5. Create data directories:
```bash
mkdir -p data/kb
```

6. Add legal documents to knowledge base (optional):
```bash
# Place PDF files of Indian legal acts in data/kb/ folder
cp your_legal_pdfs/*.pdf data/kb/
```

7. Start the server:
```bash
uvicorn app.main:app --reload
```

### Frontend Setup

1. Navigate to frontend directory:
```bash
cd frontend  # Adjust path as needed
```

2. Install dependencies:
```bash
npm install
```

3. Start development server:
```bash
npm run dev
```

## Usage

### Web Interface
1. Open https://gen-ai-nyaya-ai-1.onrender.com/ in your browser
2. Upload a PDF document (legal contract, etc.)(For sample use Sample.pdf in the repo:https://drive.google.com/file/d/1F6r2L0FKM89QvM7B5cIqXmtTlm2pjcW6/view?usp=sharing)
3. Click "Analyse Document" to process the file
4. Use the chat interface to ask questions about your document

### CLI Interface
The project includes a powerful command-line interface:

```bash
# Interactive mode
python cli.py interactive

# Check system status
python cli.py status

# Analyze document locally
python cli.py analyze document.pdf "What are the key terms?"

# Upload and query via API
python cli.py upload document.pdf
python cli.py query 1 "Explain the payment clauses"

# Knowledge base operations
python cli.py kb status
python cli.py kb rebuild
```

## API Endpoints

- `GET /health` - Check system health and configuration
- `POST /doc/upload` - Upload PDF document for analysis
- `POST /query` - Query uploaded document with questions
- `GET /knowledge/status` - Check knowledge base status
- `POST /knowledge/rebuild` - Rebuild knowledge base from PDFs

## Document Types Supported

**Legal Documents:**
- Contracts and agreements
- Terms of service
- Privacy policies  
- Legal notices
- Court documents

**Other Documents:**
- General documents (content explanation)

## Configuration

### Environment Variables
```bash
GOOGLE_API_KEY=your_google_api_key
DATA_DIR=./data
EMBEDDING_MODEL=all-MiniLM-L6-v2
LLM_MODEL=gemini-1.5-flash
```

### CORS Settings
Update `app/main.py` to allow your frontend URL:
```python
allow_origins=[
    "http://localhost:3000", 
    "http://localhost:5173",  # Vite default
    "your-frontend-url"
]
```

## Knowledge Base

The system includes a knowledge base of Indian legal acts for reference. To set up:

1. Place PDF files of legal documents in `data/kb/`
2. Run knowledge base rebuild:
```bash
python cli.py kb rebuild
```

Supported legal acts include:
- Information Technology Act 2000
- Indian Contract Act 1872
- Consumer Protection Act 2019
- And many more...

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   React Frontend│    │   FastAPI Server │    │  Google Gemini  │
│                 │◄──►│                  │◄──►│      API        │
│ - PDF Upload    │    │ - Document Store │    │ - Text Analysis │
│ - Chat Interface│    │ - RAG Pipeline   │    │ - Explanations  │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌──────────────────┐
                       │   Vector Store   │
                       │                  │
                       │ - FAISS Index    │
                       │ - Embeddings     │
                       │ - Legal KB       │
                       └──────────────────┘
```

## Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Disclaimer

This tool provides AI-generated analysis for informational purposes only. It is not a substitute for professional legal advice. Always consult qualified legal professionals for legal matters.

## Support

- Create an issue for bugs or feature requests
- Check existing issues before creating new ones
- Provide detailed information when reporting problems

## Roadmap

- [ ] Support for more document formats (DOCX, TXT)
- [ ] Multi-language support (Hindi, Tamil, etc.)
- [ ] Enhanced legal precedent matching
- [ ] Document comparison features
- [ ] API rate limiting and authentication
- [ ] Deployment guides (Docker, cloud platforms)

---

Built with ❤️ for the legal community in India
