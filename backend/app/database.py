from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone
import json

db = SQLAlchemy()

class Conversation(db.Model):
    """Model for storing chat conversations"""
    __tablename__ = 'conversations'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now(timezone.utc), nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.now(timezone.utc),  onupdate=datetime.now(timezone.utc), nullable=False)

    #Relationship to messages
    message = db.relationship('Message', backref='conversation', lazy=True, cascade='all, delete-orphan')

    def to_dict(self):
        """Convert conversation to dictionary"""
        return {
            'id': self.id,
            'title': self.title,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'message_count': len(self.messages)
        }
    
class Message(db.Model):
    """Model for storing individual messages in a conversation"""
    __tablename__ = 'messages'

    id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(db.Integer, db.ForeignKey('conversations.id'), nullable=False)
    role = db.Column(db.String(20), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now(timezone.utc), nullable=False)
    message_metadata = db.Column(db.Text, nullable=True)

    def to_dict(self):
        """Convert message to dictionary"""
        result = {
            'id': self.id,
            'conversation_id': self.conversation_id,
            'role': self.role,
            'content': self.content,
            'created_at': self.created_at.isoformat()
        }
        if self.message_metadata:
            try:
                result['message_metadata'] = json.loads(self.message_metadata)
            except:
                result['message_metadata'] = None
        return result
    
def init_db(app):
    """Initialize the database"""
    db.init_app(app)

    with app.app_context():
        db.create_all()