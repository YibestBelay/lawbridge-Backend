import uuid
from datetime import datetime
from pydantic import BaseModel, EmailStr
from typing import Optional
from models import UserRole, CaseStatus, PaymentStatus, PaymentMethod, MessageStatus, NotificationPreference


# ──────────────────────────────────────────
# USER SCHEMAS
# ──────────────────────────────────────────

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    first_name: str
    last_name: str
    phone: Optional[str] = None
    role: UserRole = UserRole.client


class UserResponse(BaseModel):
    id: uuid.UUID
    email: str
    first_name: str
    last_name: str
    phone: Optional[str] = None
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    role: UserRole
    is_active: bool
    is_verified: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class UserUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    bio: Optional[str] = None
    avatar_url: Optional[str] = None


# ──────────────────────────────────────────
# CASE SCHEMAS
# ──────────────────────────────────────────

class CaseCreate(BaseModel):
    title: str
    description: Optional[str] = None
    lawyer_id: uuid.UUID
    category_id: Optional[uuid.UUID] = None
    fee_amount: Optional[float] = None


class CaseResponse(BaseModel):
    id: uuid.UUID
    title: str
    description: Optional[str] = None
    client_id: uuid.UUID
    lawyer_id: uuid.UUID
    status: CaseStatus
    progress: int
    fee_amount: Optional[float] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class CaseUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[CaseStatus] = None
    progress: Optional[int] = None
    fee_amount: Optional[float] = None


# ──────────────────────────────────────────
# PAYMENT SCHEMAS
# ──────────────────────────────────────────

class PaymentCreate(BaseModel):
    case_id: uuid.UUID
    lawyer_id: uuid.UUID
    amount: float
    method: Optional[PaymentMethod] = None
    due_date: Optional[datetime] = None
    notes: Optional[str] = None


class PaymentResponse(BaseModel):
    id: uuid.UUID
    invoice_number: str
    client_id: uuid.UUID
    lawyer_id: uuid.UUID
    case_id: uuid.UUID
    amount: float
    status: PaymentStatus
    method: Optional[PaymentMethod] = None
    due_date: Optional[datetime] = None
    created_at: datetime

    model_config = {"from_attributes": True}


# ──────────────────────────────────────────
# MESSAGE SCHEMAS
# ──────────────────────────────────────────

class MessageCreate(BaseModel):
    receiver_id: uuid.UUID
    case_id: Optional[uuid.UUID] = None
    body: str


class MessageResponse(BaseModel):
    id: uuid.UUID
    sender_id: uuid.UUID
    receiver_id: uuid.UUID
    body: str
    status: MessageStatus
    is_read: bool
    created_at: datetime

    model_config = {"from_attributes": True}


# ──────────────────────────────────────────
# NOTIFICATION SCHEMAS
# ──────────────────────────────────────────

class NotificationResponse(BaseModel):
    id: uuid.UUID
    title: str
    body: Optional[str] = None
    is_read: bool
    link: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}
