import uuid

from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.core.config import settings
from app.models import Item
from tests.utils.item import create_random_item


def test_create_item(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    data = {"title": "Foo", "description": "Fighters"}
    response = client.post(
        f"{settings.API_V1_STR}/items/",
        headers=superuser_token_headers,
        json=data,
    )
    assert response.status_code == 200
    content = response.json()
    assert content["title"] == data["title"]
    assert content["description"] == data["description"]
    assert "id" in content
    assert "owner_id" in content


def test_read_item(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    item = create_random_item(db)
    response = client.get(
        f"{settings.API_V1_STR}/items/{item.id}",
        headers=superuser_token_headers,
    )
    assert response.status_code == 200
    content = response.json()
    assert content["title"] == item.title
    assert content["description"] == item.description
    assert content["id"] == str(item.id)
    assert content["owner_id"] == str(item.owner_id)


def test_read_item_not_found(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    response = client.get(
        f"{settings.API_V1_STR}/items/{uuid.uuid4()}",
        headers=superuser_token_headers,
    )
    assert response.status_code == 404
    content = response.json()
    assert content["detail"] == "Item not found"


def test_read_item_not_enough_permissions(
    client: TestClient, normal_user_token_headers: dict[str, str], db: Session
) -> None:
    item = create_random_item(db)
    response = client.get(
        f"{settings.API_V1_STR}/items/{item.id}",
        headers=normal_user_token_headers,
    )
    assert response.status_code == 403
    content = response.json()
    assert content["detail"] == "Not enough permissions"


def test_read_items(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    create_random_item(db)
    create_random_item(db)
    response = client.get(
        f"{settings.API_V1_STR}/items/",
        headers=superuser_token_headers,
    )
    assert response.status_code == 200
    content = response.json()
    assert len(content["data"]) >= 2


def test_update_item(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    item = create_random_item(db)
    data = {"title": "Updated title", "description": "Updated description"}
    response = client.put(
        f"{settings.API_V1_STR}/items/{item.id}",
        headers=superuser_token_headers,
        json=data,
    )
    assert response.status_code == 200
    content = response.json()
    assert content["title"] == data["title"]
    assert content["description"] == data["description"]
    assert content["id"] == str(item.id)
    assert content["owner_id"] == str(item.owner_id)


def test_update_item_not_found(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    data = {"title": "Updated title", "description": "Updated description"}
    response = client.put(
        f"{settings.API_V1_STR}/items/{uuid.uuid4()}",
        headers=superuser_token_headers,
        json=data,
    )
    assert response.status_code == 404
    content = response.json()
    assert content["detail"] == "Item not found"


def test_update_item_not_enough_permissions(
    client: TestClient, normal_user_token_headers: dict[str, str], db: Session
) -> None:
    item = create_random_item(db)
    data = {"title": "Updated title", "description": "Updated description"}
    response = client.put(
        f"{settings.API_V1_STR}/items/{item.id}",
        headers=normal_user_token_headers,
        json=data,
    )
    assert response.status_code == 403
    content = response.json()
    assert content["detail"] == "Not enough permissions"


def test_delete_item(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    item = create_random_item(db)
    response = client.delete(
        f"{settings.API_V1_STR}/items/{item.id}",
        headers=superuser_token_headers,
    )
    assert response.status_code == 200
    content = response.json()
    assert content["message"] == "Item deleted successfully"


def test_delete_item_not_found(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    response = client.delete(
        f"{settings.API_V1_STR}/items/{uuid.uuid4()}",
        headers=superuser_token_headers,
    )
    assert response.status_code == 404
    content = response.json()
    assert content["detail"] == "Item not found"


def test_delete_item_not_enough_permissions(
    client: TestClient, normal_user_token_headers: dict[str, str], db: Session
) -> None:
    item = create_random_item(db)
    response = client.delete(
        f"{settings.API_V1_STR}/items/{item.id}",
        headers=normal_user_token_headers,
    )
    assert response.status_code == 403
    content = response.json()
    assert content["detail"] == "Not enough permissions"


def test_bulk_create_items(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    suffix = uuid.uuid4().hex
    payload = [
        {"title": f"Bulk A {suffix}", "description": "first"},
        {"title": f"Bulk B {suffix}", "description": "second"},
        {"title": f"Bulk C {suffix}", "description": None},
    ]
    response = client.post(
        f"{settings.API_V1_STR}/items/bulk",
        headers=superuser_token_headers,
        json=payload,
    )
    assert response.status_code == 200
    content = response.json()
    assert content["count"] == 3
    assert len(content["data"]) == 3
    returned_titles = [item["title"] for item in content["data"]]
    assert sorted(returned_titles) == sorted(p["title"] for p in payload)
    for item in content["data"]:
        assert "id" in item
        assert "owner_id" in item


def test_bulk_create_items_validation_error(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    suffix = uuid.uuid4().hex
    payload = [
        {"title": f"Valid {suffix}", "description": "ok"},
        {"description": "missing title"},
    ]
    response = client.post(
        f"{settings.API_V1_STR}/items/bulk",
        headers=superuser_token_headers,
        json=payload,
    )
    assert response.status_code == 422


def test_bulk_create_items_duplicate_in_payload(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    suffix = uuid.uuid4().hex
    duplicate_title = f"Dup Payload {suffix}"
    payload = [
        {"title": duplicate_title, "description": "one"},
        {"title": f"Unique {suffix}", "description": "two"},
        {"title": duplicate_title, "description": "three"},
    ]
    response = client.post(
        f"{settings.API_V1_STR}/items/bulk",
        headers=superuser_token_headers,
        json=payload,
    )
    assert response.status_code == 409
    content = response.json()
    assert "detail" in content
    assert duplicate_title in content["detail"]

    existing = db.exec(
        select(Item).where(Item.title.in_([duplicate_title, f"Unique {suffix}"]))
    ).all()
    assert existing == []


def test_bulk_create_items_duplicate_against_existing(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    suffix = uuid.uuid4().hex
    existing_title = f"Existing {suffix}"

    response = client.post(
        f"{settings.API_V1_STR}/items/",
        headers=superuser_token_headers,
        json={"title": existing_title, "description": "already here"},
    )
    assert response.status_code == 200

    new_title = f"New {suffix}"
    payload = [
        {"title": new_title, "description": "fresh"},
        {"title": existing_title, "description": "conflict"},
    ]
    response = client.post(
        f"{settings.API_V1_STR}/items/bulk",
        headers=superuser_token_headers,
        json=payload,
    )
    assert response.status_code == 409
    content = response.json()
    assert "detail" in content
    assert existing_title in content["detail"]

    new_rows = db.exec(select(Item).where(Item.title == new_title)).all()
    assert new_rows == []

    existing_rows = db.exec(select(Item).where(Item.title == existing_title)).all()
    assert len(existing_rows) == 1


def test_bulk_create_items_atomic_no_partial_writes(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    suffix = uuid.uuid4().hex
    existing_title = f"Atomic Existing {suffix}"

    response = client.post(
        f"{settings.API_V1_STR}/items/",
        headers=superuser_token_headers,
        json={"title": existing_title, "description": "seed"},
    )
    assert response.status_code == 200

    non_conflicting_titles = [
        f"Atomic A {suffix}",
        f"Atomic B {suffix}",
        f"Atomic C {suffix}",
    ]
    payload = [
        {"title": non_conflicting_titles[0], "description": "a"},
        {"title": non_conflicting_titles[1], "description": "b"},
        {"title": existing_title, "description": "conflict"},
        {"title": non_conflicting_titles[2], "description": "c"},
    ]
    response = client.post(
        f"{settings.API_V1_STR}/items/bulk",
        headers=superuser_token_headers,
        json=payload,
    )
    assert response.status_code == 409

    for title in non_conflicting_titles:
        rows = db.exec(select(Item).where(Item.title == title)).all()
        assert rows == [], f"non-conflicting title {title} should not be persisted"
