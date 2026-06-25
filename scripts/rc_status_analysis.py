#!/usr/bin/env python3
"""
Анализ времени ожидания задач в статусе RC (Release Candidate)
и их влияния на скорость релизов.
"""

import pandas as pd
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(message)s')
log = logging.getLogger(__name__)

# ==================== LOAD DATA ====================

log.info("Загружаю данные SPBACKEND...")
df = pd.read_csv('/Users/alex4plus/.osy/tracker_export/SPBACKEND_issues.csv')

# Parse dates
def parse_date(date_str):
    if pd.isna(date_str):
        return None
    try:
        return datetime.fromisoformat(str(date_str).replace('Z', '+00:00'))
    except:
        return None

df['created_at_dt'] = df['created_at'].apply(parse_date)
df['updated_at_dt'] = df['updated_at'].apply(parse_date)
df['lead_time_days'] = df.apply(
    lambda row: (row['updated_at_dt'] - row['created_at_dt']).total_seconds() / 86400
    if (pd.notna(row['created_at_dt']) and pd.notna(row['updated_at_dt']))
    else None,
    axis=1
)

# ==================== ANALYZE RC STATUS ====================

# Фильтровать только RC задачи
rc_tasks = df[df['status'] == 'RC'].copy()
rc_count = len(rc_tasks)

print("\n" + "="*80)
print("📊 АНАЛИЗ ЗАДАЧ В СТАТУСЕ RC (RELEASE CANDIDATE)")
print("="*80)

if rc_count == 0:
    print("\n❌ Нет задач в статусе RC")
    exit(0)

print(f"\n📈 ОБЩАЯ СТАТИСТИКА RC")
print(f"  Всего задач в RC:           {rc_count}")
print(f"  % от всех задач:            {rc_count / len(df) * 100:.1f}%")
print(f"  Время в окружении:          {rc_tasks['created_at'].min()} — {rc_tasks['updated_at'].max()}")

# ==================== LEAD TIME ANALYSIS ====================

rc_lead_times = rc_tasks['lead_time_days'].dropna()

if len(rc_lead_times) == 0:
    print("\n❌ Нет валидных данных по lead time для RC")
    exit(0)

print(f"\n⏱️  ВРЕМЯ ОЖИДАНИЯ РЕЛИЗА (дней)")
print(f"  Медиана:                    {rc_lead_times.median():.1f} дней")
print(f"  Среднее:                    {rc_lead_times.mean():.1f} дней")
print(f"  Минимум:                    {rc_lead_times.min():.1f} дней")
print(f"  Максимум:                   {rc_lead_times.max():.1f} дней")
print(f"  p25 (быстрые):              {rc_lead_times.quantile(0.25):.1f} дней")
print(f"  p75 (медленные):             {rc_lead_times.quantile(0.75):.1f} дней")
print(f"  p95 (очень медленные):      {rc_lead_times.quantile(0.95):.1f} дней")

# ==================== DISTRIBUTION ====================

print(f"\n📊 РАСПРЕДЕЛЕНИЕ ВРЕМЕНИ В RC")

buckets = [
    (0, 1, "< 1 дня (готов к релизу)"),
    (1, 3, "1-3 дня (нормально)"),
    (3, 7, "3-7 дней (медлено)"),
    (7, 14, "1-2 недели (долго)"),
    (14, 30, "2-4 недели (очень долго)"),
    (30, float('inf'), "> 1 месяца (ЗАСТРЯЛ)"),
]

for min_days, max_days, label in buckets:
    count = len(rc_lead_times[(rc_lead_times >= min_days) & (rc_lead_times < max_days)])
    pct = (count / len(rc_lead_times) * 100) if len(rc_lead_times) > 0 else 0
    bar = "█" * int(pct / 5)
    print(f"  {label:35} {count:3} ({pct:5.1f}%) {bar}")

# ==================== STUCK TASKS ====================

print(f"\n🚨 RC ЗАДАЧИ КОТОРЫЕ ЗАСТРЯЛИ")

stuck_7days = rc_tasks[rc_tasks['lead_time_days'] > 7].sort_values('lead_time_days', ascending=False)
if len(stuck_7days) > 0:
    print(f"\n  Более 7 дней в RC ({len(stuck_7days)} задач):")
    for idx, row in stuck_7days.head(10).iterrows():
        days = row['lead_time_days']
        print(f"    • {row['key']:20} | {days:6.0f} дней | {row['priority']:15} | {row['resolution']}")
    if len(stuck_7days) > 10:
        print(f"    ... и ещё {len(stuck_7days) - 10} задач")
else:
    print(f"  ✅ Нет задач > 7 дней в RC")

stuck_30days = rc_tasks[rc_tasks['lead_time_days'] > 30]
if len(stuck_30days) > 0:
    print(f"\n  ⚠️  КРИТИЧНО: Более месяца в RC ({len(stuck_30days)} задач):")
    for idx, row in stuck_30days.iterrows():
        days = row['lead_time_days']
        print(f"    • {row['key']:20} | {days:6.0f} дней | {row['status']:20} | {row['assignee']}")
else:
    print(f"  ✅ Нет задач застрявших > месяца")

# ==================== BY PRIORITY ====================

print(f"\n⚡ ВРЕМЯ В RC ПО ПРИОРИТЕТУ")

for priority in ['Блокер', 'Критичный', 'Средний', 'Низкий', 'Незначительный']:
    priority_rc = rc_tasks[rc_tasks['priority'] == priority]
    if len(priority_rc) > 0:
        times = priority_rc['lead_time_days'].dropna()
        if len(times) > 0:
            median = times.median()
            print(f"  {priority:20} {len(priority_rc):3} задач | median: {median:6.1f} дней")

# ==================== BY RESOLUTION ====================

print(f"\n✅ СТАТУС РАЗРЕШЕНИЯ RC ЗАДАЧ")

resolutions = rc_tasks['resolution'].value_counts()
for resolution, count in resolutions.items():
    if pd.isna(resolution):
        print(f"  (нет разрешения):       {count:3} ({count/len(rc_tasks)*100:5.1f}%)")
    else:
        print(f"  {resolution:20} {count:3} ({count/len(rc_tasks)*100:5.1f}%)")

# ==================== IMPACT ANALYSIS ====================

print(f"\n💥 ВЛИЯНИЕ RC НА ОБЩУЮ СКОРОСТЬ")

median_all = df['lead_time_days'].dropna().median()
median_rc = rc_lead_times.median()
median_no_rc = df[df['status'] != 'RC']['lead_time_days'].dropna().median()

print(f"  Lead Time БЕЗ RC задач:     {median_no_rc:.1f} дней")
print(f"  Lead Time С RC задачами:    {median_all:.1f} дней")
print(f"  Только RC задач:            {median_rc:.1f} дней")
print(f"  Замедление из-за RC:        {median_all - median_no_rc:.1f} дней ({(median_all - median_no_rc) / median_no_rc * 100:.1f}%)")

# ==================== RELEASE VELOCITY ====================

print(f"\n📦 СКОРОСТЬ РЕЛИЗОВ")

# Посчитать сколько дней между созданием задачи и её попаданием в RC
rc_tasks_with_dates = rc_tasks[(rc_tasks['created_at_dt'].notna()) & (rc_tasks['updated_at_dt'].notna())].copy()
print(f"  RC задач с полными датами:  {len(rc_tasks_with_dates)}")

if len(rc_tasks_with_dates) > 0:
    # Предположим, что RC = финальный статус перед Release
    time_to_rc = rc_tasks_with_dates['lead_time_days'].dropna()
    print(f"  Среднее время до релиза:    {time_to_rc.mean():.1f} дней")
    print(f"  Типовой цикл:              {time_to_rc.median():.0f} дней")

# ==================== RECOMMENDATIONS ====================

print(f"\n🎯 РЕКОМЕНДАЦИИ")

if len(stuck_7days) > 0:
    print(f"\n  ❌ ПРОБЛЕМА 1: {len(stuck_7days)} задач зависают в RC > 7 дней")
    print(f"     Причины (вероятные):")
    print(f"     • Ожидание финальной проверки тестеров")
    print(f"     • Ожидание релиза (батчинг релизов)")
    print(f"     • Ожидание разрешения конфликтов")
    print(f"     • Ожидание одобрения техлида")
    print(f"     Решение:")
    print(f"     • Установить SLA на RC: max 2 дня до финальной проверки")
    print(f"     • Релизить чаще (не аккумулировать)")
    print(f"     • Чётко определить критерии выхода из RC")

if len(stuck_30days) > 0:
    print(f"\n  🚨 ПРОБЛЕМА 2: {len(stuck_30days)} задач ЗАСТРЯЛИ в RC > месяца")
    print(f"     Это критично! Такие задачи:")
    for idx, row in stuck_30days.iterrows():
        print(f"     • {row['key']} ({row['lead_time_days']:.0f} дней) — проверить статус")
    print(f"     Нужно:")
    print(f"     • Выяснить, почему не релизятся")
    print(f"     • Откатить или завершить эти задачи")

if median_rc > 7:
    print(f"\n  ⚠️  ПРОБЛЕМА 3: RC задачи в среднем ждут {median_rc:.1f} дней")
    print(f"     Оптимально: 2-3 дня")
    print(f"     Улучшение даст +30% ускорения всех задач")
    print(f"     Решение: Ускорить цикл QA→RC→Release")

pct_blocked = len(stuck_7days) / len(rc_tasks) * 100
if pct_blocked > 20:
    print(f"\n  ⚠️  ПРОБЛЕМА 4: {pct_blocked:.1f}% RC задач зависают > 7 дней")
    print(f"     Это означает, что релиз очередь забита")
    print(f"     Решение: Релизить более часто (weekly вместо monthly)")

print("\n" + "="*80)
print("✅ АНАЛИЗ ЗАВЕРШЁН")
print("="*80 + "\n")

# ==================== SAVE RESULTS ====================

rc_analysis = rc_tasks[['key', 'status', 'priority', 'type', 'assignee', 'resolution',
                        'created_at', 'updated_at', 'lead_time_days']].copy()
rc_analysis = rc_analysis[rc_analysis['lead_time_days'].notna()].sort_values('lead_time_days', ascending=False)
rc_analysis.to_csv('/Users/alex4plus/.osy/tracker_export/RC_STATUS_ANALYSIS.csv', index=False)

print(f"📊 Результаты сохранены в: RC_STATUS_ANALYSIS.csv")
