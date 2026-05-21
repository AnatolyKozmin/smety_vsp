"""Создаёт через API заброс «Финальный заезд» по данным меню_орги_2026.xlsx.

Можно запускать на разных средах:
    SMETY_API=http://localhost:8765 python import_final_event.py
По умолчанию: http://127.0.0.1:8765.
"""
import os
import sys
import json
import urllib.request
import urllib.error
import openpyxl

API = os.environ.get("SMETY_API", "http://127.0.0.1:8765")
XLSX = os.path.join(os.path.dirname(__file__), "..", "меню_орги_2026.xlsx")
EVENT_NAME = os.environ.get("EVENT_NAME", "Финальный заезд")
# если задано >0 — на все приёмы пищи поставим portions_override (для забросов с участниками)
PORTIONS = int(os.environ.get("PORTIONS", "0") or 0)
DAYS = ['01.08', '02.08', '03.08', '04.08', '05.08',
        '06.08', '07.08', '08.08', '09.08', '10.08']
MEAL_ORDER = ['Завтрак', 'Обед', 'Ужин', 'Перекус']


def req(method, path, body=None):
    url = API + path
    data = json.dumps(body).encode("utf-8") if body is not None else None
    r = urllib.request.Request(url, data=data, method=method,
                               headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(r) as resp:
            raw = resp.read()
            if not raw:
                return None
            return json.loads(raw)
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "ignore")
        raise SystemExit(f"HTTP {e.code} on {method} {path}: {body}")


def read_xlsx():
    """Возвращает {sheet_name: [(meal_label, [dish_names]), ...]}."""
    wb = openpyxl.load_workbook(XLSX, data_only=True)
    out = {}
    for name in DAYS:
        ws = wb[name]
        rows = list(ws.iter_rows(values_only=True))
        header = rows[0] if rows else []
        dishes_row = rows[1] if len(rows) > 1 else []
        meals = []  # сохраним порядок появления
        n_cols = len(header)
        for i in range(1, n_cols, 2):
            label = header[i]
            if not label:
                continue
            label = str(label).strip()
            if label.lower().startswith('прочее'):
                break
            dish = dishes_row[i] if i < len(dishes_row) else None
            if not dish:
                continue
            dish = str(dish).strip()
            # объединяем повторяющиеся подряд одинаковые приёмы пищи
            if meals and meals[-1][0] == label:
                meals[-1][1].append(dish)
            else:
                meals.append((label, [dish]))
        out[name] = meals
    return out


def main():
    plan = read_xlsx()

    # каталог блюд
    catalog = req("GET", "/api/dishes")
    dish_by_name = {d["name"].strip().lower(): d["id"] for d in catalog}

    def find_dish(name):
        k = name.strip().lower()
        if k in dish_by_name:
            return dish_by_name[k]
        # без кавычек
        k2 = k.strip('"«»""''')
        for cand_name, cand_id in dish_by_name.items():
            if cand_name.strip('"«»""''') == k2:
                return cand_id
        return None

    # проверим, что все блюда найдены — иначе скажем
    missing = set()
    for day, meals in plan.items():
        for _, dishes in meals:
            for d in dishes:
                if find_dish(d) is None:
                    missing.add(d)
    if missing:
        print("⚠️  Не найдены в каталоге:")
        for m in sorted(missing):
            print(f"   • {m!r}")
        print("   Добавьте их в /dishes и повторите.")
        sys.exit(1)

    # Если такой заброс уже есть — удалим (idempotency)
    for e in req("GET", "/api/events") or []:
        if e["name"] == EVENT_NAME:
            print(f"Удаляю старый «{EVENT_NAME}» (id={e['id']})…")
            req("DELETE", f"/api/events/{e['id']}")

    event = req("POST", "/api/events", {"name": EVENT_NAME, "markup_percent": 0})
    eid = event["id"]
    print(f"Создан заброс «{EVENT_NAME}» (id={eid})")

    weekday = {  # 1–10 августа 2026
        '01.08': 'СБ', '02.08': 'ВС', '03.08': 'ПН', '04.08': 'ВТ', '05.08': 'СР',
        '06.08': 'ЧТ', '07.08': 'ПТ', '08.08': 'СБ', '09.08': 'ВС', '10.08': 'ПН',
    }

    for idx, sheet_name in enumerate(DAYS):
        day_name = f"{sheet_name} ({weekday.get(sheet_name, '')})"
        day = req("POST", f"/api/events/{eid}/days", {
            "name": day_name,
            "short_name": weekday.get(sheet_name, ''),
            "sort_order": idx,
        })
        day_id = day["id"]

        # упорядочим приёмы пищи по MEAL_ORDER если возможно
        meals_sorted = sorted(
            plan[sheet_name],
            key=lambda x: MEAL_ORDER.index(x[0]) if x[0] in MEAL_ORDER else 99,
        )

        for m_idx, (mlabel, dishes) in enumerate(meals_sorted):
            meal = req("POST", f"/api/events/days/{day_id}/meals", {
                "name": mlabel, "sort_order": m_idx,
            })
            meal_id = meal["id"]
            for d_name in dishes:
                did = find_dish(d_name)
                req("POST", f"/api/events/meals/{meal_id}/dishes/from-catalog/{did}")
        print(f"  ✓ {day_name}: {sum(len(d) for _, d in meals_sorted)} блюд "
              f"в {len(meals_sorted)} приёмах")

    if PORTIONS > 0:
        req("PUT", f"/api/events/{eid}/set-all-portions?n={PORTIONS}")
        print(f"\nProportions: ставлю {PORTIONS} чел. на все приёмы пищи.")

    print(f"\nГотово. http://localhost:3000/events/{eid}/edit")


if __name__ == "__main__":
    main()
