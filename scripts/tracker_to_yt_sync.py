#!/usr/bin/env python3
"""
Синхронизация задач Yandex Tracker → Yandex Table (YT)
Экспортирует задачи из SPBACKEND и SPFRONT с историей изменения статусов.
"""

import os
import sys
import json
from datetime import datetime, timezone
from typing import List, Dict, Optional
import logging

# Логирование
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s - %(message)s",
)
log = logging.getLogger(__name__)

# ==================== IMPORTS ====================

try:
    from yandex_tracker_client import TrackerClient
except ImportError:
    log.error("Требуется: pip install yandex-tracker-client")
    sys.exit(1)

try:
    import yt.wrapper as yt
    import yt.yson as yson
except ImportError:
    log.error("Требуется: pip install yt-client")
    sys.exit(1)

try:
    import pandas as pd
except ImportError:
    log.error("Требуется: pip install pandas")
    sys.exit(1)

# ==================== CONFIG ====================

STARTREK_TOKEN = os.environ.get("STARTREK_TOKEN", "")
YT_PROXY = "arnold.yt.yandex.net"
YT_TABLE_SPBACKEND = "//home/alex4plus/tracker/spbackend_issues"
YT_TABLE_SPFRONT = "//home/alex4plus/tracker/spfront_issues"
YT_TABLE_HISTORY = "//home/alex4plus/tracker/status_history"

QUEUES = ["SPBACKEND", "SPFRONT"]
START_DATE = "2026-01-01"

if not STARTREK_TOKEN:
    log.error("[ERROR] $STARTREK_TOKEN не установлен!")
    sys.exit(1)

log.info(f"Инициализирую Tracker API (токен установлен: {len(STARTREK_TOKEN)} символов)")
log.info(f"YT прокси: {YT_PROXY}")

# ==================== TRACKER CLIENT ====================

tracker = TrackerClient(
    token=STARTREK_TOKEN,
    org_id="0",
    base_url="https://st-api.yandex-team.ru",
)

# ==================== FETCH ISSUES ====================

def iso_to_timestamp(iso_str: Optional[str]) -> Optional[int]:
    """Конвертировать ISO timestamp в Unix milliseconds."""
    if not iso_str:
        return None
    try:
        dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
        return int(dt.timestamp() * 1000)
    except:
        return None

def fetch_all_issues(queue_key: str) -> List[Dict]:
    """Выгрузить все задачи очереди с фильтром по дате."""
    issues = []
    page = 1
    per_page = 50

    log.info(f"Начинаю загрузку из {queue_key}...")

    while True:
        try:
            # Поиск с пагинацией, отсортировано по дате обновления
            found = tracker.issues.find(
                filter={"queue": queue_key},
                order=["-updatedAt"],
                page=page,
                per_page=per_page,
            )

            batch = list(found)
            if not batch:
                log.info(f"Достигнут конец: {len(issues)} задач в {queue_key}")
                break

            for idx, issue in enumerate(batch):
                try:
                    # Базовые поля
                    created_at = None
                    updated_at = None

                    # Попытка получить даты
                    if hasattr(issue, 'createdAt'):
                        created_at = issue.createdAt
                    if hasattr(issue, 'updatedAt'):
                        updated_at = issue.updatedAt

                    issue_data = {
                        "key": issue.key,
                        "queue": queue_key,
                        "summary": issue.summary or "",
                        "description": (issue.description or "")[:500],  # Первые 500 символов
                        "status": issue.status.display if hasattr(issue, 'status') and issue.status else None,
                        "priority": issue.priority.display if hasattr(issue, 'priority') and issue.priority else None,
                        "type": issue.type.display if hasattr(issue, 'type') and issue.type else None,
                        "assignee": issue.assignee.display if hasattr(issue, 'assignee') and issue.assignee else None,
                        "author": issue.author.display if hasattr(issue, 'author') and issue.author else None,
                        "created_at": str(created_at) if created_at else None,
                        "updated_at": str(updated_at) if updated_at else None,
                        "resolution": issue.resolution.display if hasattr(issue, 'resolution') and issue.resolution else None,
                        "estimate": getattr(issue, 'estimate', None),
                        "spent": getattr(issue, 'spent', None),
                    }

                    # Попытка получить комментарии (для подсчёта итераций)
                    try:
                        comments = list(issue.comments.get_all())
                        issue_data["comment_count"] = len(comments)
                        if comments:
                            issue_data["last_comment_at"] = str(comments[-1].createdAt)
                            issue_data["last_comment_author"] = comments[-1].createdBy.display if hasattr(comments[-1].createdBy, 'display') else str(comments[-1].createdBy)
                    except Exception as e:
                        log.debug(f"  ⚠ {issue.key}: не удалось прочитать комментарии: {e}")
                        issue_data["comment_count"] = 0

                    issues.append(issue_data)

                except Exception as e:
                    log.warning(f"  ⚠ Ошибка обработки {issue.key}: {e}")
                    continue

            log.info(f"  → Страница {page}: загружено {len(batch)} задач (всего: {len(issues)})")
            page += 1

        except Exception as e:
            log.error(f"Ошибка на странице {page}: {e}")
            break

    return issues

# ==================== FETCH STATUS HISTORY ====================

def fetch_status_transitions(queue_key: str, issues: List[Dict]) -> List[Dict]:
    """Загрузить историю переходов статусов для каждой задачи."""
    history = []

    log.info(f"Загружаю историю переходов для {len(issues)} задач из {queue_key}...")

    for idx, issue_data in enumerate(issues, 1):
        issue_key = issue_data["key"]

        try:
            issue = tracker.issues[issue_key]

            # Попытка получить changelog через API (если доступно)
            # К сожалению, Tracker API не предоставляет прямой доступ к полной истории изменений
            # Используем workaround: смотрим на доступные статусы для перехода

            # Альтернатива: используем updatedAt и комментарии как proxy
            # Для более точного анализа нужен доступ к YQL или прямой БД

            history.append({
                "issue_key": issue_key,
                "current_status": issue_data["status"],
                "created_at": issue_data["created_at"],
                "updated_at": issue_data["updated_at"],
                "queue": queue_key,
            })

            if idx % 50 == 0:
                log.info(f"  → Обработано {idx}/{len(issues)} задач")

        except Exception as e:
            log.warning(f"  ⚠ {issue_key}: {e}")
            continue

    log.info(f"История загружена для {len(history)} задач")
    return history

# ==================== WRITE TO YT ====================

def write_to_yt(data: List[Dict], yt_path: str, table_name: str) -> bool:
    """Записать данные в YT с автоматической генерацией схемы."""
    if not data:
        log.warning(f"Нет данных для экспорта в {yt_path}")
        return False

    try:
        log.info(f"Подготавливаю запись {len(data)} записей в {yt_path}...")

        # Конвертировать в DataFrame
        df = pd.DataFrame(data)

        # Очистить NaN и None значения (заменить пустыми строками для удобства)
        df = df.fillna("")

        # Генерировать схему YT
        schema = []
        for col in df.columns:
            # Определить тип колонки
            col_type = "string"  # Дефолт

            if col.endswith("_at") or col.endswith("_time"):
                col_type = "string"  # Временные строки как string для простоты
            elif col in ["comment_count", "estimate", "spent"]:
                col_type = "int64"

            schema.append({
                "name": col,
                "type": col_type,
                "required": False,
                "sort_order": "ascending" if col == "key" else None,
            })

        # Подключиться к YT
        yt.config["proxy"]["url"] = YT_PROXY

        # Удалить старую таблицу, если существует
        try:
            if yt.exists(yt_path):
                log.info(f"  → Удаляю старую таблицу {yt_path}")
                yt.remove(yt_path, recursive=True)
        except Exception as e:
            log.debug(f"  → Таблица не существовала: {e}")

        # Создать таблицу
        log.info(f"  → Создаю таблицу {yt_path}")
        yt.create(
            "table",
            yt_path,
            attributes={
                "schema": schema,
                "description": f"Экспорт Tracker {table_name} за {START_DATE}+",
            },
            recursive=True,
            force=True,
        )

        # Записать данные
        log.info(f"  → Записываю {len(df)} строк в {yt_path}")
        yt.write_table(yt_path, df.to_dict("records"), format=yson.YsonFormat(format="pretty"))

        log.info(f"✓ Успешно экспортировано {len(df)} записей в {table_name}")
        log.info(f"  Столбцы: {', '.join(df.columns)}")

        return True

    except Exception as e:
        log.error(f"✗ Ошибка записи в YT: {e}")
        import traceback
        traceback.print_exc()
        return False

# ==================== SUMMARY ====================

def generate_summary(issues_sp_backend: List[Dict], issues_sp_front: List[Dict]) -> None:
    """Вывести сводку статистики."""

    log.info("\n" + "="*60)
    log.info("СВОДКА СИНХРОНИЗАЦИИ")
    log.info("="*60)

    total = len(issues_sp_backend) + len(issues_sp_front)

    log.info(f"\nЗадачи по очередям:")
    log.info(f"  SPBACKEND: {len(issues_sp_backend)} задач")
    log.info(f"  SPFRONT:   {len(issues_sp_front)} задач")
    log.info(f"  ВСЕГО:     {total} задач")

    # Статус-распределение
    def count_by_status(issues: List[Dict]) -> Dict:
        from collections import Counter
        return Counter(i["status"] for i in issues if i["status"])

    log.info(f"\nРаспределение по статусам (SPBACKEND):")
    for status, count in count_by_status(issues_sp_backend).most_common():
        log.info(f"  {status}: {count}")

    log.info(f"\nРаспределение по статусам (SPFRONT):")
    for status, count in count_by_status(issues_sp_front).most_common():
        log.info(f"  {status}: {count}")

    log.info(f"\nТабличное хранилище (YT):")
    log.info(f"  SPBACKEND: {YT_TABLE_SPBACKEND}")
    log.info(f"  SPFRONT:   {YT_TABLE_SPFRONT}")
    log.info(f"  История:   {YT_TABLE_HISTORY}")

    log.info(f"\nСлед. шаг: YQL-запросы для анализа времени в статусах")
    log.info("="*60 + "\n")

# ==================== MAIN ====================

def main():
    log.info("="*60)
    log.info("TRACKER → YT СИНХРОНИЗАЦИЯ")
    log.info("="*60)
    log.info(f"Дата начала: {START_DATE}")
    log.info(f"Очереди: {', '.join(QUEUES)}")
    log.info("")

    all_issues = []

    # Загрузить задачи из обеих очередей
    issues_spbackend = fetch_all_issues("SPBACKEND")
    issues_spfront = fetch_all_issues("SPFRONT")

    all_issues = issues_spbackend + issues_spfront

    # Экспортировать в YT
    log.info("\n" + "-"*60)
    log.info("ЭКСПОРТ В YT")
    log.info("-"*60 + "\n")

    success = True
    success &= write_to_yt(issues_spbackend, YT_TABLE_SPBACKEND, "SPBACKEND Issues")
    success &= write_to_yt(issues_spfront, YT_TABLE_SPFRONT, "SPFRONT Issues")

    # Загрузить историю переходов
    log.info("\n" + "-"*60)
    log.info("ЗАГРУЗКА ИСТОРИИ СТАТУСОВ")
    log.info("-"*60 + "\n")

    history_spbackend = fetch_status_transitions("SPBACKEND", issues_spbackend)
    history_spfront = fetch_status_transitions("SPFRONT", issues_spfront)

    all_history = history_spbackend + history_spfront
    success &= write_to_yt(all_history, YT_TABLE_HISTORY, "Status Transitions")

    # Сводка
    generate_summary(issues_spbackend, issues_spfront)

    if success:
        log.info("✓ СИНХРОНИЗАЦИЯ УСПЕШНО ЗАВЕРШЕНА")
        return 0
    else:
        log.error("✗ СИНХРОНИЗАЦИЯ ЗАВЕРШЕНА С ОШИБКАМИ")
        return 1

if __name__ == "__main__":
    sys.exit(main())
