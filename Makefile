.PHONY: help install export analyze timeline all clean

help:
	@echo "📊 Tracker SPBACKEND Analysis Makefile"
	@echo ""
	@echo "Доступные команды:"
	@echo "  make install       - Установить зависимости"
	@echo "  make export        - Загрузить данные из Tracker"
	@echo "  make analyze       - Быстрый анализ CSV"
	@echo "  make timeline      - Анализ lead time"
	@echo "  make all           - Загрузить + анализировать все"
	@echo "  make clean         - Удалить CSV файлы"
	@echo ""

install:
	@echo "📦 Установка зависимостей..."
	pip install -r requirements.txt
	@echo "✅ Зависимости установлены"

export:
	@echo "📥 Загрузка данных из Tracker..."
	@if [ -z "$$STARTREK_TOKEN" ]; then \
		echo "❌ Ошибка: STARTREK_TOKEN не установлен"; \
		exit 1; \
	fi
	python3 scripts/tracker_export_analysis.py

analyze:
	@echo "📊 Быстрый анализ данных..."
	@if [ ! -f "SPBACKEND_issues.csv" ]; then \
		echo "❌ Ошибка: SPBACKEND_issues.csv не найден. Запусти 'make export' сначала"; \
		exit 1; \
	fi
	python3 scripts/quick_analysis.py

timeline:
	@echo "📈 Анализ lead time..."
	@if [ ! -f "SPBACKEND_issues.csv" ]; then \
		echo "❌ Ошибка: SPBACKEND_issues.csv не найден. Запусти 'make export' сначала"; \
		exit 1; \
	fi
	python3 scripts/tracker_timeline_analysis.py

all: export analyze timeline
	@echo ""
	@echo "✅ Все анализы завершены"
	@echo ""
	@echo "📊 Результаты:"
	@echo "  - SPBACKEND_issues.csv (основные данные)"
	@echo "  - LEAD_TIME_ANALYSIS.csv (анализ времени)"
	@echo ""
	@echo "📖 Смотри TIMELINE_ANALYSIS_REPORT.md для деталей"

clean:
	@echo "🗑️  Удаление файлов анализа..."
	rm -f SPBACKEND_issues.csv
	rm -f SPFRONT_issues.csv
	rm -f LEAD_TIME_ANALYSIS.csv
	@echo "✅ Файлы удалены"

.DEFAULT_GOAL := help
