# RAG-кулинарный ассистент

## Структура

- `app/`: приложение Gradio, интерфейс RAG
- `mock-kb`: база данных GraphQL с рецептами

## Requirements

- Python 3.10
- `uv` для разворачивания GraphQL
- API ключ для модели
- Base URL модели

## Среда

```env
MODEL_API_KEY=... 
MODEL_BASE_URL=... # по умолчанию: https://api.openai.com/v1
MODEL_NAME=... # по умолчанию: gpt-4o-mini
GRAPHQL_URL=... # по умолчанию: http://127.0.0.1:8000/graphql
```

## Запуск БД

```shell
cd mock-kb
uv sync
uv run fastapi dev
```

## Запуск RAG

- В параллельном терминале:
```shell
cd app
pip install -r requirements.txt
python app.py
```
- Открыть  http://127.0.0.1:7860

## Имплементированные фичи:

- Веб-интерфейс на Gradio;
- fuzzy поиск по GraphQL
- Адаптирование пользовательского запроса под ключевые слова для поиска в GraphQL
- Потоковый вывод ответа модели
- Демонстрация найденных документов и ключевых слов в запросе
- Базовый хендлинг ошибок: GraphQL недоступен, не найдены документы, ошибки с доступом к LLM