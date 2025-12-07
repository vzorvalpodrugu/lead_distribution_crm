from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

class Operator(Base):
    """Operator Model"""
    __tablename__ = 'operators'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    load_limit = Column(Integer, default=10)
    current_load = Column(Integer, default=0)

    contacts = relationship('Contact', back_populates='operator')
    source_weights = relationship('OperatorSourceWeight', back_populates='operator')

class Lead(Base):
    """Lead Model"""
    __tablename__ = 'leads'

    id = Column(Integer, primary_key=True, index=True)
    external_id = Column(String, unique=True, index=True, nullable=False)
    phone = Column(String, index=True)
    email = Column(String, index=True)
    created_at = Column(DateTime(timezone=True), default=func.now())

    contacts = relationship('Contact', back_populates='lead')

class Source(Base):
    """Source Model"""
    __tablename__ = 'sources'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    bot_id = Column(String, unique=True, nullable=False)

    contacts = relationship('Contact', back_populates='source')
    operator_weights = relationship('OperatorSourceWeight', back_populates='source')

class Contact(Base):
    """Contact Model"""
    __tablename__ = 'contacts'

    id = Column(Integer, primary_key=True, index=True)
    lead_id = Column(Integer, ForeignKey('leads.id'))
    source_id = Column(Integer, ForeignKey('sources.id'))
    operator_id = Column(Integer, ForeignKey('operators.id'), nullable=True)
    message = Column(String, nullable = False)
    created_at = Column(DateTime(timezone=True), default=func.now())

    lead = relationship('Lead', back_populates='contacts')
    source = relationship('Source', back_populates='contacts')
    operator = relationship('Operator', back_populates='contacts')

class OperatorSourceWeight(Base):
    """OperatorSourceWeight Model"""
    __tablename__ = 'operator_source_weights'

    id = Column(Integer, primary_key=True, index=True)
    operator_id = Column(Integer, ForeignKey('operators.id'))
    source_id = Column(Integer, ForeignKey('sources.id'))
    weight = Column(Integer, default=1)

    __table_args__ = (
        UniqueConstraint('operator_id', 'source_id',
                         name='unique_operator_source'),
    )

    operator = relationship("Operator", back_populates="source_weights")
    source = relationship("Source", back_populates="operator_weights")
