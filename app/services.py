import random
from sqlalchemy.orm import Session
from typing import List, Optional, Dict
from app import models, schemas, crud


def get_available_operators_for_source(db: Session, source_id: int) -> List[
    Dict]:
    """Get available operators for a given source"""
    weights = crud.get_weights_for_source(db, source_id)
    available_operators = []

    for weight_obj in weights:
        operator = crud.get_operator(db, weight_obj.operator_id)

        if operator and operator.is_active and operator.current_load < operator.load_limit:
            available_operators.append({
                'operator': operator,
                'weight': weight_obj.weight
            })

    return available_operators


def process_contact(db: Session,
                    contact_data: schemas.ContactCreate) -> schemas.Contact:
    """Main function for processing a contact"""
    lead = crud.get_or_create_lead(
        db=db,
        external_id=contact_data.external_id,
        phone=contact_data.phone,
        email=contact_data.email
    )

    source = crud.get_source_by_bot_id(db, contact_data.source_bot_id)
    if not source:
        raise ValueError(
            f"Source with bot_id '{contact_data.source_bot_id}' not found")

    available_operators = get_available_operators_for_source(db, source.id)

    selected_operator = None
    if available_operators:
        selected_operator = select_operator_by_weights(available_operators)

    contact = crud.create_contact(
        db=db,
        contact=contact_data,
        lead_id=lead.id,
        source_id=source.id,
        operator_id=selected_operator.id if selected_operator else None
    )

    if selected_operator:
        crud.update_operator_load(db, selected_operator.id)

    db_contact = db.query(models.Contact).filter(
        models.Contact.id == contact.id).first()

    return db_contact


def get_distribution_stats(db: Session):
    """Get distribution stats for all operators"""
    stats = db.query(
        models.Source.id.label('source_id'),
        models.Source.name.label('source_name'),
        models.Operator.id.label('operator_id'),
        models.Operator.name.label('operator_name'),
        models.Contact.id.label('contact_id')
    ).join(
        models.Contact, models.Contact.source_id == models.Source.id
    ).outerjoin(
        models.Operator, models.Contact.operator_id == models.Operator.id
    ).all()

    result = {}
    for stat in stats:
        key = f"source_{stat.source_id}_{stat.source_name}"
        if key not in result:
            result[key] = {
                'source_id': stat.source_id,
                'source_name': stat.source_name,
                'operators': {}
            }

        if stat.operator_id:
            operator_key = f"operator_{stat.operator_id}"
            if operator_key not in result[key]['operators']:
                result[key]['operators'][operator_key] = {
                    'operator_id': stat.operator_id,
                    'operator_name': stat.operator_name,
                    'count': 0
                }
            result[key]['operators'][operator_key]['count'] += 1
        else:
            if 'no_operator' not in result[key]:
                result[key]['no_operator'] = {'count': 0}
            result[key]['no_operator']['count'] += 1

    return result