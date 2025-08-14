#!/usr/bin/env python3
"""
CTI Web Interface Startup Script
Easy launcher for the multi-language CTI web interface
"""
import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def main():
    """Main startup function"""
    print("🚀 Starting CTI Multi-language Web Interface")
    print("=" * 60)
    print()
    print("🌍 Phase 3: Open WebUI Integration")
    print("   Integrating Phase 1 (RAG + Ollama) + Phase 2 (Multi-language)")
    print()
    print("✨ Features:")
    print("   💬 Multi-language chat interface")
    print("   📄 CTI document upload and processing")
    print("   🔄 Real-time text translation")
    print("   📊 System statistics and analytics")
    print("   🌐 Support for 10+ languages")
    print()
    print("🔗 Access URLs:")
    print("   Main Interface: http://localhost:8000")
    print("   API Docs: http://localhost:8000/docs")
    print("   Stats API: http://localhost:8000/api/stats")
    print()
    print("⚡ Starting server...")
    print("   Press Ctrl+C to stop")
    print("=" * 60)
    
    try:
        # Import and run the web interface
        from src.interfaces.cti_web_interface import run_server
        run_server(host="0.0.0.0", port=8000, debug=True)
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("💡 Make sure you've installed the requirements:")
        print("   pip install -r requirements_phase2_minimal.txt")
        return 1
        
    except KeyboardInterrupt:
        print("\n⏹️  Server stopped by user")
        return 0
        
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())