import os
from pathlib import Path
from dotenv import load_dotenv

from helper import simple_extractor, format_docs, clean_extra_whitespaces

load_dotenv()
os.environ.setdefault("USER_AGENT", "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)")

ROOT_URL = os.getenv("ROOT_URL", "https://antarcticwallet.com/")
SITEMAP_URL = f"{ROOT_URL.rstrip('/')}/sitemap.xml"
PERSIST_DIRECTORY = os.getenv("CHROMA_PERSIST_DIR", "./chroma_db")
MODEL_NAME = os.getenv("EMBEDDING_MODEL", "ai-forever/ru-en-RoSBERTa")

from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.embeddings import Embeddings

base_embeddings = HuggingFaceEmbeddings(model_name=MODEL_NAME)

class PrefixedEmbeddings(Embeddings):
    def __init__(self, base, query_prefix="search_query: ", doc_prefix="search_document: "):
        self.base = base
        self.query_prefix = query_prefix
        self.doc_prefix = doc_prefix
    def embed_documents(self, texts):
        return self.base.embed_documents([self.doc_prefix + t for t in texts])
    def embed_query(self, text):
        return self.base.embed_query(self.query_prefix + text)

embeddings = PrefixedEmbeddings(base_embeddings)

from langchain_community.vectorstores import Chroma

if not Path(PERSIST_DIRECTORY).exists():
    print("📦 База не найдена. Начинаем индексацию сайта...")
    from langchain_community.document_loaders import SitemapLoader, RecursiveUrlLoader
    from langchain_text_splitters import RecursiveCharacterTextSplitter

    sitemap_loader = SitemapLoader(
        web_path=SITEMAP_URL,
        filter_urls=[ROOT_URL],
        parsing_function=simple_extractor
    )
    
    recursive_loader = RecursiveUrlLoader(
        url=ROOT_URL,
        max_depth=2,
        prevent_outside=True,
        extractor=simple_extractor
    )

    all_docs_map = {doc.metadata.get('source'): doc for doc in (sitemap_loader.load() + recursive_loader.load()) if doc.metadata.get('source')}
    docs = list(all_docs_map.values())

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1500,
        chunk_overlap=150,
    )
    
    for doc in docs:
        doc.page_content = clean_extra_whitespaces(doc.page_content)
    
    splits = text_splitter.split_documents(docs)
    
    vectorstore = Chroma.from_documents(
        documents=splits,
        embedding=embeddings,
        persist_directory=PERSIST_DIRECTORY,
    )
    print(f"База создана! Обработано {len(docs)} страниц, создано {len(splits)} чанков.")
else:
    print("База найдена. Загружаем из памяти...")
    vectorstore = Chroma(
        embedding_function=embeddings,
        persist_directory=PERSIST_DIRECTORY,
    )

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough, RunnableLambda

retriever = vectorstore.as_retriever(search_type="mmr", search_kwargs={"k": 6, "fetch_k": 20})

prompt = ChatPromptTemplate.from_messages([
    ("system", "Ты помощник Antarctic Wallet. Отвечай СТРОГО НА РУССКОМ. Используй ТОЛЬКО контекст. Если ответа нет, скажи: 'Информация не найдена'. Источник: Source."),
    MessagesPlaceholder("history"),
    ("human", "Контекст:\n{context}\n\nВопрос: {question}"),
])

llm = ChatOpenAI(
    api_key="None",
    base_url=os.getenv("LLM_BASE_URL", "http://127.0.0.1:11434/v1"),
    model=os.getenv("LLM_MODEL", "hf.co/bartowski/Mistral-Nemo-Instruct-2407-GGUF:Q4_K_M"),
    temperature=float(os.getenv("LLM_TEMPERATURE", "0.1")),
)

def ensure_context(input_dict):
    if not input_dict.get("context", "").strip():
        input_dict["context"] = "Контекст пуст."
    return input_dict

rag_chain = (
    {
        "context": retriever | format_docs,
        "question": RunnablePassthrough(),
        "history": lambda _: [],
    }
    | RunnableLambda(ensure_context)
    | prompt
    | llm
    | StrOutputParser()
)

from langsmith import traceable

@traceable(name="AW_answer_question")
def answer_question(question: str) -> str:
    return rag_chain.invoke(question)

if __name__ == "__main__":
    q = "Как начать пользоваться Antarctic Wallet?"
    print(f"Вопрос: {q}\nОтвет: {answer_question(q)}")