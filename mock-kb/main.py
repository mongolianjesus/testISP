import json
import os
import uuid
import time
from typing import List, Optional

from fastapi import FastAPI
import strawberry
from strawberry.fastapi import GraphQLRouter
from rapidfuzz import fuzz

DATA_FILE = "documents.json"


# --- 1. DUMMY DATA INITIALIZATION ---
# Creates a sample documents.json if it doesn't exist yet
def initialize_mock_data():
    if not os.path.exists(DATA_FILE):
        current_time = int(time.time())
        sample_docs = [
            {
                "id": str(uuid.uuid4()),
                "title": "Картофельная запеканка с творогом",
                "text": "Творог протереть через сито или смолоть в мясорубке. Перемешать с размягченным маслом до однородности. Посолить и поперчить по вкусу.\nКартофель очистить и нарезать очень тонкими кружочками.\nГлубокую форму для запекания смазать сливочным маслом. На дно выложить слой картофельных кружков, посолить и поперчить. Сверху распределить тонкий слой творожной массы.\nПродолжать выкладывать слои, пока не закончатся все ингредиенты. Сверху должен быть картофель. Противень выбирайте очень глубокий или не заполняйте его до верха. Я допустила такую ошибку. В процессе запекания выделяется много жидкости, затем часть ее испаряется, часть впитывается картофелем, но первоначально она начинает вытекать за бортики противня. Пришлось помещать его в другой большой противень.\nПрежде, чем поставить форму в духовку, разогретую до 200 градусов, ее надо плотно закрыть фольгой. Запекать 1 час.\nНатереть на крупной терке твердый сыр. Приготовить заливку. Взбить вилкой яйца, добавить сметану, посолить и поперчить, добавить мускатный орех или другие любимые специи. Снять фольгу с формы и залить картофель заливкой. Сверху посыпать тертым сыром. Запекать в духовке 30 минут и еще на 15 минут оставить запеканку картофельную в выключенной духовке.",
                "publicationDate": current_time - 86400,
            },
            {
                "id": str(uuid.uuid4()),
                "title": "Зразы из творога",
                "text": "Смешать творог сахар и яйца.\nЗатем добавить муку и замесить тесто. Количество муки может меняться в зависимости от влажности творога. Готовое тесто должно быть мягким, но хорошо лепиться.\nПрисыпать стол мукой. Разделить тесто на кусочки, величиной с крупную сливу. Сформировать лепешку. Положить 0,5-1 ч. ложку начинки.\nЗатем аккуратно залепить края, чтобы вся начинка оказалась внутри.\nВскипятить воду. Опустить зразы в кипяток и варить при среднем кипении 5 минут. Они должны всплыть.\nЗатем разогреть на сковороде сливочное масло. Обжаривать зразы на среднем огне 5-7 мин с одной стороны.\nЗатем аккуратно перевернуть зразы и обжаривать их с другой стороны еще 5 минут.\n",
                "publicationDate": current_time - 172800,
            },
            {
                "id": str(uuid.uuid4()),
                "title": "Оливковый пияз с грецкими орехами и зеленью",
                "text": "Подготавливаем необходимые продукты.\nГрецкие орехи измельчаем удобным для себя способом.\nОливки нарезаем произвольно (я предпочитаю кружочками).\nЗелёный лук промываем и мелко нарезаем ножом.\nПетрушку или любисток промываем и мелко нарезаем.\nВ миске соединяем измельчённые орехи, оливки, зелёный лук и петрушку (любисток).\nАккуратно перемешиваем.\nДля заправки соединяем лимонный сок, наршараб, чёрный перец и хлопья чили. Перемешиваем до однородности.\nПоливаем салат заправкой и ещё раз перемешиваем.\nВыкладываем оливковый пияз на блюдо или в салатник. Украшаем зеленью и грецкими орехами, по желанию поливаем оливковым маслом.",
                "publicationDate": current_time,
            },
            {
                "id": str(uuid.uuid4()),
                "title": "Плескавица - большая плоская котлета из Сербии",
                "text": "Шаг 1. Лук нарежьте кубиками с ребром 5 мм, чеснок мелко порубите. Овощи и специи соедините с мясом. Тщательно вымешивайте фарш около 10 минут: масса должна стать эластичной и хорошо держать форму.\n\nШаг 2. Фарш уберите в холодильник на 30 минут. От бумаги для выпечки отрежьте два прямоугольника примерно 17 × 35 см.\n\nШаг 3. Мясо разделите на две части по 250 г, выложите на листы бумаги для выпечки. Сформируйте плоские котлеты диаметром около 15 см и высотой 1 см. Шаг 4. Сковороду с маслом разогрейте на средне-высоком огне. Обжарьте каждую котлету прямо в конверте с каждой стороны до золотистой корочки по 4—5 минут.\n\nЕсли хотите сделать плескавицу румянее, с почти готовой котлеты снимите бумагу и обжарьте с каждой стороны еще по полминуты. Шаг 5. Готовую плескавицу выложите на тарелку или в кармашек питы.\n\n",
                "publicationDate": current_time - 3600,
            },
        ]
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(sample_docs, f, indent=4)


# initialize_mock_data()


# --- 2. GRAPHQL SCHEMA DEFINITION ---


@strawberry.input
class PaginationParams:
    offset: int = 0
    limit: int = 10


@strawberry.input
class FilterSettings:
    searchString: Optional[str] = None
    publicationDate: Optional[int] = None


@strawberry.type
class Document:
    id: strawberry.ID
    title: str
    text: str
    publicationDate: int


@strawberry.type
class PaginatedDocuments:
    total: int
    listDocument: List[Document]


# --- 3. GRAPHQL RESOLVERS & LOGIC ---


def get_documents() -> List[dict]:
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


@strawberry.type
class Query:
    @strawberry.field
    def paginate_documents(
        self,
        pagination_params: Optional[PaginationParams] = None,
        filter_settings: Optional[FilterSettings] = None,
    ) -> PaginatedDocuments:

        all_docs = get_documents()
        filtered_docs = all_docs

        # Apply filters if provided
        if filter_settings:
            # 1. Filter by search string (Fuzzy match on Title or Text)
            if filter_settings.searchString:
                search_query = filter_settings.searchString.lower()
                matched_docs = []
                for doc in filtered_docs:
                    # Calculate similarity scores using rapidfuzz partial ratio
                    title_score = fuzz.partial_ratio(search_query, doc["title"].lower())
                    text_score = fuzz.partial_ratio(search_query, doc["text"].lower())

                    # If either title or text has a similarity > 60%, keep it
                    if max(title_score, text_score) > 60:
                        matched_docs.append(doc)
                filtered_docs = matched_docs

            # 2. Filter by publication date (Exact match timestamp, adjust logic if ">=" is needed)
            if filter_settings.publicationDate is not None:
                filtered_docs = [
                    doc
                    for doc in filtered_docs
                    if doc["publicationDate"] == filter_settings.publicationDate
                ]

        # Calculate Total BEFORE pagination
        total_count = len(filtered_docs)

        # Apply pagination (offset & limit)
        offset = pagination_params.offset if pagination_params else 0
        limit = pagination_params.limit if pagination_params else 10

        start_idx = offset
        end_idx = start_idx + limit
        paginated_chunk = filtered_docs[start_idx:end_idx]

        # Map dicts to GraphQL Document types
        return PaginatedDocuments(
            total=total_count, listDocument=[Document(**doc) for doc in paginated_chunk]
        )


# --- 4. FASTAPI SETUP ---

schema = strawberry.Schema(query=Query)
graphql_app = GraphQLRouter(schema)

app = FastAPI(title="Mock GraphQL Document Service")

# Register the GraphQL route
app.include_router(graphql_app, prefix="/graphql")


@app.get("/")
def read_root():
    return {"message": "Welcome! Go to /graphql to access the GraphQL UI."}
