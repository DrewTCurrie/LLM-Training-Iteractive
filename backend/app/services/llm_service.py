from llama_cpp import Llama
from typing import Generator, Dict, Any
import logging

logger = logging.getLogger(__name__)


class LLMService:
    """Service for managing LLM inference using llama.cpp"""

    def __init__(
        self,
        model_path: str,
        n_ctx: int = 2048,
        n_gpu_layers: int = -1,
        n_threads: int = 4,
    ):
        """
        Initialize the LLM service

        Args:
            model_path: Path to the .gguf model file
            n_ctx: Context window size (default: 2048)
            n_gpu_layers: Number of layers to offload to GPU (0 = CPU only, -1 = all)
            n_threads: Number of CPU threads to use
        """
        self.model_path = model_path
        self.llm = None
        self.n_ctx = n_ctx
        self.n_gpu_layers = n_gpu_layers
        self.n_threads = n_threads

        logger.info(f"Initializing LLM service with model: {model_path}")
        self._load_model()

    def _load_model(self):
        """Load the model into memory"""
        try:
            self.llm = Llama(
                model_path=str(self.model_path),
                n_ctx=self.n_ctx,
                n_gpu_layers=self.n_gpu_layers,
                n_threads=self.n_threads,
                verbose=True,
            )
            logger.info("Model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            raise

    def generate(
        self,
        prompt: str,
        max_tokens: int = 512,
        temperature: float = 0.7,
        top_p: float = 0.9,
        top_k: int = 40,
        stop: list = None,
        stream: bool = False,
    ) -> Dict[str, Any] | Generator:
        """
        Generate a response from the model

        Args:
            prompt: The input text prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature (0.0 to 1.0)
            top_p: Nucleus sampling parameter
            top_k: Top-k sampling parameter
            stop: List of stop sequences
            stream: Whether to stream the response

        Returns:
            Dict with 'text' key containing the response, or a generator if streaming
        """
        if self.llm is None:
            raise RuntimeError("Model not loaded")

        if stop is None:
            stop = []

        try:
            response = self.llm(
                prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=top_p,
                top_k=top_k,
                stop=stop,
                stream=stream,
                echo=False,
            )

            if stream:
                return self._stream_generator(response)
            else:
                return {
                    "text": response["choices"][0]["text"],
                    "tokens_used": response["usage"]["total_tokens"],
                }
        except Exception as e:
            logger.error(f"Generation failed: {e}")
            raise

    def _stream_generator(self, response_stream) -> Generator:
        """Convert llama.cpp stream to a cleaner generator"""
        for chunk in response_stream:
            if "choices" in chunk and len(chunk["choices"]) > 0:
                delta = chunk["choices"][0].get("text", "")
                if delta:
                    yield delta

    def chat(
        self,
        messages: list,
        max_tokens: int = 512,
        temperature: float = 0.7,
        stream: bool = False,
    ) -> Dict[str, Any] | Generator:
        """
        Chat completion format (converts messages to prompt)

        Args:
            messages: List of message dicts with 'role' and 'content' keys
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            stream: Whether to stream the response

        Returns:
            Dict with 'text' key or generator if streaming
        """
        # Convert chat messages to a single prompt
        # This is a simple format - you can customize based on your model's training
        prompt = self._format_chat_prompt(messages)

        return self.generate(
            prompt=prompt, max_tokens=max_tokens, temperature=temperature, stream=stream
        )

    def _format_chat_prompt(self, messages: list) -> str:
        """
        Format chat messages into a prompt string
        Uses ChatML format (works with Qwen3, Mistral, etc.)
        """
        # ChatML format: <|im_start|>role\ncontent<|im_end|>
        prompt_parts = []

        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            prompt_parts.append(f"<|im_start|>{role}\n{content}<|im_end|>")

        # Add the assistant start token to prompt generation
        prompt_parts.append("<|im_start|>assistant\n")

        return "\n".join(prompt_parts)

    def unload_model(self):
        """Unload the model from memory"""
        if self.llm is not None:
            del self.llm
            self.llm = None
            logger.info("Model unloaded")
