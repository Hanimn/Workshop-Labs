"""
Language Detection Service for Multi-language CTI Processing
"""
import logging
from typing import Dict, Optional, Tuple, List
from dataclasses import dataclass
from langdetect import detect, detect_langs, LangDetectException
try:
    import pycld2 as cld2
    CLD2_AVAILABLE = True
except ImportError:
    CLD2_AVAILABLE = False
    cld2 = None
from config.settings import get_config

logger = logging.getLogger(__name__)


@dataclass
class LanguageDetectionResult:
    """Result of language detection"""
    language: str
    confidence: float
    is_reliable: bool
    detector_used: str
    alternatives: List[Tuple[str, float]] = None


class LanguageDetector:
    """
    Multi-language detection service with fallback mechanisms
    Supports multiple detection libraries for improved accuracy
    """
    
    def __init__(self, config=None):
        self.config = config or get_config()
        self.lang_config = self.config.multi_language
        
        # Supported language codes mapping
        self.language_names = {
            'en': 'English',
            'fr': 'French', 
            'de': 'German',
            'es': 'Spanish',
            'it': 'Italian',
            'pt': 'Portuguese',
            'ru': 'Russian',
            'zh': 'Chinese',
            'ja': 'Japanese',
            'ar': 'Arabic'
        }
        
    def detect_language(self, text: str, min_chars: int = 20) -> LanguageDetectionResult:
        """
        Detect language of input text using multiple detection methods
        
        Args:
            text: Input text to analyze
            min_chars: Minimum characters required for reliable detection
            
        Returns:
            LanguageDetectionResult: Detection result with confidence
        """
        if not text or len(text.strip()) < min_chars:
            logger.warning(f"Text too short for reliable detection: {len(text)} chars")
            return LanguageDetectionResult(
                language=self.lang_config.default_language,
                confidence=0.0,
                is_reliable=False,
                detector_used="default"
            )
        
        # Try langdetect first (Google's language detection library port)
        langdetect_result = self._detect_with_langdetect(text)
        if langdetect_result and langdetect_result.confidence >= self.lang_config.min_confidence_threshold:
            return langdetect_result
            
        # Fallback to CLD2 (Compact Language Detector 2)
        cld2_result = self._detect_with_cld2(text)
        if cld2_result and cld2_result.confidence >= self.lang_config.min_confidence_threshold:
            return cld2_result
            
        # If both fail or low confidence, use best available result
        best_result = langdetect_result or cld2_result
        if best_result:
            best_result.is_reliable = False
            return best_result
            
        # Final fallback to default language
        logger.warning(f"Could not detect language reliably, using default: {self.lang_config.default_language}")
        return LanguageDetectionResult(
            language=self.lang_config.default_language,
            confidence=0.0,
            is_reliable=False,
            detector_used="default"
        )
    
    def _detect_with_langdetect(self, text: str) -> Optional[LanguageDetectionResult]:
        """Detect language using langdetect library"""
        try:
            # Get primary detection
            detected_lang = detect(text)
            
            # Get probabilities for all languages
            lang_probs = detect_langs(text)
            primary_prob = next((lp for lp in lang_probs if lp.lang == detected_lang), None)
            
            if primary_prob is None:
                return None
                
            # Check if language is supported
            if detected_lang not in self.lang_config.supported_languages:
                logger.warning(f"Detected unsupported language: {detected_lang}")
                detected_lang = self.lang_config.default_language
                
            alternatives = [(lp.lang, lp.prob) for lp in lang_probs if lp.lang != detected_lang][:3]
            
            return LanguageDetectionResult(
                language=detected_lang,
                confidence=primary_prob.prob,
                is_reliable=primary_prob.prob >= self.lang_config.min_confidence_threshold,
                detector_used="langdetect",
                alternatives=alternatives
            )
            
        except LangDetectException as e:
            logger.warning(f"Langdetect failed: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error in langdetect: {e}")
            return None
    
    def _detect_with_cld2(self, text: str) -> Optional[LanguageDetectionResult]:
        """Detect language using CLD2 library"""
        if not CLD2_AVAILABLE:
            return None
            
        try:
            is_reliable, text_bytes_found, details = cld2.detect(text)
            
            if not details:
                return None
                
            # CLD2 returns (language_name, language_code, confidence, bytes_found)
            primary_detection = details[0]
            detected_lang = primary_detection[1]  # language_code
            confidence = primary_detection[2] / 100.0  # Convert percentage to decimal
            
            # Check if language is supported
            if detected_lang not in self.lang_config.supported_languages:
                logger.warning(f"CLD2 detected unsupported language: {detected_lang}")
                detected_lang = self.lang_config.default_language
                
            alternatives = [(det[1], det[2]/100.0) for det in details[1:4] if det[1] != detected_lang]
            
            return LanguageDetectionResult(
                language=detected_lang,
                confidence=confidence,
                is_reliable=is_reliable and confidence >= self.lang_config.min_confidence_threshold,
                detector_used="cld2",
                alternatives=alternatives
            )
            
        except Exception as e:
            logger.error(f"CLD2 detection failed: {e}")
            return None
    
    def is_supported_language(self, language_code: str) -> bool:
        """Check if language is supported"""
        return language_code in self.lang_config.supported_languages
    
    def get_language_name(self, language_code: str) -> str:
        """Get human-readable language name"""
        return self.language_names.get(language_code, language_code.upper())
    
    def batch_detect(self, texts: List[str]) -> List[LanguageDetectionResult]:
        """
        Detect languages for multiple texts
        
        Args:
            texts: List of text strings to analyze
            
        Returns:
            List[LanguageDetectionResult]: Detection results for each text
        """
        results = []
        for text in texts:
            try:
                result = self.detect_language(text)
                results.append(result)
            except Exception as e:
                logger.error(f"Error detecting language for text: {e}")
                results.append(LanguageDetectionResult(
                    language=self.lang_config.default_language,
                    confidence=0.0,
                    is_reliable=False,
                    detector_used="error_fallback"
                ))
        
        return results
    
    def get_language_stats(self, texts: List[str]) -> Dict[str, int]:
        """
        Get language distribution statistics for a collection of texts
        
        Args:
            texts: List of text strings to analyze
            
        Returns:
            Dict[str, int]: Language code to count mapping
        """
        results = self.batch_detect(texts)
        stats = {}
        
        for result in results:
            lang = result.language
            stats[lang] = stats.get(lang, 0) + 1
            
        return dict(sorted(stats.items(), key=lambda x: x[1], reverse=True))