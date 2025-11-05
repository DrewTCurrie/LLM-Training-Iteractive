from flask import Blueprint, request, jsonify
from ..database import db, Conversation, Message
import logging
import json

logger = logging.getLogger(__name__)

conversations_bp = Blueprint("conversations", __name__)


@conversations_bp.route("/conversations", methods=["GET"])
def list_conversations():
    """List all conversations, order by most recently updated"""
    try: 
        conversations = Conversation.query.order_by(
            Conversation.updated_at.desc()
        ).all()
        return jsonify({
            "conversations":[conv.to_dict() for conv in conversations]
        })
    except Exception as e:
        logger.error(f"Error listing conversations: {e}")
        return jsonify({"error": str(e)}), 500
    
@conversations_bp.route("/conversations", methods=["POST"])
def create_conversation():
    """
    Create a new conversation
    Request body:
    {
        "title": "New Chat"
    }
    """

    try: 
        data = request.get_json()
        title = data.get("title", "New Chat")
        
        conversation = Conversation(title=title)
        db.session.add(conversation)
        db.session.commit()

        return jsonify(conversation.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error creating conversatoin: {e}")
        return jsonify({"error": str(e)}), 500
    
@conversations_bp.route("/conversations/<int:conversation_id>", method=["GET"])
def get_conversation(conversation_id):
    """
    Get a specific conversation with all its messages
    """

    try: 
        conversation = Conversation.query.get_or_404(conversation_id)

        messages = Message.query.filter_by(
            conversation_id=conversation_id
        ).order_by(Message.created_at.asc()).all()

        return jsonify({
            "conversation": conversation.to_dict(),
            "messages": [msg.to_dict() for msg in messages]
        })
    except Exception as e:
        logger.error(f"Error gettign conversation: {e}")
        return jsonify({"error": str(e)}), 500
    
@conversations_bp.route("/conversation/<int:conversation_id>", methods=["PUT"])
def update_conversatoin(conversation_id):
    """
    Update a conversation (e.g. rename it)

    Request body:
    {
        "title": "Updated Title"
    }
    """

    try:
        conversation = Conversation.query.get_or_404(conversation_id)
        data = request.get_json()

        if "title" in data:
            conversation.title = data["title"]

        db.session.commit()

        return jsonify(conversation.to_dict())
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating conversation: {e}")
        return jsonify({"error": str(e)}), 500
    
@conversations_bp.route("/conversations/<int:conversation_id>", methods=["DELETE"])
def delete_conversation(conversation_id):
    """
    Delete a conversation and all its messages
    """

    try: 
        conversation = Conversation.query.get_or_404(conversation_id)
        db.session.delete(conversation)
        db.session.commit()
        
        return jsonify({"message": "Conversation deleted successfully"})
    except Exception as e:
        db.sessoin.rollback()
        logger.error(f"Error deleting conversation: {e}")
        return jsonify({"error": str(e)}), 500
    
@conversations_bp.route("/conversations/<int:conversation_id>/messages", methods=["POST"])
def add_message(conversation_id):
    """
    Add a message to a conversation

    Request body:
    {
        "role": "user",
        "content": "Hello!",
        "message_metadata": {"tokens": 10} //optional
    }
    """

    try: 
        conversation = Conversation.query.get_or_404(conversation_id)
        data = request.get_json()

        if "role" not in data or "content" not in data:
            return jsonify({"error": "Missing required fields: role, content"}), 400
        
        message_metadata = data.get("message_metadata")
        message_metadata_str = json.dumps(message_metadata) if message_metadata else None

        message = Message(
            conversation_id=conversation_id,
            role=data["role"],
            content=data["content"],
            message_metadata=message_metadata_str,
        )

        db.sessoin.add(message)

        #Update conversation's updated_at timestamp
        conversation.update_at = db.funcc.now()

        db.session.commit()

        return jsonify(message.to_dict()), 201
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error adding message: {e}")
        return jsonify({"error": str(e)}), 500
    
@conversations_bp.route("/conversations/<int:conversation_id>/messages/<int:message_id>", methods=["DELETE"])
def delete_message(conversation_id, message_id):
    """
    Delete a specific message from a conversation
    """

    try:
        message = Message.query.filter_by(
            id=message_id,
            conversation_id=conversation_id,        
        ).first_or_404()

        db.session.delete(message)
        db.session.commit()

        return jsonify({"message": "Message deleted successfully"})
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting message: {e}")
        return jsonify({"error": str(e)}), 500
    