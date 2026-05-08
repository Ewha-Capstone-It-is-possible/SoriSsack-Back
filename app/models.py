from datetime import datetime
from typing import Any, Optional

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class BabyBasicInformation(Base):
    __tablename__ = "baby_basic_information"

    baby_id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    baby_name: Mapped[str] = mapped_column(String(100), nullable=False)
    sex: Mapped[str] = mapped_column(String(1), nullable=False)
    birth: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    baby_cards = relationship("BabyCard", back_populates="baby")
    vocab_logs = relationship("BabyVocabLog", back_populates="baby")
    sentences = relationship("SentenceMaster", back_populates="baby")


class CardMaster(Base):
    __tablename__ = "card_master"

    card_id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    base_text: Mapped[str] = mapped_column(String(255), nullable=False)
    normalized_text: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, unique=True)
    part_of_speech: Mapped[str] = mapped_column(String(50), nullable=False)
    default_image_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    baby_cards = relationship("BabyCard", back_populates="card_master")
    vocab_logs = relationship("BabyVocabLog", back_populates="card_master")
    category_maps = relationship("CardCategoryMapMaster", back_populates="card_master")


class BabyCard(Base):
    __tablename__ = "baby_card"

    baby_card_id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    baby_id: Mapped[int] = mapped_column(ForeignKey("baby_basic_information.baby_id"), nullable=False, index=True)
    card_id: Mapped[Optional[int]] = mapped_column(ForeignKey("card_master.card_id"), nullable=True, index=True)
    text: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    part_of_speech: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    custom_image_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    is_favorite: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    source: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="default", nullable=False)
    usage_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_used_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    baby = relationship("BabyBasicInformation", back_populates="baby_cards")
    card_master = relationship("CardMaster", back_populates="baby_cards")
    vocab_logs = relationship("BabyVocabLog", back_populates="baby_card")
    category_maps = relationship("BabyCardCategoryMap", back_populates="baby_card")


class CategoryMaster(Base):
    __tablename__ = "category_master"

    category_id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    icon_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    baby_categories = relationship("BabyCategory", back_populates="category_master")
    card_maps = relationship("CardCategoryMapMaster", back_populates="category_master")


class CardCategoryMapMaster(Base):
    __tablename__ = "card_category_map_master"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    card_id: Mapped[int] = mapped_column(ForeignKey("card_master.card_id"), nullable=False, index=True)
    category_id: Mapped[int] = mapped_column(ForeignKey("category_master.category_id"), nullable=False, index=True)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    card_master = relationship("CardMaster", back_populates="category_maps")
    category_master = relationship("CategoryMaster", back_populates="card_maps")


class BabyCategory(Base):
    __tablename__ = "baby_category"

    baby_category_id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    baby_id: Mapped[int] = mapped_column(ForeignKey("baby_basic_information.baby_id"), nullable=False, index=True)
    category_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("category_master.category_id"), nullable=True, index=True
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    icon_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_favorite: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    priority: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    system_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    manual_order: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    category_master = relationship("CategoryMaster", back_populates="baby_categories")
    card_maps = relationship("BabyCardCategoryMap", back_populates="baby_category")


class BabyCardCategoryMap(Base):
    __tablename__ = "baby_card_category_map"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    baby_id: Mapped[int] = mapped_column(ForeignKey("baby_basic_information.baby_id"), nullable=False, index=True)
    baby_card_id: Mapped[int] = mapped_column(ForeignKey("baby_card.baby_card_id"), nullable=False, index=True)
    baby_category_id: Mapped[int] = mapped_column(
        ForeignKey("baby_category.baby_category_id"), nullable=False, index=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    baby_card = relationship("BabyCard", back_populates="category_maps")
    baby_category = relationship("BabyCategory", back_populates="card_maps")


class BabyVocabLog(Base):
    __tablename__ = "baby_vocab_log"

    log_id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    baby_id: Mapped[int] = mapped_column(ForeignKey("baby_basic_information.baby_id"), nullable=False, index=True)
    baby_card_id: Mapped[Optional[int]] = mapped_column(ForeignKey("baby_card.baby_card_id"), nullable=True, index=True)
    card_id: Mapped[Optional[int]] = mapped_column(ForeignKey("card_master.card_id"), nullable=True, index=True)
    text_snapshot: Mapped[str] = mapped_column(String(255), nullable=False)
    context_json: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON, nullable=True)
    used_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    baby = relationship("BabyBasicInformation", back_populates="vocab_logs")
    baby_card = relationship("BabyCard", back_populates="vocab_logs")
    card_master = relationship("CardMaster", back_populates="vocab_logs")


class SentenceMaster(Base):
    __tablename__ = "sentence_master"

    sentence_id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    baby_id: Mapped[int] = mapped_column(ForeignKey("baby_basic_information.baby_id"), nullable=False, index=True)
    sentence_text: Mapped[str] = mapped_column(Text, nullable=False)
    played_tts: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    avatar_image_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    avatar_audio_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    baby = relationship("BabyBasicInformation", back_populates="sentences")
