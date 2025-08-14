#!/usr/bin/env python3
"""
Phase 2 Multi-language CTI Demo Script
Demonstrates multi-language processing capabilities
"""
import sys
import json
from pathlib import Path
from typing import List, Dict
import time

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from config.settings import get_config
from src.processing.language_detector import LanguageDetector
from src.processing.translator import TranslationService
from src.ingestion.multilang_processor import MultiLanguageProcessor
from src.rag.multilang_query_processor import MultiLanguageQueryProcessor


def print_header(title: str):
    """Print formatted header"""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def print_separator():
    """Print separator line"""
    print("-" * 60)


def demo_language_detection():
    """Demonstrate language detection capabilities"""
    print_header("PHASE 2 DEMO: Language Detection")
    
    # Sample texts in different languages
    sample_texts = {
        "English": "APT29 has been observed using spear-phishing emails targeting healthcare organizations.",
        "French": "APT28 a été observé utilisant des techniques d'hameçonnage ciblé contre les institutions financières.",
        "German": "Die Lazarus-Gruppe nutzt Supply-Chain-Angriffe gegen deutsche Finanzinstitutionen.",
        "Spanish": "FIN7 ha desarrollado nuevas técnicas de evasión para comprometer sistemas de punto de venta.",
        "Russian": "Группа Turla использует сложные методы шифрования для скрытия командных каналов.",
        "Chinese": "APT40海莲花组织采用定制化后门程序维持长期访问权限。",
        "Japanese": "BlackTechグループは製造業企業の産業制御システムを標的としている。",
        "Arabic": "مجموعة MuddyWater تستخدم تقنيات التصيد المتقدمة ضد المؤسسات الحكومية。"
    }
    
    try:
        detector = LanguageDetector()
        
        for expected_lang, text in sample_texts.items():
            print(f"\n📝 Text: {text[:50]}...")
            print(f"🏷️  Expected: {expected_lang}")
            
            result = detector.detect_language(text)
            
            print(f"🔍 Detected: {detector.get_language_name(result.language)} ({result.language})")
            print(f"🎯 Confidence: {result.confidence:.2f}")
            print(f"🛠️  Detector: {result.detector_used}")
            print(f"✅ Reliable: {result.is_reliable}")
            
            if result.alternatives:
                print(f"🔄 Alternatives: {result.alternatives[:2]}")
            
            print_separator()
            
    except Exception as e:
        print(f"❌ Language detection demo failed: {e}")
        print("💡 Make sure to install language detection dependencies:")
        print("   pip install langdetect pycld2")


def demo_translation():
    """Demonstrate translation capabilities"""
    print_header("PHASE 2 DEMO: Translation Service")
    
    # Sample threat intelligence texts for translation
    sample_texts = [
        ("fr", "APT28 utilise des techniques d'hameçonnage sophistiquées pour cibler les institutions financières européennes."),
        ("de", "Die Lazarus-Gruppe hat ihre Angriffstechniken weiterentwickelt und nutzt jetzt Zero-Day-Exploits."),
        ("es", "FIN7 ha implementado nuevos métodos de evasión para comprometer sistemas de punto de venta en Europa."),
        ("ru", "Группа Turla разработала новые методы шифрования для обхода систем обнаружения."),
    ]
    
    try:
        translator = TranslationService()
        
        print("🌍 Translating threat intelligence to English...\n")
        
        for source_lang, text in sample_texts:
            print(f"📝 Original ({source_lang}): {text}")
            
            try:
                result = translator.translate_text(text, source_lang=source_lang, target_lang='en')
                
                print(f"🔄 Translated: {result.translated_text}")
                print(f"🎯 Confidence: {result.confidence:.2f}")
                print(f"🛠️  Service: {result.translation_service}")
                print(f"⚡ Cached: {result.cached}")
                
            except Exception as e:
                print(f"❌ Translation failed: {e}")
            
            print_separator()
            
    except Exception as e:
        print(f"❌ Translation demo failed: {e}")
        print("💡 Make sure translation services are available:")
        print("   pip install googletrans==4.0.0rc1 deep-translator")


def demo_document_processing():
    """Demonstrate multi-language document processing"""
    print_header("PHASE 2 DEMO: Multi-language Document Processing")
    
    sample_file = Path("data/raw/sample_multilang_cti.json")
    
    if not sample_file.exists():
        print(f"❌ Sample file not found: {sample_file}")
        print("💡 Please ensure sample_multilang_cti.json exists in data/raw/")
        return
    
    try:
        processor = MultiLanguageProcessor()
        
        print(f"📂 Processing file: {sample_file}")
        print("🔄 Loading and processing documents...\n")
        
        # Process the sample file
        documents = processor.process_file(sample_file)
        
        print(f"📊 Processed {len(documents)} documents")
        print_separator()
        
        # Display processing statistics
        stats = processor.get_processing_stats()
        
        print("📈 PROCESSING STATISTICS:")
        print(f"   Total documents: {stats.total_documents}")
        print(f"   Translated: {stats.translated_documents}")
        print(f"   Skipped: {stats.skipped_documents}")
        print(f"   Failed: {stats.failed_documents}")
        print(f"   Processing time: {stats.processing_time:.2f}s")
        
        if stats.languages_detected:
            print("\n🌍 LANGUAGE DISTRIBUTION:")
            for lang, count in sorted(stats.languages_detected.items(), key=lambda x: x[1], reverse=True):
                percentage = (count / stats.total_documents) * 100
                print(f"   {lang}: {count} documents ({percentage:.1f}%)")
        
        print_separator()
        
        # Show sample processed documents
        print("📄 SAMPLE PROCESSED DOCUMENTS:\n")
        
        for i, doc in enumerate(documents[:3]):  # Show first 3
            print(f"🔹 Document {i+1}:")
            print(f"   ID: {doc.document_id}")
            print(f"   Original Language: {doc.original_language}")
            print(f"   Confidence: {doc.confidence:.2f}")
            print(f"   Source: {doc.source}")
            
            # Show original vs translated title if available
            if doc.original_content and doc.english_content:
                orig_title = doc.original_content.get('title', 'N/A')
                eng_title = doc.english_content.get('title', 'N/A')
                
                if orig_title != eng_title:
                    print(f"   Original Title: {orig_title}")
                    print(f"   Translated Title: {eng_title}")
                else:
                    print(f"   Title: {orig_title}")
            
            print()
            
    except Exception as e:
        print(f"❌ Document processing demo failed: {e}")
        import traceback
        traceback.print_exc()


def demo_query_processing():
    """Demonstrate multi-language query processing"""
    print_header("PHASE 2 DEMO: Multi-language Query Processing")
    
    # Sample queries in different languages
    sample_queries = [
        ("en", "What are the latest techniques used by APT29?"),
        ("fr", "Quelles sont les dernières techniques utilisées par APT28?"),
        ("de", "Welche neuen Angriffsmethoden nutzt die Lazarus-Gruppe?"),
        ("es", "¿Cuáles son las nuevas tácticas de FIN7 contra el sector retail?"),
    ]
    
    try:
        query_processor = MultiLanguageQueryProcessor()
        
        print("🔍 Processing multi-language queries...\n")
        
        for expected_lang, query in sample_queries:
            print(f"❓ Query ({expected_lang}): {query}")
            
            try:
                # Process the query
                processed_query = query_processor.process_query(query)
                
                print(f"🔍 Detected Language: {processed_query.original_language}")
                print(f"🔄 English Query: {processed_query.english_query}")
                print(f"📊 Confidence: {processed_query.confidence:.2f}")
                print(f"🌐 Translation Needed: {processed_query.translation_needed}")
                
                # Mock RAG pipeline response
                mock_response = f"Analysis shows various techniques for the queried threat actor. The latest intelligence indicates sophisticated methods being employed."
                
                # Demonstrate response localization
                if processed_query.original_language != 'en':
                    try:
                        localized_response = query_processor.localize_response(
                            mock_response, 
                            processed_query.original_language
                        )
                        print(f"📤 English Response: {mock_response}")
                        print(f"🌍 Localized Response: {localized_response.localized_response}")
                    except Exception as e:
                        print(f"⚠️  Response localization failed: {e}")
                
            except Exception as e:
                print(f"❌ Query processing failed: {e}")
            
            print_separator()
        
        # Display query statistics
        stats = query_processor.get_query_statistics()
        print("📊 QUERY PROCESSING STATISTICS:")
        print(f"   Total queries: {stats['total_queries_processed']}")
        print(f"   Translations needed: {stats['queries_requiring_translation']}")
        print(f"   Translation rate: {stats['translation_rate']:.1f}%")
        print(f"   Avg processing time: {stats['average_processing_time_seconds']:.3f}s")
        
        if stats['language_distribution']:
            print("\n🌍 QUERY LANGUAGE DISTRIBUTION:")
            for lang, count in stats['language_distribution'].items():
                print(f"   {lang}: {count} queries")
        
    except Exception as e:
        print(f"❌ Query processing demo failed: {e}")


def demo_supported_languages():
    """Demonstrate supported languages"""
    print_header("PHASE 2 DEMO: Supported Languages")
    
    try:
        config = get_config()
        detector = LanguageDetector()
        query_processor = MultiLanguageQueryProcessor()
        
        print("🌍 SUPPORTED LANGUAGES:")
        print()
        
        supported_langs = query_processor.get_supported_languages()
        
        for lang_code, lang_name in supported_langs.items():
            print(f"   {lang_code} - {lang_name}")
        
        print(f"\n📊 Total supported languages: {len(supported_langs)}")
        
        print("\n⚙️  CONFIGURATION:")
        print(f"   Default language: {config.multi_language.default_language}")
        print(f"   Translation service: {config.multi_language.translation_service}")
        print(f"   Auto-detect queries: {config.multi_language.auto_detect_query_language}")
        print(f"   Translate responses: {config.multi_language.translate_response}")
        print(f"   Preserve originals: {config.multi_language.preserve_original}")
        print(f"   Cache translations: {config.multi_language.enable_translation_cache}")
        
    except Exception as e:
        print(f"❌ Language configuration demo failed: {e}")


def main():
    """Run Phase 2 demonstration"""
    print("🚀 RAG CTI Pipeline - Phase 2: Multi-language Support Demo")
    print("🌍 Demonstrating language detection, translation, and multi-language processing")
    
    try:
        # Run demonstrations
        demo_supported_languages()
        demo_language_detection()
        demo_translation()
        demo_document_processing()
        demo_query_processing()
        
        print_header("PHASE 2 DEMO COMPLETE")
        print("✅ Multi-language CTI processing capabilities demonstrated successfully!")
        print("\n🎯 Key Features Demonstrated:")
        print("   • Language detection with multiple backends")
        print("   • Text translation with caching")
        print("   • Multi-language document processing")
        print("   • Query translation and response localization")
        print("   • Comprehensive statistics and reporting")
        
        print("\n📚 Next Steps:")
        print("   • Install dependencies: pip install -r requirements.txt")
        print("   • Configure .env with translation service settings")
        print("   • Process your own multi-language CTI documents")
        print("   • Integrate with RAG pipeline for full functionality")
        
    except KeyboardInterrupt:
        print("\n⏹️  Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Demo failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())