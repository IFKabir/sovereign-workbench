from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """Application settings using pydantic-settings."""
    
    # vLLM Configuration
    vllm_base_url: str = 'http://localhost:8002/v1'
    vllm_model_name: str = 'Qwen/Qwen2.5-VL-7B-Instruct'
    
    # Qdrant Configuration  
    qdrant_url: str = 'http://localhost:6333'
    qdrant_collection: str = 'mrpl_standards'
    
    # YOLO Service
    yolo_service_url: str = 'http://localhost:8001'
    
    # Embedding Models
    embedding_model: str = 'BAAI/bge-m3'
    reranker_model: str = 'BAAI/bge-reranker-large'
    
    # Router Model
    router_model_path: str = './models/task-router'
    
    # YOLO Model
    yolo_model_path: str = './models/yolo-pid/best.pt'
    
    # Sandbox
    sandbox_image: str = 'sovereign-sandbox:latest'
    sandbox_timeout: int = 30
    
    # Audit
    audit_db_path: str = './data/audit_ledger.db'
    
    # Server
    cors_origins: list[str] = [
        'http://localhost:3000',
        'http://127.0.0.1:3000',
    ]
    api_host: str = '0.0.0.0'
    api_port: int = 8080
    log_level: str = 'info'
    
    # JWT
    jwt_secret_key: str = 'sovereign-workbench-secret-change-in-production'
    jwt_algorithm: str = 'HS256'
    jwt_expire_minutes: int = 480
    
    model_config = {'env_file': '.env', 'env_file_encoding': 'utf-8'}

settings = Settings()
