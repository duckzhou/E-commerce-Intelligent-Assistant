from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # 通义千问API配置
    dashscope_api_key: str = "sk-xxx"
    dashscope_base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    llm_model: str = "qwen-turbo"
    embedding_model: str = "text-embedding-v3"

    # 数据库
    database_url: str = "sqlite:///./data/app.db"

    # ChromaDB
    chroma_path: str = "./data/chroma_db"

    # 文本切分配置
    chunk_size: int = 500
    chunk_overlap: int = 50

    # 置信度阈值
    high_confidence_threshold: float = 0.75
    medium_confidence_threshold: float = 0.5

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()