#!/usr/bin/env python3
"""
Phase 2 Multi-language Support Verification Script
Verifies all Phase 2 components are properly set up and functional
"""
import sys
import traceback
from pathlib import Path

def verify_phase2():
    """Verify all Phase 2 components are properly set up"""
    print("🔍 Verifying Phase 2: Multi-language Support...\n")
    
    success = True
    
    # Check Phase 2 specific files
    required_files = [
        "src/processing/language_detector.py",
        "src/processing/translator.py", 
        "src/ingestion/multilang_processor.py",
        "src/rag/multilang_query_processor.py",
        "tests/unit/test_multilang_components.py",
        "data/raw/sample_multilang_cti.json",
        "demo_phase2.py"
    ]
    
    print("📄 Checking Phase 2 files:")
    for file_path in required_files:
        path = Path(file_path)
        status = "✅" if path.exists() else "❌"
        print(f"  {status} {file_path}")
        if not path.exists():
            success = False
    
    # Check dependencies
    print("\n📦 Checking Phase 2 dependencies:")
    
    dependencies = [
        ("langdetect", "Language detection"),
        ("googletrans", "Google translation service"),
        ("deep_translator", "Deep translation service"),
        ("pycld2", "CLD2 language detection (optional)")
    ]
    
    for dep, description in dependencies:
        try:
            if dep == "pycld2":
                import pycld2 as cld2
            elif dep == "langdetect":
                from langdetect import detect
            elif dep == "googletrans":
                from googletrans import Translator
            elif dep == "deep_translator":
                from deep_translator import GoogleTranslator
            
            print(f"  ✅ {dep}: {description}")
        except ImportError:
            print(f"  ❌ {dep}: {description} (not installed)")
            if dep != "pycld2":  # pycld2 is optional
                success = False
    
    # Test configuration loading
    print("\n⚙️  Testing Phase 2 configuration:")
    try:
        from config.settings import get_config
        config = get_config()
        
        # Check multi-language config exists
        if hasattr(config, 'multi_language'):
            ml_config = config.multi_language
            print(f"  ✅ Multi-language config loaded")
            print(f"      Default language: {ml_config.default_language}")
            print(f"      Translation service: {ml_config.translation_service}")
            print(f"      Supported languages: {len(ml_config.supported_languages)}")
            print(f"      Translate to English: {ml_config.translate_to_english}")
        else:
            print(f"  ❌ Multi-language configuration missing")
            success = False
            
    except Exception as e:
        print(f"  ❌ Configuration error: {e}")
        success = False
    
    # Test language detection
    print("\n🔍 Testing language detection:")
    try:
        from src.processing.language_detector import LanguageDetector
        detector = LanguageDetector()
        
        # Test with English text
        result = detector.detect_language("This is a test of the language detection system")
        print(f"  ✅ Language detection working")
        print(f"      Detected: {result.language} (confidence: {result.confidence:.2f})")
        
    except Exception as e:
        print(f"  ❌ Language detection error: {e}")
        success = False
    
    # Test translation service (without actual translation to avoid API calls)
    print("\n🔄 Testing translation service:")
    try:
        from src.processing.translator import TranslationService
        translator = TranslationService()
        
        # Check if services are initialized
        if translator.services:
            print(f"  ✅ Translation service initialized")
            print(f"      Primary service: {translator.primary_service}")
            print(f"      Available services: {list(translator.services.keys())}")
        else:
            print(f"  ❌ No translation services available")
            success = False
            
    except Exception as e:
        print(f"  ❌ Translation service error: {e}")
        success = False
    
    # Test multi-language processor
    print("\n📄 Testing multi-language processor:")
    try:
        from src.ingestion.multilang_processor import MultiLanguageProcessor
        processor = MultiLanguageProcessor()
        
        print(f"  ✅ Multi-language processor initialized")
        
        # Test with sample document
        sample_doc = {
            "title": "Test Threat Report",
            "description": "This is a test threat intelligence document"
        }
        
        # This won't do actual translation to avoid API calls
        result = processor._extract_text_content(sample_doc)
        if result:
            print(f"  ✅ Document text extraction working")
        
    except Exception as e:
        print(f"  ❌ Multi-language processor error: {e}")
        success = False
    
    # Test query processor
    print("\n💬 Testing query processor:")
    try:
        from src.rag.multilang_query_processor import MultiLanguageQueryProcessor
        query_processor = MultiLanguageQueryProcessor()
        
        print(f"  ✅ Query processor initialized")
        
        # Test supported languages
        supported = query_processor.get_supported_languages()
        print(f"      Supported languages: {len(supported)}")
        
    except Exception as e:
        print(f"  ❌ Query processor error: {e}")
        success = False
    
    # Test sample data
    print("\n📊 Testing sample data:")
    try:
        sample_file = Path("data/raw/sample_multilang_cti.json")
        if sample_file.exists():
            import json
            with open(sample_file, 'r', encoding='utf-8') as f:
                sample_data = json.load(f)
            
            print(f"  ✅ Sample multi-language data loaded")
            print(f"      Documents: {len(sample_data)}")
            
            # Check for different languages
            languages = set()
            for doc in sample_data:
                if 'language' in doc:
                    languages.add(doc['language'])
            
            print(f"      Languages in sample: {', '.join(sorted(languages))}")
        else:
            print(f"  ⚠️  Sample data file not found (optional)")
            
    except Exception as e:
        print(f"  ❌ Sample data error: {e}")
    
    # Summary
    print("\n" + "="*50)
    
    if success:
        print("🎉 Phase 2 Verification Complete - All Components Ready!")
        print("\n✅ Multi-language Support Features:")
        print("  • Language detection (langdetect, CLD2)")
        print("  • Translation services (Google, Deep Translator)")
        print("  • Multi-language document processing")
        print("  • Query translation and response localization")
        print("  • Translation caching and statistics")
        
        print("\n📋 Next Steps:")
        print("  1. Run demo: python demo_phase2.py")
        print("  2. Process multi-language CTI: see README Phase 2 examples")
        print("  3. Configure translation services in .env if needed")
        print("  4. Begin Phase 3: Graph-based threat analysis")
        
        return True
    else:
        print("❌ Phase 2 Verification Failed - Issues Found")
        print("\n🔧 Fix Required Issues:")
        print("  1. Install missing dependencies: pip install -r requirements.txt") 
        print("  2. Check file existence and permissions")
        print("  3. Verify configuration settings")
        print("  4. Re-run verification: python verify_phase2.py")
        
        return False

def main():
    """Main verification function"""
    try:
        success = verify_phase2()
        return 0 if success else 1
    except KeyboardInterrupt:
        print("\n⏹️  Verification interrupted by user")
        return 1
    except Exception as e:
        print(f"\n💥 Verification failed with unexpected error: {e}")
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())