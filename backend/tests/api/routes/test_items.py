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


def test_create_items_bulk(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    first_title = f"bulk-{uuid.uuid4()}"
    second_title = f"bulk-{uuid.uuid4()}"
    data = [
        {"title": first_title, "description": "Bulk item one"},
        {"title": second_title, "description": "Bulk item two"},
    ]
    response = client.post(
        f"{settings.API_V1_STR}/items/bulk",
        headers=superuser_token_headers,
        json=data,
    )
    assert response.status_code == 200
    content = response.json()
    assert content["count"] == 2
    assert len(content["data"]) == 2
    assert content["data"][0]["title"] == first_title
    assert content["data"][1]["title"] == second_title
    assert "id" in content["data"][0]
    assert "id" in content["data"][1]
    assert "owner_id" in content["data"][0]
    assert "owner_id" in content["data"][1]


def test_create_items_bulk_validation_error(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    response = client.post(
        f"{settings.API_V1_STR}/items/bulk",
        headers=superuser_token_headers,
        json=[{"description": "Missing title"}],
    )
    assert response.status_code == 422
    content = response.json()
    assert "detail" in content


def test_create_items_bulk_duplicate_titles_in_payload(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    duplicate_title = f"bulk-duplicate-{uuid.uuid4()}"
    data = [
        {"title": duplicate_title, "description": "first"},
        {"title": duplicate_title, "description": "second"},
    ]
    response = client.post(
        f"{settings.API_V1_STR}/items/bulk",
        headers=superuser_token_headers,
        json=data,
    )
    assert response.status_code == 409
    content = response.json()
    assert content["detail"] == "Item with this title already exists"


def test_create_items_bulk_duplicate_title_existing_item(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    existing_title = f"bulk-existing-{uuid.uuid4()}"
    create_response = client.post(
        f"{settings.API_V1_STR}/items/",
        headers=superuser_token_headers,
        json={"title": existing_title, "description": "Already there"},
    )
    assert create_response.status_code == 200
    owner_id = create_response.json()["owner_id"]
    new_title = f"bulk-new-{uuid.uuid4()}"
    response = client.post(
        f"{settings.API_V1_STR}/items/bulk",
        headers=superuser_token_headers,
        json=[
            {"title": existing_title, "description": "Duplicate"},
            {"title": new_title, "description": "Should not be created"},
        ],
    )
    assert response.status_code == 409
    content = response.json()
    assert content["detail"] == "Item with this title already exists"
    should_not_exist = db.exec(
        select(Item).where(Item.owner_id == owner_id, Item.title == new_title)
    ).first()
    assert should_not_exist is None


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
