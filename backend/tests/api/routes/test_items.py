import uuid

from fastapi.testclient import TestClient
from sqlmodel import Session, delete

from app import crud
from app.core.config import settings
from app.models import Item, ItemCreate, User
from tests.utils.item import create_random_item
from tests.utils.user import create_random_user
from tests.utils.utils import random_lower_string


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


def _reset_items(db: Session) -> None:
    db.execute(delete(Item))
    db.commit()


def _get_superuser(db: Session) -> User:
    from sqlmodel import select

    user = db.exec(
        select(User).where(User.email == settings.FIRST_SUPERUSER)
    ).one()
    return user


def test_read_items_filter_by_status_mine(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    _reset_items(db)
    superuser = _get_superuser(db)
    other_user = create_random_user(db)

    own_item = crud.create_item(
        session=db,
        item_in=ItemCreate(title="mine-title", description="own desc"),
        owner_id=superuser.id,
    )
    other_item = crud.create_item(
        session=db,
        item_in=ItemCreate(title="others-title", description="other desc"),
        owner_id=other_user.id,
    )

    response = client.get(
        f"{settings.API_V1_STR}/items/?status=mine",
        headers=superuser_token_headers,
    )
    assert response.status_code == 200
    content = response.json()
    ids = {row["id"] for row in content["data"]}
    assert str(own_item.id) in ids
    assert str(other_item.id) not in ids
    assert content["count"] == 1

    response = client.get(
        f"{settings.API_V1_STR}/items/?status=others",
        headers=superuser_token_headers,
    )
    assert response.status_code == 200
    content = response.json()
    ids = {row["id"] for row in content["data"]}
    assert str(other_item.id) in ids
    assert str(own_item.id) not in ids
    assert content["count"] == 1


def test_read_items_q_search_case_insensitive(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    _reset_items(db)
    superuser = _get_superuser(db)

    needle = "ZeBrA-" + random_lower_string()
    matching_title = crud.create_item(
        session=db,
        item_in=ItemCreate(title=f"hello {needle} world", description="desc-a"),
        owner_id=superuser.id,
    )
    matching_desc = crud.create_item(
        session=db,
        item_in=ItemCreate(title="unrelated", description=f"stuff {needle} stuff"),
        owner_id=superuser.id,
    )
    non_matching = crud.create_item(
        session=db,
        item_in=ItemCreate(title="no-match", description="nothing here"),
        owner_id=superuser.id,
    )

    response = client.get(
        f"{settings.API_V1_STR}/items/?q={needle.lower()}",
        headers=superuser_token_headers,
    )
    assert response.status_code == 200
    content = response.json()
    ids = {row["id"] for row in content["data"]}
    assert str(matching_title.id) in ids
    assert str(matching_desc.id) in ids
    assert str(non_matching.id) not in ids
    assert content["count"] == 2


def test_read_items_sort_title_asc_and_desc(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    _reset_items(db)
    superuser = _get_superuser(db)

    titles = ["banana", "apple", "cherry"]
    for title in titles:
        crud.create_item(
            session=db,
            item_in=ItemCreate(title=title, description="sort-test"),
            owner_id=superuser.id,
        )

    response = client.get(
        f"{settings.API_V1_STR}/items/?sort=title_asc",
        headers=superuser_token_headers,
    )
    assert response.status_code == 200
    titles_asc = [row["title"] for row in response.json()["data"]]
    assert titles_asc == ["apple", "banana", "cherry"]

    response = client.get(
        f"{settings.API_V1_STR}/items/?sort=title_desc",
        headers=superuser_token_headers,
    )
    assert response.status_code == 200
    titles_desc = [row["title"] for row in response.json()["data"]]
    assert titles_desc == ["cherry", "banana", "apple"]


def test_read_items_sort_created_at_asc_and_default_desc(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    _reset_items(db)
    superuser = _get_superuser(db)

    created = []
    for i in range(3):
        item = crud.create_item(
            session=db,
            item_in=ItemCreate(title=f"item-{i}", description="chrono"),
            owner_id=superuser.id,
        )
        created.append(item)

    # Default (no sort) should equal created_at_desc.
    response_default = client.get(
        f"{settings.API_V1_STR}/items/",
        headers=superuser_token_headers,
    )
    assert response_default.status_code == 200
    ids_default = [row["id"] for row in response_default.json()["data"]]

    response_desc = client.get(
        f"{settings.API_V1_STR}/items/?sort=created_at_desc",
        headers=superuser_token_headers,
    )
    assert response_desc.status_code == 200
    ids_desc = [row["id"] for row in response_desc.json()["data"]]
    assert ids_default == ids_desc

    response_asc = client.get(
        f"{settings.API_V1_STR}/items/?sort=created_at_asc",
        headers=superuser_token_headers,
    )
    assert response_asc.status_code == 200
    ids_asc = [row["id"] for row in response_asc.json()["data"]]
    assert ids_asc == list(reversed(ids_desc))


def test_read_items_invalid_sort_returns_422(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    response = client.get(
        f"{settings.API_V1_STR}/items/?sort=bogus",
        headers=superuser_token_headers,
    )
    assert response.status_code == 422


def test_read_items_invalid_status_returns_422(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    response = client.get(
        f"{settings.API_V1_STR}/items/?status=bogus",
        headers=superuser_token_headers,
    )
    assert response.status_code == 422
