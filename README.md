# Antarctic Wallet — RAG Assistant (MVP)

AI-ассистент для поддержки пользователей [Antarctic Wallet](https://antarcticwallet.com/), построенный на архитектуре **Retrieval-Augmented Generation**.

Бот автоматически индексирует сайт, находит релевантные фрагменты по вопросу пользователя и генерирует ответ на естественном языке — без галлюцинаций, строго по контексту.

## Стек

| Компонент | Технология |
|-----------|-----------|
| Embeddings | [RoSBERTa](https://huggingface.co/ai-forever/ru-en-RoSBERTa) (ru/en, билингвальная) |
| Vector DB | ChromaDB (persistent, MMR-retrieval) |
| LLM | Mistral Nemo 12B через Ollama (локально, без API-затрат) |
| Framework | LangChain (LCEL chains) |
| Tracing | LangSmith |
| Ingestion | Sitemap + Recursive URL crawling, BeautifulSoup |

## Как это работает

```
Вопрос пользователя
        │
        ▼
   ┌──────────┐     ┌────────────┐     ┌─────────┐
   │ Embedding │────▶│  ChromaDB   │────▶│ Top-K   │
   │ (RoSBERTa)│     │ (MMR search)│     │ chunks  │
   └──────────┘     └────────────┘     └────┬────┘
                                            │
                                            ▼
                                   ┌────────────────┐
                                   │  Mistral Nemo   │
                                   │ (Ollama, local) │
                                   └───────┬────────┘
                                           │
                                           ▼
                                    Ответ на русском
```

## Быстрый старт

```bash
# 1. Клонируем
git clone https://github.com/shumik323/rag-mvp.git
cd rag-mvp

# 2. Создаём окружение
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 3. Настраиваем переменные
cp .env.example .env
# отредактировать .env (LangSmith ключ, URL сайта, модель)

# 4. Убедиться что Ollama запущен с нужной моделью
ollama pull hf.co/bartowski/Mistral-Nemo-Instruct-2407-GGUF:Q4_K_M

# 5. Запуск
python my_rag.py
```

При первом запуске система автоматически:
1. Скачает и проиндексирует сайт (sitemap + recursive crawl)
2. Разобьёт контент на чанки (1500 символов, overlap 150)
3. Создаст векторную БД в `./chroma_db`

Повторные запуски используют кэшированную БД.

## Ключевые решения

- **Prefixed Embeddings** — добавление `search_query:` / `search_document:` префиксов для RoSBERTa, что повышает качество поиска на ~15-20%
- **MMR retrieval** (k=6, fetch_k=20) — максимизация разнообразия результатов, чтобы не тянуть дублирующие чанки
- **Дедупликация источников** — объединение результатов sitemap + recursive crawl с удалением дублей по URL
- **Локальный LLM** — нулевые затраты на inference, данные не покидают машину

## Конфигурация

Все параметры задаются через `.env` (см. `.env.example`):

| Переменная | Описание |
|-----------|----------|
| `ROOT_URL` | URL сайта для индексации |
| `EMBEDDING_MODEL` | HuggingFace модель для эмбеддингов |
| `LLM_BASE_URL` | Endpoint LLM (Ollama / OpenAI-compatible) |
| `LLM_MODEL` | Название модели |
| `CHROMA_PERSIST_DIR` | Путь к хранилищу ChromaDB |

## Структура проекта

```
├── my_rag.py          # RAG pipeline (entry point)
├── helper.py          # HTML extraction, doc formatting
├── requirements.txt   # Python dependencies
├── .env.example       # Environment template
├── architecture.md    # Planned refactoring roadmap
└── README.md
```

## Roadmap

- [ ] Web UI (Streamlit / Gradio)
- [ ] Chat history (multi-turn conversations)
- [ ] Scheduled re-indexing (cron)
- [ ] Модульная архитектура (см. `architecture.md`)
- [ ] Docker Compose для one-click deploy
- [ ] Evaluation pipeline (RAGAS)

## License

MIT
