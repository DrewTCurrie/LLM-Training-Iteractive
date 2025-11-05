from flask import Blueprint, request, jsonify, Response, stream_with_context
import logging

logger = logging.getLogger(__name__)

chat_bp = Blueprint("chat", __name__)

# LLM service will be injected when blueprint is registered
llm_service = None


def init_chat_routes(service):
    """Initialize the chat routes with the LLM service"""
    global llm_service
    llm_service = service


@chat_bp.route("/chat", methods=["POST"])
def chat():
    """
    Chat endpoint that accepts messages and returns AI responses

    Request body:
    {
        "messages": [
            {"role": "system", "content": "You are a helpful assistant"},
            {"role": "user", "content": "Hello!"}
        ],
        "stream": false,
        "max_tokens": 512,
        "temperature": 0.7
    }
    """
    try:
        data = request.get_json()

        if not data or "messages" not in data:
            return jsonify({"error": "Missing required field: messages"}), 400

        messages = data["messages"]
        stream = data.get("stream", False)
        max_tokens = data.get("max_tokens", 512)
        temperature = data.get("temperature", 0.7)

        # Validate messages format
        if not isinstance(messages, list) or len(messages) == 0:
            return jsonify({"error": "Messages must be a non-empty list"}), 400

        for msg in messages:
            if "role" not in msg or "content" not in msg:
                return jsonify(
                    {"error": "Each message must have role and content"}
                ), 400

        if stream:
            # Streaming response
            def generate():
                try:
                    for chunk in llm_service.chat(
                        messages=messages,
                        max_tokens=max_tokens,
                        temperature=temperature,
                        stream=True,
                    ):
                        # Send as server-sent events (SSE)
                        yield f"data: {chunk}\n\n"
                    yield "data: [DONE]\n\n"
                except Exception as e:
                    logger.error(f"Streaming error: {e}")
                    yield f"data: [ERROR: {str(e)}]\n\n"

            return Response(
                stream_with_context(generate()),
                mimetype="text/event-stream",
                headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
            )
        else:
            # Non-streaming response
            response = llm_service.chat(
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
                stream=False,
            )

            return jsonify(
                {
                    "message": {"role": "assistant", "content": response["text"]},
                    "tokens_used": response.get("tokens_used", 0),
                }
            )

    except Exception as e:
        logger.error(f"Chat endpoint error: {e}")
        return jsonify({"error": str(e)}), 500


@chat_bp.route("/chat/models", methods=["GET"])
def list_models():
    """List available models (for future expansion)"""
    # For now, just return info about the loaded model
    return jsonify(
        {
            "models": [
                {
                    "name": "default",
                    "path": str(llm_service.model_path) if llm_service else None,
                    "loaded": llm_service is not None,
                }
            ]
        }
    )


@chat_bp.route("/health", methods=["GET"])
def health():
    """Health check endpoint"""
    return jsonify(
        {
            "status": "healthy",
            "model_loaded": llm_service is not None and llm_service.llm is not None,
        }
    )
