# RAG Pipeline for Cyber Threat Intelligence

A comprehensive Retrieval-Augmented Generation (RAG) system that ingests curated Cyber Threat Intelligence (CTI) data, creates vector embeddings, and provides intelligent responses to cybersecurity investigation queries using Anthropic's Claude API.

## 🎯 Project Overview

This hands-on lab demonstrates how RAG technology can enhance cybersecurity operations by:

- **Grounding LLM responses** in verified threat intelligence data
- **Providing up-to-date information** from live threat feeds
- **Supporting investigation workflows** with source-attributed insights
- **Visualizing TTPs** using integrated MITRE ATT&CK Navigator
- **Reducing hallucination** through evidence-based responses

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Data Sources  │───▶│   Ingestion     │───▶│   Processing    │
│                 │    │                 │    │                 │
│ • STIX/TAXII    │    │ • Parsers       │    │ • Chunking      │
│ • MITRE ATT&CK  │    │ • Validators    │    │ • Embeddings    │
│ • CVE Feeds     │    │ • Normalizers   │    │ • Metadata      │
│ • Threat Reports│    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   User Query    │───▶│   RAG Pipeline  │───▶│   Response      │
│                 │    │                 │    │                 │
│ • CLI Interface │    │ • Vector Search │    │ • Grounded Text │
│ • Web Interface │    │ • Claude API    │    │ • Source Attrs  │
│ • Jupyter NB    │    │ • Prompt Eng.   │    │ • TTP Visualization │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                               │
                               ▼
                    ┌─────────────────┐
                    │  ChromaDB       │
                    │  Vector Store   │
                    └─────────────────┘
```

## 🚀 Quick Start

### Prerequisites

- Python 3.12+
- Git
- Anthropic API key

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/Hanimn/Workshop-Labs.git
   cd Workshop-Labs
   ```

2. **Set up virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment:**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

5. **Initialize the system:**
   ```bash
   python -m src.setup.init_system
   ```

## 📁 Project Structure

```
├── data/                    # Data storage
│   ├── raw/                # Raw CTI data
│   ├── processed/          # Cleaned and normalized data
│   └── embeddings/         # Vector database
├── src/                    # Source code
│   ├── ingestion/          # Data collection and parsing
│   ├── processing/         # Data processing and embeddings
│   ├── rag/                # RAG pipeline implementation
│   └── interfaces/         # User interfaces (CLI, web, etc.)
├── notebooks/              # Jupyter notebooks for analysis
├── config/                 # Configuration management
├── tests/                  # Unit and integration tests
├── requirements.txt        # Python dependencies
├── .env.example           # Environment template
└── README.md              # This file
```

## 🔧 Configuration

The system uses environment variables and YAML configuration files. Key settings:

```bash
# LLM Configuration
LLM_ANTHROPIC_API_KEY=your_api_key_here
LLM_MODEL_NAME=claude-3-sonnet-20240229

# Database Configuration
DB_COLLECTION_NAME=cti_documents
DB_EMBEDDING_MODEL=all-MiniLM-L6-v2

# RAG Configuration
RAG_RETRIEVAL_TOP_K=10
RAG_CHUNK_SIZE=1000

# Phase 2: Multi-language Configuration
LANG_DEFAULT_LANGUAGE=en
LANG_TRANSLATION_SERVICE=google
LANG_TRANSLATE_TO_ENGLISH=true
LANG_TRANSLATE_RESPONSE=true
LANG_PRESERVE_ORIGINAL=true
```

## 🎮 Usage Examples

### Command Line Interface

```bash
# Query threat intelligence
python -m src.interfaces.cli "What TTPs does APT29 use against healthcare?"

# Batch processing
python -m src.interfaces.cli --batch queries.txt

# Export results
python -m src.interfaces.cli --query "CVE-2024-1234 exploits" --export results.json
```

### Phase 2: Multi-language Support

```bash
# Demo Phase 2 capabilities
python demo_phase2.py

# Process multi-language CTI documents
python -c "
from src.ingestion.multilang_processor import MultiLanguageProcessor
processor = MultiLanguageProcessor()
docs = processor.process_file('data/raw/sample_multilang_cti.json')
print(f'Processed {len(docs)} documents')
processor.save_processed_documents(docs, 'data/processed/multilang_cti.json')
"

# Multi-language query processing
python -c "
from src.rag.multilang_query_processor import MultiLanguageQueryProcessor
processor = MultiLanguageQueryProcessor()
query = processor.process_query('¿Cuáles son las técnicas de APT29?')
print(f'Original: {query.original_query}')
print(f'English: {query.english_query}')
print(f'Language: {query.original_language}')
"

# Language detection
python -c "
from src.processing.language_detector import LanguageDetector
detector = LanguageDetector()
result = detector.detect_language('APT28 utilise des techniques sophistiquées')
print(f'Language: {result.language}, Confidence: {result.confidence}')
"
```

### Phase 3: Web Interface Integration

```bash
# Demo Phase 3 web interface
python demo_phase3.py

# Start the CTI web interface
python start_cti_web.py
# Access at: http://localhost:8000

# Alternative startup methods
python -m src.interfaces.cti_web_interface

# Test API endpoints
curl http://localhost:8000/api/stats
curl -X POST http://localhost:8000/api/detect-language -F "text=Bonjour le monde"
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What are APT29 techniques?", "language": "en"}'
```

### Jupyter Notebooks

```bash
# Start Jupyter
jupyter notebook notebooks/

# Available notebooks:
# - 01_Data_Ingestion.ipynb
# - 02_Vector_Database.ipynb  
# - 03_RAG_Pipeline.ipynb
# - 04_Investigation_Scenarios.ipynb
```

### Web Interface

```bash
# Start web application
streamlit run src/interfaces/web_app.py

# Features:
# - Interactive chat interface
# - MITRE ATT&CK Navigator integration
# - Query history and export
# - Investigation scenario templates
```

## 🌍 Phase 2: Multi-language Support

### Supported Languages
- **English (en)** - Primary language
- **French (fr)** - Français
- **German (de)** - Deutsch  
- **Spanish (es)** - Español
- **Italian (it)** - Italiano
- **Portuguese (pt)** - Português
- **Russian (ru)** - Русский
- **Chinese (zh)** - 中文
- **Japanese (ja)** - 日本語
- **Arabic (ar)** - العربية

### Key Features
- **🔍 Language Detection**: Automatic detection using multiple algorithms (langdetect, CLD2)
- **🔄 Translation Services**: Support for Google Translate, Deep Translator with fallbacks
- **📄 Document Processing**: Batch processing of multi-language CTI documents
- **💬 Query Processing**: Multi-language query translation and response localization
- **💾 Caching**: Translation caching to improve performance and reduce API calls
- **📊 Analytics**: Comprehensive language processing statistics and reporting

### Configuration Options
```bash
# Language Settings
LANG_DEFAULT_LANGUAGE=en                    # Fallback language
LANG_SUPPORTED_LANGUAGES=en,fr,de,es,it    # Comma-separated list
LANG_MIN_CONFIDENCE_THRESHOLD=0.8           # Detection confidence threshold

# Translation Settings  
LANG_TRANSLATION_SERVICE=google             # google, deep_translator
LANG_TRANSLATE_TO_ENGLISH=true              # Auto-translate to English
LANG_PRESERVE_ORIGINAL=true                 # Keep original content
LANG_TRANSLATE_RESPONSE=true                # Localize responses

# Performance Settings
LANG_ENABLE_TRANSLATION_CACHE=true          # Enable caching
LANG_CACHE_EXPIRY_HOURS=168                 # Cache lifetime (1 week)
```

## 🌐 Phase 3: Web Interface Integration

### Key Features
- **💬 Multi-language Chat Interface**: Natural conversation with CTI pipeline in any supported language
- **📄 Document Processing Pipeline**: Drag & drop CTI documents for automatic language detection and processing
- **🔄 Real-time Translation**: Instant translation of CTI content between supported languages
- **📊 System Analytics**: Comprehensive statistics and monitoring dashboard
- **🔗 RESTful API**: Full API access to all multi-language CTI capabilities
- **🎨 Professional UI**: Modern, responsive web interface built with FastAPI

### Web Interface Features
- **Chat System**: Ask questions about threat intelligence in any language
- **File Upload**: Process JSON, TXT, PDF CTI documents
- **Translation Tool**: Translate threat intelligence content between languages
- **Statistics Dashboard**: Monitor query processing, language distribution, and performance metrics
- **API Documentation**: Interactive API docs with OpenAPI/Swagger

### Quick Start
```bash
# Install Phase 3 dependencies
pip install fastapi uvicorn python-multipart jinja2

# Start the web interface
python start_cti_web.py

# Access the interface
open http://localhost:8000
```

### API Endpoints
- `POST /api/chat` - Multi-language chat with CTI pipeline
- `POST /api/detect-language` - Language detection for text
- `POST /api/translate` - Text translation between languages  
- `POST /api/upload-document` - CTI document upload and processing
- `GET /api/documents` - List processed documents
- `GET /api/stats` - System statistics
- `GET /api/history` - Query history
- `GET /docs` - Interactive API documentation

## 🧪 Testing

```bash
# Run all tests
pytest

# Run specific test categories
pytest tests/unit/          # Unit tests
pytest tests/integration/   # Integration tests

# Run multi-language specific tests
pytest tests/unit/test_multilang_components.py

# Run with coverage
pytest --cov=src tests/
```

## 📊 Evaluation Metrics

The system tracks performance using:

- **Context Precision**: Relevance of retrieved documents
- **Faithfulness**: Response grounding in sources  
- **Answer Relevancy**: Response alignment with queries
- **Response Time**: Query processing speed
- **Source Attribution**: Citation accuracy

## 🔒 Security Considerations

- **API Keys**: Stored securely in environment variables
- **Input Validation**: Query sanitization and length limits
- **Data Protection**: Encrypted storage of sensitive CTI
- **Access Control**: Role-based permissions (future enhancement)

## 🛠️ Development

### Adding New Data Sources

1. Create parser in `src/ingestion/parsers/`
2. Add configuration in `config/settings.py`
3. Update data schema in `src/processing/schema.py`
4. Add tests in `tests/unit/ingestion/`

### Extending RAG Pipeline

1. Implement new retrieval strategy in `src/rag/retrieval/`
2. Add prompt templates in `src/rag/prompts/`
3. Update response processing in `src/rag/generation/`

## 📈 Roadmap

- [x] **Phase 1**: RAG CTI Pipeline foundation with Ollama integration ✅
- [x] **Phase 2**: Multi-language CTI support ✅
  - Language detection (langdetect, CLD2)
  - Translation services (Google, Deep Translator)
  - Multi-language document ingestion
  - Query translation and response localization
  - Translation caching and statistics
- [x] **Phase 3**: Web Interface Integration ✅
  - Professional multi-language web interface
  - Real-time chat with CTI pipeline
  - Document upload and processing
  - Translation services API
  - System analytics and statistics
- [ ] **Phase 4**: Graph-based threat analysis
- [ ] **Phase 5**: Real-time feed integration
- [ ] **Phase 6**: SIEM platform connectors
- [ ] **Phase 7**: Automated threat hunting workflows

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- [MITRE ATT&CK](https://attack.mitre.org/) for the threat framework
- [STIX/TAXII](https://oasis-open.github.io/cti-documentation/) for CTI standards
- [Anthropic](https://www.anthropic.com/) for Claude API
- [Ollama](https://ollama.com/) for local LLM deployment
- [GPT-OSS](https://ollama.com/library/gpt-oss) for open-source language model
- [ChromaDB](https://www.trychroma.com/) for vector database
- [LangChain](https://langchain.readthedocs.io/) for RAG framework

## 📞 Support

For questions, issues, or contributions:

- 📧 Email: momeninia.hani@investcyber.com
- 🐛 Issues: [GitHub Issues](https://github.com/Hanimn/Workshop-Labs/issues)