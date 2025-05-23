# app/db/models/chat_room_participant_model.py
from datetime import datetime, date
from typing import Optional, TYPE_CHECKING, List
from sqlmodel import Field, SQLModel, Relationship

if TYPE_CHECKING:
    from app.db.models.user_model import User
    from app.db.models.chat_room_model import ChatRoom
    # from app.db.models.user_model import UserRead # 如果 ChatRoomParticipantRead 需要嵌套 UserRead

class ChatRoomParticipantBase(SQLModel):
    user_id: int = Field(foreign_key="user.id", index=True)
    room_id: int = Field(foreign_key="chatroom.id", index=True)
    joined_at: datetime = Field(default_factory=datetime.utcnow, description="用户加入房间的时间 (UTC)")
    # 可以在此记录用户参与时的一些状态，如果需要的话

class ChatRoomParticipant(ChatRoomParticipantBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

    # 关系：参与者属于哪个用户
    user: Optional["User"] = Relationship() # back_populates 可以不设置，如果 User 模型不直接反向访问它
    # 关系：参与者属于哪个房间
    room: Optional["ChatRoom"] = Relationship(back_populates="participants")

class ChatRoomParticipantCreate(ChatRoomParticipantBase):
    pass

# 用于API返回的，可能包含更详细的用户信息
class ChatRoomParticipantRead(ChatRoomParticipantBase):
    id: int
    # user: Optional["UserRead"] = None # 嵌套用户信息

# 扩展 ChatRoomRead 以包含完整的参与者信息
# 需要在 chat_room_model.py 中调整 ChatRoomRead，或者创建一个新的复合模型
# 例如:
# class ChatRoomReadWithParticipants(ChatRoomRead):
#     participants: List[ChatRoomParticipantRead] = []

from app.db.models.user_model import UserRead
# 用于用户查询自己匹配结果的响应模型
class MyMatchResult(SQLModel):
    room_identifier: str
    event_date: date
    room_type: Optional[str] = None
    participants: List["UserRead"]