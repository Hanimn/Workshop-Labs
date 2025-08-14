"""
Configuration management for RAG CTI Pipeline
"""
import os
from pathlib import Path
from typing import Optional, Dict, Any
from dotenv import load_dotenv
import yaml
try:
    from pydantic_settings import BaseSettings
except ImportError:
    from pydantic import BaseSettings
from pydantic import Field


# Load environment variables from .env file
load_dotenv()


class DatabaseConfig(BaseSettings):
    """ChromaDB configuration"""
    chroma_persist_directory: str = Field(default="./data/embeddings/chroma_db")
    collection_name: str = Field(default="cti_documents")
    embedding_model: str = Field(default="all-MiniLM-L6-v2")
    
    class Config:
        env_prefix = "DB_"


class LLMConfig(BaseSettings):
    """Large Language Model configuration"""
    # Ollama configuration
    ollama_base_url: str = Field(default="http://localhost:11434")
    model_name: str = Field(default="gpt-oss:120b")
    max_tokens: int = Field(default=4096)
    temperature: float = Field(default=0.1)
    
    # Legacy Anthropic support
    anthropic_api_key: Optional[str] = Field(default=None)
    
    class Config:
        env_prefix = "LLM_"


class RAGConfig(BaseSettings):
    """RAG Pipeline configuration"""
    retrieval_top_k: int = Field(default=10)
    chunk_size: int = Field(default=1000)
    chunk_overlap: int = Field(default=200)
    similarity_threshold: float = Field(default=0.7)
    
    class Config:
        env_prefix = "RAG_"


class DataSourceConfig(BaseSettings):
    """Data source configuration"""
    mitre_attack_url: str = Field(default="https://raw.githubusercontent.com/mitre/cti/master/enterprise-attack/enterprise-attack.json")
    cve_api_url: str = Field(default="https://services.nvd.nist.gov/rest/json/cves/2.0")
    taxii_server_url: Optional[str] = Field(default=None)
    taxii_username: Optional[str] = Field(default=None)
    taxii_password: Optional[str] = Field(default=None)
    
    class Config:
        env_prefix = "DATA_"


class MultiLanguageConfig(BaseSettings):
    """Multi-language processing configuration"""
    # Language detection settings
    default_language: str = Field(default="en")
    supported_languages: list = Field(default=["en", "fr", "de", "es", "it", "pt", "ru", "zh", "ja", "ar"])
    min_confidence_threshold: float = Field(default=0.8)
    
    # Translation settings
    translation_service: str = Field(default="basic_translate")  # basic_translate, deep_translator
    translate_to_english: bool = Field(default=True)
    preserve_original: bool = Field(default=True)
    
    # Query processing
    auto_detect_query_language: bool = Field(default=True)
    translate_response: bool = Field(default=True)
    
    # Cache settings
    enable_translation_cache: bool = Field(default=True)
    cache_expiry_hours: int = Field(default=168)  # 1 week
    
    class Config:
        env_prefix = "LANG_"


class AppConfig(BaseSettings):
    """Main application configuration"""
    project_root: Path = Field(default=Path(__file__).parent.parent)
    data_dir: Path = Field(default=Path(__file__).parent.parent / "data")
    log_level: str = Field(default="INFO")
    debug: bool = Field(default=False)
    
    # Sub-configurations
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    llm: LLMConfig = Field(default_factory=LLMConfig)
    rag: RAGConfig = Field(default_factory=RAGConfig)
    data_sources: DataSourceConfig = Field(default_factory=DataSourceConfig)
    multi_language: MultiLanguageConfig = Field(default_factory=MultiLanguageConfig)
    
    class Config:
        env_prefix = "APP_"
        case_sensitive = False


def load_config(config_file: Optional[str] = None) -> AppConfig:
    """
    Load configuration from environment variables and optional YAML file
    
    Args:
        config_file: Optional YAML configuration file path
        
    Returns:
        AppConfig: Application configuration object
    """
    if config_file and Path(config_file).exists():
        with open(config_file, 'r') as f:
            config_data = yaml.safe_load(f)
        
        # Override environment variables with YAML values
        for key, value in config_data.items():
            if isinstance(value, dict):
                for sub_key, sub_value in value.items():
                    env_key = f"{key.upper()}_{sub_key.upper()}"
                    os.environ[env_key] = str(sub_value)
            else:
                os.environ[key.upper()] = str(value)
    
    return AppConfig()


def get_config() -> AppConfig:
    """Get the global configuration instance"""
    return load_config()


# Global configuration instance
config = get_config()