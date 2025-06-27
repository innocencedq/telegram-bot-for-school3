from sqlalchemy import BigInteger, Column, String, DateTime, Boolean, Integer
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.ext.asyncio import AsyncAttrs, async_sessionmaker, create_async_engine
from datetime import datetime
import pytz

from config import sqlalchemy_url


#Все названия отвечают сами за себя
engine = create_async_engine(sqlalchemy_url)

async_session = async_sessionmaker(engine)


class Base(AsyncAttrs, DeclarativeBase):
    pass


class User(Base):
    __tablename__ = 'users'

    tg_id = Column(BigInteger, primary_key=True, unique=True, nullable=False)
    username = Column(String, default='unspecified_username')
    date_started = Column(DateTime, default=lambda: datetime.now(pytz.timezone('Asia/Krasnoyarsk')))
    notify_vk = Column(Boolean, default=False)
    quick_menu = Column(Boolean, default=False)
    requests_ai: Mapped[int] = mapped_column(default=35)
    refresh_token: Mapped[str] = mapped_column(unique=True, default='None')
    access_token: Mapped[str] = mapped_column(unique=True, default='None')
    extended_diary = Column(Boolean, default=True)
    tester = Column(Boolean, default=False)


class Admin(Base):
    __tablename__ = 'admins'

    tg_id = Column(BigInteger, primary_key=True, unique=True, nullable=False)
    username = Column(String, nullable=False)


class Images(Base):
    __tablename__ = 'images'

    id: Mapped[int] = mapped_column(primary_key=True, unique=True, nullable=False)
    image_id: Mapped[str] = mapped_column(unique=False)
    image_name: Mapped[str] = mapped_column()


class Static(Base):
    __tablename__ = 'static'

    id: Mapped[int] = mapped_column(primary_key=True, unique=True, nullable=False)
    active_users: Mapped[int] = mapped_column()


class Advert(Base):
    __tablename__ = 'advert'

    id: Mapped[int] = mapped_column(primary_key=True, nullable=False, unique=True)
    title: Mapped[str] = mapped_column(default='Без заголовка')
    description: Mapped[str] = mapped_column(default='Без описания')
    file_id: Mapped[str] = mapped_column()


async def async_main():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
