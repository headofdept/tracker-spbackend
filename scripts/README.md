# 🔧 Вспомогательные скрипты для анализа Tracker

Набор Python и YQL скриптов для загрузки, анализа и экспорта данных из Yandex Tracker.

## 📋 Скрипты

### 1. **tracker_export_analysis.py** (основной)
Загружает все задачи из очередей Tracker, собирает статистику и экспортирует в CSV.

**Использование:**
```bash
python3 scripts/tracker_export_analysis.py
```

**Требует:**
- `$STARTREK_TOKEN` в окружении
- Пакеты: `yandex-tracker-client`, `pandas`

**Выходные данные:**
- `~/.osy/tracker_export/SPBACKEND_issues.csv` (или в текущей директории)
- Статистика по статусам, типам, приоритетам, исполнителям

**Параметры:** Отредактируй в коде:
- `QUEUES` — какие очереди загружать (по умолчанию: SPBACKEND, SPFRONT)
- `START_DATE` — начальная дата (по умолчанию: 2026-01-01)
- `OUTPUT_DIR` — директория для экспорта

---

### 2. **tracker_timeline_analysis.py** (анализ lead time)
Анализирует время выполнения задач (lead time) на основе дат создания и обновления.

**Использование:**
```bash
python3 scripts/tracker_timeline_analysis.py
```

**Требует:**
- CSV файл с задачами (SPBACKEND_issues.csv)
- Пакеты: `pandas`

**Выходные данные:**
- Медиана, среднее, p95 lead time
- Распределение по бакетам времени
- Анализ по статусам, приоритетам, исполнителям
- `LEAD_TIME_ANALYSIS.csv` с lead time для каждой задачи

**Параметры:** Отредактируй в коде:
- Путь к входному CSV файлу (строка 72)
- Бакеты времени в функции `calculate_lead_time()`

---

### 3. **quick_analysis.py** (быстрая аналитика)
Быстрый анализ CSV файла — распределение по статусам, типам, приоритетам, исполнителям.

**Использование:**
```bash
python3 scripts/quick_analysis.py
```

**Требует:**
- CSV файл: `SPBACKEND_issues.csv` (в текущей директории)
- Пакет: `pandas`

**Выходные данные:**
- Консольный отчёт с таблицами и гистограммами
- Быстрая проверка статистики без долгого анализа

---

### 4. **tracker_to_yt_sync.py** (синхронизация в YT)
Экспортирует данные из Tracker в Yandex Table (YT) для анализа через YQL.

**Использование:**
```bash
python3 scripts/tracker_to_yt_sync.py
```

**Требует:**
- `$STARTREK_TOKEN` в окружении
- `$YT_TOKEN` в окружении
- Пакеты: `yandex-tracker-client`, `yt-client`, `pandas`

**Выходные данные:**
- Таблицы в YT:
  - `//home/alex4plus/tracker/spbackend_issues`
  - `//home/alex4plus/tracker/spfront_issues`
  - `//home/alex4plus/tracker/status_history`

**Параметры:** Отредактируй в коде:
- `YT_PROXY` — YT кластер (по умолчанию: arnold.yt.yandex.net)
- `YT_TABLE_*` — пути к таблицам в YT
- `QUEUES` — какие очереди экспортировать

**⚠️ Статус:** Требует `yt-client` SDK (не доступен через pip, нужна установка через Яндекс инструменты)

---

### 5. **tracker_status_analysis.yql** (YQL запрос)
YQL запрос для анализа времени нахождения в статусах (если данные в YT).

**Использование:**
```bash
yql --proxy arnold.yt.yandex.net --format pretty < scripts/tracker_status_analysis.yql
```

**Требует:**
- Данные в Yandex Table (YT)
- YQL CLI инструмент

**Выходные данные:**
- Таблица с issue_key, status, duration, бакет времени

---

## 🚀 Быстрый старт

### Загрузить и проанализировать данные с нуля:

```bash
# 1. Убедиться, что токен установлен
echo $STARTREK_TOKEN

# 2. Загрузить данные из Tracker
python3 scripts/tracker_export_analysis.py
# → Создаёт SPBACKEND_issues.csv

# 3. Быстрая проверка статистики
python3 scripts/quick_analysis.py
# → Выводит таблицы с распределением

# 4. Детальный анализ lead time
python3 scripts/tracker_timeline_analysis.py
# → Создаёт LEAD_TIME_ANALYSIS.csv + отчёт в консоль
```

### Анализировать существующий CSV файл:

```bash
# Скопировать CSV в текущую директорию
cp SPBACKEND_issues.csv .

# Запустить анализ
python3 scripts/quick_analysis.py
python3 scripts/tracker_timeline_analysis.py
```

---

## 📦 Зависимости

Создай `requirements.txt` и установи:

```bash
pip install -r requirements.txt
```

**Содержимое requirements.txt:**
```
yandex-tracker-client>=10.0.0
pandas>=1.3.0
```

**Опционально** (для синхронизации в YT):
- `yt-client` (требует Яндекс инструменты)

---

## 🔐 Требования к окружению

### STARTREK_TOKEN
Требуется для загрузки данных из Tracker.

Получи токен:
1. Перейди на https://st.yandex-team.ru/settings/oauth-tokens
2. Создай новый OAuth токен
3. Сохрани в `~/.osy-tokens.sh`:
```bash
export STARTREK_TOKEN="your_token_here"
```

Или установи вручную:
```bash
export STARTREK_TOKEN="your_token_here"
python3 scripts/tracker_export_analysis.py
```

### YT_TOKEN (опционально)
Требуется только если используешь `tracker_to_yt_sync.py`.

---

## 🐛 Решение проблем

### "Требуется: pip install yandex-tracker-client"
```bash
pip install yandex-tracker-client
```

### "$STARTREK_TOKEN не установлен"
```bash
export STARTREK_TOKEN="your_token"
python3 scripts/tracker_export_analysis.py
```

### "ModuleNotFoundError: No module named 'pandas'"
```bash
pip install pandas
```

### Timeout при загрузке SPFRONT
Скрипт может медленно работать для больших очередей. Это нормально — просто жди или модифицируй:
- Уменьши `per_page` в скрипте (меньше задач за раз)
- Или загружай по одной очереди

### YQL "command not found"
YQL CLI не установлен на macOS по умолчанию. Используй вместо этого Python скрипты.

---

## 📊 Пример использования

```bash
# Загрузить данные
python3 scripts/tracker_export_analysis.py
# Выведет статистику в консоль и создаст CSV

# Проверить результат
python3 scripts/quick_analysis.py
# Выведет быструю аналитику

# Детальный анализ lead time
python3 scripts/tracker_timeline_analysis.py
# Создаст LEAD_TIME_ANALYSIS.csv для дальнейшего анализа в Excel

# Теперь в директории есть:
# - SPBACKEND_issues.csv (779 KB) ← полный экспорт
# - LEAD_TIME_ANALYSIS.csv (418 KB) ← анализ времени
```

---

## 🎯 Что дальше

После запуска скриптов:

1. **Откройи CSV файлы в Excel/Google Sheets** для интерактивного анализа
2. **Используй LEAD_TIME_ANALYSIS.csv** для фильтрации долгих задач:
   - Сортируй по `lead_time_days` DESC
   - Фильтруй > 180 дней (6+ месяцев)
   - Посмотри, почему эти задачи так долго выполняются
3. **Добавь свои метрики** в скрипты для анализа под свои нужды

---

## 📝 Модификация скриптов

Скрипты написаны так, чтобы легко модифицировать:

### Добавить новую метрику в анализ:
В `tracker_export_analysis.py` добавь строку в функцию `fetch_all_issues()`:
```python
issue_data["my_custom_field"] = issue.custom_field if hasattr(issue, 'custom_field') else None
```

### Изменить фильтр задач:
В `tracker_export_analysis.py` найди `filter={"queue": queue_key}` и добавь условия:
```python
filter={
    "queue": queue_key,
    "status": "Закрыт",  # Только закрытые
    "created": {"from": "2026-01-01"}  # С января 2026
}
```

---

## 🔗 Связанные файлы

- `../README.md` — основной README проекта
- `../TIMELINE_ANALYSIS_REPORT.md` — детальный анализ результатов
- `../ANALYSIS_REPORT.md` — общая статистика

---

*Скрипты созданы: 2026-06-25*  
*Для использования требуется: Python 3.7+, $STARTREK_TOKEN*
