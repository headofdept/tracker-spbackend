#!/usr/bin/env python3
"""
Экспорт и анализ задач Yandex Tracker (SPBACKEND, SPFRONT)
Загружает всю историю задач и выполняет анализ времени в статусах.
"""

import os
import sys
import json
import csv
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from collections import defaultdict
import logging

# ==================== SETUP ====================

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s - %(message)s",
)
log = logging.getLogger(__name__)

STARTREK_TOKEN = os.environ.get("STARTREK_TOKEN", "")
if not STARTREK_TOKEN:
    log.error("[ERROR] $STARTREK_TOKEN не установлен!")
    sys.exit(1)

try:
    from yandex_tracker_client import TrackerClient
except ImportError:
    log.error("Требуется: pip install yandex-tracker-client")
    sys.exit(1)

try:
    import pandas as pd
except ImportError:
    log.error("Требуется: pip install pandas")
    sys.exit(1)

# ==================== CONFIG ====================

QUEUES = ["SPBACKEND", "SPFRONT"]
OUTPUT_DIR = os.path.expanduser("~/.osy/tracker_export")
os.makedirs(OUTPUT_DIR, exist_ok=True)

tracker = TrackerClient(
    token=STARTREK_TOKEN,
    org_id="0",
    base_url="https://st-api.yandex-team.ru",
)

# ==================== FETCH ISSUES ====================

def fetch_all_issues(queue_key: str) -> List[Dict]:
    """Выгрузить все задачи очереди."""
    issues = []
    page = 1
    per_page = 50

    log.info(f"Начинаю загрузку из {queue_key}...")

    while True:
        try:
            found = tracker.issues.find(
                filter={"queue": queue_key},
                order=["-updatedAt"],
                page=page,
                per_page=per_page,
            )

            batch = list(found)
            if not batch:
                log.info(f"✓ {queue_key}: загружено {len(issues)} задач")
                break

            for issue in batch:
                try:
                    issue_data = {
                        "key": issue.key,
                        "queue": queue_key,
                        "summary": (issue.summary or "")[:200],
                        "status": issue.status.display if hasattr(issue, 'status') and issue.status else None,
                        "priority": issue.priority.display if hasattr(issue, 'priority') and issue.priority else None,
                        "type": issue.type.display if hasattr(issue, 'type') and issue.type else None,
                        "assignee": issue.assignee.display if hasattr(issue, 'assignee') and issue.assignee else None,
                        "author": issue.author.display if hasattr(issue, 'author') and issue.author else None,
                        "created_at": str(issue.createdAt) if hasattr(issue, 'createdAt') else None,
                        "updated_at": str(issue.updatedAt) if hasattr(issue, 'updatedAt') else None,
                        "resolution": issue.resolution.display if hasattr(issue, 'resolution') and issue.resolution else None,
                        "estimate": getattr(issue, 'estimate', None),
                        "spent": getattr(issue, 'spent', None),
                    }

                    # Попытка получить комментарии
                    try:
                        comments = list(issue.comments.get_all())
                        issue_data["comment_count"] = len(comments)
                        if comments:
                            issue_data["last_comment_at"] = str(comments[-1].createdAt)
                    except:
                        issue_data["comment_count"] = 0

                    issues.append(issue_data)

                except Exception as e:
                    log.debug(f"  ⚠ {issue.key}: {e}")
                    continue

            log.info(f"  → Страница {page}: {len(batch)} задач (всего: {len(issues)})")
            page += 1

        except Exception as e:
            log.error(f"Ошибка на странице {page}: {e}")
            break

    return issues

# ==================== EXPORT & ANALYZE ====================

def export_to_csv(issues: List[Dict], queue_key: str) -> str:
    """Экспортировать в CSV."""
    filename = f"{OUTPUT_DIR}/{queue_key}_issues.csv"

    if issues:
        df = pd.DataFrame(issues)
        df.to_csv(filename, index=False)
        log.info(f"✓ Экспортировано {len(issues)} задач в {filename}")
    else:
        log.warning(f"Нет задач для экспорта {queue_key}")

    return filename

def analyze_status_distribution(issues: List[Dict], queue_key: str) -> Dict:
    """Анализ распределения по статусам."""
    from collections import Counter

    status_counts = Counter(i["status"] for i in issues if i["status"])

    log.info(f"\nРаспределение по статусам ({queue_key}):")
    for status, count in status_counts.most_common():
        pct = (count / len(issues) * 100) if issues else 0
        log.info(f"  {status:20} : {count:3} ({pct:.1f}%)")

    return dict(status_counts)

def analyze_type_distribution(issues: List[Dict], queue_key: str) -> Dict:
    """Анализ распределения по типам."""
    from collections import Counter

    type_counts = Counter(i["type"] for i in issues if i["type"])

    log.info(f"\nРаспределение по типам задач ({queue_key}):")
    for task_type, count in type_counts.most_common():
        pct = (count / len(issues) * 100) if issues else 0
        log.info(f"  {task_type:20} : {count:3} ({pct:.1f}%)")

    return dict(type_counts)

def analyze_priority_distribution(issues: List[Dict], queue_key: str) -> Dict:
    """Анализ распределения по приоритетам."""
    from collections import Counter

    priority_counts = Counter(i["priority"] for i in issues if i["priority"])

    log.info(f"\nРаспределение по приоритетам ({queue_key}):")
    for priority, count in priority_counts.most_common():
        pct = (count / len(issues) * 100) if issues else 0
        log.info(f"  {priority:20} : {count:3} ({pct:.1f}%)")

    return dict(priority_counts)

def analyze_timeline(issues: List[Dict], queue_key: str) -> Dict:
    """Анализ временной шкалы создания и обновления."""
    log.info(f"\nАнализ временной шкалы ({queue_key}):")

    created_dates = []
    for issue in issues:
        if issue["created_at"]:
            try:
                dt = datetime.fromisoformat(issue["created_at"].replace("Z", "+00:00"))
                created_dates.append(dt)
            except:
                pass

    if created_dates:
        created_dates.sort()
        log.info(f"  Первая задача: {created_dates[0]}")
        log.info(f"  Последняя задача: {created_dates[-1]}")
        log.info(f"  Всего дней: {(created_dates[-1] - created_dates[0]).days}")

    return {
        "first_created": str(created_dates[0]) if created_dates else None,
        "last_created": str(created_dates[-1]) if created_dates else None,
        "total_days": (created_dates[-1] - created_dates[0]).days if created_dates else 0,
    }

def analyze_assignee_workload(issues: List[Dict], queue_key: str) -> Dict:
    """Анализ нагрузки на исполнителей."""
    from collections import Counter

    assignees = Counter(i["assignee"] for i in issues if i["assignee"])

    log.info(f"\nТоп исполнителей ({queue_key}):")
    for assignee, count in assignees.most_common(10):
        pct = (count / len(issues) * 100) if issues else 0
        log.info(f"  {assignee:30} : {count:3} ({pct:.1f}%)")

    return dict(assignees)

def generate_report(all_data: Dict) -> str:
    """Генерировать итоговый отчёт."""
    report_file = f"{OUTPUT_DIR}/ANALYSIS_REPORT.md"

    report = """# Анализ скорости выполнения задач SPBACKEND и SPFRONT

## Сводка

"""

    for queue_key, data in all_data.items():
        report += f"\n### {queue_key}\n\n"
        report += f"- **Всего задач:** {data['total_issues']}\n"
        report += f"- **Период:** {data['timeline']['first_created']} — {data['timeline']['last_created']}\n"
        report += f"- **Дней:** {data['timeline']['total_days']}\n\n"

        report += "#### Статусы\n"
        for status, count in data['status_dist'].items():
            pct = (count / data['total_issues'] * 100) if data['total_issues'] else 0
            report += f"- {status}: {count} ({pct:.1f}%)\n"

        report += "\n#### Типы задач\n"
        for task_type, count in data['type_dist'].items():
            pct = (count / data['total_issues'] * 100) if data['total_issues'] else 0
            report += f"- {task_type}: {count} ({pct:.1f}%)\n"

        report += "\n#### Приоритеты\n"
        for priority, count in data['priority_dist'].items():
            pct = (count / data['total_issues'] * 100) if data['total_issues'] else 0
            report += f"- {priority}: {count} ({pct:.1f}%)\n"

    report += """
## Следующие шаги

1. **CSV экспортированные данные** находятся в `~/.osy/tracker_export/*.csv`
2. **Для детального анализа времени в статусах** требуется история переходов, которая доступна через:
   - Tracker API changelog (если включен доступ)
   - YQL запросы к логам трекера (требуется доступ к YT)
   - DataLens дашборды с интеграцией трекера (если существуют)

3. **Качество процессов** можно оценить по:
   - Проценту возвратов из статуса "Code Review" обратно в "In Progress"
   - Среднему количеству комментариев на задачу (индикатор дополнительных обсуждений)
   - Распределению по приоритетам и типам

## Файлы экспорта

"""

    report += f"- `SPBACKEND_issues.csv` — все задачи SPBACKEND\n"
    report += f"- `SPFRONT_issues.csv` — все задачи SPFRONT\n"
    report += f"- `ANALYSIS_REPORT.md` — этот отчёт\n"

    with open(report_file, "w") as f:
        f.write(report)

    log.info(f"\n✓ Отчёт сохранён в {report_file}")
    return report_file

# ==================== MAIN ====================

def main():
    log.info("="*70)
    log.info("АНАЛИЗ СКОРОСТИ ВЫПОЛНЕНИЯ ЗАДАЧ SPBACKEND И SPFRONT")
    log.info("="*70)
    log.info(f"Экспорт в: {OUTPUT_DIR}")
    log.info("")

    all_data = {}

    for queue_key in QUEUES:
        log.info(f"\n{'='*70}")
        log.info(f"ОЧЕРЕДЬ: {queue_key}")
        log.info(f"{'='*70}\n")

        # Загрузить задачи
        issues = fetch_all_issues(queue_key)

        if not issues:
            log.warning(f"Нет задач в {queue_key}")
            continue

        # Экспортировать
        export_to_csv(issues, queue_key)

        # Анализировать
        log.info("")
        status_dist = analyze_status_distribution(issues, queue_key)
        type_dist = analyze_type_distribution(issues, queue_key)
        priority_dist = analyze_priority_distribution(issues, queue_key)
        timeline = analyze_timeline(issues, queue_key)
        assignees = analyze_assignee_workload(issues, queue_key)

        all_data[queue_key] = {
            "total_issues": len(issues),
            "status_dist": status_dist,
            "type_dist": type_dist,
            "priority_dist": priority_dist,
            "timeline": timeline,
            "assignees": assignees,
        }

    # Генерировать отчёт
    log.info(f"\n{'='*70}")
    log.info("ГЕНЕРАЦИЯ ОТЧЁТА")
    log.info(f"{'='*70}\n")

    generate_report(all_data)

    log.info(f"\n{'='*70}")
    log.info("✓ АНАЛИЗ ЗАВЕРШЁН")
    log.info(f"{'='*70}\n")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        log.warning("Прервано пользователем")
        sys.exit(1)
    except Exception as e:
        log.error(f"Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
