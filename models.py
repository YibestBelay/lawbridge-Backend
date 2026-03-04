import uuid
import enum
from datetime import datetime
from sqlalchemy import (
    Column, String, Text, Integer, Numeric, Boolean,
    DateTime, ForeignKey, Enum as SAEnum
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base  # ← imported from database.py instead of defined here


# ──────────────────────────────────────────
# ENUMS
# ──────────────────────────────────────────

class UserRole(str, enum.Enum):
    client = "client"
    lawyer = "lawyer"
    student = "student"
    admin = "admin"


class CaseStatus(str, enum.Enum):
    pending_review = "Pending Review"
    in_progress = "In Progress"
    submitted = "Submitted"
    completed = "Completed"
    cancelled = "Cancelled"


class PaymentStatus(str, enum.Enum):
    pending = "Pending"
    partial = "Partial"
    completed = "Completed"
    refunded = "Refunded"
    failed = "Failed"


class PaymentMethod(str, enum.Enum):
    bank_transfer = "Bank Transfer"
    card = "Card Payment"
    mobile_money = "Mobile Money"


class MessageStatus(str, enum.Enum):
    sent = "sent"
    delivered = "delivered"
    read = "read"


class NotificationPreference(str, enum.Enum):
    all = "all"
    important_only = "important_only"
    none = "none"


# ──────────────────────────────────────────
# USER
# ──────────────────────────────────────────

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    phone = Column(String(30))
    bio = Column(Text)
    avatar_url = Column(String(500))
    role = Column(SAEnum(UserRole), nullable=False, default=UserRole.client)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    cases = relationship("Case", back_populates="client", foreign_keys="Case.client_id")
    payments = relationship("Payment", back_populates="client")
    sent_messages = relationship("Message", back_populates="sender", foreign_keys="Message.sender_id")
    received_messages = relationship("Message", back_populates="receiver", foreign_keys="Message.receiver_id")
    notifications = relationship("Notification", back_populates="user")
    notification_settings = relationship("NotificationSettings", back_populates="user", uselist=False)
    privacy_settings = relationship("PrivacySettings", back_populates="user", uselist=False)


# ──────────────────────────────────────────
# CASE CATEGORY
# ──────────────────────────────────────────

class CaseCategory(Base):
    __tablename__ = "case_categories"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), unique=True, nullable=False)
    description = Column(Text)

    cases = relationship("Case", back_populates="category")


# ──────────────────────────────────────────
# CASE
# ──────────────────────────────────────────

class Case(Base):
    __tablename__ = "cases"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    client_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    lawyer_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    category_id = Column(UUID(as_uuid=True), ForeignKey("case_categories.id"))
    status = Column(SAEnum(CaseStatus), default=CaseStatus.pending_review, nullable=False)
    progress = Column(Integer, default=0)
    fee_amount = Column(Numeric(12, 2))
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    client = relationship("User", back_populates="cases", foreign_keys=[client_id])
    lawyer = relationship("User", foreign_keys=[lawyer_id])
    category = relationship("CaseCategory", back_populates="cases")
    payments = relationship("Payment", back_populates="case")
    messages = relationship("Message", back_populates="case")
    updates = relationship("CaseUpdate", back_populates="case", order_by="CaseUpdate.created_at.desc()")


# ──────────────────────────────────────────
# CASE UPDATE
# ──────────────────────────────────────────

class CaseUpdate(Base):
    __tablename__ = "case_updates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    case_id = Column(UUID(as_uuid=True), ForeignKey("cases.id"), nullable=False)
    author_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    note = Column(Text, nullable=False)
    new_status = Column(SAEnum(CaseStatus))
    new_progress = Column(Integer)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    case = relationship("Case", back_populates="updates")
    author = relationship("User")


# ──────────────────────────────────────────
# PAYMENT
# ──────────────────────────────────────────

class Payment(Base):
    __tablename__ = "payments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    invoice_number = Column(String(50), unique=True, nullable=False)
    client_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    lawyer_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    case_id = Column(UUID(as_uuid=True), ForeignKey("cases.id"), nullable=False)
    amount = Column(Numeric(12, 2), nullable=False)
    status = Column(SAEnum(PaymentStatus), default=PaymentStatus.pending, nullable=False)
    method = Column(SAEnum(PaymentMethod))
    paid_at = Column(DateTime(timezone=True))
    due_date = Column(DateTime(timezone=True))
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    client = relationship("User", back_populates="payments", foreign_keys=[client_id])
    lawyer = relationship("User", foreign_keys=[lawyer_id])
    case = relationship("Case", back_populates="payments")


# ──────────────────────────────────────────
# CONVERSATION
# ──────────────────────────────────────────

class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    client_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    lawyer_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    case_id = Column(UUID(as_uuid=True), ForeignKey("cases.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    client = relationship("User", foreign_keys=[client_id])
    lawyer = relationship("User", foreign_keys=[lawyer_id])
    case = relationship("Case")
    messages = relationship("Message", back_populates="conversation", order_by="Message.created_at")


# ──────────────────────────────────────────
# MESSAGE
# ──────────────────────────────────────────

class Message(Base):
    __tablename__ = "messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id"), nullable=False)
    case_id = Column(UUID(as_uuid=True), ForeignKey("cases.id"), nullable=True)
    sender_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    receiver_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    body = Column(Text, nullable=False)
    status = Column(SAEnum(MessageStatus), default=MessageStatus.sent)
    is_read = Column(Boolean, default=False)
    read_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    conversation = relationship("Conversation", back_populates="messages")
    case = relationship("Case", back_populates="messages")
    sender = relationship("User", back_populates="sent_messages", foreign_keys=[sender_id])
    receiver = relationship("User", back_populates="received_messages", foreign_keys=[receiver_id])


# ──────────────────────────────────────────
# NOTIFICATION
# ──────────────────────────────────────────

class Notification(Base):
    __tablename__ = "notifications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    title = Column(String(255), nullable=False)
    body = Column(Text)
    is_read = Column(Boolean, default=False)
    link = Column(String(500))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="notifications")


# ──────────────────────────────────────────
# NOTIFICATION SETTINGS
# ──────────────────────────────────────────

class NotificationSettings(Base):
    __tablename__ = "notification_settings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), unique=True, nullable=False)
    email_notifications = Column(Boolean, default=True)
    sms_notifications = Column(Boolean, default=False)
    case_updates = Column(Boolean, default=True)
    payment_alerts = Column(Boolean, default=True)
    message_alerts = Column(Boolean, default=True)
    preference = Column(SAEnum(NotificationPreference), default=NotificationPreference.all)

    user = relationship("User", back_populates="notification_settings")


# ──────────────────────────────────────────
# PRIVACY SETTINGS
# ──────────────────────────────────────────

class PrivacySettings(Base):
    __tablename__ = "privacy_settings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), unique=True, nullable=False)
    profile_visible_to_lawyers = Column(Boolean, default=True)
    allow_data_export = Column(Boolean, default=True)
    marketing_emails = Column(Boolean, default=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    user = relationship("User", back_populates="privacy_settings")