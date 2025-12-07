import requests
import time
import uuid

BASE_URL = "http://localhost:8000"


def test_without_limits():
    print("ТЕСТ БЕЗ ЛИМИТОВ НАГРУЗКИ")
    print("=" * 60)

    # 1. Создаем операторов с ОГРОМНЫМИ лимитами
    print("1. Создаем операторов без ограничений...")

    ops = []
    for i, (name, weight) in enumerate(
            [("25% оператор", 1), ("75% оператор", 3)], 1):
        op_data = {"name": name, "is_active": True,
                   "load_limit": 1000}
        resp = requests.post(f"{BASE_URL}/operators/", json=op_data)
        if resp.status_code == 200:
            ops.append(resp.json())
            print(f"   ✓ {name}: вес {weight}, лимит 1000")

    if len(ops) < 2:
        return

    # 2. Создаем источник
    bot_id = f"no_limit_{uuid.uuid4().hex[:8]}"

    print(f"\n2. Создаем источник (bot_id: {bot_id})...")
    source_data = {"name": "No Limit Bot", "bot_id": bot_id}
    resp = requests.post(f"{BASE_URL}/sources/", json=source_data)

    if resp.status_code != 200:
        print(f"✗ Ошибка: {resp.text[:100]}")
        return

    source = resp.json()
    source_id = source['id']

    # Назначаем веса 1:3
    print("\n3. Назначаем веса 1:3...")
    weights = [
        {"operator_id": ops[0]['id'], "source_id": source_id, "weight": 1},
        {"operator_id": ops[1]['id'], "source_id": source_id, "weight": 3},
    ]

    for w in weights:
        requests.post(f"{BASE_URL}/source-weights/", json=w)

    #Тест на 40 обращений
    print("\n4. Тестируем 40 обращений (без ограничений)...")
    stats = {ops[0]['id']: 0, ops[1]['id']: 0}

    for i in range(40):
        contact = {
            "external_id": f"nolimit_{i}",
            "source_bot_id": bot_id,
            "message": f"Тест без лимитов #{i}"
        }

        resp = requests.post(f"{BASE_URL}/contacts/", json=contact)
        if resp.status_code == 200:
            data = resp.json()
            if data.get('operator'):
                op_id = data['operator']['id']
                stats[op_id] += 1
                op_name = data['operator']['name']
                print(f"   {i:2d}: {op_name}")
        else:
            print(f"   {i:2d}: ✗ Ошибка")

    #Анализ
    print("\n5. Результаты (без ограничений):")
    total = sum(stats.values())

    if total > 0:
        op1_percent = stats[ops[0]['id']] / total * 100
        op2_percent = stats[ops[1]['id']] / total * 100

        print(f"   Всего: {total} обращений")
        print(
            f"   {ops[0]['name']}: {stats[ops[0]['id']]} ({op1_percent:.1f}%)")
        print(
            f"   {ops[1]['name']}: {stats[ops[1]['id']]} ({op2_percent:.1f}%)")

        # Проверяем
        expected_op1 = total * 0.25
        expected_op2 = total * 0.75

        diff1 = abs(stats[ops[0]['id']] - expected_op1)
        diff2 = abs(stats[ops[1]['id']] - expected_op2)

        if diff1 <= 5 and diff2 <= 15:
            print(f"Распределение правильное!")
        else:
            print(f"Отклонение: {diff1:.1f} и {diff2:.1f}")

    # Проверяем нагрузку
    print("\n6. Итоговая нагрузка:")
    for op in ops:
        resp = requests.get(f"{BASE_URL}/operators/{op['id']}")
        if resp.status_code == 200:
            op_status = resp.json()
            print(
                f"   {op_status['name']}: {op_status['current_load']}/{op_status['load_limit']}")

    print("\n" + "=" * 60)
    print("ТЕСТ ЗАВЕРШЕН!")


if __name__ == "__main__":
    test_without_limits()