# helper.py
import re
from bs4 import BeautifulSoup

def simple_extractor(content) -> str:
    """
    Универсальный экстрактор: принимает либо строку (HTML), 
    либо готовый объект BeautifulSoup.
    """
    # 1. Если пришла строка (от RecursiveUrlLoader), превращаем в Soup
    if isinstance(content, str):
        soup = BeautifulSoup(content, "html.parser")
    # 2. Если уже пришел Soup (от SitemapLoader), используем как есть
    else:
        soup = content

    # Если по какой-то причине контент пустой
    if soup is None:
        return ""

    # Удаляем мусор
    for junk in soup(["script", "style", "header", "footer", "nav", "form", "noscript"]):
        junk.decompose()

    # Извлекаем текст
    text = soup.get_text(separator=" ")
    
    # Чистим лишние пробелы (включая неразрывные и табуляцию)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def format_docs(docs, max_chars=16000):
    """Форматирует документы для промпта с лимитом символов."""
    formatted = []
    total_len = 0
    for doc in docs:
        source = doc.metadata.get("source", "unknown")
        text = doc.page_content.strip()
        block = f"Source: {source}\n{text}"
        
        if total_len + len(block) > max_chars:
            break
        formatted.append(block)
        total_len += len(block)
    return "\n\n---\n\n".join(formatted)

def clean_extra_whitespaces(text: str) -> str:
    """Дополнительная очистка текста (если нужно)."""
    return re.sub(r'\s+', ' ', text).strip()