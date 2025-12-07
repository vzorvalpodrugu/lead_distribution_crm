import random
from sqlalchemy.orm import Session
from typing import List, Optional, Dict
from app import models, schemas, crud
from sqlalchemy.orm import joinedload


def get_available_operators_for_source(db: Session, source_id: int) -> List[
    Dict]:
    """Получить доступных операторов для источника с учетом лимитов нагрузки"""
    weights = crud.get_weights_for_source(db, source_id)
    available_operators = []

    print(f"DEBUG: Веса для источника {source_id}: {len(weights)} записей")

    for weight_obj in weights:
        operator = crud.get_operator(db, weight_obj.operator_id)

        if not operator:
            print(f"DEBUG: Оператор {weight_obj.operator_id} не найден")
            continue

        # Получаем текущую нагрузку оператора
        current_load = crud.get_operator_active_contacts_count(db, operator.id)

        print(f"DEBUG: Оператор {operator.id} ({operator.name}): "
              f"активен={operator.is_active}, "
              f"нагрузка={current_load}/{operator.load_limit}")

        # Проверяем условия:
        # 1. Оператор активен
        # 2. Текущая нагрузка меньше лимита
        if operator.is_active and current_load < operator.load_limit:
            available_operators.append({
                'operator': operator,
                'weight': weight_obj.weight
            })
            print(
                f"DEBUG: Оператор {operator.id} ДОСТУПЕН, вес {weight_obj.weight}")
        else:
            print(f"DEBUG: Оператор {operator.id} НЕДОСТУПЕН")

    print(f"DEBUG: Доступных операторов: {len(available_operators)}")
    return available_operators


def select_operator_by_weights(available_operators: List[Dict]):
    """Математически точный выбор оператора по весам - ИСПРАВЛЕННАЯ ВЕРСИЯ"""
    if not available_operators:
        return None

    print(f"DEBUG: Выбор из {len(available_operators)} операторов")

    # 1. Считаем сумму весов
    total_weight = sum(op['weight'] for op in available_operators)
    print(f"DEBUG: Сумма весов: {total_weight}")

    # 2. Генерируем случайное число от 0 до total_weight
    rand_value = random.uniform(0,
                                total_weight)  # uniform лучше чем random() * total
    print(f"DEBUG: Случайное значение: {rand_value:.2f}")

    # 3. Находим оператора, чей диапазон содержит rand_value
    cumulative = 0
    for i, op_data in enumerate(available_operators):
        weight = op_data['weight']
        cumulative += weight
        operator = op_data['operator']

        print(
            f"DEBUG: Оператор {operator.id} ({operator.name}): вес {weight}, накопительно {cumulative}")

        # ВАЖНО: rand_value должен быть МЕНЬШЕ cumulative
        if rand_value < cumulative:
            print(
                f"DEBUG: ✓ Выбран оператор {operator.id} (диапазон: {cumulative - weight} - {cumulative})")
            return operator

    # Если не выбрали (маловероятно), возвращаем первого
    print(f"DEBUG: ⚠️  Не выбрано, возвращаем первого")
    return available_operators[0]['operator']

def process_contact(db: Session,
                    contact_data: schemas.ContactCreate) -> schemas.Contact:
    """Основная функция обработки обращения"""
    try:
        # 1. Найти или создать лида
        lead = crud.get_or_create_lead(
            db=db,
            external_id=contact_data.external_id,
            phone=contact_data.phone,
            email=contact_data.email
        )

        # 2. Найти источник по bot_id
        source = crud.get_source_by_bot_id(db, contact_data.source_bot_id)
        if not source:
            raise ValueError(
                f"Source with bot_id '{contact_data.source_bot_id}' not found")

        # 3. Найти доступных операторов для этого источника
        available_operators = get_available_operators_for_source(db, source.id)

        # 4. Выбрать оператора по весам
        selected_operator = None
        if available_operators:
            selected_operator = select_operator_by_weights(
                available_operators)  # ← Исправлено!

        # 5. Создать обращение
        contact = crud.create_contact(
            db=db,
            contact=contact_data,
            lead_id=lead.id,
            source_id=source.id,
            operator_id=selected_operator.id if selected_operator else None
        )

        # 6. Обновить нагрузку оператора (если оператор был назначен)
        if selected_operator:
            crud.update_operator_load(db, selected_operator.id)

        # Получить полный объект контакта для ответа
        db_contact = db.query(models.Contact).filter(
            models.Contact.id == contact.id).first()

        return db_contact

    except Exception as e:
        # Добавь логирование ошибки
        print(f"ERROR in process_contact: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        raise


def get_distribution_stats(db: Session):
    """Получить статистику распределения обращений"""
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

    # Группируем результаты
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