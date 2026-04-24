import uuid
from typing import Any

from fastapi import APIRouter, HTTPException
from sqlmodel import col, func, select

from app.api.deps import CurrentUser, SessionDep
from app.models import Item, ItemCreate, ItemPublic, ItemsPublic, ItemUpdate, Message

router = APIRouter(prefix="/items", tags=["items"])


@router.get("/", response_model=ItemsPublic)
def read_items(
    session: SessionDep, current_user: CurrentUser, skip: int = 0, limit: int = 100
) -> Any:
    """
    Retrieve items.
    """

    if current_user.is_superuser:
        count_statement = select(func.count()).select_from(Item)
        count = session.exec(count_statement).one()
        statement = (
            select(Item).order_by(col(Item.created_at).desc()).offset(skip).limit(limit)
        )
        items = session.exec(statement).all()
    else:
        count_statement = (
            select(func.count())
            .select_from(Item)
            .where(Item.owner_id == current_user.id)
        )
        count = session.exec(count_statement).one()
        statement = (
            select(Item)
            .where(Item.owner_id == current_user.id)
            .order_by(col(Item.created_at).desc())
            .offset(skip)
            .limit(limit)
        )
        items = session.exec(statement).all()

    items_public = [ItemPublic.model_validate(item) for item in items]
    return ItemsPublic(data=items_public, count=count)


@router.get("/{id}", response_model=ItemPublic)
def read_item(session: SessionDep, current_user: CurrentUser, id: uuid.UUID) -> Any:
    """
    Get item by ID.
    """
    item = session.get(Item, id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    if not current_user.is_superuser and (item.owner_id != current_user.id):
        raise HTTPException(status_code=403, detail="Not enough permissions")
    return item


@router.post("/", response_model=ItemPublic)
def create_item(
    *, session: SessionDep, current_user: CurrentUser, item_in: ItemCreate
) -> Any:
    """
    Create new item.
    """
    item = Item.model_validate(item_in, update={"owner_id": current_user.id})
    session.add(item)
    session.commit()
    session.refresh(item)
    return item


@router.post("/bulk", response_model=ItemsPublic)
def bulk_create_items(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    items_in: list[ItemCreate],
) -> Any:
    """
    Create multiple items in a single atomic operation.

    Returns 409 if any title is duplicated within the payload or already exists
    for the current user. No items are persisted on conflict.
    """
    titles = [item_in.title for item_in in items_in]

    seen: set[str] = set()
    duplicates_in_payload: set[str] = set()
    for title in titles:
        if title in seen:
            duplicates_in_payload.add(title)
        seen.add(title)
    if duplicates_in_payload:
        raise HTTPException(
            status_code=409,
            detail=(
                "Duplicate titles in payload: "
                f"{sorted(duplicates_in_payload)}"
            ),
        )

    existing_statement = select(Item.title).where(
        Item.owner_id == current_user.id,
        col(Item.title).in_(titles),
    )
    existing_titles = list(session.exec(existing_statement).all())
    if existing_titles:
        raise HTTPException(
            status_code=409,
            detail=(
                "Items with these titles already exist: "
                f"{sorted(existing_titles)}"
            ),
        )

    items: list[Item] = [
        Item.model_validate(item_in, update={"owner_id": current_user.id})
        for item_in in items_in
    ]
    try:
        session.add_all(items)
        session.commit()
    except Exception:
        session.rollback()
        raise
    for item in items:
        session.refresh(item)

    items_public = [ItemPublic.model_validate(item) for item in items]
    return ItemsPublic(data=items_public, count=len(items_public))


@router.put("/{id}", response_model=ItemPublic)
def update_item(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    id: uuid.UUID,
    item_in: ItemUpdate,
) -> Any:
    """
    Update an item.
    """
    item = session.get(Item, id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    if not current_user.is_superuser and (item.owner_id != current_user.id):
        raise HTTPException(status_code=403, detail="Not enough permissions")
    update_dict = item_in.model_dump(exclude_unset=True)
    item.sqlmodel_update(update_dict)
    session.add(item)
    session.commit()
    session.refresh(item)
    return item


@router.delete("/{id}")
def delete_item(
    session: SessionDep, current_user: CurrentUser, id: uuid.UUID
) -> Message:
    """
    Delete an item.
    """
    item = session.get(Item, id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    if not current_user.is_superuser and (item.owner_id != current_user.id):
        raise HTTPException(status_code=403, detail="Not enough permissions")
    session.delete(item)
    session.commit()
    return Message(message="Item deleted successfully")
