import pytest

from fastcrud import FastCRUD, JoinConfig
from ..conftest import (
    Article,
    Author,
)


@pytest.mark.asyncio
async def test_sort_nested_one_to_many_relationships(async_session):
    # Create test data
    author1 = Author(id=1, name="Author 1")
    author2 = Author(id=2, name="Author 2")

    # Create articles with different titles and dates for sorting
    article1 = Article(
        id=1,
        title="C Article",
        content="Content 1",
        author_id=1,
        published_date="2023-01-01",
    )
    article2 = Article(
        id=2,
        title="A Article",
        content="Content 2",
        author_id=1,
        published_date="2023-03-01",
    )
    article3 = Article(
        id=3,
        title="B Article",
        content="Content 3",
        author_id=1,
        published_date="2023-02-01",
    )
    article4 = Article(
        id=4,
        title="D Article",
        content="Content 4",
        author_id=2,
        published_date="2023-01-15",
    )

    async_session.add_all([author1, author2, article1, article2, article3, article4])
    await async_session.commit()

    # Test sorting by title in ascending order
    author_crud = FastCRUD(Author)
    joins_config = [
        JoinConfig(
            model=Article,
            join_on=Author.id == Article.author_id,
            join_prefix="articles_",
            relationship_type="one-to-many",
            sort_columns="title",
            sort_orders="asc",
        )
    ]

    result = await author_crud.get_multi_joined(
        db=async_session, joins_config=joins_config, nest_joins=True
    )

    # Verify that articles are sorted by title in ascending order
    author1_data = next(item for item in result["data"] if item["id"] == 1)
    assert [article["title"] for article in author1_data["articles"]] == [
        "A Article",
        "B Article",
        "C Article",
    ]

    # Test sorting by title in descending order
    joins_config = [
        JoinConfig(
            model=Article,
            join_on=Author.id == Article.author_id,
            join_prefix="articles_",
            relationship_type="one-to-many",
            sort_columns="title",
            sort_orders="desc",
        )
    ]

    result = await author_crud.get_multi_joined(
        db=async_session, joins_config=joins_config, nest_joins=True
    )

    # Verify that articles are sorted by title in descending order
    author1_data = next(item for item in result["data"] if item["id"] == 1)
    assert [article["title"] for article in author1_data["articles"]] == [
        "C Article",
        "B Article",
        "A Article",
    ]

    # Test sorting by published_date
    joins_config = [
        JoinConfig(
            model=Article,
            join_on=Author.id == Article.author_id,
            join_prefix="articles_",
            relationship_type="one-to-many",
            sort_columns="published_date",
            sort_orders="asc",
        )
    ]

    result = await author_crud.get_multi_joined(
        db=async_session, joins_config=joins_config, nest_joins=True
    )

    # Verify that articles are sorted by published_date in ascending order
    author1_data = next(item for item in result["data"] if item["id"] == 1)
    assert [article["published_date"] for article in author1_data["articles"]] == [
        "2023-01-01",
        "2023-02-01",
        "2023-03-01",
    ]

    # Test sorting by multiple columns
    joins_config = [
        JoinConfig(
            model=Article,
            join_on=Author.id == Article.author_id,
            join_prefix="articles_",
            relationship_type="one-to-many",
            sort_columns=["published_date", "title"],
            sort_orders=["desc", "asc"],
        )
    ]

    result = await author_crud.get_multi_joined(
        db=async_session, joins_config=joins_config, nest_joins=True
    )

    # Verify that articles are sorted by published_date in descending order and then by title in ascending order
    author1_data = next(item for item in result["data"] if item["id"] == 1)
    assert [article["published_date"] for article in author1_data["articles"]] == [
        "2023-03-01",
        "2023-02-01",
        "2023-01-01",
    ]
