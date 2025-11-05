from flask import Blueprint, request, jsonify, Response, stream_with_context
from ..database import db, Conversation, Message
import logging
import json


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
        save_conversation = data.get("save_conversation", False)
        conversation_id = data.get("conversation_id")

        # Validate messages format
        if not isinstance(messages, list) or len(messages) == 0:
            return jsonify({"error": "Messages must be a non-empty list"}), 400

        for msg in messages:
            if "role" not in msg or "content" not in msg:
                return jsonify(
                    {"error": "Each message must have role and content"}
                ), 400

        #Create or get conversation if saving
        conversation = None
        if save_conversation:
            if conversation_id:
                conversation = Conversation.query.get(conversation_id)
                if not conversation: 
                    return jsonify({"error": "Conversation not found"}), 404
            else:
                #Create a new coversation with title from first user message
                user_msg = next((m for m in messages if m["role"] == "user"), None)
                title = (user_msg["content"][:50] + "...") if user_msg and len(user_msg["content"]) > 50 else (user_msg["content"] if user_msg else "New Chat")

                conversation = Conversation(title=title)
                db.session.add(conversation)
                db.session.flush() #Get the ID without committing 

                if stream:
            # Streaming response
            def generate():
                full_response = ""
                try:
                    for chunk in llm_service.chat(
                        messages=messages,
                        max_tokens=max_tokens,
                        temperature=temperature,
                        stream=True,
                    ):
                        full_response += chunk
                        # Send as server-sent events (SSE)
                        yield f"data: {chunk}\n\n"
                    
                    # Save conversation after streaming is complete
                    if save_conversation and conversation:
                        try:
                            # Save user message
                            last_user_msg = next((m for m in reversed(messages) if m["role"] == "user"), None)
                            if last_user_msg:
                                user_message = Message(
                                    conversation_id=conversation.id,
                                    role="user",
                                    content=last_user_msg["content"]
                                )
                                db.session.add(user_message)
                            
                            # Save assistant response
                            assistant_message = Message(
                                conversation_id=conversation.id,
                                role="assistant",
                                content=full_response
                            )
                            db.session.add(assistant_message)
                            
                            conversation.updated_at = db.func.now()
                            db.session.commit()
                            
                            # Send conversation ID to client
                            yield f"data: [CONVERSATION_ID:{conversation.id}]\n\n"
                        except Exception as e:
                            logger.error(f"Error saving conversation: {e}")
                            db.session.rollback()
                    
                    yield "data: [DONE]\n\n"
                except Exception as e:
                    logger.error(f"Streaming error: {e}")
                    if save_conversation:
                        db.session.rollback()
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

            #Save conversation if requested
            if save_conversation and conversation:
                try:
                    # Save user message
                    last_user_msg = next((m for m in reversed(messages) if m["role"] == "user"), None)
                    if last_user_msg:
                        user_message = Message(
                            conversation_id=conversation.id,
                            role="user",
                            content=last_user_msg["content"]
                        )
                        db.session.add(user_message)

                    #Save assistant response
                    assistant_message = Message(
                        conversation_id=conversation.id,
                        role="assistant",
                        content=response["text"],
                        metadata=json.dumps({"tokens_used": response.get("tokens_used", 0)})
                    )

                    db.session.add(assistant_message)

                    conversation.updated_at = db.func.now()
                    db.session.commit()
                except Exception as e:
                    logger.error(f"Error saving conversation: {e}")
                    db.session.rollback()
                
                result = {
                    "message": {"role": "assistant", "content": response["text"]},
                    "tokens_used": response.get("tokens_used",0)
                }

                if save_conversation and conversation:
                    result["conversation_id"] = conversation.id
                
                return jsonify(result)

    except Exception as e:
        logger.error(f"Chat endpoint error: {e}")
        if save_conversation:
            db.session.rollback()        
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
