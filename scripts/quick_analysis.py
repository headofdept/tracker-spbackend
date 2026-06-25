#!/usr/bin/env python3
"""Быстрый анализ SPBACKEND данных."""

import pandas as pd
from collections import Counter

df = pd.read_csv('/Users/alex4plus/.osy/tracker_export/SPBACKEND_issues.csv')

print("=" * 70)
print("АНАЛИЗ СКОРОСТИ ВЫПОЛНЕНИЯ ЗАДАЧ SPBACKEND")
print("=" * 70)

print(f"\n📊 ВСЕГО ЗАДАЧ: {len(df)}")
print(f"📅 Период: {df['created_at'].min()[:10]} — {df['created_at'].max()[:10]}")

# Статусы
print("\n📌 РАСПРЕДЕЛЕНИЕ ПО СТАТУСАМ:")
status_counts = df['status'].value_counts()
for status, count in status_counts.items():
    pct = (count / len(df) * 100)
    bar = "█" * int(pct / 2)
    print(f"  {status:20} {count:4} ({pct:5.1f}%) {bar}")

# Типы задач
print("\n📋 РАСПРЕДЕЛЕНИЕ ПО ТИПАМ ЗАДАЧ:")
type_counts = df['type'].value_counts()
for task_type, count in type_counts.items():
    if pd.isna(task_type):
        continue
    pct = (count / len(df) * 100)
    print(f"  {str(task_type):20} {count:4} ({pct:5.1f}%)")

# Приоритеты
print("\n⚡ РАСПРЕДЕЛЕНИЕ ПО ПРИОРИТЕТАМ:")
priority_counts = df['priority'].value_counts()
for priority, count in priority_counts.items():
    if pd.isna(priority):
        continue
    pct = (count / len(df) * 100)
    print(f"  {str(priority):20} {count:4} ({pct:5.1f}%)")

# Исполнители
print("\n👥 ТОП-10 ИСПОЛНИТЕЛЕЙ:")
assignee_counts = df['assignee'].value_counts()
for i, (assignee, count) in enumerate(assignee_counts.head(10).items(), 1):
    if pd.isna(assignee):
        continue
    pct = (count / len(df) * 100)
    print(f"  {i:2}. {str(assignee)[:35]:35} {count:4} ({pct:5.1f}%)")

# Комментарии (как индикатор активности)
print("\n💬 СТАТИСТИКА КОММЕНТАРИЕВ:")
print(f"  Среднее кол-во: {df['comment_count'].mean():.2f}")
print(f"  Медиана: {df['comment_count'].median():.1f}")
print(f"  Макс: {df['comment_count'].max()}")
print(f"  Без комментариев: {(df['comment_count'] == 0).sum()} задач ({(df['comment_count'] == 0).sum() / len(df) * 100:.1f}%)")

# Разрешение
print("\n✅ СТАТИСТИКА РАЗРЕШЕНИЙ:")
resolution_counts = df['resolution'].value_counts()
for resolution, count in resolution_counts.items():
    if pd.isna(resolution):
        print(f"  (нет разрешения): {count} ({count / len(df) * 100:.1f}%)")
    else:
        print(f"  {resolution:20} {count:4} ({count / len(df) * 100:.1f}%)")

print("\n" + "=" * 70)
print("✅ ДАННЫЕ ЭКСПОРТИРОВАНЫ В: ~/.osy/tracker_export/SPBACKEND_issues.csv")
print("=" * 70)
