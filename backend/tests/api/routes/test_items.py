import uuid

from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app import crud
from app.core.config import settings
from app.models import Item, ItemCreate, UserCreate
from tests.utils.item import create_random_item
from tests.utils.user import create_random_user


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


def test_read_items_filter_status_superuser(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    active_user = create_random_user(db)
    inactive_user = create_random_user(db)
    inactive_user.is_active = False
    db.add(inactive_user)
    db.commit()
    db.refresh(inactive_user)

    active_item = crud.create_item(
        session=db,
        item_in=ItemCreate(
            title=f"status-active-{uuid.uuid4()}",
            description="active owner item",
        ),
        owner_id=active_user.id,
    )
    inactive_item = crud.create_item(
        session=db,
        item_in=ItemCreate(
            title=f"status-inactive-{uuid.uuid4()}",
            description="inactive owner item",
        ),
        owner_id=inactive_user.id,
    )

    active_response = client.get(
        f"{settings.API_V1_STR}/items/?status=active",
        headers=superuser_token_headers,
    )
    assert active_response.status_code == 200
    active_data = active_response.json()["data"]
    active_ids = {item["id"] for item in active_data}
    assert str(active_item.id) in active_ids
    assert str(inactive_item.id) not in active_ids

    inactive_response = client.get(
        f"{settings.API_V1_STR}/items/?status=inactive",
        headers=superuser_token_headers,
    )
    assert inactive_response.status_code == 200
    inactive_data = inactive_response.json()["data"]
    inactive_ids = {item["id"] for item in inactive_data}
    assert str(inactive_item.id) in inactive_ids
    assert str(active_item.id) not in inactive_ids


def test_read_items_filter_q_superuser(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    needle = f"needle-{uuid.uuid4()}"
    match_title = f"title-{needle}"
    no_match_title = f"q-title-{uuid.uuid4()}"

    first_response = client.post(
        f"{settings.API_V1_STR}/items/",
        headers=superuser_token_headers,
        json={"title": match_title, "description": "unrelated description"},
    )
    assert first_response.status_code == 200
    title_item_id = first_response.json()["id"]

    second_response = client.post(
        f"{settings.API_V1_STR}/items/",
        headers=superuser_token_headers,
        json={"title": f"q-title-{uuid.uuid4()}", "description": f"contains {needle}"},
    )
    assert second_response.status_code == 200
    description_item_id = second_response.json()["id"]

    third_response = client.post(
        f"{settings.API_V1_STR}/items/",
        headers=superuser_token_headers,
        json={"title": no_match_title, "description": "does not contain token"},
    )
    assert third_response.status_code == 200
    no_match_item_id = third_response.json()["id"]

    response = client.get(
        f"{settings.API_V1_STR}/items/?q={needle}",
        headers=superuser_token_headers,
    )
    assert response.status_code == 200
    content = response.json()
    ids = {item["id"] for item in content["data"]}
    assert title_item_id in ids
    assert description_item_id in ids
    assert no_match_item_id not in ids


def test_read_items_sort_title_asc_deterministic(
    client: TestClient, db: Session
) -> None:
    sort_user = crud.create_user(
        session=db,
        user_create=UserCreate(
            email=f"sort-{uuid.uuid4()}@example.com",
            password="sortpass123",
        ),
    )

    titles = ["zeta", "alpha", "gamma"]
    for title in titles:
        crud.create_item(
            session=db,
            item_in=ItemCreate(
                title=title,
                description=f"sort-seed-{uuid.uuid4()}",
            ),
            owner_id=sort_user.id,
        )

    login_response = client.post(
        f"{settings.API_V1_STR}/login/access-token",
        data={"username": sort_user.email, "password": "sortpass123"},
    )
    assert login_response.status_code == 200
    sort_headers = {"Authorization": f"Bearer {login_response.json()['access_token']}"}

    response = client.get(
        f"{settings.API_V1_STR}/items/?sort=title_asc",
        headers=sort_headers,
    )
    assert response.status_code == 200
    data = response.json()["data"]
    returned_titles = [item["title"] for item in data]
    assert returned_titles == sorted(titles)


def test_read_items_invalid_sort_validation(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    response = client.get(
        f"{settings.API_V1_STR}/items/?sort=bad_value",
        headers=superuser_token_headers,
    )
    assert response.status_code == 422
    content = response.json()
    assert "detail" in content


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
