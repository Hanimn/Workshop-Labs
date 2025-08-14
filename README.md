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

## 🧪 Testing

```bash
# Run all tests
pytest

# Run specific test categories
pytest tests/unit/          # Unit tests
pytest tests/integration/   # Integration tests

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
- [ ] **Phase 2**: Multi-language CTI support
- [ ] **Phase 3**: Graph-based threat analysis
- [ ] **Phase 4**: Real-time feed integration
- [ ] **Phase 5**: SIEM platform connectors
- [ ] **Phase 6**: Automated threat hunting workflows

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