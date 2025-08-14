"""
Multi-language CTI Ingestion Pipeline
Processes threat intelligence documents in multiple languages
"""
import logging
import json
from typing import Dict, List, Optional, Any, Iterator
from pathlib import Path
from dataclasses import dataclass, asdict
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

from config.settings import get_config
from ..processing.language_detector import LanguageDetector, LanguageDetectionResult
from ..processing.translator import TranslationService, TranslationResult

logger = logging.getLogger(__name__)


@dataclass
class MultiLangDocument:
    """Multi-language CTI document container"""
    document_id: str
    source: str
    original_language: str
    confidence: float
    english_content: Dict[str, Any]
    original_content: Optional[Dict[str, Any]] = None
    translation_metadata: Optional[Dict] = None
    processing_timestamp: float = None
    
    def __post_init__(self):
        if self.processing_timestamp is None:
            self.processing_timestamp = time.time()


@dataclass
class ProcessingStats:
    """Statistics from multi-language processing"""
    total_documents: int = 0
    translated_documents: int = 0
    skipped_documents: int = 0
    failed_documents: int = 0
    languages_detected: Dict[str, int] = None
    processing_time: float = 0.0
    
    def __post_init__(self):
        if self.languages_detected is None:
            self.languages_detected = {}


class MultiLanguageProcessor:
    """
    Processes CTI documents in multiple languages
    Detects language, translates content, and prepares for RAG pipeline
    """
    
    def __init__(self, config=None):
        self.config = config or get_config()
        self.lang_config = self.config.multi_language
        
        # Initialize services
        self.language_detector = LanguageDetector(self.config)
        self.translator = TranslationService(self.config)
        
        # Processing statistics
        self.stats = ProcessingStats()
        
    def process_document(self, document: Dict[str, Any], source: str = "unknown") -> MultiLangDocument:
        """
        Process a single CTI document for multi-language support
        
        Args:
            document: Raw CTI document
            source: Source identifier for the document
            
        Returns:
            MultiLangDocument: Processed document with language metadata
        """
        start_time = time.time()
        
        # Generate document ID if not present
        doc_id = document.get('id') or document.get('_id') or f"{source}_{hash(str(document))}"
        
        # Extract text content for language detection
        text_content = self._extract_text_content(document)
        
        if not text_content:
            logger.warning(f"No text content found in document {doc_id}")
            return self._create_fallback_document(doc_id, document, source)
        
        # Detect language
        detection_result = self.language_detector.detect_language(text_content)
        
        # Update language statistics
        lang = detection_result.language
        self.stats.languages_detected[lang] = self.stats.languages_detected.get(lang, 0) + 1
        
        # Process based on detected language
        if detection_result.language == 'en' and detection_result.is_reliable:
            # Already in English, no translation needed
            processed_doc = MultiLangDocument(
                document_id=doc_id,
                source=source,
                original_language='en',
                confidence=detection_result.confidence,
                english_content=document,
                original_content=document if self.lang_config.preserve_original else None
            )
            self.stats.skipped_documents += 1
            
        else:
            # Translate document to English
            try:
                if self.lang_config.translate_to_english:
                    translated_doc = self.translator.translate_cti_document(document)
                    
                    processed_doc = MultiLangDocument(
                        document_id=doc_id,
                        source=source,
                        original_language=detection_result.language,
                        confidence=detection_result.confidence,
                        english_content=translated_doc,
                        original_content=document if self.lang_config.preserve_original else None,
                        translation_metadata=translated_doc.get('_translation_metadata')
                    )
                    
                    self.stats.translated_documents += 1
                else:
                    # Keep original without translation
                    processed_doc = MultiLangDocument(
                        document_id=doc_id,
                        source=source,
                        original_language=detection_result.language,
                        confidence=detection_result.confidence,
                        english_content=document,  # Keep original as "english" content
                        original_content=document if self.lang_config.preserve_original else None
                    )
                    self.stats.skipped_documents += 1
                    
            except Exception as e:
                logger.error(f"Translation failed for document {doc_id}: {e}")
                processed_doc = self._create_fallback_document(doc_id, document, source, detection_result)
                self.stats.failed_documents += 1
        
        self.stats.total_documents += 1
        self.stats.processing_time += time.time() - start_time
        
        return processed_doc
    
    def process_batch(self, documents: List[Dict[str, Any]], source: str = "batch", 
                     max_workers: int = 4) -> List[MultiLangDocument]:
        """
        Process multiple documents in parallel
        
        Args:
            documents: List of raw CTI documents
            source: Source identifier for the batch
            max_workers: Maximum number of worker threads
            
        Returns:
            List[MultiLangDocument]: Processed documents
        """
        logger.info(f"Processing batch of {len(documents)} documents with {max_workers} workers")
        
        results = []
        
        # Process documents in parallel
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all documents for processing
            future_to_doc = {
                executor.submit(self.process_document, doc, f"{source}_{i}"): i 
                for i, doc in enumerate(documents)
            }
            
            # Collect results as they complete
            for future in as_completed(future_to_doc):
                doc_idx = future_to_doc[future]
                try:
                    result = future.result()
                    results.append((doc_idx, result))
                except Exception as e:
                    logger.error(f"Failed to process document {doc_idx}: {e}")
                    # Create fallback document
                    fallback = self._create_fallback_document(
                        f"{source}_{doc_idx}", 
                        documents[doc_idx], 
                        source
                    )
                    results.append((doc_idx, fallback))
                    self.stats.failed_documents += 1
        
        # Sort results by original order
        results.sort(key=lambda x: x[0])
        return [result[1] for result in results]
    
    def process_file(self, file_path: Path, source: str = None) -> List[MultiLangDocument]:
        """
        Process CTI documents from a file
        
        Args:
            file_path: Path to the CTI file
            source: Source identifier (uses filename if not provided)
            
        Returns:
            List[MultiLangDocument]: Processed documents
        """
        if source is None:
            source = file_path.stem
        
        logger.info(f"Processing file: {file_path}")
        
        try:
            # Load documents from file
            with open(file_path, 'r', encoding='utf-8') as f:
                if file_path.suffix.lower() == '.json':
                    data = json.load(f)
                    
                    # Handle different JSON structures
                    if isinstance(data, list):
                        documents = data
                    elif isinstance(data, dict):
                        # Check for common CTI bundle structures
                        if 'objects' in data:  # STIX bundle
                            documents = data['objects']
                        elif 'data' in data:  # Generic data wrapper
                            documents = data['data']
                        else:
                            documents = [data]  # Single document
                    else:
                        raise ValueError(f"Unsupported JSON structure in {file_path}")
                        
                else:
                    raise ValueError(f"Unsupported file format: {file_path.suffix}")
            
            logger.info(f"Loaded {len(documents)} documents from {file_path}")
            
            # Process documents
            return self.process_batch(documents, source)
            
        except Exception as e:
            logger.error(f"Failed to process file {file_path}: {e}")
            raise
    
    def process_directory(self, dir_path: Path, pattern: str = "*.json", 
                         recursive: bool = True) -> List[MultiLangDocument]:
        """
        Process all CTI files in a directory
        
        Args:
            dir_path: Directory containing CTI files
            pattern: File pattern to match
            recursive: Whether to search recursively
            
        Returns:
            List[MultiLangDocument]: All processed documents
        """
        logger.info(f"Processing directory: {dir_path} (pattern: {pattern}, recursive: {recursive})")
        
        if recursive:
            files = list(dir_path.rglob(pattern))
        else:
            files = list(dir_path.glob(pattern))
        
        if not files:
            logger.warning(f"No files matching {pattern} found in {dir_path}")
            return []
        
        logger.info(f"Found {len(files)} files to process")
        
        all_documents = []
        
        for file_path in files:
            try:
                documents = self.process_file(file_path)
                all_documents.extend(documents)
                logger.info(f"Processed {len(documents)} documents from {file_path}")
            except Exception as e:
                logger.error(f"Failed to process file {file_path}: {e}")
                continue
        
        logger.info(f"Processed {len(all_documents)} total documents from {len(files)} files")
        return all_documents
    
    def _extract_text_content(self, document: Dict[str, Any]) -> str:
        """Extract text content from document for language detection"""
        
        # Common fields that contain text content in CTI documents
        text_fields = [
            'description', 'summary', 'content', 'text', 'title', 'name',
            'details', 'analysis', 'comments', 'notes', 'pattern'
        ]
        
        text_parts = []
        
        for field in text_fields:
            if field in document:
                value = document[field]
                if isinstance(value, str) and value.strip():
                    text_parts.append(value.strip())
                elif isinstance(value, list):
                    # Handle lists of strings
                    for item in value:
                        if isinstance(item, str) and item.strip():
                            text_parts.append(item.strip())
        
        # Also check nested objects (common in STIX)
        if isinstance(document, dict):
            for key, value in document.items():
                if isinstance(value, dict):
                    # Recursively extract from nested objects
                    nested_text = self._extract_text_content(value)
                    if nested_text:
                        text_parts.append(nested_text)
        
        return ' '.join(text_parts)
    
    def _create_fallback_document(self, doc_id: str, document: Dict[str, Any], 
                                source: str, detection: LanguageDetectionResult = None) -> MultiLangDocument:
        """Create a fallback document when processing fails"""
        
        if detection is None:
            detection = LanguageDetectionResult(
                language=self.lang_config.default_language,
                confidence=0.0,
                is_reliable=False,
                detector_used="fallback"
            )
        
        return MultiLangDocument(
            document_id=doc_id,
            source=source,
            original_language=detection.language,
            confidence=detection.confidence,
            english_content=document,
            original_content=document if self.lang_config.preserve_original else None
        )
    
    def get_processing_stats(self) -> ProcessingStats:
        """Get current processing statistics"""
        return self.stats
    
    def reset_stats(self):
        """Reset processing statistics"""
        self.stats = ProcessingStats()
    
    def save_processed_documents(self, documents: List[MultiLangDocument], 
                               output_path: Path, format: str = 'json'):
        """
        Save processed documents to file
        
        Args:
            documents: Processed documents to save
            output_path: Output file path
            format: Output format ('json' or 'jsonl')
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        if format.lower() == 'json':
            # Save as single JSON array
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump([asdict(doc) for doc in documents], f, 
                         ensure_ascii=False, indent=2)
        
        elif format.lower() == 'jsonl':
            # Save as JSON Lines
            with open(output_path, 'w', encoding='utf-8') as f:
                for doc in documents:
                    json.dump(asdict(doc), f, ensure_ascii=False)
                    f.write('\n')
        
        else:
            raise ValueError(f"Unsupported format: {format}")
        
        logger.info(f"Saved {len(documents)} processed documents to {output_path}")
    
    def generate_language_report(self) -> Dict[str, Any]:
        """Generate a report of language processing statistics"""
        
        total_docs = self.stats.total_documents
        if total_docs == 0:
            return {"message": "No documents processed"}
        
        return {
            "summary": {
                "total_documents": total_docs,
                "translated_documents": self.stats.translated_documents,
                "skipped_documents": self.stats.skipped_documents,
                "failed_documents": self.stats.failed_documents,
                "success_rate": (total_docs - self.stats.failed_documents) / total_docs * 100,
                "translation_rate": self.stats.translated_documents / total_docs * 100
            },
            "language_distribution": dict(sorted(
                self.stats.languages_detected.items(),
                key=lambda x: x[1], reverse=True
            )),
            "performance": {
                "total_processing_time": self.stats.processing_time,
                "average_time_per_document": self.stats.processing_time / total_docs if total_docs > 0 else 0
            },
            "configuration": {
                "translate_to_english": self.lang_config.translate_to_english,
                "preserve_original": self.lang_config.preserve_original,
                "translation_service": self.lang_config.translation_service,
                "supported_languages": self.lang_config.supported_languages
            }
        }