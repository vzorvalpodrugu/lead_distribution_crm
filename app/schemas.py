from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime

# Schames for operator
class OperatorBase(BaseModel):
    name: str
    is_active: bool
    load_limit: int = 10

class OperatorCreate(OperatorBase):
    pass

class OperatorUpdate(BaseModel):
    name: Optional[str] = None
    is_active: Optional[bool] = None
    load_limit: Optional[int] = None

class Operator(OperatorBase):
    id: int
    current_load: int

    class Config:
        from_attributes = True

# Schames for lead
class LeadBase(BaseModel):
    external_id: str
    phone: Optional[str] = None
    email: Optional[EmailStr] = None

class Lead(LeadBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

# Schemas for sourse
class SourceBase(BaseModel):
    name: str
    bot_id: str

class SourceCreate(SourceBase):
    pass

class Sourse(SourceBase):
    id: int

    class Config:
        from_attributes = True

# Basic schemas for weight operator in source
class OperatorSourceWeightBase(BaseModel):
    operator_id: int
    source_id: int
    weight: int = 1

class OperatorSourceWeightCreate(SourceBase):
    pass

class OperatorSourceWeigth(OperatorSourceWeightBase):
    id: int

    class Config:
        from_attributes = True

# Basic schemas for contact
class ContactBase(BaseModel):
    external_id: str
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    source_bot_id: str
    message: Optional[str] = None

class ContactCreate(ContactBase):
    pass

class Contact(BaseModel):
    id: int
    lead_id: int
    source_id: int
    operator_id: Optional[int] = None
    message: Optional[str] = None
    created_at: datetime
    lead: Lead
    source: Sourse
    operator: Optional[Operator]

    class Config:
        from_attributes = True

class ContactSimple(BaseModel):
    id: int
    source_id: int
    operator_id: Optional[int] = None
    created_at: datetime
    source: Sourse
    operator: Optional[Operator]

    class Config:
        from_attributes = True

class LeadWithContacts(Lead):
    contacts: List[ContactSimple]

    class Config:
        from_attributes = True

class DistributionStats(BaseModel):
    source_id: int
    source_name: str
    operator_id: Optional[int] = None
    operator_name: Optional[str] = None
    contact_count: int

