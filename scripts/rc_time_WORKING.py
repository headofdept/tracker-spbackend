#!/usr/bin/env python3
"""
✅ РАБОЧИЙ СКРИПТ: получение правильного времени в RC через changelog.
Парсим структуру fields для поиска переходов в статус RC.
"""

import os
import sys
from datetime import datetime
import logging

logging.basicConfig(level=logging.WARNING)
log = logging.getLogger(__name__)

STARTREK_TOKEN = os.environ.get("STARTREK_TOKEN", "")
if not STARTREK_TOKEN:
    log.error("$STARTREK_TOKEN не установлен")
    sys.exit(1)

try:
    from yandex_tracker_client import TrackerClient
except ImportError:
    log.error("Требуется: pip install yandex-tracker-client")
    sys.exit(1)

import pandas as pd

# ==================== TRACKER CLIENT ====================

tracker = TrackerClient(
    token=STARTREK_TOKEN,
    org_id="0",
    base_url="https://st-api.yandex-team.ru",
)

# ==================== LOAD RC TASKS ====================

log.info("Загружаю данные SPBACKEND...")
df = pd.read_csv('/Users/alex4plus/.osy/tracker_export/SPBACKEND_issues.csv')

rc_tasks = df[df['status'] == 'RC'].copy()
rc_count = len(rc_tasks)

print("\n" + "="*80)
print("✅ ПРАВИЛЬНЫЙ АНАЛИЗ: ВРЕМЯ В СТАТУСЕ RC (через Tracker API)")
print("="*80)

if rc_count == 0:
    print("\n❌ Нет задач в статусе RC")
    exit(0)

print(f"\n📈 RC ЗАДАЧ: {rc_count}")
print(f"🔍 Получаю и парсю changelog...\n")

rc_results = []

for idx, task in enumerate(rc_tasks.iterrows(), 1):
    task_data = task[1]
    task_key = task_data['key']

    try:
        issue = tracker.issues[task_key]

        # ==================== ПАРСИМ CHANGELOG ====================

        changelog = issue.changelog
        if not changelog:
            continue

        changelog_list = list(changelog)

        rc_enter_dt = None
        rc_exit_dt = None

        # Парсим каждую запись в порядке от новой к старой
        for record in reversed(changelog_list):  # От старого к новому

            # Проверяем если есть поля (fields)
            if not hasattr(record, 'fields') or not record.fields:
                continue

            # Ищем изменения статуса в полях
            for field_change in record.fields:
                try:
                    # field_change это dict с keys: field, from, to
                    field = field_change.get('field')
                    from_status = field_change.get('from')
                    to_status = field_change.get('to')

                    # Проверяем если это изменение статуса
                    if field and 'status' in str(field).lower():

                        # Преобразуем статусы в строки
                        from_str = str(from_status) if from_status else None
                        to_str = str(to_status) if to_status else None

                        # Ищем переход в RC
                        if to_str and 'RC' in to_str:
                            if not rc_enter_dt:  # Первый переход в RC (самый ранний)
                                rc_enter_dt = datetime.fromisoformat(
                                    record.updatedAt.replace('Z', '+00:00')
                                )

                        # Ищем переход из RC
                        if from_str and 'RC' in from_str and to_str and 'RC' not in to_str:
                            if not rc_exit_dt:  # Первый выход из RC (самый ранний)
                                rc_exit_dt = datetime.fromisoformat(
                                    record.updatedAt.replace('Z', '+00:00')
                                )

                except Exception as e:
                    pass

        # ==================== РЕЗУЛЬТАТЫ ДЛЯ ЭТОЙ ЗАДАЧИ ====================

        time_in_rc_days = None
        status_str = "❓"

        if rc_enter_dt and rc_exit_dt:
            time_in_rc_days = (rc_exit_dt - rc_enter_dt).total_seconds() / 86400
            status_str = "✅"
            print(f"  [{idx:2}/{rc_count}] {task_key:20} {time_in_rc_days:6.1f} дней  {status_str}")

        elif rc_enter_dt and not rc_exit_dt:
            # Задача в RC сейчас, вышла после нашего периода
            status_str = "⏳"
            print(f"  [{idx:2}/{rc_count}] {task_key:20} (ещё в RC)         {status_str}")

        else:
            # Не нашли информацию
            print(f"  [{idx:2}/{rc_count}] {task_key:20} (нет данных)       ❌")

        rc_results.append({
            'key': task_key,
            'rc_enter_date': rc_enter_dt,
            'rc_exit_date': rc_exit_dt,
            'time_in_rc_days': time_in_rc_days,
            'status': status_str,
        })

    except Exception as e:
        log.warning(f"  [{idx:2}/{rc_count}] {task_key}: Ошибка — {e}")
        print(f"  [{idx:2}/{rc_count}] {task_key:20} (ошибка API)       ⚠️")

# ==================== ИТОГОВАЯ СТАТИСТИКА ====================

print("\n" + "="*80)
print("📊 ИТОГИ")
print("="*80)

results_df = pd.DataFrame(rc_results)

# Задачи с информацией о времени в RC
tasks_with_time = results_df[results_df['time_in_rc_days'].notna()]

if len(tasks_with_time) > 0:
    print(f"\n✅ УСПЕШНО ИЗМЕРЕНО время в RC: {len(tasks_with_time)} задач")

    time_values = tasks_with_time['time_in_rc_days'].values
    print(f"\n⏱️  СТАТИСТИКА:")
    print(f"  Медиана:      {sorted(time_values)[len(time_values)//2]:.1f} дней")
    print(f"  Среднее:      {sum(time_values)/len(time_values):.1f} дней")
    print(f"  Min:          {min(time_values):.1f} дней")
    print(f"  Max:          {max(time_values):.1f} дней")

    print(f"\n🏆 ТОП-10 ЗАДАЧ КОТОРЫЕ ДОЛЬШЕ В RC:")
    slowest = tasks_with_time.nlargest(10, 'time_in_rc_days')
    for idx, row in slowest.iterrows():
        print(f"  {idx+1:2}. {row['key']:20} {row['time_in_rc_days']:6.1f} дней")

    # Распределение
    print(f"\n📊 РАСПРЕДЕЛЕНИЕ ПО ВРЕМЕНИ:")
    buckets = [
        (0, 1, "< 1 дня"),
        (1, 3, "1-3 дня"),
        (3, 7, "3-7 дней"),
        (7, 14, "1-2 недели"),
        (14, 30, "2-4 недели"),
        (30, float('inf'), "> 1 месяца"),
    ]
    for min_d, max_d, label in buckets:
        count = len(tasks_with_time[(tasks_with_time['time_in_rc_days'] >= min_d) &
                                     (tasks_with_time['time_in_rc_days'] < max_d)])
        pct = count / len(tasks_with_time) * 100
        bar = "█" * int(pct / 5)
        print(f"  {label:15} {count:3} ({pct:5.1f}%) {bar}")

else:
    print(f"\n⚠️  Не удалось измерить время в RC ни для одной задачи")
    print(f"   (возможно, задачи уже вышли из RC и информация недоступна)")

tasks_still_in_rc = results_df[results_df['status'] == "⏳"]
if len(tasks_still_in_rc) > 0:
    print(f"\n📋 ЗАДАЧИ КОТОРЫЕ ЕЩЁ В RC (вошли но не вышли):")
    for idx, row in tasks_still_in_rc.iterrows():
        enter = row['rc_enter_date']
        if enter:
            days_now = (datetime.now(enter.tzinfo) - enter).total_seconds() / 86400
            print(f"  • {row['key']:20} в RC с {enter.date()} ({days_now:.0f} дней назад)")

print("\n" + "="*80)
print("✅ АНАЛИЗ ЗАВЕРШЁН")
print("="*80 + "\n")

# Save results
results_df.to_csv('/Users/alex4plus/.osy/tracker_export/RC_TIME_FINAL.csv', index=False)
print(f"📊 Результаты сохранены в: RC_TIME_FINAL.csv\n")
