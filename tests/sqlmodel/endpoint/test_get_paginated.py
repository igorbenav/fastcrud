import pytest
from fastapi.testclient import TestClient

@pytest.mark.asyncio
async def test_read_items_with_pagination(
    client: TestClient, async_session, test_model, test_data
):
    for data in test_data:
        new_item = test_model(**data)
        async_session.add(new_item)
    await async_session.commit()

    page = 1
    items_per_page = 5

    response = client.get(f"/test/get_multi?page={page}&itemsPerPage={items_per_page}")

    assert response.status_code == 200

    data = response.json()

    assert "data" in data
    assert "total_count" in data
    assert "page" in data
    assert "items_per_page" in data
    assert "has_more" in data
    assert "cursor" in data

    assert len(data["data"]) > 0
    assert len(data["data"]) <= items_per_page

    test_item = test_data[0]
    assert any(item["name"] == test_item["name"] for item in data["data"])

    assert data["page"] == page
    assert data["items_per_page"] == items_per_page


@pytest.mark.asyncio
async def test_read_items_with_pagination_and_filters(
    filtered_client: TestClient, async_session, test_model, test_data
):
    for data in test_data:
        new_item = test_model(**data)
        async_session.add(new_item)
    await async_session.commit()

    page = 1
    items_per_page = 5

    tier_id = 1
    response = filtered_client.get(
        f"/test/get_multi?page={page}&itemsPerPage={items_per_page}&tier_id={tier_id}"
    )

    assert response.status_code == 200
    data = response.json()

    assert "data" in data
    assert "total_count" in data
    assert "page" in data
    assert "items_per_page" in data
    assert "has_more" in data
    assert "cursor" in data

    assert len(data["data"]) > 0
    assert len(data["data"]) <= items_per_page

    for item in data["data"]:
        assert item["tier_id"] == tier_id

    name = "Alice"
    response = filtered_client.get(
        f"/test/get_multi?page={page}&itemsPerPage={items_per_page}&name={name}"
    )

    assert response.status_code == 200
    data = response.json()

    assert "data" in data
    assert "total_count" in data
    assert "page" in data
    assert "items_per_page" in data
    assert "has_more" in data
    assert "cursor" in data

    assert len(data["data"]) > 0
    assert len(data["data"]) <= items_per_page

    for item in data["data"]:
        assert item["name"] == name


@pytest.mark.asyncio
async def test_read_items_with_partial_pagination_params(
    client: TestClient, async_session, test_model, test_data
):
    for data in test_data:
        new_item = test_model(**data)
        async_session.add(new_item)
    await async_session.commit()

    response = client.get("/test/get_multi?page=2")
    assert response.status_code == 200
    data = response.json()
    assert data["page"] == 2
    assert data["items_per_page"] == 10

    response = client.get("/test/get_multi?itemsPerPage=5")
    assert response.status_code == 200
    data = response.json()
    assert data["page"] == 1
    assert data["items_per_page"] == 5

@pytest.mark.asyncio
async def test_read_items_with_pagination_correctly_ordered(
    client: TestClient, async_session, test_model, test_data
):
    for data in test_data:
        new_item = test_model(**data)
        async_session.add(new_item)
    await async_session.commit()

    page = 1
    items_per_page = 5

    response = client.get(f"/test/get_multi?page={page}&itemsPerPage={items_per_page}")

    assert response.status_code == 200

    data = response.json()

    assert "data" in data
    assert "total_count" in data
    assert "page" in data
    assert "items_per_page" in data
    assert "has_more" in data
    assert "cursor" in data

    assert len(data["data"]) > 0
    assert len(data["data"]) <= items_per_page

    test_item = test_data[0]
    assert any(item["name"] == test_item["name"] for item in data["data"])

    assert data["page"] == page
    assert data["items_per_page"] == items_per_page

    # pagination should automatically order results by 
    # primary key to ensure consistent responses 
    page = 2
    response2 = client.get(f"/test/get_multi?page={page}&itemsPerPage={items_per_page}")
    data2 = response2.json()
    ids1 = [td["id"] for td in data["data"]]
    ids2 = [td["id"] for td in data2["data"]]
    # this checks for disjoint sets of ids
    # and for correct sequential ordering
    assert max(ids1) < min(ids2), f"ids are not sequential response 1:{ids1} -- response 2:{ids2}"

@pytest.mark.asyncio
async def test_read_items_with_pagination_and_filters_correctly_ordered(
    filtered_client: TestClient, async_session, test_model, test_data
):
    for data in test_data:
        new_item = test_model(**data)
        async_session.add(new_item)
    await async_session.commit()

    page = 1
    items_per_page = 5

    tier_id = 1
    response = filtered_client.get(
        f"/test/get_multi?page={page}&itemsPerPage={items_per_page}&tier_id={tier_id}"
    )

    assert response.status_code == 200
    data = response.json()

    assert "data" in data
    assert "total_count" in data
    assert "page" in data
    assert "items_per_page" in data
    assert "has_more" in data
    assert "cursor" in data

    assert len(data["data"]) > 0
    assert len(data["data"]) <= items_per_page

    for item in data["data"]:
        assert item["tier_id"] == tier_id

    # pagination should automatically order results by 
    # primary key to ensure consistent responses 
    # e.g. for itemsPerPage=5, the first page should deliver items 1-5 and the second page items 6-10
    page = 2
    response2 = filtered_client.get(
        f"/test/get_multi?page={page}&itemsPerPage={items_per_page}&tier_id={tier_id}"
    )
    data2 = response2.json()
    ids1 = [td["id"] for td in data["data"]]
    ids2 = [td["id"] for td in data2["data"]]
    # this checks for disjoint sets of ids
    # and for correct sequential ordering
    assert max(ids1) < min(ids2) 

    page = 1
    name = "Alice"
    response = filtered_client.get(
        f"/test/get_multi?page={page}&itemsPerPage={items_per_page}&name={name}"
    )

    assert response.status_code == 200
    data = response.json()

    assert "data" in data
    assert "total_count" in data
    assert "page" in data
    assert "items_per_page" in data
    assert "has_more" in data
    assert "cursor" in data

    assert len(data["data"]) > 0
    assert len(data["data"]) <= items_per_page

    for item in data["data"]:
        assert item["name"] == name

@pytest.mark.asyncio
async def test_read_items_with_pagination_cursor(
    client: TestClient, async_session, test_model, test_data
):
    for data in test_data:
        new_item = test_model(**data)
        async_session.add(new_item)
    await async_session.commit()

    cursor = True
    limit = 5
    response = client.get(f"/test/get_multi?cursor={cursor}&limit={limit}")

    assert response.status_code == 200

    data = response.json()

    assert "data" in data
    assert "total_count" in data
    assert "page" in data
    assert "items_per_page" in data
    assert "has_more" in data
    assert "cursor" in data

    assert len(data["data"]) > 0
    assert len(data["data"]) <= limit

    test_item = test_data[0]
    assert any(item["name"] == test_item["name"] for item in data["data"])

    ids = [item["id"] for item in data["data"]]
    assert (data["cursor"] is None and not data["has_more"] and data["total_count"] == len(data["data"])) or data["cursor"] == max(ids)

@pytest.mark.asyncio
async def test_read_items_with_pagination_multicursor(
    client: TestClient, async_session, multi_pk_model, test_data_multipk_list
):
    for data in test_data_multipk_list:
        new_item = multi_pk_model(**data)
        async_session.add(new_item)
    await async_session.commit()

    cursor = True
    limit = 5
    response = client.get(f"/multi_pk/get_multi?cursor={cursor}&limit={limit}")

    assert response.status_code == 200

    data = response.json()

    assert "data" in data
    assert "total_count" in data
    assert "page" in data
    assert "items_per_page" in data
    assert "has_more" in data
    assert "cursor" in data

    assert len(data["data"]) > 0
    assert len(data["data"]) <= limit

    test_item = test_data_multipk_list[0]
    assert any(item["name"] == test_item["name"] for item in data["data"])

    ids1 = [(item["id"],item["uuid"]) for item in data["data"]]
    ids1_max = max(ids1)
    assert (data["cursor"] is None and not data["has_more"] and data["total_count"] == len(data["data"])) \
        or (len(data["cursor"]) == len(ids1_max) and not any(data["cursor"][i] != ids1_max[i] for i in range(len(ids1_max))))

    # pagination should automatically order results by 
    # primary key to ensure consistent responses 
    cursor = data["cursor"]
    response2 = client.get(f"/multi_pk/get_multi?cursor={','.join([str(c) for c in cursor])}&limit={limit}")
    data2 = response2.json()
    ids2 = [(item["id"],item["uuid"]) for item in data2["data"]]
    # this checks for disjoint sets of ids
    # and for correct sequential ordering
    assert max(ids1) < min(ids2) 

@pytest.mark.asyncio
async def test_read_items_with_pagination_cursor_and_filters(
    filtered_client: TestClient, async_session, test_model, test_data
):
    for data in test_data:
        new_item = test_model(**data)
        async_session.add(new_item)
    await async_session.commit()

    cursor = True
    limit = 5

    tier_id = 1
    response = filtered_client.get(
        f"/test/get_multi?cursor={cursor}&limit={limit}&tier_id={tier_id}"
    )

    assert response.status_code == 200
    data = response.json()

    assert "data" in data
    assert "total_count" in data
    assert "page" in data
    assert "items_per_page" in data
    assert "has_more" in data
    assert "cursor" in data

    assert len(data["data"]) > 0
    assert len(data["data"]) <= limit

    for item in data["data"]:
        assert item["tier_id"] == tier_id

    ids = [item["id"] for item in data["data"]]
    assert (data["cursor"] is None and not data["has_more"] and data["total_count"] == len(data["data"])) or data["cursor"] == max(ids)

    name = "Alice"
    response = filtered_client.get(
        f"/test/get_multi?cursor={cursor}&limit={limit}&name={name}"
    )

    assert response.status_code == 200
    data = response.json()

    assert "data" in data
    assert "total_count" in data
    assert "has_more" in data
    assert "cursor" in data

    assert len(data["data"]) > 0
    assert len(data["data"]) <= limit

    for item in data["data"]:
        assert item["name"] == name

    ids = [item["id"] for item in data["data"]]
    assert (data["cursor"] is None and not data["has_more"] and data["total_count"] == len(data["data"])) or data["cursor"] == max(ids)


@pytest.mark.asyncio
async def test_read_items_with_partial_pagination_cursor_params(
    client: TestClient, async_session, test_model, test_data
):
    for data in test_data:
        new_item = test_model(**data)
        async_session.add(new_item)
    await async_session.commit()
    cursor = True

    response = client.get(f"/test/get_multi?cursor={cursor}")
    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]) > 0

@pytest.mark.asyncio
async def test_read_items_with_pagination_cursor_correctly_ordered(
    client: TestClient, async_session, test_model, test_data
):
    for data in test_data:
        new_item = test_model(**data)
        async_session.add(new_item)
    await async_session.commit()

    cursor = True
    limit = 5

    response = client.get(f"/test/get_multi?cursor={cursor}&limit={limit}")

    assert response.status_code == 200

    data = response.json()

    assert "data" in data
    assert "total_count" in data
    assert "has_more" in data
    assert "cursor" in data

    assert len(data["data"]) > 0
    assert len(data["data"]) <= limit

    test_item = test_data[0]
    assert any(item["name"] == test_item["name"] for item in data["data"])

    ids1 = [item["id"] for item in data["data"]]
    assert data["cursor"] == max(ids1)

    # pagination should automatically order results by 
    # primary key to ensure consistent responses 
    cursor = data["cursor"]
    response2 = client.get(f"/test/get_multi?cursor={cursor}&limit={limit}")
    data2 = response2.json()
    ids1 = [td["id"] for td in data["data"]]
    ids2 = [td["id"] for td in data2["data"]]
    # this checks for disjoint sets of ids
    # and for correct sequential ordering
    assert max(ids1) < min(ids2) 

@pytest.mark.asyncio
async def test_read_items_with_pagination_cursor_and_filters_correctly_ordered(
    filtered_client: TestClient, async_session, test_model, test_data
):
    for data in test_data:
        new_item = test_model(**data)
        async_session.add(new_item)
    await async_session.commit()

    cursor = True
    limit = 5

    tier_id = 1
    response = filtered_client.get(
        f"/test/get_multi?cursor={cursor}&limit={limit}&tier_id={tier_id}"
    )

    assert response.status_code == 200
    data = response.json()

    assert "data" in data
    assert "total_count" in data
    assert "has_more" in data
    assert "cursor" in data

    assert len(data["data"]) > 0
    assert len(data["data"]) <= limit

    for item in data["data"]:
        assert item["tier_id"] == tier_id

    ids1 = [td["id"] for td in data["data"]]
    assert data["cursor"] == max(ids1)

    # pagination should automatically order results by 
    # primary key to ensure consistent responses 
    # e.g. for itemsPerPage=5, the first page should deliver items 1-5 and the second page items 6-10
    cursor = data["cursor"]
    response2 = filtered_client.get(
        f"/test/get_multi?cursor={cursor}&limit={limit}&tier_id={tier_id}"
    )
    data2 = response2.json()
    ids2 = [td["id"] for td in data2["data"]]
    # this checks for disjoint sets of ids
    # and for correct sequential ordering
    assert max(ids1) < min(ids2) 

    name = "Alice"
    response = filtered_client.get(
        f"/test/get_multi?cursor={cursor}&limit={limit}&name={name}"
    )

    assert response.status_code == 200
    data = response.json()

    assert "data" in data
    assert "total_count" in data
    assert "has_more" in data
    assert "cursor" in data

    assert len(data["data"]) > 0
    assert len(data["data"]) <= limit

    for item in data["data"]:
        assert item["name"] == name

