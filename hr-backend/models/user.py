import enum
from typing import List, Optional

from pwdlib import PasswordHash
from sqlalchemy import String, Boolean, Enum as SEnum, ForeignKey, Table, Column
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import BaseModel, Base

password_hasher = PasswordHash.recommended()#密码哈希器

# 用户状态枚举
class UserStatus(enum.Enum):
    ACTIVE = "ACTIVE"  
    BLOCKED = "BLOCKED"
    RESIGNED = "RESIGNED" # 离职


# 存储HR管理员与部门的多对多关系，一个HR管理员可以管理多个部门，一个部门也可以被多个HR管理员管理
hr_managed_departments = Table(
    "hr_managed_departments", 
    Base.metadata, 
    Column("user_id", ForeignKey("users.id"), primary_key=True),
    Column("department_id", ForeignKey("departments.id"), primary_key=True),
)


class UserModel(BaseModel):
    __tablename__ = "users"

    username: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    _password: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    phone_number: Mapped[Optional[str]] = mapped_column(String(20), unique=True, index=True)
    realname: Mapped[str] = mapped_column(String(50), nullable=False)
    avatar: Mapped[Optional[str]] = mapped_column(String(255))
    department_id: Mapped[Optional[str]] = mapped_column(ForeignKey("departments.id"))
    status: Mapped[UserStatus] = mapped_column(SEnum(UserStatus), default=UserStatus.ACTIVE)
    is_hr: Mapped[bool] = mapped_column(Boolean, default=False)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False)

    # 关联: 所属部门（多对一），一个部门可以有多个用户
    department: Mapped[Optional["DepartmentModel"]] = relationship(
        back_populates="members", foreign_keys=[department_id],
    )
    # 关联: HR 管理的部门（多对多）
    managed_departments: Mapped[List["DepartmentModel"]] = relationship(
        secondary=hr_managed_departments, back_populates="managing_hrs",
    )
    # 关联: 钉钉信息（一对一）
    dingding_user: Mapped["DingdingUserModel"] = relationship(
        back_populates="user", uselist=False,
    )
    
    #创建用户时对密码进行哈希处理
    def __init__(self, **kwargs):
        if "password" in kwargs:
            raw_password = kwargs.pop("password")
            kwargs["_password"] = password_hasher.hash(raw_password)
        super().__init__(**kwargs)
    
    #读取密码时只获取哈希值
    @property  # 将方法变成属性访问，user.password 调用此方法。
    def password(self) -> str:
        return self._password

    # 设置密码时自动哈希
    @password.setter
    def password(self, password: str) -> None:
        self._password = password_hasher.hash(password)

    # 验证密码
    def check_password(self, password: str) -> bool:
        return password_hasher.verify(password, self._password)


class DepartmentModel(BaseModel):
    __tablename__ = "departments"

    name: Mapped[str] = mapped_column(
        String(100), unique=True, index=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(255))

    members: Mapped[List["UserModel"]] = relationship(
        back_populates="department")
    managing_hrs: Mapped[List["UserModel"]] = relationship(
        secondary=hr_managed_departments, back_populates="managed_departments",
    )


class DingdingUserModel(BaseModel):
    __tablename__ = "dingding_user"

    nick: Mapped[str] = mapped_column(String(100), nullable=False)
    union_id: Mapped[str] = mapped_column(
        String(100), unique=True, index=True, nullable=False)
    open_id: Mapped[str] = mapped_column(
        String(100), unique=True, index=True, nullable=False)
    mobile: Mapped[str] = mapped_column(
        String(20), unique=True, index=True, nullable=False)
    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id"), nullable=False)

    user: Mapped["UserModel"] = relationship(back_populates="dingding_user")
