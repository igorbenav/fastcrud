import pytest

from fastcrud.crud.fast_crud import FastCRUD, JoinConfig

from ..conftest import (
    Article,
    Card,
    ArticleSchema,
    CardSchema,
)


@pytest.mark.asyncio
async def test_nest_multi_join_data_new_row_none(async_session):
    cards = [
        Card(title="Card A"),
        Card(title="Card B"),
    ]
    async_session.add_all(cards)
    await async_session.flush()

    articles = [
        Article(
            title="Article 1", content="Content 1", author_id=1, card_id=cards[0].id
        ),
        Article(
            title="Article 2", content="Content 2", author_id=2, card_id=None
        ),  # This should trigger new_row[key] = []
    ]
    async_session.add_all(articles)
    await async_session.commit()

    card_crud = FastCRUD(Card)

    result = await card_crud.get_multi_joined(
        db=async_session,
        nest_joins=True,
        schema_to_select=CardSchema,
        joins_config=[
            JoinConfig(
                model=Article,
                join_on=Article.card_id == Card.id,
                join_prefix="articles_",
                join_type="left",
                relationship_type="one-to-many",
            )
        ],
    )

    assert result is not None, "No data returned from the database."
    assert "data" in result, "Result should contain 'data' key."
    data = result["data"]

    card_a = next((c for c in data if c["id"] == cards[0].id), None)
    assert (
        card_a is not None and "articles" in card_a
    ), "Card A should have nested articles."
    assert len(card_a["articles"]) == 1, "Card A should have one valid article."
    assert (
        card_a["articles"][0]["title"] == "Article 1"
    ), "Card A's article title should be 'Article 1'."

    card_b = next((c for c in data if c["id"] == cards[1].id), None)
    assert (
        card_b is not None and "articles" in card_b
    ), "Card B should have nested articles."
    assert (
        len(card_b["articles"]) == 0
    ), "Card B should have no articles due to None card_id in Article."


@pytest.mark.asyncio
async def test_nest_multi_join_data_existing_row_none(async_session):
    cards = [
        Card(title="Card A"),
    ]
    async_session.add_all(cards)
    await async_session.flush()

    articles = [
        Article(
            title="Article 1", content="Content 1", author_id=1, card_id=cards[0].id
        ),
        Article(
            title="Article 2", content="Content 2", author_id=2, card_id=cards[0].id
        ),
        Article(
            title="Article 3", content="Content 3", author_id=3, card_id=None
        ),  # This will trigger existing_row[key] = []
    ]
    async_session.add_all(articles)
    await async_session.commit()

    card_crud = FastCRUD(Card)

    result = await card_crud.get_multi_joined(
        db=async_session,
        nest_joins=True,
        schema_to_select=CardSchema,
        joins_config=[
            JoinConfig(
                model=Article,
                join_on=Article.card_id == Card.id,
                join_prefix="articles_",
                join_type="left",
                relationship_type="one-to-many",
            )
        ],
    )

    assert result is not None, "No data returned from the database."
    assert "data" in result, "Result should contain 'data' key."
    data = result["data"]

    card_a = next((c for c in data if c["id"] == cards[0].id), None)
    assert (
        card_a is not None and "articles" in card_a
    ), "Card A should have nested articles."
    assert len(card_a["articles"]) == 2, "Card A should have two valid articles."
    assert (
        card_a["articles"][0]["title"] == "Article 1"
    ), "Card A's first article title should be 'Article 1'."
    assert (
        card_a["articles"][1]["title"] == "Article 2"
    ), "Card A's second article title should be 'Article 2'."


@pytest.mark.asyncio
async def test_nest_multi_join_data_nested_schema(async_session):
    cards = [
        Card(title="Card A"),
    ]
    async_session.add_all(cards)
    await async_session.flush()

    articles = [
        Article(
            title="Article 1", content="Content 1", author_id=1, card_id=cards[0].id
        ),
    ]
    async_session.add_all(articles)
    await async_session.commit()

    card_crud = FastCRUD(Card)

    result = await card_crud.get_multi_joined(
        db=async_session,
        nest_joins=True,
        return_as_model=True,
        schema_to_select=CardSchema,
        joins_config=[
            JoinConfig(
                model=Article,
                join_on=Article.card_id == Card.id,
                join_prefix="articles_",
                join_type="left",
                schema_to_select=ArticleSchema,
                relationship_type="one-to-many",
            )
        ],
    )

    assert result is not None, "No data returned from the database."
    assert "data" in result, "Result should contain 'data' key."
    data = result["data"]

    assert len(data) == 1, "Expected one card record."
    card_a = data[0]
    assert isinstance(card_a, CardSchema), "Card should be an instance of CardSchema."
    assert hasattr(card_a, "articles"), "Card should have nested articles."
    assert len(card_a.articles) == 1, "Card should have one article."
    assert isinstance(
        card_a.articles[0], ArticleSchema
    ), "Article should be an instance of ArticleSchema."
    assert (
        card_a.articles[0].title == "Article 1"
    ), "Article title should be 'Article 1'."


@pytest.mark.asyncio
async def test_nest_multi_join_data_prefix_in_item(async_session):
    cards = [
        Card(title="Card A"),
    ]
    async_session.add_all(cards)
    await async_session.flush()

    articles = [
        Article(
            title="Article 1", content="Content 1", author_id=1, card_id=cards[0].id
        ),
    ]
    async_session.add_all(articles)
    await async_session.commit()

    card_crud = FastCRUD(Card)

    result = await card_crud.get_multi_joined(
        db=async_session,
        nest_joins=True,
        return_as_model=True,
        schema_to_select=CardSchema,
        joins_config=[
            JoinConfig(
                model=Article,
                join_on=Article.card_id == Card.id,
                join_prefix="articles_",
                join_type="left",
                schema_to_select=ArticleSchema,
                relationship_type="one-to-many",
            )
        ],
    )

    assert result is not None, "No data returned from the database."
    assert "data" in result, "Result should contain 'data' key."
    data = result["data"]

    assert len(data) == 1, "Expected one card record."
    card_a = data[0]
    assert isinstance(card_a, CardSchema), "Card should be an instance of CardSchema."
    assert hasattr(card_a, "articles"), "Card should have nested articles."
    assert len(card_a.articles) == 1, "Card should have one article."
    assert isinstance(
        card_a.articles[0], ArticleSchema
    ), "Article should be an instance of ArticleSchema."
    assert (
        card_a.articles[0].title == "Article 1"
    ), "Article title should be 'Article 1'."


@pytest.mark.asyncio
async def test_nest_multi_join_data_isinstance_list(async_session):
    cards = [
        Card(title="Card A"),
    ]
    async_session.add_all(cards)
    await async_session.flush()

    articles = [
        Article(
            title="Article 1", content="Content 1", author_id=1, card_id=cards[0].id
        ),
        Article(
            title="Article 2", content="Content 2", author_id=2, card_id=cards[0].id
        ),
    ]
    async_session.add_all(articles)
    await async_session.commit()

    card_crud = FastCRUD(Card)

    result = await card_crud.get_multi_joined(
        db=async_session,
        nest_joins=True,
        return_as_model=True,
        schema_to_select=CardSchema,
        joins_config=[
            JoinConfig(
                model=Article,
                join_on=Article.card_id == Card.id,
                join_prefix="articles_",
                join_type="left",
                schema_to_select=ArticleSchema,
                relationship_type="one-to-many",
            )
        ],
    )

    assert result is not None, "No data returned from the database."
    assert "data" in result, "Result should contain 'data' key."
    data = result["data"]

    assert len(data) == 1, "Expected one card record."
    card_a = data[0]
    assert isinstance(card_a, CardSchema), "Card should be an instance of CardSchema."
    assert hasattr(card_a, "articles"), "Card should have nested articles."
    assert len(card_a.articles) == 2, "Card should have two articles."
    assert all(
        isinstance(article, ArticleSchema) for article in card_a.articles
    ), "All articles should be instances of ArticleSchema."


@pytest.mark.asyncio
async def test_nest_multi_join_data_convert_list_to_schema(async_session):
    cards = [
        Card(title="Card A"),
    ]
    async_session.add_all(cards)
    await async_session.flush()

    articles = [
        Article(
            title="Article 1", content="Content 1", author_id=1, card_id=cards[0].id
        ),
        Article(
            title="Article 2", content="Content 2", author_id=2, card_id=cards[0].id
        ),
    ]
    async_session.add_all(articles)
    await async_session.commit()

    card_crud = FastCRUD(Card)

    result = await card_crud.get_multi_joined(
        db=async_session,
        nest_joins=True,
        return_as_model=True,
        schema_to_select=CardSchema,
        joins_config=[
            JoinConfig(
                model=Article,
                join_on=Article.card_id == Card.id,
                join_prefix="articles_",
                join_type="left",
                schema_to_select=ArticleSchema,
                relationship_type="one-to-many",
            )
        ],
    )

    assert result is not None, "No data returned from the database."
    assert "data" in result, "Result should contain 'data' key."
    data = result["data"]

    assert len(data) == 1, "Expected one card record."
    card_a = data[0]
    assert isinstance(card_a, CardSchema), "Card should be an instance of CardSchema."
    assert hasattr(card_a, "articles"), "Card should have nested articles."
    assert len(card_a.articles) == 2, "Card should have two articles."
    assert all(
        isinstance(article, ArticleSchema) for article in card_a.articles
    ), "All articles should be instances of ArticleSchema."


@pytest.mark.asyncio
async def test_nest_multi_join_data_convert_dict_to_schema(async_session):
    cards = [
        Card(title="Card A"),
    ]
    async_session.add_all(cards)
    await async_session.flush()

    articles = [
        Article(
            title="Article 1", content="Content 1", author_id=1, card_id=cards[0].id
        ),
    ]
    async_session.add_all(articles)
    await async_session.commit()

    card_crud = FastCRUD(Card)

    result = await card_crud.get_multi_joined(
        db=async_session,
        nest_joins=True,
        return_as_model=True,
        schema_to_select=CardSchema,
        joins_config=[
            JoinConfig(
                model=Article,
                join_on=Article.card_id == Card.id,
                join_prefix="articles_",
                join_type="left",
                schema_to_select=ArticleSchema,
                relationship_type="one-to-many",
            )
        ],
    )

    assert result is not None, "No data returned from the database."
    assert "data" in result, "Result should contain 'data' key."
    data = result["data"]

    assert len(data) == 1, "Expected one card record."
    card_a = data[0]
    assert isinstance(card_a, CardSchema), "Card should be an instance of CardSchema."
    assert hasattr(card_a, "articles"), "Card should have nested articles."
    assert len(card_a.articles) == 1, "Card should have one article."
    assert isinstance(
        card_a.articles[0], ArticleSchema
    ), "Article should be an instance of ArticleSchema."
    assert (
        card_a.articles[0].title == "Article 1"
    ), "Article title should be 'Article 1'."
