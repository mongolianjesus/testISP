import os
import requests
from typing import Dict, List
from langchain_openai import ChatOpenAI
import dotenv
import rag_utils as rag
import gradio as gr


import logging

logging.basicConfig(level=logging.INFO)
_LOG = logging.getLogger(__name__)

dotenv.load_dotenv()


# ####################
# GraphQL
# ####################


# Темплейт запроса для fuzzysearch по GraphQL.
SEARCH_QUERY = """
query Search($search: String!){
paginateDocuments(
    filterSettings: {searchString: $search}
  ) {
    listDocument {
      title
      text
    }
  }
}
"""
# URL для GraphQL.
APP_URL = os.getenv("GRAPHQL_URL", "http://127.0.0.1:8000/graphql")


# ##############
# МОДЕЛЬ
# ##############

MODEL_API_KEY = os.getenv("MODEL_API_KEY")
MODEL_NAME = os.getenv("MODEL_NAME", "gpt-4o-mini")
MODEL_BASE_URL = os.getenv("MODEL_BASE_URL", "https://api.openai.com/v1")

KEYWORD_LLM = ChatOpenAI(
    model_name=MODEL_NAME,
    openai_api_key=MODEL_API_KEY,
    base_url=MODEL_BASE_URL,
    temperature=0.0,
)

RAG_LLM = ChatOpenAI(
    model_name=MODEL_NAME,
    openai_api_key=MODEL_API_KEY,
    base_url=MODEL_BASE_URL,
    temperature=0.3,
)


# ##############
# ФУНКЦИИ
# ##############


def transform_query_to_keywords(user_query: str) -> str:
    prompt_value = rag.KEYWORD_PROMPT.format(query=user_query)
    try:
        keywords = KEYWORD_LLM.invoke(prompt_value).content
    except Exception as e:
        _LOG.exception("Keyword rewrite failed: %s", e)
        return user_query
    if not keywords:
        return user_query
    return keywords


def retrieve_documents(user_query: str):
    # Переписать запрос до ключевых слов.
    try:
        response = requests.post(
            APP_URL,
            json={"query": SEARCH_QUERY, "variables": {"search": user_query}},
            timeout=10,
        )
        response.raise_for_status()
        payload = response.json()
    except requests.exceptions.RequestException as e:
        _LOG.exception(e)
        raise RuntimeError("База знаний сейчас недоступна. Попробуйте позже.") from e
    except ValueError as e:
        _LOG.exception(e)
        raise RuntimeError("База знаний вернула некорректный ответ.") from e
    except Exception as e:
        _LOG.exception(e)
        raise RuntimeError("Неизвестная ошибка при запросе в базу.") from e
    if payload.get("errors"):
        _LOG.error("GraphQL returned errors: %s", payload["errors"])
        raise RuntimeError("Неудачный запрос к базе знаний")

    documents = payload["data"]["paginateDocuments"]["listDocument"]
    return documents


def format_context(responses: List[Dict[str, str]]):
    context_template = """НАЗВАНИЕ РЕЦЕПТА:\n{title}\n\nТЕКСТ РЕЦЕПТА:\n{text}\n\n"""
    formatted_context = ""
    for response in responses:
        formatted_text = context_template.format(
            title=response["title"], text=response["text"]
        )
        formatted_context += formatted_text
    return formatted_context


def render_context_html(documents: List[Dict[str, str]]) -> str:
    if not documents:
        return "Контекст отсутствует."
    blocks = ["<div>"]
    for i, doc in enumerate(documents, start=1):
        title = doc.get("title", "Без названия")
        text = doc.get("text", "").replace("\n", "<br>")
        blocks.append(f"""
            <details style="margin-bottom: 12px;">
                <summary><strong>{i}. {title}</strong></summary>
                <div style="margin-top: 8px; line-height: 1.45;">{text}</div>
            </details>
            """)
    blocks.append("</div>")
    context_html = "\n".join(blocks)
    return context_html


def answer_question(
    user_query: str,
) -> str:
    """
    Предоставить ответ на запрос пользователя.

    :param user_query: запрос пользователя
    :return: ответ модели
    """
    documents = retrieve_documents(user_query)
    formatted_context = format_context(documents)
    prompt_value = rag.GENERAL_PROMPT.invoke(
        {
            "question": user_query,
            "context": formatted_context,
        }
    )
    response = RAG_LLM.invoke(prompt_value)
    model_answer = response.content
    return model_answer


def stream_answer_question(
    user_query: str,
):
    """
    Ответить на вопрос пользователя с текстовым потоком.

    :param user_query: запрос пользователя
    :return: ответ модели
    """
    # Выйти при пустом запросе.
    if not user_query:
        yield "Введите вопрос!", "Контекст отсутствует", ""
        return
    # Запрос в GraphQL.
    try:
        search_query = transform_query_to_keywords(user_query)
        documents = retrieve_documents(search_query)
    # Вывести ошибку при ретривале.
    except RuntimeError as e:
        yield str(e), "Контекст отсутствует.", ""
        return
    # Если документы не были найдены.
    if not documents:
        yield "Я не знаю! Спроси что-нибудь другое!", "Контекст отсутствует.", ""
        return
    # Создать контекст и промпт.
    formatted_context = format_context(documents)
    context_html = render_context_html(documents)
    prompt_value = rag.GENERAL_PROMPT.invoke(
        {
            "question": user_query,
            "context": formatted_context,
        }
    )
    # Потоковый вывод ответа.
    model_answer = ""
    try:
        for chunk in RAG_LLM.stream(prompt_value):
            if chunk.content:
                model_answer += chunk.content
                yield model_answer, context_html, search_query
    # Неизвестная ошибка при выводе.
    except Exception as e:
        _LOG.exception("Ошибка LLM: %s", e)
        yield (
            "Я не смог получить ответ от языковой модели. Попробуйте повторить запрос позже.",
            context_html,
            search_query,
        )


# ###########
# Приложение
# ###########

with gr.Blocks(title="RAG App Demo with Feedback") as demo:
    gr.Markdown("# Demo RAG: вопрос для котенка-поваренка")
    gr.Markdown(
        "Задайте вопрос об ингредиенте или блюде, например: 'Подскажи мне рецепт из творога'"
    )
    question_input = gr.Textbox(
        label="Ваш вопрос",
        placeholder="Введите вопрос здесь...",
        lines=1,
    )
    keyword_query_output = gr.Textbox(
        label="Поисковый запрос в GraphQL", interactive=False, lines=1
    )
    answer_output = gr.Textbox(
        label="Последний ответ котенка-поваренка",
        interactive=False,
        lines=3,
        max_lines=16,
    )
    with gr.Accordion("Последний использованный контекст", open=True):
        context_output = gr.HTML("Контекст отсутствует.")
    submit_btn = gr.Button("Отправить", variant="primary")
    #
    submit_btn.click(
        fn=stream_answer_question,
        inputs=[
            question_input,
        ],
        outputs=[answer_output, context_output, keyword_query_output],
        show_progress="minimal",
    )


def main():
    demo.queue(default_concurrency_limit=2)
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
    )


if __name__ == "__main__":
    main()
