import uuid
from enum import Enum
from typing import Any

from fastapi import APIRouter, HTTPException, Query
from sqlmodel import col, func, or_, select

from app.api.deps import CurrentUser, SessionDep
from app.models import Item, ItemCreate, ItemPublic, ItemsPublic, ItemUpdate, Message

router = APIRouter(prefix="/items", tags=["items"])


class ItemSort(str, Enum):
    created_at_desc = "created_at_desc"
    created_at_asc = "created_at_asc"
    title_asc = "title_asc"
    title_desc = "title_desc"


class ItemStatus(str, Enum):
    """Filter items by ownership.

    The ``Item`` model has no explicit ``status`` column, so we expose the
    closest existing domain concept: whether the item belongs to the current
    user (``mine``) or to another user (``others``). Normal users can only
    read their own items, so ``others`` is mainly meaningful for superusers.
    """

    mine = "mine"
    others = "others"


@router.get("/", response_model=ItemsPublic)
def read_items(
    session: SessionDep,
    current_user: CurrentUser,
    skip: int = 0,
    limit: int = 100,
    status: ItemStatus | None = Query(
        default=None,
        description="Filter by ownership: 'mine' or 'others'.",
    ),
    sort: ItemSort = Query(
        default=ItemSort.created_at_desc,
        description="Sort order for results.",
    ),
    q: str | None = Query(
        default=None,
        description="Case-insensitive search across title and description.",
    ),
) -> Any:
    """
    Retrieve items.

    Supports optional filtering (``status``, ``q``) and sorting (``sort``).
    Omitting all optional query parameters preserves the previous default
    behavior: items are returned sorted by ``created_at`` descending, scoped
    by the caller's permissions.
    """

    count_statement = select(func.count()).select_from(Item)
    statement = select(Item)

    if not current_user.is_superuser:
        count_statement = count_statement.where(Item.owner_id == current_user.id)
        statement = statement.where(Item.owner_id == current_user.id)

    if status is ItemStatus.mine:
        count_statement = count_statement.where(Item.owner_id == current_user.id)
        statement = statement.where(Item.owner_id == current_user.id)
    elif status is ItemStatus.others:
        count_statement = count_statement.where(Item.owner_id != current_user.id)
        statement = statement.where(Item.owner_id != current_user.id)

    if q:
        like_pattern = f"%{q}%"
        search_clause = or_(
            col(Item.title).ilike(like_pattern),
            col(Item.description).ilike(like_pattern),
        )
        count_statement = count_statement.where(search_clause)
        statement = statement.where(search_clause)

    # Apply a deterministic ordering with a stable tie-breaker on the
    # primary key so that pagination and equal-key rows are reproducible.
    if sort is ItemSort.created_at_asc:
        statement = statement.order_by(col(Item.created_at).asc(), col(Item.id).asc())
    elif sort is ItemSort.title_asc:
        statement = statement.order_by(
            col(Item.title).asc(),
            col(Item.created_at).desc(),
            col(Item.id).asc(),
        )
    elif sort is ItemSort.title_desc:
        statement = statement.order_by(
            col(Item.title).desc(),
            col(Item.created_at).desc(),
            col(Item.id).asc(),
        )
    else:
        statement = statement.order_by(col(Item.created_at).desc(), col(Item.id).asc())

    count = session.exec(count_statement).one()
    statement = statement.offset(skip).limit(limit)
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
