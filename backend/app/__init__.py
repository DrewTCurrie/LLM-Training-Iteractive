from flask import Flask
from flask_cors import CORS
import logging
from .config import Config
from .services.llm_service import LLMService
from .routes.chat import chat_bp, init_chat_routes

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_app(config_class=Config):
    """Application factory pattern"""
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Enable CORS for frontend communication
    CORS(app)
    
    # Only initialize LLM in the main process (not the reloader parent)
    import os
    if os.environ.get('WERKZEUG_RUN_MAIN') == 'true' or not app.debug:
        # Initialize LLM service
        logger.info("Initializing LLM service...")
        logger.info(f"Config - N_GPU_LAYERS: {config_class.N_GPU_LAYERS}")
        logger.info(f"Config - N_CTX: {config_class.N_CTX}")
        logger.info(f"Config - N_THREADS: {config_class.N_THREADS}")
        logger.info(f"Config - Model path: {config_class.get_model_path()}")
        
        try:
            model_path = config_class.get_model_path()
            llm_service = LLMService(
                model_path=model_path,
                n_ctx=config_class.N_CTX,
                n_gpu_layers=config_class.N_GPU_LAYERS,
                n_threads=config_class.N_THREADS
            )
            logger.info("LLM service initialized successfully")
            
            # Initialize routes with the service
            init_chat_routes(llm_service)
            
        except Exception as e:
            logger.error(f"Failed to initialize LLM service: {e}")
            logger.warning("Server will start but chat endpoints will not work")
            init_chat_routes(None)
    else:
        logger.info("Skipping model load in reloader parent process")
        init_chat_routes(None)
    
    # Register blueprints
    app.register_blueprint(chat_bp, url_prefix='/api')
    
    @app.route('/')
    def index():
        return {
            'message': 'LLM Training Platform API',
            'version': '0.1.0',
            'endpoints': {
                'chat': '/api/chat',
                'health': '/api/health',
                'models': '/api/chat/models'
            }
        }
    
    return app