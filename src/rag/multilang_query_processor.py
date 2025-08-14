"""
Multi-language Query Processing for RAG Pipeline
Handles queries in multiple languages and provides localized responses
"""
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
import time

from config.settings import get_config
from ..processing.language_detector import LanguageDetector, LanguageDetectionResult
from ..processing.translator import TranslationService, TranslationResult

logger = logging.getLogger(__name__)


@dataclass
class MultiLangQuery:
    """Multi-language query container"""
    original_query: str
    original_language: str
    english_query: str
    confidence: float
    translation_needed: bool
    query_id: str = None
    timestamp: float = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()
        if self.query_id is None:
            self.query_id = f"query_{hash(self.original_query)}_{int(self.timestamp)}"


@dataclass
class MultiLangResponse:
    """Multi-language response container"""
    query: MultiLangQuery
    english_response: str
    localized_response: Optional[str]
    response_language: str
    sources: List[Dict[str, Any]]
    confidence: float
    response_id: str = None
    timestamp: float = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()
        if self.response_id is None:
            self.response_id = f"response_{self.query.query_id}_{int(self.timestamp)}"


class MultiLanguageQueryProcessor:
    """
    Processes queries in multiple languages for the RAG pipeline
    Handles language detection, translation, and response localization
    """
    
    def __init__(self, config=None):
        self.config = config or get_config()
        self.lang_config = self.config.multi_language
        
        # Initialize language services
        self.language_detector = LanguageDetector(self.config)
        self.translator = TranslationService(self.config)
        
        # Query processing statistics
        self.query_stats = {
            'total_queries': 0,
            'translated_queries': 0,
            'languages_processed': {},
            'average_processing_time': 0.0
        }
    
    def process_query(self, query: str, user_language: str = None) -> MultiLangQuery:
        """
        Process an incoming query for multi-language support
        
        Args:
            query: Raw query string
            user_language: Preferred user language (auto-detected if None)
            
        Returns:
            MultiLangQuery: Processed query with language metadata
        """
        start_time = time.time()
        
        if not query or not query.strip():
            raise ValueError("Empty query provided")
        
        query = query.strip()
        
        # Detect query language if not specified by user
        if user_language is None or not self.language_detector.is_supported_language(user_language):
            if self.lang_config.auto_detect_query_language:
                detection = self.language_detector.detect_language(query)
                detected_language = detection.language
                confidence = detection.confidence
            else:
                detected_language = self.lang_config.default_language
                confidence = 1.0
        else:
            detected_language = user_language
            confidence = 1.0
        
        # Update statistics
        self.query_stats['total_queries'] += 1
        lang_count = self.query_stats['languages_processed'].get(detected_language, 0)
        self.query_stats['languages_processed'][detected_language] = lang_count + 1
        
        # Translate query to English if needed
        translation_needed = detected_language != 'en'
        
        if translation_needed:
            try:
                translation_result = self.translator.translate_text(
                    query, 
                    source_lang=detected_language, 
                    target_lang='en'
                )
                english_query = translation_result.translated_text
                self.query_stats['translated_queries'] += 1
                
                logger.info(f"Translated query from {detected_language} to English")
                
            except Exception as e:
                logger.error(f"Query translation failed: {e}")
                # Fallback to original query
                english_query = query
                translation_needed = False
                confidence = 0.5  # Lower confidence due to translation failure
                
        else:
            english_query = query
        
        # Update processing time statistics
        processing_time = time.time() - start_time
        total_time = self.query_stats['average_processing_time'] * (self.query_stats['total_queries'] - 1)
        self.query_stats['average_processing_time'] = (total_time + processing_time) / self.query_stats['total_queries']
        
        return MultiLangQuery(
            original_query=query,
            original_language=detected_language,
            english_query=english_query,
            confidence=confidence,
            translation_needed=translation_needed
        )
    
    def localize_response(self, english_response: str, target_language: str, 
                         sources: List[Dict[str, Any]] = None) -> MultiLangResponse:
        """
        Localize English response to target language
        
        Args:
            english_response: Response text in English
            target_language: Target language for localization
            sources: Source documents used for the response
            
        Returns:
            MultiLangResponse: Localized response
        """
        if not english_response or not english_response.strip():
            raise ValueError("Empty response provided for localization")
        
        sources = sources or []
        
        # Create dummy query for response container
        dummy_query = MultiLangQuery(
            original_query="",
            original_language=target_language,
            english_query="",
            confidence=1.0,
            translation_needed=False
        )
        
        # Check if localization is needed
        if target_language == 'en' or not self.lang_config.translate_response:
            return MultiLangResponse(
                query=dummy_query,
                english_response=english_response,
                localized_response=english_response,
                response_language='en',
                sources=sources,
                confidence=1.0
            )
        
        # Translate response to target language
        try:
            translation_result = self.translator.translate_text(
                english_response,
                source_lang='en',
                target_lang=target_language
            )
            
            localized_response = translation_result.translated_text
            confidence = translation_result.confidence
            
            logger.info(f"Localized response to {target_language}")
            
        except Exception as e:
            logger.error(f"Response localization failed: {e}")
            # Fallback to English response
            localized_response = english_response
            confidence = 0.5
            target_language = 'en'
        
        return MultiLangResponse(
            query=dummy_query,
            english_response=english_response,
            localized_response=localized_response,
            response_language=target_language,
            sources=sources,
            confidence=confidence
        )
    
    def process_query_response_cycle(self, query: str, rag_pipeline_func, 
                                   user_language: str = None) -> MultiLangResponse:
        """
        Complete query-response cycle with multi-language support
        
        Args:
            query: User query
            rag_pipeline_func: Function that processes English queries and returns (response, sources)
            user_language: Preferred user language
            
        Returns:
            MultiLangResponse: Complete multi-language response
        """
        # Process the query
        processed_query = self.process_query(query, user_language)
        
        # Execute RAG pipeline with English query
        try:
            english_response, sources = rag_pipeline_func(processed_query.english_query)
        except Exception as e:
            logger.error(f"RAG pipeline execution failed: {e}")
            raise
        
        # Determine response language
        response_language = processed_query.original_language
        
        # Localize response if needed
        if response_language != 'en' and self.lang_config.translate_response:
            try:
                translation_result = self.translator.translate_text(
                    english_response,
                    source_lang='en',
                    target_lang=response_language
                )
                localized_response = translation_result.translated_text
                confidence = translation_result.confidence
                
            except Exception as e:
                logger.error(f"Response localization failed: {e}")
                localized_response = english_response
                response_language = 'en'
                confidence = 0.5
        else:
            localized_response = english_response
            confidence = 1.0
        
        return MultiLangResponse(
            query=processed_query,
            english_response=english_response,
            localized_response=localized_response,
            response_language=response_language,
            sources=sources,
            confidence=confidence
        )
    
    def enhance_sources_with_translation(self, sources: List[Dict[str, Any]], 
                                       target_language: str) -> List[Dict[str, Any]]:
        """
        Enhance source documents with translations if available
        
        Args:
            sources: List of source documents
            target_language: Target language for translations
            
        Returns:
            List[Dict[str, Any]]: Enhanced sources with translation metadata
        """
        enhanced_sources = []
        
        for source in sources:
            enhanced_source = source.copy()
            
            # Check if source has translation metadata
            if '_translation_metadata' in source:
                metadata = source['_translation_metadata']
                translations = metadata.get('translations', {})
                
                # Add translation information for relevant fields
                enhanced_source['_multilang_info'] = {
                    'original_language': None,
                    'available_translations': list(translations.keys()),
                    'translation_service': metadata.get('service_used'),
                    'translation_timestamp': metadata.get('timestamp')
                }
                
                # Try to determine original language from translations
                for field, trans_data in translations.items():
                    if 'source_language' in trans_data:
                        enhanced_source['_multilang_info']['original_language'] = trans_data['source_language']
                        break
            
            enhanced_sources.append(enhanced_source)
        
        return enhanced_sources
    
    def get_supported_languages(self) -> Dict[str, str]:
        """
        Get supported languages with human-readable names
        
        Returns:
            Dict[str, str]: Language code to name mapping
        """
        return {
            lang: self.language_detector.get_language_name(lang) 
            for lang in self.lang_config.supported_languages
        }
    
    def get_query_statistics(self) -> Dict[str, Any]:
        """Get query processing statistics"""
        return {
            'total_queries_processed': self.query_stats['total_queries'],
            'queries_requiring_translation': self.query_stats['translated_queries'],
            'language_distribution': dict(sorted(
                self.query_stats['languages_processed'].items(),
                key=lambda x: x[1], reverse=True
            )),
            'average_processing_time_seconds': self.query_stats['average_processing_time'],
            'translation_rate': (
                self.query_stats['translated_queries'] / self.query_stats['total_queries'] * 100
                if self.query_stats['total_queries'] > 0 else 0
            )
        }
    
    def reset_statistics(self):
        """Reset query processing statistics"""
        self.query_stats = {
            'total_queries': 0,
            'translated_queries': 0,
            'languages_processed': {},
            'average_processing_time': 0.0
        }
    
    def create_conversation_context(self, conversation_history: List[Dict[str, str]], 
                                  user_language: str = None) -> str:
        """
        Create conversation context from multi-language history
        
        Args:
            conversation_history: List of {'role': 'user'/'assistant', 'content': '...', 'language': '...'}
            user_language: Preferred language for context
            
        Returns:
            str: Formatted conversation context
        """
        if not conversation_history:
            return ""
        
        context_parts = []
        
        for turn in conversation_history[-5:]:  # Last 5 turns
            role = turn.get('role', 'unknown')
            content = turn.get('content', '')
            language = turn.get('language', 'unknown')
            
            if not content:
                continue
            
            # Translate to English for context if needed
            if language != 'en' and language != 'unknown':
                try:
                    translation_result = self.translator.translate_text(
                        content, source_lang=language, target_lang='en'
                    )
                    content = translation_result.translated_text
                except Exception as e:
                    logger.warning(f"Failed to translate conversation context: {e}")
            
            context_parts.append(f"{role.title()}: {content}")
        
        return "\n".join(context_parts)
    
    def validate_language_support(self, language_code: str) -> Tuple[bool, str]:
        """
        Validate if a language is supported
        
        Args:
            language_code: Language code to validate
            
        Returns:
            Tuple[bool, str]: (is_supported, message)
        """
        if not language_code:
            return False, "Empty language code provided"
        
        if language_code not in self.lang_config.supported_languages:
            supported = ", ".join(self.lang_config.supported_languages)
            return False, f"Language '{language_code}' not supported. Supported languages: {supported}"
        
        return True, f"Language '{language_code}' is supported"