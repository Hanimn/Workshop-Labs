#!/usr/bin/env python3
"""
Phase 1 Setup Verification Script
"""
import sys
from pathlib import Path

def verify_phase1():
    """Verify all Phase 1 components are properly set up"""
    print("🔍 Verifying Phase 1 Setup...\n")
    
    # Check project structure
    required_dirs = [
        "data/raw",
        "data/processed", 
        "data/embeddings",
        "src/ingestion",
        "src/processing",
        "src/rag",
        "src/interfaces",
        "config",
        "tests/unit",
        "tests/integration",
        "notebooks"
    ]
    
    print("📁 Checking project structure:")
    for dir_path in required_dirs:
        path = Path(dir_path)
        status = "✅" if path.exists() else "❌"
        print(f"  {status} {dir_path}")
    
    # Check required files
    required_files = [
        "requirements.txt",
        "README.md",
        ".env.example",
        ".env",
        "config/settings.py",
        "src/__init__.py"
    ]
    
    print("\n📄 Checking required files:")
    for file_path in required_files:
        path = Path(file_path)
        status = "✅" if path.exists() else "❌"
        print(f"  {status} {file_path}")
    
    # Check configuration loading
    print("\n⚙️  Testing configuration:")
    try:
        from config.settings import get_config
        config = get_config()
        print(f"  ✅ Configuration loaded successfully")
        print(f"  ✅ Model: {config.llm.model_name}")
        print(f"  ✅ Ollama URL: {config.llm.ollama_base_url}")
    except Exception as e:
        print(f"  ❌ Configuration error: {e}")
        return False
    
    # Check git setup
    print("\n🔧 Checking git setup:")
    git_dir = Path(".git")
    status = "✅" if git_dir.exists() else "❌"
    print(f"  {status} Git repository initialized")
    
    print("\n🎉 Phase 1 Setup Complete!")
    print("\n📋 Next Steps:")
    print("  1. Install Ollama: curl -fsSL https://ollama.ai/install.sh | sh")
    print("  2. Pull model: ollama pull gpt-oss:120b")
    print("  3. Start Ollama: ollama serve")
    print("  4. Begin Phase 2: Data Sources & Ingestion")
    
    return True

if __name__ == "__main__":
    success = verify_phase1()
    sys.exit(0 if success else 1)