"""
Application configuration using Pydantic settings
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List, Optional
from datetime import datetime
import secrets


class Settings(BaseSettings):
    """Application settings"""
    
    # Application
    APP_NAME: str = "DataInsights AI"
    VERSION: str = "1.0.0"
    DEBUG: bool = False
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # Security
    SECRET_KEY: str = secrets.token_urlsafe(32)
    JWT_SECRET_KEY: str = secrets.token_urlsafe(32)
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # CORS
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:8000",
        "http://127.0.0.1:3000"
    ]
    
    # OpenAI Configuration
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-4-turbo-preview"
    OPENAI_TEMPERATURE: float = 0.1
    OPENAI_MAX_TOKENS: int = 4096
    
    # Anthropic Configuration (alternative)
    ANTHROPIC_API_KEY: Optional[str] = None
    ANTHROPIC_MODEL: str = "claude-3-opus-20240229"
    
    # Database Configuration
    # PostgreSQL
    POSTGRES_HOST: Optional[str] = None
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: Optional[str] = None
    POSTGRES_PASSWORD: Optional[str] = None
    POSTGRES_DB: Optional[str] = None
    
    # MySQL
    MYSQL_HOST: Optional[str] = None
    MYSQL_PORT: int = 3306
    MYSQL_USER: Optional[str] = None
    MYSQL_PASSWORD: Optional[str] = None
    MYSQL_DB: Optional[str] = None
    
    # SQL Server
    MSSQL_HOST: Optional[str] = None
    MSSQL_PORT: int = 1433
    MSSQL_USER: Optional[str] = None
    MSSQL_PASSWORD: Optional[str] = None
    MSSQL_DB: Optional[str] = None
    
    # MongoDB
    MONGODB_URI: Optional[str] = None
    MONGODB_DB: Optional[str] = None
    
    # Redis Configuration
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: Optional[str] = None
    REDIS_CACHE_TTL: int = 3600  # 1 hour
    
    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_CALLS: int = 100
    RATE_LIMIT_PERIOD: int = 60  # seconds
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "logs/app.log"
    
    # Query Configuration
    MAX_QUERY_TIMEOUT: int = 300  # 5 minutes
    MAX_RESULT_ROWS: int = 10000
    ENABLE_QUERY_CACHING: bool = True
    
    # AI Agent Configuration
    AGENT_MAX_ITERATIONS: int = 10
    AGENT_VERBOSE: bool = True
    ENABLE_AGENTIC_MODE: bool = True
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="allow"
    )
    
    @property
    def postgres_url(self) -> Optional[str]:
        """Build PostgreSQL connection URL"""
        if all([self.POSTGRES_HOST, self.POSTGRES_USER, self.POSTGRES_PASSWORD, self.POSTGRES_DB]):
            return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        return None
    
    @property
    def mysql_url(self) -> Optional[str]:
        """Build MySQL connection URL"""
        if all([self.MYSQL_HOST, self.MYSQL_USER, self.MYSQL_PASSWORD, self.MYSQL_DB]):
            return f"mysql+pymysql://{self.MYSQL_USER}:{self.MYSQL_PASSWORD}@{self.MYSQL_HOST}:{self.MYSQL_PORT}/{self.MYSQL_DB}"
        return None
    
    @property
    def mssql_url(self) -> Optional[str]:
        """Build SQL Server connection URL"""
        if all([self.MSSQL_HOST, self.MSSQL_USER, self.MSSQL_PASSWORD, self.MSSQL_DB]):
            return f"mssql+pymssql://{self.MSSQL_USER}:{self.MSSQL_PASSWORD}@{self.MSSQL_HOST}:{self.MSSQL_PORT}/{self.MSSQL_DB}"
        return None
    
    @property
    def redis_url(self) -> str:
        """Build Redis connection URL"""
        if self.REDIS_PASSWORD:
            return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
    
    @staticmethod
    def get_current_timestamp() -> str:
        """Get current timestamp in ISO format"""
        return datetime.utcnow().isoformat()


# Global settings instance
settings = Settings()
