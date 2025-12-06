from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app import models, schemas, crud, services
from app.database import SessionLocal, engine, Base

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Мини-CRM распределения лидов", version="1.0.0")


# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Endpoints for operators
@app.post("/operators/", response_model=schemas.Operator)
def create_operator(operator: schemas.OperatorCreate,
                    db: Session = Depends(get_db)):
    """Create a new operator"""
    return crud.create_operator(db=db, operator=operator)


@app.get("/operators/", response_model=List[schemas.Operator])
def read_operators(skip: int = 0, limit: int = 100,
                   db: Session = Depends(get_db)):
    """Get all operators"""
    operators = crud.get_operators(db, skip=skip, limit=limit)
    return operators


@app.put("/operators/{operator_id}", response_model=schemas.Operator)
def update_operator(
        operator_id: int,
        operator: schemas.OperatorUpdate,
        db: Session = Depends(get_db)
):
    """Update an existing operator"""
    db_operator = crud.get_operator(db, operator_id=operator_id)
    if not db_operator:
        raise HTTPException(status_code=404, detail="Operator not found")
    return crud.update_operator(db=db, operator_id=operator_id,
                                operator=operator)


# Endpoints for sources
@app.post("/sources/", response_model=schemas.Source)
def create_source(source: schemas.SourceCreate, db: Session = Depends(get_db)):
    """Create a new source"""
    return crud.create_source(db=db, source=source)


@app.get("/sources/", response_model=List[schemas.Source])
def read_sources(skip: int = 0, limit: int = 100,
                 db: Session = Depends(get_db)):
    """Get all sources"""
    sources = crud.get_sources(db, skip=skip, limit=limit)
    return sources


@app.post("/source-weights/", response_model=schemas.OperatorSourceWeight)
def create_source_weight(
        weight: schemas.OperatorSourceWeightCreate,
        db: Session = Depends(get_db)
):
    """Create a new source weight"""
    operator = crud.get_operator(db, operator_id=weight.operator_id)
    if not operator:
        raise HTTPException(status_code=404, detail="Operator not found")

    source = crud.get_source(db, source_id=weight.source_id)
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")

    return crud.create_operator_source_weight(db=db, weight=weight)

# Endpoints for contacts
@app.post("/contacts/", response_model=schemas.Contact)
def create_contact(
        contact: schemas.ContactCreate,
        db: Session = Depends(get_db)
):
    """Create a new contact"""
    return services.process_contact(db=db, contact_data=contact)


@app.get("/contacts/", response_model=List[schemas.Contact])
def read_contacts(skip: int = 0, limit: int = 100,
                  db: Session = Depends(get_db)):
    """Get all contacts"""
    contacts = crud.get_contacts(db, skip=skip, limit=limit)
    return contacts

# Endpoints for leads
@app.get("/leads/", response_model=List[schemas.LeadWithContacts])
def read_leads(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Get all leads"""
    return crud.get_leads_with_contacts(db, skip=skip, limit=limit)

@app.get("/stats/distribution/")
def get_distribution_stats(db: Session = Depends(get_db)):
    """Get distribution statistics"""
    return services.get_distribution_stats(db)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)