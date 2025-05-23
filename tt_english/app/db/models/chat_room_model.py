# app/db/models/chat_room_model.py
from datetime import datetime, date
from typing import Optional, List, TYPE_CHECKING
from sqlmodel import Field, SQLModel, Relationship
import uuid # 用于生成唯一的房间标识

if TYPE_CHECKING:
    from app.db.models.user_model import User # 用于类型提示和关系
    from app.db.models.chat_room_participant_model import ChatRoomParticipant # 用于关系

class ChatRoomBase(SQLModel):
    event_date: date = Field(index=True, description="活动日期，与报名日期对应")
    # 使用 UUID 作为房间的唯一业务标识符，方便前端使用
    room_identifier: str = Field(default_factory=lambda: str(uuid.uuid4()), unique=True, index=True, description="房间的唯一业务标识符")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="房间创建时间 (UTC)")
    # 可以增加一个字段表示房间类型，例如 2人房，3人房
    room_type: Optional[str] = Field(default=None, description="房间类型 (e.g., '2-person', '3-person')")


class ChatRoom(ChatRoomBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

    # 关系：一个聊天室可以有多个参与者
    participants: List["ChatRoomParticipant"] = Relationship(back_populates="room")

class ChatRoomCreate(ChatRoomBase):
    pass

class ChatRoomRead(ChatRoomBase):
    id: int
    # 如果需要在读取房间信息时同时返回参与者信息，可以添加
    # from app.db.models.chat_room_participant_model import ChatRoomParticipantRead (需要先定义)
    # participants: List["ChatRoomParticipantRead"] = []