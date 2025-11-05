import os
from pathlib import Path


class Config:
    """Base configuration"""

    # Flask settings
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
    DEBUG = os.getenv("DEBUG", "True") == "True"

    # Database settings
    BASE_DIR = Path(__file__).parent.parent
    DATABASE_DIR = BASE_DIR / "data"
    DATABASE_DIR.mkdir(exist_ok=True)

    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        f"sqlite:///{DATABASE_DIR / 'webui.db'}"
    )
    SQLACHEMY_TRACK_MODIFICATIONS = False


    # Model settings
    BASE_DIR = Path(__file__).parent.parent
    MODEL_DIR = BASE_DIR / "models"
    DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "model.gguf")

    # LLM settings
    N_CTX = int(os.getenv("N_CTX", "8192"))  # Context window size
    N_GPU_LAYERS = int(os.getenv("N_GPU_LAYERS", "-1"))  # Changed default to -1 for GPU
    N_THREADS = int(os.getenv("N_THREADS", "4"))  # CPU threads to use

    # Generation settings
    MAX_TOKENS = int(os.getenv("MAX_TOKENS", "8192"))
    TEMPERATURE = float(os.getenv("TEMPERATURE", "0.7"))
    TOP_P = float(os.getenv("TOP_P", "0.9"))
    TOP_K = int(os.getenv("TOP_K", "40"))

    @classmethod
    def get_model_path(cls):
        """Get the full path to the model file"""
        return cls.MODEL_DIR / cls.DEFAULT_MODEL
