#!/usr/bin/env python3
"""
Анализ времени нахождения задач в статусах на основе Tracker API и CSV.
"""

import os
import json
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
import pandas as pd
from collections import defaultdict
import logging

logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(message)s')
log = logging.getLogger(__name__)

STARTREK_TOKEN = os.environ.get("STARTREK_TOKEN", "")
if not STARTREK_TOKEN:
    log.error("$STARTREK_TOKEN не установлен")
    exit(1)

try:
    from yandex_tracker_client import TrackerClient
except ImportError:
    log.error("Требуется: pip install yandex-tracker-client")
    exit(1)

# ==================== SETUP ====================

tracker = TrackerClient(
    token=STARTREK_TOKEN,
    org_id="0",
    base_url="https://st-api.yandex-team.ru",
)

# Загрузить CSV с общей информацией
df = pd.read_csv('/Users/alex4plus/.osy/tracker_export/SPBACKEND_issues.csv')

# ==================== ANALYZE TIMELINE ====================

def parse_date(date_str):
    """Парсить ISO дату."""
    if pd.isna(date_str):
        return None
    try:
        return datetime.fromisoformat(str(date_str).replace('Z', '+00:00'))
    except:
        return None

def get_status_history(issue_key: str) -> List[Dict]:
    """Получить историю переходов статусов задачи."""
    try:
        issue = tracker.issues[issue_key]
        # К сожалению, Tracker API не предоставляет полную историю статусов напрямую
        # Используем workaround: комментарии часто содержат info о переходах
        history = []

        # Альтернатива: использовать changelog если доступен
        # Для теперь используем created_at и updated_at из CSV
        return history
    except Exception as e:
        log.debug(f"Ошибка получения истории {issue_key}: {e}")
        return []

def calculate_lead_time(created_at, updated_at, status):
    """Рассчитать lead time (время от создания до закрытия)."""
    if pd.isna(created_at) or pd.isna(updated_at):
        return None

    created = parse_date(created_at)
    updated = parse_date(updated_at)

    if not created or not updated:
        return None

    return (updated - created).total_seconds() / 86400  # в днях

# ==================== MAIN ANALYSIS ====================

log.info("Анализирую lead time задач...")

df['created_at_dt'] = df['created_at'].apply(parse_date)
df['updated_at_dt'] = df['updated_at'].apply(parse_date)
df['lead_time_days'] = df.apply(
    lambda row: calculate_lead_time(row['created_at'], row['updated_at'], row['status']),
    axis=1
)

# Фильтровать валидные значения
valid_lead_times = df[df['lead_time_days'].notna()]['lead_time_days']

print("\n" + "="*70)
print("АНАЛИЗ ВРЕМЕНИ ВЫПОЛНЕНИЯ ЗАДАЧ (LEAD TIME)")
print("="*70)

print(f"\n📊 ОБЩАЯ СТАТИСТИКА (всего {len(valid_lead_times)} задач):")
print(f"  Среднее (mean):           {valid_lead_times.mean():.1f} дней")
print(f"  Медиана (p50):            {valid_lead_times.median():.1f} дней")
print(f"  Квартиль 25% (p25):       {valid_lead_times.quantile(0.25):.1f} дней")
print(f"  Квартиль 75% (p75):       {valid_lead_times.quantile(0.75):.1f} дней")
print(f"  Макс (95-й процентиль):   {valid_lead_times.quantile(0.95):.1f} дней")
print(f"  Абсолютный максимум:      {valid_lead_times.max():.0f} дней")
print(f"  Минимум:                  {valid_lead_times.min():.0f} дней")

# Распределение по бакетам
print(f"\n⏱️  РАСПРЕДЕЛЕНИЕ LEAD TIME:")
buckets = [
    (0, 1, "< 1 дня"),
    (1, 3, "1-3 дня"),
    (3, 7, "3-7 дней"),
    (7, 14, "1-2 недели"),
    (14, 30, "2-4 недели"),
    (30, 60, "1-2 месяца"),
    (60, 180, "2-6 месяцев"),
    (180, float('inf'), "> 6 месяцев"),
]

for min_days, max_days, label in buckets:
    count = len(valid_lead_times[(valid_lead_times >= min_days) & (valid_lead_times < max_days)])
    pct = (count / len(valid_lead_times) * 100) if valid_lead_times.any() else 0
    bar = "█" * int(pct / 2)
    print(f"  {label:20} {count:5} ({pct:5.1f}%) {bar}")

# Анализ по статусам
print(f"\n🎯 LEAD TIME ПО ФИНАЛЬНОМУ СТАТУСУ:")
status_lead_times = {}
for status in df['status'].unique():
    if pd.isna(status):
        continue
    status_df = df[df['status'] == status]
    status_times = status_df['lead_time_days'].dropna()

    if len(status_times) > 0:
        status_lead_times[status] = {
            'count': len(status_times),
            'mean': status_times.mean(),
            'median': status_times.median(),
            'p95': status_times.quantile(0.95),
        }

# Сортировать по median
for status, stats in sorted(status_lead_times.items(), key=lambda x: x[1]['median'], reverse=True):
    print(f"  {status:25} median={stats['median']:6.1f}д  mean={stats['mean']:6.1f}д  p95={stats['p95']:6.1f}д  (n={stats['count']:4})")

# Анализ по приоритетам
print(f"\n⚡ LEAD TIME ПО ПРИОРИТЕТУ:")
priority_lead_times = {}
for priority in df['priority'].dropna().unique():
    priority_df = df[df['priority'] == priority]
    priority_times = priority_df['lead_time_days'].dropna()

    if len(priority_times) > 0:
        priority_lead_times[priority] = {
            'count': len(priority_times),
            'mean': priority_times.mean(),
            'median': priority_times.median(),
            'p95': priority_times.quantile(0.95),
        }

for priority, stats in sorted(priority_lead_times.items(), key=lambda x: x[1]['median']):
    print(f"  {priority:20} median={stats['median']:6.1f}д  mean={stats['mean']:6.1f}д  p95={stats['p95']:6.1f}д  (n={stats['count']:4})")

# Анализ по исполнителям (топ разработчиков)
print(f"\n👥 LEAD TIME ПО ИСПОЛНИТЕЛЯМ (топ-10):")
assignee_lead_times = {}
for assignee in df['assignee'].dropna().unique():
    assignee_df = df[df['assignee'] == assignee]
    assignee_times = assignee_df['lead_time_days'].dropna()

    if len(assignee_times) > 3:  # Только те, у кого > 3 задач
        assignee_lead_times[assignee] = {
            'count': len(assignee_times),
            'mean': assignee_times.mean(),
            'median': assignee_times.median(),
        }

for assignee, stats in sorted(assignee_lead_times.items(), key=lambda x: x[1]['median'])[:10]:
    name = str(assignee)[:30]
    print(f"  {name:30} median={stats['median']:6.1f}д  mean={stats['mean']:6.1f}д  (n={stats['count']:4})")

# ==================== INSIGHTS ====================

print("\n" + "="*70)
print("🔍 КЛЮЧЕВЫЕ ВЫВОДЫ")
print("="*70)

median_lt = valid_lead_times.median()
p95_lt = valid_lead_times.quantile(0.95)

if median_lt < 7:
    print("✅ Хороший lead time: медиана < 7 дней")
elif median_lt < 14:
    print("⚠️  Средний lead time: медиана 7-14 дней")
else:
    print("❌ Большой lead time: медиана > 14 дней")

fast_tasks = len(valid_lead_times[valid_lead_times <= 3]) / len(valid_lead_times) * 100
print(f"   Быстрые задачи (≤3 дней): {fast_tasks:.1f}%")

slow_tasks = len(valid_lead_times[valid_lead_times > 60]) / len(valid_lead_times) * 100
print(f"   Долгие задачи (>2 месяцев): {slow_tasks:.1f}%")

print(f"\n📈 Медиана Lead Time по типам:")
for status, stats in sorted(status_lead_times.items(), key=lambda x: x[1]['median'])[:3]:
    print(f"   ✅ {status}: {stats['median']:.0f} дней")

for status, stats in sorted(status_lead_times.items(), key=lambda x: x[1]['median'], reverse=True)[:3]:
    if status != "Закрыт":  # Пропустить если все закрыты
        print(f"   ⚠️  {status}: {stats['median']:.0f} дней")

# Сохранить результаты в CSV
results_df = df[['key', 'status', 'priority', 'assignee', 'created_at', 'updated_at', 'lead_time_days']].copy()
results_df = results_df[results_df['lead_time_days'].notna()].sort_values('lead_time_days', ascending=False)
results_df.to_csv('/Users/alex4plus/.osy/tracker_export/LEAD_TIME_ANALYSIS.csv', index=False)

print(f"\n✅ Результаты сохранены в: ~/.osy/tracker_export/LEAD_TIME_ANALYSIS.csv")
print("="*70)
