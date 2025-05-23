# app/crud/match_crud.py
from datetime import date, datetime
from typing import List, Optional, Sequence
from sqlmodel import Session, select

from app.db.models.chat_room_model import ChatRoom, ChatRoomCreate
from app.db.models.chat_room_participant_model import ChatRoomParticipant, ChatRoomParticipantCreate
from app.db.models.user_model import User # 用于类型提示

def create_chat_room(db: Session, event_date: date, room_type: Optional[str] = None) -> ChatRoom:
    room_create = ChatRoomCreate(event_date=event_date, room_type=room_type)
    # room_identifier 会自动生成
    db_room = ChatRoom.model_validate(room_create)
    db.add(db_room)
    db.commit()
    db.refresh(db_room)
    return db_room

def add_participant_to_room(db: Session, room_id: int, user_id: int) -> ChatRoomParticipant:
    participant_create = ChatRoomParticipantCreate(room_id=room_id, user_id=user_id)
    db_participant = ChatRoomParticipant.model_validate(participant_create)
    db.add(db_participant)
    db.commit()
    db.refresh(db_participant)
    return db_participant

def get_user_match_for_date(db: Session, user_id: int, event_date: date) -> Optional[ChatRoom]:
    """获取用户在特定日期的匹配房间信息"""
    statement = (
        select(ChatRoom)
        .join(ChatRoomParticipant, ChatRoom.id == ChatRoomParticipant.room_id)
        .where(ChatRoomParticipant.user_id == user_id)
        .where(ChatRoom.event_date == event_date)
    )
    room = db.exec(statement).first()
    return room

def get_participants_for_room(db: Session, room_id: int) -> List[User]:
    """获取特定房间的所有参与用户信息"""
    statement = (
        select(User)
        .join(ChatRoomParticipant, User.id == ChatRoomParticipant.user_id)
        .where(ChatRoomParticipant.room_id == room_id)
    )
    users = db.exec(statement).all()
    return users

def check_if_matches_generated_for_date(db: Session, event_date: date) -> bool:
    """检查指定日期是否已生成过匹配"""
    statement = select(ChatRoom).where(ChatRoom.event_date == event_date).limit(1)
    return db.exec(statement).first() is not None

def delete_matches_for_date(db: Session, event_date: date) -> int:
    """删除指定日期的所有匹配房间和参与者记录 (用于重新匹配或清理)"""
    # 先删除参与者，再删除房间，或者配置级联删除
    # 获取当天所有房间ID
    rooms_stmt = select(ChatRoom.id).where(ChatRoom.event_date == event_date)
    room_ids_result = db.exec(rooms_stmt).all()
    if not room_ids_result:
        return 0
    
    room_ids = [r_id for r_id in room_ids_result] # 解包元组

    # 删除参与者
    delete_participants_stmt = ChatRoomParticipant.__table__.delete().where(ChatRoomParticipant.room_id.in_(room_ids))
    db.exec(delete_participants_stmt) # 使用 execute 对于批量删除

    # 删除房间
    delete_rooms_stmt = ChatRoom.__table__.delete().where(ChatRoom.id.in_(room_ids))
    result = db.exec(delete_rooms_stmt)
    
    db.commit()
    return result.rowcount if result else 0 # 返回删除的房间数量