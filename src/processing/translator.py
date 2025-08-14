"""
Translation Service for Multi-language CTI Processing
"""
import logging
import hashlib
import json
import time
from typing import Dict, Optional, List, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
from abc import ABC, abstractmethod

# Translation libraries
from deep_translator import GoogleTranslator as DeepGoogleTranslator, MicrosoftTranslator
from translate import Translator as BasicTranslator
from textblob import TextBlob

from config.settings import get_config
from .language_detector import LanguageDetector, LanguageDetectionResult

logger = logging.getLogger(__name__)


@dataclass
class TranslationResult:
    """Result of translation operation"""
    original_text: str
    translated_text: str
    source_language: str
    target_language: str
    confidence: float
    translation_service: str
    cached: bool = False
    timestamp: float = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()


class TranslationCache:
    """Simple file-based cache for translations"""
    
    def __init__(self, cache_dir: Path, expiry_hours: int = 168):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.expiry_seconds = expiry_hours * 3600
        self.cache_file = self.cache_dir / "translation_cache.json"
        self._load_cache()
    
    def _load_cache(self):
        """Load cache from disk"""
        try:
            if self.cache_file.exists():
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    self.cache = json.load(f)
            else:
                self.cache = {}
        except Exception as e:
            logger.error(f"Error loading translation cache: {e}")
            self.cache = {}
    
    def _save_cache(self):
        """Save cache to disk"""
        try:
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.cache, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Error saving translation cache: {e}")
    
    def _generate_key(self, text: str, source_lang: str, target_lang: str, service: str) -> str:
        """Generate cache key for translation"""
        key_data = f"{text}|{source_lang}|{target_lang}|{service}"
        return hashlib.md5(key_data.encode('utf-8')).hexdigest()
    
    def get(self, text: str, source_lang: str, target_lang: str, service: str) -> Optional[TranslationResult]:
        """Get translation from cache if available and not expired"""
        key = self._generate_key(text, source_lang, target_lang, service)
        
        if key not in self.cache:
            return None
        
        cached_data = self.cache[key]
        
        # Check expiry
        if time.time() - cached_data['timestamp'] > self.expiry_seconds:
            del self.cache[key]
            return None
        
        # Return cached result
        result = TranslationResult(**cached_data)
        result.cached = True
        return result
    
    def set(self, result: TranslationResult):
        """Store translation result in cache"""
        key = self._generate_key(
            result.original_text, 
            result.source_language, 
            result.target_language, 
            result.translation_service
        )
        
        self.cache[key] = asdict(result)
        self._save_cache()
    
    def cleanup_expired(self):
        """Remove expired entries from cache"""
        current_time = time.time()
        expired_keys = [
            key for key, data in self.cache.items()
            if current_time - data['timestamp'] > self.expiry_seconds
        ]
        
        for key in expired_keys:
            del self.cache[key]
        
        if expired_keys:
            self._save_cache()
            logger.info(f"Cleaned up {len(expired_keys)} expired cache entries")


class BaseTranslator(ABC):
    """Base class for translation services"""
    
    @abstractmethod
    def translate(self, text: str, source_lang: str, target_lang: str) -> TranslationResult:
        pass
    
    @abstractmethod
    def get_supported_languages(self) -> List[str]:
        pass


class BasicTranslationService(BaseTranslator):
    """Basic translation service using translate library"""
    
    def __init__(self):
        self.service_name = "basic_translate"
    
    def translate(self, text: str, source_lang: str = 'auto', target_lang: str = 'en') -> TranslationResult:
        """Translate text using basic translate library"""
        try:
            # Handle auto-detection with TextBlob
            if source_lang == 'auto':
                try:
                    blob = TextBlob(text)
                    source_lang = blob.detect_language()
                    confidence = 0.8  # Basic confidence since TextBlob doesn't provide it
                except:
                    source_lang = 'en'
                    confidence = 0.5
            else:
                confidence = 1.0
            
            # Skip translation if same language
            if source_lang == target_lang:
                return TranslationResult(
                    original_text=text,
                    translated_text=text,
                    source_language=source_lang,
                    target_language=target_lang,
                    confidence=confidence,
                    translation_service=self.service_name
                )
            
            # Perform translation using translate library
            translator = BasicTranslator(from_lang=source_lang, to_lang=target_lang)
            translated_text = translator.translate(text)
            
            return TranslationResult(
                original_text=text,
                translated_text=translated_text,
                source_language=source_lang,
                target_language=target_lang,
                confidence=confidence,
                translation_service=self.service_name
            )
            
        except Exception as e:
            logger.error(f"Basic translation failed: {e}")
            raise
    
    def get_supported_languages(self) -> List[str]:
        """Get list of supported language codes"""
        return ['en', 'fr', 'de', 'es', 'it', 'pt', 'ru', 'zh', 'ja', 'ar', 'auto']


class DeepTranslatorService(BaseTranslator):
    """Deep Translator service wrapper (using Google backend)"""
    
    def __init__(self):
        self.service_name = "deep_translator"
    
    def translate(self, text: str, source_lang: str = 'auto', target_lang: str = 'en') -> TranslationResult:
        """Translate text using Deep Translator"""
        try:
            translator = DeepGoogleTranslator(source=source_lang, target=target_lang)
            translated_text = translator.translate(text)
            
            return TranslationResult(
                original_text=text,
                translated_text=translated_text,
                source_language=source_lang,
                target_language=target_lang,
                confidence=0.9,  # Deep Translator doesn't provide confidence
                translation_service=self.service_name
            )
            
        except Exception as e:
            logger.error(f"Deep Translator failed: {e}")
            raise
    
    def get_supported_languages(self) -> List[str]:
        """Get list of supported language codes"""
        return ['en', 'fr', 'de', 'es', 'it', 'pt', 'ru', 'zh', 'ja', 'ar', 'auto']


class TranslationService:
    """
    Multi-service translation manager for CTI content
    Provides translation with caching, fallback, and language detection
    """
    
    def __init__(self, config=None):
        self.config = config or get_config()
        self.lang_config = self.config.multi_language
        
        # Initialize language detector
        self.language_detector = LanguageDetector(config)
        
        # Initialize cache if enabled
        self.cache = None
        if self.lang_config.enable_translation_cache:
            cache_dir = self.config.data_dir / "cache" / "translations"
            self.cache = TranslationCache(cache_dir, self.lang_config.cache_expiry_hours)
        
        # Initialize translation services
        self.services = {
            'basic_translate': BasicTranslationService(),
            'deep_translator': DeepTranslatorService()
        }
        
        self.primary_service = self.lang_config.translation_service
        if self.primary_service not in self.services:
            logger.warning(f"Unknown translation service: {self.primary_service}, using basic_translate")
            self.primary_service = 'basic_translate'
    
    def translate_text(self, text: str, source_lang: str = None, target_lang: str = 'en') -> TranslationResult:
        """
        Translate text with language detection and caching
        
        Args:
            text: Text to translate
            source_lang: Source language (auto-detected if None)
            target_lang: Target language code
            
        Returns:
            TranslationResult: Translation result
        """
        if not text or not text.strip():
            raise ValueError("Empty text provided for translation")
        
        # Auto-detect source language if not provided
        if source_lang is None:
            detection = self.language_detector.detect_language(text)
            source_lang = detection.language
            
            # Skip translation if already in target language
            if source_lang == target_lang:
                return TranslationResult(
                    original_text=text,
                    translated_text=text,
                    source_language=source_lang,
                    target_language=target_lang,
                    confidence=detection.confidence,
                    translation_service="no_translation_needed"
                )
        
        # Check cache first
        if self.cache:
            cached_result = self.cache.get(text, source_lang, target_lang, self.primary_service)
            if cached_result:
                logger.debug(f"Using cached translation for {len(text)} chars")
                return cached_result
        
        # Perform translation
        result = self._translate_with_fallback(text, source_lang, target_lang)
        
        # Cache result if successful
        if self.cache and result:
            self.cache.set(result)
        
        return result
    
    def _translate_with_fallback(self, text: str, source_lang: str, target_lang: str) -> TranslationResult:
        """Translate with fallback to alternative services"""
        
        # Try primary service first
        try:
            service = self.services[self.primary_service]
            result = service.translate(text, source_lang, target_lang)
            logger.debug(f"Translation successful using {self.primary_service}")
            return result
        except Exception as e:
            logger.warning(f"Primary service {self.primary_service} failed: {e}")
        
        # Try fallback services
        for service_name, service in self.services.items():
            if service_name == self.primary_service:
                continue  # Already tried
            
            try:
                result = service.translate(text, source_lang, target_lang)
                logger.info(f"Translation successful using fallback service {service_name}")
                return result
            except Exception as e:
                logger.warning(f"Fallback service {service_name} failed: {e}")
        
        # All services failed
        logger.error("All translation services failed")
        raise RuntimeError("Translation failed with all available services")
    
    def translate_cti_document(self, document: Dict) -> Dict:
        """
        Translate a CTI document while preserving structure
        
        Args:
            document: CTI document dictionary
            
        Returns:
            Dict: Translated document with original preserved if configured
        """
        if not isinstance(document, dict):
            raise ValueError("Document must be a dictionary")
        
        translated_doc = document.copy()
        
        # Fields commonly found in CTI documents that need translation
        translatable_fields = [
            'title', 'description', 'summary', 'content', 'text',
            'name', 'details', 'analysis', 'comments', 'notes'
        ]
        
        translations = {}
        
        for field in translatable_fields:
            if field in document and isinstance(document[field], str):
                original_text = document[field]
                
                if not original_text.strip():
                    continue
                
                try:
                    result = self.translate_text(original_text, target_lang='en')
                    
                    # Update the field with translated text
                    translated_doc[field] = result.translated_text
                    
                    # Store translation metadata
                    if self.lang_config.preserve_original:
                        translations[field] = {
                            'original': result.original_text,
                            'translated': result.translated_text,
                            'source_language': result.source_language,
                            'confidence': result.confidence,
                            'service': result.translation_service
                        }
                
                except Exception as e:
                    logger.error(f"Failed to translate field '{field}': {e}")
                    # Keep original text if translation fails
                    translated_doc[field] = original_text
        
        # Add translation metadata if preserving originals
        if self.lang_config.preserve_original and translations:
            translated_doc['_translation_metadata'] = {
                'translations': translations,
                'timestamp': time.time(),
                'service_used': self.primary_service
            }
        
        return translated_doc
    
    def batch_translate(self, texts: List[str], source_lang: str = None, target_lang: str = 'en') -> List[TranslationResult]:
        """
        Translate multiple texts
        
        Args:
            texts: List of texts to translate
            source_lang: Source language (auto-detected if None)
            target_lang: Target language code
            
        Returns:
            List[TranslationResult]: Translation results
        """
        results = []
        
        for text in texts:
            try:
                result = self.translate_text(text, source_lang, target_lang)
                results.append(result)
            except Exception as e:
                logger.error(f"Failed to translate text: {e}")
                # Add error result
                results.append(TranslationResult(
                    original_text=text,
                    translated_text=text,  # Keep original on error
                    source_language=source_lang or 'unknown',
                    target_language=target_lang,
                    confidence=0.0,
                    translation_service="error"
                ))
        
        return results
    
    def get_supported_languages(self) -> List[str]:
        """Get supported languages from primary service"""
        return self.services[self.primary_service].get_supported_languages()
    
    def cleanup_cache(self):
        """Clean up expired cache entries"""
        if self.cache:
            self.cache.cleanup_expired()