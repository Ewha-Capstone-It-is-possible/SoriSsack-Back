from datetime import datetime
from typing import Any, Optional

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class BabyBasicInformation(Base):
    __tablename__ = "baby_basic_information"

    baby_id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    age: Mapped[int] = mapped_column(Integer, nullable=False)
    development_stage: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    preferred_tts_voice: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    preferred_tts_speed: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
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


class BabyCard(Base):
    __tablename__ = "baby_card"

    baby_card_id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    baby_id: Mapped[int] = mapped_column(ForeignKey("baby_basic_information.baby_id"), nullable=False, index=True)
    card_id: Mapped[Optional[int]] = mapped_column(ForeignKey("card_master.card_id"), nullable=True, index=True)
    text: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
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


class BabyVocabLog(Base):
    __tablename__ = "baby_vocab_log"

    log_id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    baby_id: Mapped[int] = mapped_column(ForeignKey("baby_basic_information.baby_id"), nullable=False, index=True)
    baby_card_id: Mapped[Optional[int]] = mapped_column(ForeignKey("baby_card.baby_card_id"), nullable=True, index=True)
    card_id: Mapped[Optional[int]] = mapped_column(ForeignKey("card_master.card_id"), nullable=True, index=True)
    text: Mapped[str] = mapped_column(String(255), nullable=False)
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
    audio_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    image_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    avatar_video_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    baby = relationship("BabyBasicInformation", back_populates="sentences")
