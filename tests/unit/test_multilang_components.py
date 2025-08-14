"""
Unit Tests for Multi-language CTI Components
"""
import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

from src.processing.language_detector import LanguageDetector, LanguageDetectionResult
from src.processing.translator import TranslationService, TranslationResult
from src.ingestion.multilang_processor import MultiLanguageProcessor, MultiLangDocument
from src.rag.multilang_query_processor import MultiLanguageQueryProcessor, MultiLangQuery, MultiLangResponse


class TestLanguageDetector:
    """Test cases for language detection service"""
    
    @pytest.fixture
    def detector(self):
        """Create language detector instance"""
        with patch('src.processing.language_detector.get_config') as mock_config:
            mock_config.return_value.multi_language.supported_languages = ['en', 'fr', 'de', 'es']
            mock_config.return_value.multi_language.default_language = 'en'
            mock_config.return_value.multi_language.min_confidence_threshold = 0.8
            return LanguageDetector()
    
    def test_detect_english_text(self, detector):
        """Test detection of English text"""
        text = "This is a cyber threat intelligence report about APT29 activities."
        
        with patch('src.processing.language_detector.detect') as mock_detect:
            mock_detect.return_value = 'en'
            with patch('src.processing.language_detector.detect_langs') as mock_detect_langs:
                mock_lang = Mock()
                mock_lang.lang = 'en'
                mock_lang.prob = 0.95
                mock_detect_langs.return_value = [mock_lang]
                
                result = detector.detect_language(text)
                
                assert result.language == 'en'
                assert result.confidence > 0.8
                assert result.is_reliable
                assert result.detector_used == 'langdetect'
    
    def test_detect_short_text(self, detector):
        """Test detection with short text"""
        text = "Hello"
        
        result = detector.detect_language(text, min_chars=10)
        
        assert result.language == 'en'  # default language
        assert result.confidence == 0.0
        assert not result.is_reliable
        assert result.detector_used == 'default'
    
    def test_detect_unsupported_language(self, detector):
        """Test detection of unsupported language"""
        text = "这是一个中文文本"  # Chinese text
        
        with patch('src.processing.language_detector.detect') as mock_detect:
            mock_detect.return_value = 'zh'
            with patch('src.processing.language_detector.detect_langs') as mock_detect_langs:
                mock_lang = Mock()
                mock_lang.lang = 'zh'
                mock_lang.prob = 0.95
                mock_detect_langs.return_value = [mock_lang]
                
                result = detector.detect_language(text)
                
                assert result.language == 'en'  # fallback to default
                assert result.detector_used == 'langdetect'
    
    def test_batch_detect(self, detector):
        """Test batch language detection"""
        texts = [
            "This is English text about cybersecurity",
            "Ceci est un texte français",
            "Dies ist deutscher Text"
        ]
        
        with patch.object(detector, 'detect_language') as mock_detect:
            mock_detect.side_effect = [
                LanguageDetectionResult('en', 0.9, True, 'langdetect'),
                LanguageDetectionResult('fr', 0.85, True, 'langdetect'),
                LanguageDetectionResult('de', 0.88, True, 'langdetect')
            ]
            
            results = detector.batch_detect(texts)
            
            assert len(results) == 3
            assert results[0].language == 'en'
            assert results[1].language == 'fr'
            assert results[2].language == 'de'


class TestTranslationService:
    """Test cases for translation service"""
    
    @pytest.fixture
    def translator(self):
        """Create translation service instance"""
        with patch('src.processing.translator.get_config') as mock_config:
            mock_config.return_value.multi_language.translation_service = 'google'
            mock_config.return_value.multi_language.preserve_original = True
            mock_config.return_value.multi_language.enable_translation_cache = False
            mock_config.return_value.data_dir = Path('/tmp')
            return TranslationService()
    
    def test_translate_text_same_language(self, translator):
        """Test translation when source and target are the same"""
        with patch.object(translator.language_detector, 'detect_language') as mock_detect:
            mock_detect.return_value = LanguageDetectionResult('en', 0.9, True, 'langdetect')
            
            result = translator.translate_text("This is English text", target_lang='en')
            
            assert result.translated_text == "This is English text"
            assert result.source_language == 'en'
            assert result.target_language == 'en'
            assert result.translation_service == 'no_translation_needed'
    
    def test_translate_text_different_language(self, translator):
        """Test translation between different languages"""
        with patch.object(translator.language_detector, 'detect_language') as mock_detect:
            mock_detect.return_value = LanguageDetectionResult('fr', 0.9, True, 'langdetect')
            
            with patch.object(translator.services['google'], 'translate') as mock_translate:
                mock_translate.return_value = TranslationResult(
                    original_text="Bonjour le monde",
                    translated_text="Hello world",
                    source_language='fr',
                    target_language='en',
                    confidence=0.95,
                    translation_service='google'
                )
                
                result = translator.translate_text("Bonjour le monde", target_lang='en')
                
                assert result.translated_text == "Hello world"
                assert result.source_language == 'fr'
                assert result.target_language == 'en'
                assert result.translation_service == 'google'
    
    def test_translate_cti_document(self, translator):
        """Test CTI document translation"""
        document = {
            'id': 'test-1',
            'title': 'Rapport de menace',
            'description': 'Ceci est une description de menace',
            'timestamp': '2024-01-01',
            'non_text_field': 123
        }
        
        with patch.object(translator, 'translate_text') as mock_translate:
            mock_translate.side_effect = [
                TranslationResult("Rapport de menace", "Threat report", 'fr', 'en', 0.9, 'google'),
                TranslationResult("Ceci est une description de menace", "This is a threat description", 'fr', 'en', 0.9, 'google')
            ]
            
            result = translator.translate_cti_document(document)
            
            assert result['title'] == 'Threat report'
            assert result['description'] == 'This is a threat description'
            assert result['timestamp'] == '2024-01-01'  # Unchanged
            assert result['non_text_field'] == 123  # Unchanged
            assert '_translation_metadata' in result
    
    def test_batch_translate(self, translator):
        """Test batch translation"""
        texts = ["Bonjour", "Au revoir"]
        
        with patch.object(translator, 'translate_text') as mock_translate:
            mock_translate.side_effect = [
                TranslationResult("Bonjour", "Hello", 'fr', 'en', 0.9, 'google'),
                TranslationResult("Au revoir", "Goodbye", 'fr', 'en', 0.9, 'google')
            ]
            
            results = translator.batch_translate(texts, source_lang='fr', target_lang='en')
            
            assert len(results) == 2
            assert results[0].translated_text == "Hello"
            assert results[1].translated_text == "Goodbye"


class TestMultiLanguageProcessor:
    """Test cases for multi-language processor"""
    
    @pytest.fixture
    def processor(self):
        """Create multi-language processor instance"""
        with patch('src.ingestion.multilang_processor.get_config') as mock_config:
            mock_config.return_value.multi_language.translate_to_english = True
            mock_config.return_value.multi_language.preserve_original = True
            return MultiLanguageProcessor()
    
    def test_process_english_document(self, processor):
        """Test processing document already in English"""
        document = {
            'id': 'test-1',
            'title': 'Cyber Threat Report',
            'description': 'This is a threat intelligence report'
        }
        
        with patch.object(processor.language_detector, 'detect_language') as mock_detect:
            mock_detect.return_value = LanguageDetectionResult('en', 0.9, True, 'langdetect')
            
            result = processor.process_document(document, source='test')
            
            assert isinstance(result, MultiLangDocument)
            assert result.original_language == 'en'
            assert result.english_content == document
            assert result.source == 'test'
    
    def test_process_foreign_document(self, processor):
        """Test processing document in foreign language"""
        document = {
            'id': 'test-1',
            'title': 'Rapport de menace',
            'description': 'Ceci est un rapport de renseignement sur les menaces'
        }
        
        with patch.object(processor.language_detector, 'detect_language') as mock_detect:
            mock_detect.return_value = LanguageDetectionResult('fr', 0.9, True, 'langdetect')
            
            with patch.object(processor.translator, 'translate_cti_document') as mock_translate:
                translated_doc = document.copy()
                translated_doc['title'] = 'Threat report'
                translated_doc['description'] = 'This is a threat intelligence report'
                mock_translate.return_value = translated_doc
                
                result = processor.process_document(document, source='test')
                
                assert isinstance(result, MultiLangDocument)
                assert result.original_language == 'fr'
                assert result.english_content['title'] == 'Threat report'
                assert result.original_content == document
    
    def test_extract_text_content(self, processor):
        """Test text extraction from document"""
        document = {
            'title': 'Test Title',
            'description': 'Test Description',
            'details': {
                'analysis': 'Nested analysis text'
            },
            'metadata': {
                'timestamp': '2024-01-01'
            }
        }
        
        text = processor._extract_text_content(document)
        
        assert 'Test Title' in text
        assert 'Test Description' in text
        assert 'Nested analysis text' in text
        assert '2024-01-01' not in text  # Non-text field
    
    def test_process_batch(self, processor):
        """Test batch processing"""
        documents = [
            {'title': 'English doc', 'description': 'English description'},
            {'title': 'Français doc', 'description': 'Description française'}
        ]
        
        with patch.object(processor, 'process_document') as mock_process:
            mock_process.side_effect = [
                MultiLangDocument('doc1', 'test', 'en', 0.9, documents[0]),
                MultiLangDocument('doc2', 'test', 'fr', 0.9, documents[1])
            ]
            
            results = processor.process_batch(documents, source='test', max_workers=1)
            
            assert len(results) == 2
            assert all(isinstance(r, MultiLangDocument) for r in results)


class TestMultiLanguageQueryProcessor:
    """Test cases for multi-language query processor"""
    
    @pytest.fixture
    def query_processor(self):
        """Create multi-language query processor instance"""
        with patch('src.rag.multilang_query_processor.get_config') as mock_config:
            mock_config.return_value.multi_language.auto_detect_query_language = True
            mock_config.return_value.multi_language.translate_response = True
            mock_config.return_value.multi_language.default_language = 'en'
            return MultiLanguageQueryProcessor()
    
    def test_process_english_query(self, query_processor):
        """Test processing English query"""
        query = "What are the latest APT29 techniques?"
        
        with patch.object(query_processor.language_detector, 'detect_language') as mock_detect:
            mock_detect.return_value = LanguageDetectionResult('en', 0.9, True, 'langdetect')
            
            result = query_processor.process_query(query)
            
            assert isinstance(result, MultiLangQuery)
            assert result.original_language == 'en'
            assert result.english_query == query
            assert not result.translation_needed
    
    def test_process_foreign_query(self, query_processor):
        """Test processing non-English query"""
        query = "Quelles sont les dernières techniques d'APT29?"
        
        with patch.object(query_processor.language_detector, 'detect_language') as mock_detect:
            mock_detect.return_value = LanguageDetectionResult('fr', 0.9, True, 'langdetect')
            
            with patch.object(query_processor.translator, 'translate_text') as mock_translate:
                mock_translate.return_value = TranslationResult(
                    query, "What are the latest APT29 techniques?", 'fr', 'en', 0.9, 'google'
                )
                
                result = query_processor.process_query(query)
                
                assert isinstance(result, MultiLangQuery)
                assert result.original_language == 'fr'
                assert result.english_query == "What are the latest APT29 techniques?"
                assert result.translation_needed
    
    def test_localize_response(self, query_processor):
        """Test response localization"""
        english_response = "APT29 uses spear-phishing and living-off-the-land techniques."
        
        with patch.object(query_processor.translator, 'translate_text') as mock_translate:
            mock_translate.return_value = TranslationResult(
                english_response, 
                "APT29 utilise des techniques de spear-phishing et de living-off-the-land.", 
                'en', 'fr', 0.9, 'google'
            )
            
            result = query_processor.localize_response(english_response, 'fr', [])
            
            assert isinstance(result, MultiLangResponse)
            assert result.english_response == english_response
            assert result.localized_response == "APT29 utilise des techniques de spear-phishing et de living-off-the-land."
            assert result.response_language == 'fr'
    
    def test_process_query_response_cycle(self, query_processor):
        """Test complete query-response cycle"""
        query = "Quelles sont les techniques d'APT29?"
        
        # Mock RAG pipeline function
        def mock_rag_pipeline(english_query):
            return "APT29 uses various techniques.", [{'title': 'APT29 Report'}]
        
        with patch.object(query_processor, 'process_query') as mock_process_query:
            mock_query = MultiLangQuery(
                query, 'fr', "What are APT29 techniques?", 0.9, True
            )
            mock_process_query.return_value = mock_query
            
            with patch.object(query_processor.translator, 'translate_text') as mock_translate:
                mock_translate.return_value = TranslationResult(
                    "APT29 uses various techniques.", 
                    "APT29 utilise diverses techniques.", 
                    'en', 'fr', 0.9, 'google'
                )
                
                result = query_processor.process_query_response_cycle(
                    query, mock_rag_pipeline, 'fr'
                )
                
                assert isinstance(result, MultiLangResponse)
                assert result.query.original_query == query
                assert result.english_response == "APT29 uses various techniques."
                assert result.localized_response == "APT29 utilise diverses techniques."
    
    def test_get_supported_languages(self, query_processor):
        """Test getting supported languages"""
        with patch.object(query_processor.language_detector, 'get_language_name') as mock_get_name:
            mock_get_name.side_effect = lambda x: {'en': 'English', 'fr': 'French'}.get(x, x)
            query_processor.lang_config.supported_languages = ['en', 'fr']
            
            result = query_processor.get_supported_languages()
            
            assert result == {'en': 'English', 'fr': 'French'}
    
    def test_validate_language_support(self, query_processor):
        """Test language support validation"""
        query_processor.lang_config.supported_languages = ['en', 'fr', 'de']
        
        # Test supported language
        is_supported, message = query_processor.validate_language_support('fr')
        assert is_supported
        assert 'supported' in message.lower()
        
        # Test unsupported language
        is_supported, message = query_processor.validate_language_support('zh')
        assert not is_supported
        assert 'not supported' in message.lower()
        
        # Test empty language
        is_supported, message = query_processor.validate_language_support('')
        assert not is_supported
        assert 'empty' in message.lower()


@pytest.fixture
def sample_cti_documents():
    """Sample CTI documents for testing"""
    return [
        {
            'id': 'cti-001',
            'title': 'APT29 Campaign Analysis',
            'description': 'Analysis of recent APT29 activities targeting healthcare sector',
            'techniques': ['T1566.001', 'T1055'],
            'timestamp': '2024-01-15'
        },
        {
            'id': 'cti-002',
            'title': 'Analyse de campagne APT28',
            'description': 'Analyse des activités récentes d\'APT28 ciblant le secteur financier',
            'techniques': ['T1190', 'T1083'],
            'timestamp': '2024-01-16'
        },
        {
            'id': 'cti-003',
            'title': 'Lazarus-Gruppe Kampagnenanalyse',
            'description': 'Analyse der jüngsten Aktivitäten der Lazarus-Gruppe',
            'techniques': ['T1027', 'T1105'],
            'timestamp': '2024-01-17'
        }
    ]


class TestIntegrationMultiLang:
    """Integration tests for multi-language components"""
    
    def test_end_to_end_multilang_processing(self, sample_cti_documents):
        """Test complete multi-language processing pipeline"""
        with patch('src.ingestion.multilang_processor.get_config') as mock_config:
            mock_config.return_value.multi_language.translate_to_english = True
            mock_config.return_value.multi_language.preserve_original = True
            mock_config.return_value.multi_language.supported_languages = ['en', 'fr', 'de']
            
            processor = MultiLanguageProcessor()
            
            # Mock language detection and translation
            with patch.object(processor.language_detector, 'detect_language') as mock_detect:
                with patch.object(processor.translator, 'translate_cti_document') as mock_translate:
                    # Setup mocks for different languages
                    mock_detect.side_effect = [
                        LanguageDetectionResult('en', 0.9, True, 'langdetect'),  # English doc
                        LanguageDetectionResult('fr', 0.85, True, 'langdetect'),  # French doc
                        LanguageDetectionResult('de', 0.88, True, 'langdetect')   # German doc
                    ]
                    
                    # Mock translations
                    def mock_translate_func(doc):
                        if 'APT28' in doc.get('title', ''):
                            doc['title'] = 'APT28 Campaign Analysis'
                            doc['description'] = 'Analysis of recent APT28 activities targeting financial sector'
                        elif 'Lazarus' in doc.get('title', ''):
                            doc['title'] = 'Lazarus Group Campaign Analysis'
                            doc['description'] = 'Analysis of recent Lazarus Group activities'
                        return doc
                    
                    mock_translate.side_effect = mock_translate_func
                    
                    # Process documents
                    results = processor.process_batch(sample_cti_documents, source='integration_test')
                    
                    # Verify results
                    assert len(results) == 3
                    assert all(isinstance(r, MultiLangDocument) for r in results)
                    
                    # Check language assignments
                    assert results[0].original_language == 'en'
                    assert results[1].original_language == 'fr'
                    assert results[2].original_language == 'de'
                    
                    # Check translations occurred for non-English docs
                    assert 'APT28 Campaign Analysis' in results[1].english_content['title']
                    assert 'Lazarus Group Campaign Analysis' in results[2].english_content['title']
    
    def test_multilang_query_with_rag_pipeline(self):
        """Test multi-language query processing with mock RAG pipeline"""
        with patch('src.rag.multilang_query_processor.get_config') as mock_config:
            mock_config.return_value.multi_language.auto_detect_query_language = True
            mock_config.return_value.multi_language.translate_response = True
            mock_config.return_value.multi_language.default_language = 'en'
            
            query_processor = MultiLanguageQueryProcessor()
            
            # Mock RAG pipeline
            def mock_rag_pipeline(english_query):
                response = f"Analysis of query: {english_query}"
                sources = [{'title': 'Threat Report 1', 'score': 0.85}]
                return response, sources
            
            # Test French query
            french_query = "Quelles sont les techniques utilisées par APT29?"
            
            with patch.object(query_processor.language_detector, 'detect_language') as mock_detect:
                mock_detect.return_value = LanguageDetectionResult('fr', 0.9, True, 'langdetect')
                
                with patch.object(query_processor.translator, 'translate_text') as mock_translate:
                    # Mock query translation
                    mock_translate.side_effect = [
                        TranslationResult(
                            french_query, 
                            "What techniques are used by APT29?", 
                            'fr', 'en', 0.9, 'google'
                        ),
                        TranslationResult(
                            "Analysis of query: What techniques are used by APT29?",
                            "Analyse de la requête: Quelles techniques sont utilisées par APT29?",
                            'en', 'fr', 0.9, 'google'
                        )
                    ]
                    
                    result = query_processor.process_query_response_cycle(
                        french_query, mock_rag_pipeline, 'fr'
                    )
                    
                    assert isinstance(result, MultiLangResponse)
                    assert result.query.original_language == 'fr'
                    assert 'What techniques are used by APT29?' in result.query.english_query
                    assert 'Analyse de la requête' in result.localized_response
                    assert result.response_language == 'fr'
                    assert len(result.sources) == 1