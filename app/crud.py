from sqlalchemy.orm import Session
from typing import List, Optional
from app import models, schemas
from app.models import Operator

# CRUD for operator
def create_operator(db: Session, operator: schemas.OperatorCreate) -> Operator:
    """Create a new operator"""
    operator_db = models.Operator(**operator.model_dump())
    db.add(operator_db)
    db.commit()
    db.refresh(operator_db)
    return operator_db

def get_operator(db: Session, operator_id: int) -> Optional[Operator]:
    """Get an existing operator"""
    operator_db = (db.query(models.Operator).filter(models.Operator.id == operator_id).first())
    if not operator_db:
        raise HTTPException(status_code=401, detail="Operator not found")
    return operator_db

def get_operators(db: Session, skip: int = 0, limit: int = 100) -> List[Operator]:
    """Get all operators"""
    return db.query(models.Operator).offset(skip).limit(limit).all()

def update_operator(db: Session, operator_id: int, operator: schemas.OperatorUpdate) -> Operator:
    """Update an existing operator"""
    try:
        operator_db = get_operator(db, operator_id)
    except DoesNotExist(Operator):
        raise HTTPException(status_code=401, detail="Operator not found")

    updated_data = operator_db.model_dump(exclude_unset=True)
    for key, value in updated_data.items():
        setattr(operator_db, key, value)

    db.commit()
    db.refresh(operator_db)
    return operator_db


# CRUD for lead
def get_lead_by_external_id(db: Session, external_id: str):
    """Get a lead by an external id"""
    return db.query(models.Lead).filter(
        models.Lead.external_id == external_id).first()

def get_lead_by_phone(db: Session, phone: str):
    """Get a lead by a phone"""
    return db.query(models.Lead).filter(models.Lead.phone == phone).first()

def create_lead(db: Session, lead: schemas.LeadBase):
    """Create a new lead"""
    db_lead = models.Lead(**lead.model_dump())
    db.add(db_lead)
    db.commit()
    db.refresh(db_lead)
    return db_lead

def get_or_create_lead(db: Session, external_id: str,
                       phone: Optional[str] = None,
                       email: Optional[str] = None):
    """Get an existing lead"""
    lead = get_lead_by_external_id(db, external_id)
    if lead:
        return lead

    if phone:
        lead = get_lead_by_phone(db, phone)
        if lead:
            return lead

    lead_data = schemas.LeadBase(external_id=external_id, phone=phone,
                                 email=email)
    return create_lead(db, lead_data)


# CRUD for sources
def create_source(db: Session, source: schemas.SourceCreate):
    """Create a new source"""
    db_source = models.Source(**source.model_dump())
    db.add(db_source)
    db.commit()
    db.refresh(db_source)
    return db_source

def get_source(db: Session, source_id: int):
    """Get an existing source"""
    return db.query(models.Source).filter(
        models.Source.id == source_id).first()

def get_source_by_bot_id(db: Session, bot_id: str):
    """Get an existing source"""
    return db.query(models.Source).filter(
        models.Source.bot_id == bot_id).first()

def get_sources(db: Session, skip: int = 0, limit: int = 100):
    """Get all sources"""
    return db.query(models.Source).offset(skip).limit(limit).all()


# CRUD for weight
def create_operator_source_weight(db: Session,
                                  weight: schemas.OperatorSourceWeightCreate):
    """Create a new source weight for an operator"""
    db_weight = models.OperatorSourceWeight(**weight.model_dump())
    db.add(db_weight)
    db.commit()
    db.refresh(db_weight)
    return db_weight

def get_weights_for_source(db: Session, source_id: int):
    """Get all weights for a source"""
    return db.query(models.OperatorSourceWeight).filter(
        models.OperatorSourceWeight.source_id == source_id
    ).all()


# CRUD for contacts
def create_contact(db: Session, contact: schemas.ContactBase, lead_id: int,
                   source_id: int, operator_id: Optional[int] = None):
    """Create a new contact"""
    db_contact = models.Contact(
        lead_id=lead_id,
        source_id=source_id,
        operator_id=operator_id,
        message=contact.message
    )
    db.add(db_contact)
    db.commit()
    db.refresh(db_contact)
    return db_contact

def get_contacts(db: Session, skip: int = 0, limit: int = 100):
    """Get all contacts"""
    return db.query(models.Contact).offset(skip).limit(limit).all()

def get_leads_with_contacts(db: Session, skip: int = 0, limit: int = 100):
    """Get all leads with contacts"""
    return db.query(models.Lead).options(
        joinedload(models.Lead.contacts).joinedload(models.Contact.source),
        joinedload(models.Lead.contacts).joinedload(models.Contact.operator)
    ).offset(skip).limit(limit).all()

def get_operator_active_contacts_count(db: Session, operator_id: int):
    """Get active contacts count"""
    return db.query(models.Contact).filter(
        models.Contact.operator_id == operator_id
    ).count()

def update_operator_load(db: Session, operator_id: int):
    """Update an existing operator"""
    operator = get_operator(db, operator_id)
    if operator:
        operator.current_load = get_operator_active_contacts_count(db,
                                                                   operator_id)
        db.commit()
        db.refresh(operator)
    return operator