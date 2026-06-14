from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
import json

from database import get_db
from models import User, GroupSession, GroupMember, GroupItem, CartItem, UserProfile
from routers.auth import get_current_user
from services.group_service import generate_code, resolve_consensus
from services.product_service import get_product_by_id

router = APIRouter(prefix="/api/group", tags=["group"])


# ── Request models ────────────────────────────────────────────────────────────

class CreateGroupRequest(BaseModel):
    name: str = "Group Cart"


class AddItemRequest(BaseModel):
    product_id: str


# ── Helpers ────────────────────────────────────────────────────────────────────

def _get_session(code: str, db: Session) -> GroupSession:
    s = db.query(GroupSession).filter(GroupSession.code == code.upper()).first()
    if not s:
        raise HTTPException(status_code=404, detail="Group session not found")
    return s


def _ensure_member(session: GroupSession, user: User, db: Session) -> GroupMember:
    """Get or create the current user's membership in this session, copying diet prefs."""
    member = (
        db.query(GroupMember)
        .filter(GroupMember.session_id == session.id, GroupMember.user_id == user.id)
        .first()
    )
    if member:
        return member
    profile = db.query(UserProfile).filter(UserProfile.user_id == user.id).first()
    member = GroupMember(
        session_id=session.id,
        user_id=user.id,
        display_name=user.username,
        is_vegetarian=bool(profile.is_vegetarian) if profile else False,
        is_vegan=bool(profile.is_vegan) if profile else False,
    )
    db.add(member)
    db.commit()
    db.refresh(member)
    return member


def _serialize(session: GroupSession, db: Session, me: GroupMember) -> dict:
    members = db.query(GroupMember).filter(GroupMember.session_id == session.id).all()
    items = db.query(GroupItem).filter(GroupItem.session_id == session.id).all()

    item_list = []
    for it in items:
        product = get_product_by_id(it.product_id)
        try:
            voters = json.loads(it.votes or "[]")
        except Exception:
            voters = []
        item_list.append({
            "item_id": it.id,
            "product": product,
            "product_name": it.product_name,
            "added_by": it.added_by,
            "vote_count": len(voters),
            "voted_by_me": me.id in voters,
        })
    item_list.sort(key=lambda x: -x["vote_count"])

    consensus = resolve_consensus(members, items)

    return {
        "code": session.code,
        "name": session.name,
        "me": {"id": me.id, "display_name": me.display_name},
        "members": [
            {
                "id": m.id,
                "display_name": m.display_name,
                "is_vegetarian": m.is_vegetarian,
                "is_vegan": m.is_vegan,
            }
            for m in members
        ],
        "items": item_list,
        "consensus": consensus,
    }


# ── Endpoints ────────────────────────────────────────────────────────────────

@router.post("/create")
def create_group(
    data: CreateGroupRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # generate a unique code
    code = generate_code()
    while db.query(GroupSession).filter(GroupSession.code == code).first():
        code = generate_code()

    session = GroupSession(code=code, name=data.name, owner_id=current_user.id)
    db.add(session)
    db.commit()
    db.refresh(session)

    me = _ensure_member(session, current_user, db)
    return _serialize(session, db, me)


@router.post("/{code}/join")
def join_group(
    code: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    session = _get_session(code, db)
    me = _ensure_member(session, current_user, db)
    return _serialize(session, db, me)


@router.get("/{code}")
def get_group(
    code: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    session = _get_session(code, db)
    me = _ensure_member(session, current_user, db)
    return _serialize(session, db, me)


@router.post("/{code}/items")
def add_item(
    code: str,
    data: AddItemRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    session = _get_session(code, db)
    me = _ensure_member(session, current_user, db)
    product = get_product_by_id(data.product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    # avoid duplicates
    existing = (
        db.query(GroupItem)
        .filter(GroupItem.session_id == session.id, GroupItem.product_id == data.product_id)
        .first()
    )
    if not existing:
        item = GroupItem(
            session_id=session.id,
            product_id=data.product_id,
            product_name=product["name"],
            added_by=me.display_name,
            votes=json.dumps([me.id]),   # adder auto-upvotes
        )
        db.add(item)
        db.commit()
    return _serialize(session, db, me)


@router.post("/{code}/items/{item_id}/vote")
def vote_item(
    code: str,
    item_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    session = _get_session(code, db)
    me = _ensure_member(session, current_user, db)
    item = db.query(GroupItem).filter(GroupItem.id == item_id, GroupItem.session_id == session.id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    try:
        voters = json.loads(item.votes or "[]")
    except Exception:
        voters = []
    if me.id in voters:
        voters.remove(me.id)        # toggle off
    else:
        voters.append(me.id)
    item.votes = json.dumps(voters)
    db.commit()
    return _serialize(session, db, me)


@router.delete("/{code}/items/{item_id}")
def remove_item(
    code: str,
    item_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    session = _get_session(code, db)
    me = _ensure_member(session, current_user, db)
    item = db.query(GroupItem).filter(GroupItem.id == item_id, GroupItem.session_id == session.id).first()
    if item:
        db.delete(item)
        db.commit()
    return _serialize(session, db, me)


@router.post("/{code}/checkout-to-cart")
def push_consensus_to_cart(
    code: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Add the group-approved final cart to the current user's personal cart."""
    session = _get_session(code, db)
    me = _ensure_member(session, current_user, db)
    members = db.query(GroupMember).filter(GroupMember.session_id == session.id).all()
    items = db.query(GroupItem).filter(GroupItem.session_id == session.id).all()
    consensus = resolve_consensus(members, items)

    added = 0
    for prod in consensus["final_cart"]:
        pid = prod["id"]
        existing = (
            db.query(CartItem)
            .filter(CartItem.user_id == current_user.id, CartItem.product_id == pid)
            .first()
        )
        if existing:
            existing.quantity += 1
        else:
            db.add(CartItem(user_id=current_user.id, product_id=pid, quantity=1))
        added += 1
    db.commit()
    return {"added": added, "message": f"Added {added} group-approved items to your cart!"}
