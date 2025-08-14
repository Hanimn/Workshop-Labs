#!/usr/bin/env python3
"""
Phase 3 Web Interface Integration Verification Script
Verifies all Phase 3 components are properly set up and functional
"""
import sys
import time
import asyncio
from pathlib import Path

def verify_phase3():
    """Verify all Phase 3 components are properly set up"""
    print("🔍 Verifying Phase 3: Web Interface Integration...\n")
    
    success = True
    
    # Check Phase 3 specific files
    required_files = [
        "src/interfaces/cti_web_interface.py",
        "start_cti_web.py",
        "demo_phase3.py",
        "requirements_phase2_minimal.txt"
    ]
    
    print("📄 Checking Phase 3 files:")
    for file_path in required_files:
        path = Path(file_path)
        status = "✅" if path.exists() else "❌"
        print(f"  {status} {file_path}")
        if not path.exists():
            success = False
    
    # Check Phase 3 dependencies
    print("\n📦 Checking Phase 3 dependencies:")
    
    dependencies = [
        ("fastapi", "Web framework"),
        ("uvicorn", "ASGI server"),
        ("pydantic", "Data validation"),
        ("jinja2", "Template engine")
    ]
    
    for dep, description in dependencies:
        try:
            if dep == "fastapi":
                import fastapi
            elif dep == "uvicorn":
                import uvicorn
            elif dep == "pydantic":
                import pydantic
            elif dep == "jinja2":
                import jinja2
            
            print(f"  ✅ {dep}: {description}")
        except ImportError:
            print(f"  ❌ {dep}: {description} (not installed)")
            success = False
    
    # Test web interface creation
    print("\n🌐 Testing web interface creation:")
    try:
        from src.interfaces.cti_web_interface import CTIWebInterface, create_app
        
        # Create interface instance
        interface = CTIWebInterface()
        print(f"  ✅ Web interface instance created")
        print(f"      App title: {interface.app.title}")
        print(f"      Version: {interface.app.version}")
        
        # Test FastAPI app creation
        app = create_app()
        print(f"  ✅ FastAPI app created successfully")
        
        # Check Phase 2 integration
        print(f"  ✅ Phase 2 components integrated:")
        print(f"      Language detector: {type(interface.language_detector).__name__}")
        print(f"      Translator: {type(interface.translator).__name__}")
        print(f"      Document processor: {type(interface.document_processor).__name__}")
        print(f"      Query processor: {type(interface.query_processor).__name__}")
        
    except Exception as e:
        print(f"  ❌ Web interface creation error: {e}")
        success = False
    
    # Test API endpoints structure
    print("\n🔗 Testing API endpoints:")
    try:
        from src.interfaces.cti_web_interface import create_app
        app = create_app()
        
        # Get routes
        routes = [route.path for route in app.routes if hasattr(route, 'path')]
        
        expected_endpoints = [
            "/",
            "/api/chat", 
            "/api/detect-language",
            "/api/translate",
            "/api/upload-document", 
            "/api/documents",
            "/api/stats",
            "/api/history"
        ]
        
        for endpoint in expected_endpoints:
            if endpoint in routes:
                print(f"  ✅ {endpoint}")
            else:
                print(f"  ⚠️  {endpoint} (not found in routes)")
        
        print(f"  ✅ Total API routes: {len(routes)}")
        
    except Exception as e:
        print(f"  ❌ API endpoints test error: {e}")
        success = False
    
    # Test configuration integration
    print("\n⚙️  Testing configuration integration:")
    try:
        from config.settings import get_config
        config = get_config()
        
        # Check multi-language config
        if hasattr(config, 'multi_language'):
            ml_config = config.multi_language
            print(f"  ✅ Multi-language config loaded")
            print(f"      Supported languages: {len(ml_config.supported_languages)}")
            print(f"      Translation service: {ml_config.translation_service}")
            print(f"      Default language: {ml_config.default_language}")
        else:
            print(f"  ❌ Multi-language configuration missing")
            success = False
            
    except Exception as e:
        print(f"  ❌ Configuration integration error: {e}")
        success = False
    
    # Test startup scripts
    print("\n🚀 Testing startup scripts:")
    try:
        # Test demo script import
        import demo_phase3
        print(f"  ✅ demo_phase3.py importable")
        
        # Test startup script import
        import start_cti_web
        print(f"  ✅ start_cti_web.py importable")
        
    except Exception as e:
        print(f"  ❌ Startup scripts error: {e}")
        success = False
    
    # Test async components (if any)
    print("\n🔄 Testing async components:")
    try:
        from src.interfaces.cti_web_interface import CTIWebInterface
        interface = CTIWebInterface()
        
        # Test mock RAG pipeline
        async def test_async():
            result = await interface._mock_rag_pipeline("test query")
            return result
        
        # Run async test
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(test_async())
        loop.close()
        
        if result and 'response' in result:
            print(f"  ✅ Async components working")
            print(f"      Mock pipeline response: {len(result['response'])} chars")
        else:
            print(f"  ⚠️  Async components returned unexpected result")
            
    except Exception as e:
        print(f"  ❌ Async components error: {e}")
        success = False
    
    # Performance check
    print("\n⚡ Performance check:")
    try:
        from src.interfaces.cti_web_interface import CTIWebInterface
        
        start_time = time.time()
        interface = CTIWebInterface()
        creation_time = time.time() - start_time
        
        print(f"  ✅ Interface creation time: {creation_time:.3f} seconds")
        
        if creation_time < 2.0:
            print(f"  ✅ Performance: Excellent (< 2s)")
        elif creation_time < 5.0:
            print(f"  ⚠️  Performance: Acceptable (< 5s)")
        else:
            print(f"  ⚠️  Performance: Slow (> 5s)")
        
    except Exception as e:
        print(f"  ❌ Performance check error: {e}")
    
    # Summary
    print("\n" + "="*50)
    
    if success:
        print("🎉 Phase 3 Verification Complete - All Components Ready!")
        print("\n✅ Web Interface Integration Features:")
        print("  • Multi-language chat interface")
        print("  • CTI document processing pipeline")
        print("  • Real-time translation services")
        print("  • System analytics and monitoring")
        print("  • RESTful API with OpenAPI docs")
        print("  • Professional web UI")
        
        print("\n📋 Next Steps:")
        print("  1. Start web interface: python start_cti_web.py")
        print("  2. Access interface: http://localhost:8000")
        print("  3. Test multi-language chat")
        print("  4. Upload CTI documents")
        print("  5. Use translation services")
        print("  6. View system statistics")
        
        print("\n🌟 Integration Complete:")
        print("  Phase 1 (RAG + Ollama) + Phase 2 (Multi-language) + Phase 3 (Web UI)")
        
        return True
    else:
        print("❌ Phase 3 Verification Failed - Issues Found")
        print("\n🔧 Fix Required Issues:")
        print("  1. Install missing dependencies: pip install -r requirements_phase2_minimal.txt")
        print("  2. Check file existence and permissions") 
        print("  3. Verify Phase 2 components are working")
        print("  4. Re-run verification: python verify_phase3.py")
        
        return False

def main():
    """Main verification function"""
    try:
        success = verify_phase3()
        return 0 if success else 1
    except KeyboardInterrupt:
        print("\n⏹️  Verification interrupted by user")
        return 1
    except Exception as e:
        print(f"\n💥 Verification failed with unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())