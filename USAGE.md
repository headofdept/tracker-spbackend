# 📖 Инструкция по использованию проекта

Полное руководство по работе с проектом анализа Tracker SPBACKEND.

## 🚀 Быстрый старт (5 минут)

### 1️⃣ Установить зависимости
```bash
cd ~/Documents/tracker-spbackend
make install
```

Или вручную:
```bash
pip install -r requirements.txt
```

### 2️⃣ Загрузить данные (требует $STARTREK_TOKEN)
```bash
export STARTREK_TOKEN="your_oauth_token"
make export
```

Это создаст `SPBACKEND_issues.csv` с 3000+ задачами.

### 3️⃣ Анализировать данные
```bash
make analyze      # Быстрый обзор
make timeline     # Детальный анализ lead time
make all          # Всё вместе
```

### 4️⃣ Прочитать результаты
- Смотри `README.md` — обзор находок
- Смотри `TIMELINE_ANALYSIS_REPORT.md` — детальный план действий
- Открой `LEAD_TIME_ANALYSIS.csv` в Excel для интерактивного анализа

---

## 🔐 Получить STARTREK_TOKEN

### Способ 1: OAuth токен (рекомендуется)
1. Открой https://st.yandex-team.ru/settings/oauth-tokens
2. Нажми "Создать новый токен"
3. Выбери scope: `tracker:manage`
4. Скопируй токен

### Способ 2: Сохранить в файл (для всех скриптов)
```bash
# Создай файл с токеном
echo 'export STARTREK_TOKEN="your_token_here"' >> ~/.osy-tokens.sh

# Источни перед запуском скриптов
source ~/.osy-tokens.sh
python3 scripts/tracker_export_analysis.py
```

### Способ 3: Передать как переменную окружения
```bash
STARTREK_TOKEN="your_token" python3 scripts/tracker_export_analysis.py
```

---

## 📊 Сценарии использования

### Сценарий A: Первый запуск анализа
```bash
cd ~/Documents/tracker-spbackend

# 1. Установить зависимости (один раз)
pip install -r requirements.txt

# 2. Загрузить свежие данные из Tracker
STARTREK_TOKEN="your_token" python3 scripts/tracker_export_analysis.py

# 3. Быстро проверить статистику
python3 scripts/quick_analysis.py

# 4. Детальный анализ lead time
python3 scripts/tracker_timeline_analysis.py

# 5. Открыть результаты в текстовом редакторе
cat TIMELINE_ANALYSIS_REPORT.md
```

### Сценарий B: Еженедельное обновление данных
```bash
# Обновить данные (быстрый способ с Makefile)
make export analyze timeline

# Или вручную
make all
```

### Сценарий C: Анализ существующего CSV файла
```bash
# Если уже есть SPBACKEND_issues.csv
python3 scripts/quick_analysis.py
python3 scripts/tracker_timeline_analysis.py

# Или с Makefile
make analyze timeline
```

### Сценарий D: Модифицировать анализ под свои нужды
```bash
# 1. Открыть скрипт в редакторе
vim scripts/tracker_timeline_analysis.py

# 2. Найти функцию analyze_* и модифицировать
# 3. Запустить снова
python3 scripts/tracker_timeline_analysis.py
```

---

## 📁 Структура файлов

```
tracker-spbackend/
├── README.md                          ← Обзор проекта
├── TIMELINE_ANALYSIS_REPORT.md        ← Детальный анализ
├── ANALYSIS_REPORT.md                 ← Общая статистика
│
├── SPBACKEND_issues.csv               ← Данные (создаётся при export)
├── LEAD_TIME_ANALYSIS.csv             ← Анализ lead time (создаётся)
│
├── scripts/                           ← Вспомогательные скрипты
│   ├── README.md                      ← Документация скриптов
│   ├── tracker_export_analysis.py     ← Основной скрипт (загрузка)
│   ├── quick_analysis.py              ← Быстрый анализ
│   ├── tracker_timeline_analysis.py   ← Анализ lead time
│   ├── tracker_to_yt_sync.py          ← Синхронизация в YT (опционально)
│   └── tracker_status_analysis.yql    ← YQL запрос (опционально)
│
├── requirements.txt                   ← Python зависимости
├── Makefile                           ← Удобные команды
├── .gitignore                         ← Git конфигурация
└── USAGE.md                           ← Эта файл
```

---

## 🔍 Что искать в результатах

### После `make export`
- Выведет статистику в консоль:
  - Распределение по статусам
  - Распределение по типам задач
  - Нагрузка на разработчиков
  - Другие метрики

### После `make analyze`
- Быстрый обзор CSV файла:
  - Всего задач
  - Без комментариев (%)
  - Макс комментариев
  - Статистика разрешения

### После `make timeline`
- Детальный отчёт lead time:
  - Медиана, среднее, p95 дней
  - Распределение по бакетам времени
  - Анализ по статусам, приоритетам, исполнителям
  - CSV файл для Excel анализа

---

## 🛠️ Частые вопросы и решение проблем

### Q: "ModuleNotFoundError: No module named 'yandex_tracker_client'"
**A:** Установи зависимости:
```bash
pip install -r requirements.txt
```

### Q: "STARTREK_TOKEN не установлен"
**A:** Передай токен явно:
```bash
STARTREK_TOKEN="your_token" make export
```

### Q: "SPBACKEND_issues.csv не найден"
**A:** Сначала загрузи данные:
```bash
make export
```

### Q: Скрипт медленно работает (timeout)
**A:** Это нормально для 3000+ задач. Просто жди. Если хочешь ускорить:
- Загружай по одной очереди (отредактируй QUEUES в скрипте)
- Или уменьши per_page в скрипте (меньше задач за раз)

### Q: Как загрузить SPFRONT вместо SPBACKEND?
**A:** Отредактируй скрипт:
```python
# В tracker_export_analysis.py строка ~71
QUEUES = ["SPFRONT"]  # Вместо ["SPBACKEND", "SPFRONT"]
```

### Q: Как экспортировать в формате Excel вместо CSV?
**A:** В скрипте замени `.to_csv()` на `.to_excel()`:
```python
# В tracker_export_analysis.py строка ~120
df.to_excel(filename)  # Требует: pip install openpyxl
```

### Q: Я хочу анализировать другие поля (не created_at/updated_at)
**A:** Добавь их в `fetch_all_issues()` функции:
```python
issue_data["my_field"] = issue.my_field if hasattr(issue, 'my_field') else None
```

---

## 📈 Следующие шаги после анализа

### Неделя 1: Понимание проблем
1. ✅ Запусти `make all` — получи исходные данные
2. ✅ Прочитай `TIMELINE_ANALYSIS_REPORT.md` — поймёшь проблемы
3. ✅ Скопируй `LEAD_TIME_ANALYSIS.csv` в Excel
4. ✅ Фильтруй и сортируй: покажи техлиду

### Неделя 2-3: Планирование
1. ✅ Обсудите 5 критичных проблем с командой
2. ✅ Выберите top-3 для решения
3. ✅ Запланируйте метрики для мониторинга

### Месяц 1: Исполнение
1. ✅ Реализуйте SLA на code review
2. ✅ Распределите нагрузку
3. ✅ Запустите еженедельный мониторинг: `make all`

### Квартал: Оптимизация
1. ✅ Отслеживайте KPI (см. TIMELINE_ANALYSIS_REPORT.md)
2. ✅ Каждые 2 недели обновляйте анализ: `make all`
3. ✅ Корректируйте процессы на основе данных

---

## 🔧 Кастомизация скриптов

### Добавить новую очередь
В `scripts/tracker_export_analysis.py`:
```python
QUEUES = ["SPBACKEND", "SPFRONT", "YOUR_QUEUE"]
```

### Изменить дату начала анализа
В скриптах найди `START_DATE` и измени:
```python
START_DATE = "2025-01-01"  # Вместо 2026-01-01
```

### Добавить фильтр по статусу
В `tracker_export_analysis.py` в функции `fetch_all_issues()`:
```python
filter={
    "queue": queue_key,
    "status": "Закрыт"  # Только закрытые
}
```

### Экспортировать дополнительные поля
В `tracker_export_analysis.py` добавь строку в `issue_data`:
```python
issue_data["parent_key"] = getattr(issue, 'parent', {}).get('key', None)
issue_data["links"] = len(getattr(issue, 'links', []))
```

---

## 📊 Использование в Excel/Google Sheets

### Импортировать CSV:
1. Открой Excel/Google Sheets
2. File → Open → выбери `SPBACKEND_issues.csv` или `LEAD_TIME_ANALYSIS.csv`
3. Готово!

### Фильтровать долгие задачи:
1. Открой `LEAD_TIME_ANALYSIS.csv`
2. Отсортируй по `lead_time_days` (DESC)
3. Фильтруй > 180 дней
4. Посмотри, почему эти задачи так долго выполняются

### Создать сводную таблицу (pivot):
1. Выдели все данные
2. Insert → Pivot Table
3. Rows: assignee, Columns: status, Values: COUNT()
4. Посмотри распределение нагрузки

---

## 🚀 Автоматизация еженедельного анализа

### С Cron (на macOS/Linux):
```bash
# Открой crontab
crontab -e

# Добавь строку (каждый понедельник в 9 утра)
0 9 * * 1 cd ~/Documents/tracker-spbackend && STARTREK_TOKEN="your_token" make all

# Сохрани и выйди
```

### С GitHub Actions (если запушишь в приватный репо):
1. Создай `.github/workflows/analyze.yml`
2. Добавь токен как secret
3. Запусти анализ автоматически

---

## 📝 Вещи, которые стоит знать

1. **Скрипты требуют интернет** — загружают данные из Tracker API
2. **Первый export медленный** — 3000+ задач, может занять 5+ минут
3. **CSV файлы большие** — SPBACKEND_issues.csv ≈ 778 KB, фильтруй в Excel
4. **Токен приватный** — не коммитируй токены, добавь в .gitignore
5. **Данные refresh еженедельно** — запускай анализ каждый понедельник

---

## 🎯 Цель проекта

Этот проект помогает:
- ✅ Выявить узкие места в процессе разработки
- ✅ Измерить скорость выполнения задач
- ✅ Отследить прогресс оптимизации
- ✅ Принять обоснованные решения на основе данных

Больше информации в `README.md` и `TIMELINE_ANALYSIS_REPORT.md`.

---

*Обновлено: 2026-06-25*  
*Для вопросов или улучшений — смотри CONTRIBUTING.md (если есть)*
