"""
SupportIQ — models package.
Import all models here so SQLAlchemy metadata is populated before create_all().
"""
from app.models.user import User, UserRole  # noqa: F401
from app.models.conversation import Conversation, Message, IntentPrediction, ConversationStatus, MessageSender  # noqa: F401
from app.models.ticket import SupportTicket, TicketPriority, TicketStatus  # noqa: F401
from app.models.knowledge import KnowledgeDocument  # noqa: F401
from app.models.feedback import Feedback, Notification  # noqa: F401
