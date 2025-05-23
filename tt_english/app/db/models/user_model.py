from typing import Optional, List
from sqlmodel import Field, SQLModel, Relationship

class UserBase(SQLModel):
    openid: str = Field(unique=True, index=True, description="微信用户唯一标识")
    nickname: Optional[str] = Field(default=None, description="用户昵称")
    avatar_url: Optional[str] = Field(default=None, description="用户头像URL")
    industry: Optional[str] = Field(default=None, description="工作行业")
    eng_level: Optional[int] = Field(default=None, description="英语水平")
    introduction: Optional[str] = Field(default=None, description="用户填入的about me内容")
    is_active: bool = Field(default=True, description="true为可正常使用的用户，false为进入黑名单的用户")

class User(UserBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

class UserCreate(UserBase):
    pass

class UserRead(UserBase):
    id: int

class UserUpdate(SQLModel):
    #? 其实我认为这里应该也可以改industry
    introduction: Optional[str] = None  #* 目前的设计用户只能修改about me部分信息

class TokenData(SQLModel): 
    openid: Optional[str] = None

class Token(SQLModel):
    access_token: str
    token_type: str
    user_info: UserRead
    is_new_user: bool

class LoginRequest(SQLModel):
    code: str
    nickname: Optional[str] = None
    avatar_url: Optional[str] = None

# 新用户需要输入的英语水平和所在行业信息
class OrigianlInfo(SQLModel):
    eng_level: int
    industry: str