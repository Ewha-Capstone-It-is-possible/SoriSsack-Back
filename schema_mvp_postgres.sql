-- =============================================
-- SoriSsack MVP PostgreSQL Schema
-- 기준: 현재 FastAPI 백엔드 코드(app/models.py)
-- 목적: 현재 백엔드 구조와 1:1로 맞는 PostgreSQL DDL
-- =============================================

-- 실행 전 sorissack 데이터베이스에 접속되어 있어야 함

-- =============================================
-- 1. 아동 기본 정보
-- =============================================
CREATE TABLE baby_basic_information (
    baby_id              SERIAL PRIMARY KEY,
    name                 VARCHAR(100) NOT NULL,
    age                  INT NOT NULL,
    development_stage    VARCHAR(100),
    preferred_tts_voice  VARCHAR(50),
    preferred_tts_speed  FLOAT,
    created_at           TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at           TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- =============================================
-- 2. 공용 카드 마스터
-- =============================================
CREATE TABLE card_master (
    card_id             SERIAL PRIMARY KEY,
    base_text           VARCHAR(255) NOT NULL,
    normalized_text     VARCHAR(255) UNIQUE,
    part_of_speech      VARCHAR(50) NOT NULL,
    default_image_url   VARCHAR(500),
    is_active           BOOLEAN NOT NULL DEFAULT TRUE,
    created_at          TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at          TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- =============================================
-- 3. 아동별 카드
-- =============================================
CREATE TABLE baby_card (
    baby_card_id       SERIAL PRIMARY KEY,
    baby_id            INT NOT NULL,
    card_id            INT,
    text               VARCHAR(255),
    type               VARCHAR(50),
    custom_image_url   VARCHAR(500),
    is_favorite        BOOLEAN NOT NULL DEFAULT FALSE,
    source             VARCHAR(50) NOT NULL,
    status             VARCHAR(50) NOT NULL DEFAULT 'default',
    usage_count        INT NOT NULL DEFAULT 0,
    last_used_at       TIMESTAMP,
    is_active          BOOLEAN NOT NULL DEFAULT TRUE,
    created_at         TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at         TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_baby_card_baby FOREIGN KEY (baby_id) REFERENCES baby_basic_information (baby_id) ON DELETE CASCADE,
    CONSTRAINT fk_baby_card_card FOREIGN KEY (card_id) REFERENCES card_master (card_id) ON DELETE SET NULL
);

CREATE INDEX idx_baby_card_baby_id ON baby_card (baby_id);
CREATE INDEX idx_baby_card_card_id ON baby_card (card_id);

-- =============================================
-- 4. 단어 사용 로그
-- =============================================
CREATE TABLE baby_vocab_log (
    log_id             SERIAL PRIMARY KEY,
    baby_id            INT NOT NULL,
    baby_card_id       INT,
    card_id            INT,
    text               VARCHAR(255) NOT NULL,
    context_json       JSONB,
    used_at            TIMESTAMP NOT NULL,
    created_at         TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_baby_vocab_log_baby FOREIGN KEY (baby_id) REFERENCES baby_basic_information (baby_id) ON DELETE CASCADE,
    CONSTRAINT fk_baby_vocab_log_baby_card FOREIGN KEY (baby_card_id) REFERENCES baby_card (baby_card_id) ON DELETE SET NULL,
    CONSTRAINT fk_baby_vocab_log_card FOREIGN KEY (card_id) REFERENCES card_master (card_id) ON DELETE SET NULL
);

CREATE INDEX idx_baby_vocab_log_baby_id ON baby_vocab_log (baby_id);
CREATE INDEX idx_baby_vocab_log_baby_card_id ON baby_vocab_log (baby_card_id);
CREATE INDEX idx_baby_vocab_log_card_id ON baby_vocab_log (card_id);

-- =============================================
-- 5. 생성 문장 저장
-- =============================================
CREATE TABLE sentence_master (
    sentence_id         SERIAL PRIMARY KEY,
    baby_id             INT NOT NULL,
    sentence_text       TEXT NOT NULL,
    played_tts          BOOLEAN NOT NULL DEFAULT FALSE,
    audio_url           VARCHAR(500),
    image_url           VARCHAR(500),
    avatar_video_url    VARCHAR(500),
    created_at          TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_sentence_master_baby FOREIGN KEY (baby_id) REFERENCES baby_basic_information (baby_id) ON DELETE CASCADE
);

CREATE INDEX idx_sentence_master_baby_id ON sentence_master (baby_id);

-- =============================================
-- updated_at 자동 갱신 트리거
-- =============================================
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_baby_basic_information_updated_at
    BEFORE UPDATE ON baby_basic_information
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER trg_card_master_updated_at
    BEFORE UPDATE ON card_master
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER trg_baby_card_updated_at
    BEFORE UPDATE ON baby_card
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

-- =============================================
-- 샘플 데이터
-- =============================================
INSERT INTO baby_basic_information (
    baby_id, name, age, development_stage, preferred_tts_voice, preferred_tts_speed
) VALUES
    (1, '민수', 7, '초기 문장 단계', 'female', 1.0);

INSERT INTO card_master (
    card_id, base_text, normalized_text, part_of_speech, default_image_url, is_active
) VALUES
    (1, '사과', '사과', 'Noun', NULL, TRUE),
    (2, '물', '물', 'Noun', NULL, TRUE),
    (3, '주세요', '주세요', 'verb', NULL, TRUE);

INSERT INTO baby_card (
    baby_card_id, baby_id, card_id, text, type, custom_image_url,
    is_favorite, source, status, usage_count, last_used_at, is_active
) VALUES
    (101, 1, 1, NULL, NULL, NULL, TRUE, 'system_default', 'default', 3, CURRENT_TIMESTAMP, TRUE);
