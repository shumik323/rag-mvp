antarctic-rag/
├── data/               # Локальное хранилище (ChromaDB, PDF-исходники)
├── src/
│   ├── ingestion/      # Код для наполнения базы (ETL)
│   │   ├── loaders.py  # Настройка Sitemap/URL Loader
│   │   └── splitter.py # Настройка логики нарезки текста
│   ├── chains/         # Описание логики RAG (LCEL цепочки)
│   │   └── rag_chain.py
│   ├── components/     # Инициализация моделей
│   │   ├── llm.py      # Настройка Ollama/OpenAI
│   │   └── embedding.py# Настройка RoSBERTa
│   └── utils/          # Твои хелперы (bs4, format_docs)
├── main.py             # Точка входа для запуска бота/интерфейса
├── ingest.py           # Скрипт для разового наполнения базы
└── .env                # Конфигурация и ключи
