from collections import Counter
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import BabyBasicInformation, BabyVocabLog, SentenceMaster
from app.schemas import (
    EmotionDiaryData,
    ReportSummaryData,
    SuccessResponse,
    TopWordOut,
)
from app.services.ai_client import fetch_emotion_diary, fetch_report_insight


router = APIRouter(prefix="/reports", tags=["reports"])


def _build_insight(
    *,
    total_selections: int,
    total_sentences: int,
    top_words: list[TopWordOut],
    average_sentence_length: float,
) -> str:
    if total_selections == 0:
        return "최근 기록이 아직 없어 리포트 데이터가 충분하지 않습니다."

    leading_word = top_words[0].text if top_words else "핵심 단어"
    sentence_note = "문장 생성 기록이 충분합니다." if total_sentences >= 3 else "문장 생성 기록은 아직 적은 편입니다."
    return (
        f"최근 기간 동안 '{leading_word}' 사용 빈도가 가장 높았습니다. "
        f"평균 문장 길이는 {average_sentence_length:.1f}어절이며, {sentence_note}"
    )


def _report_payload(baby_id: int, days: int, db: Session) -> ReportSummaryData:
    baby = db.get(BabyBasicInformation, baby_id)
    if baby is None:
        raise HTTPException(status_code=404, detail="아동 정보를 찾을 수 없습니다.")

    since = datetime.utcnow() - timedelta(days=days)
    logs = (
        db.query(BabyVocabLog)
        .filter(BabyVocabLog.baby_id == baby_id, BabyVocabLog.used_at >= since)
        .order_by(BabyVocabLog.used_at.desc())
        .all()
    )
    sentences = (
        db.query(SentenceMaster)
        .filter(SentenceMaster.baby_id == baby_id, SentenceMaster.created_at >= since)
        .order_by(SentenceMaster.created_at.desc())
        .all()
    )

    word_counter = Counter(log.text_snapshot.strip() for log in logs if log.text_snapshot and log.text_snapshot.strip())
    top_words = [
        TopWordOut(text=text, count=count)
        for text, count in word_counter.most_common(5)
    ]

    emotion_counter: Counter[str] = Counter()
    for log in logs:
        if isinstance(log.context_json, dict):
            emotion = log.context_json.get("emotion") or log.context_json.get("mood")
            if emotion:
                emotion_counter[str(emotion)] += 1

    sentence_lengths = [len(sentence.sentence_text.split()) for sentence in sentences if sentence.sentence_text]
    average_sentence_length = (
        round(sum(sentence_lengths) / len(sentence_lengths), 2) if sentence_lengths else 0.0
    )

    return ReportSummaryData(
        baby_id=baby_id,
        period_days=days,
        total_selections=len(logs),
        unique_words=len(word_counter),
        total_sentences=len(sentences),
        average_sentence_length=average_sentence_length,
        top_words=top_words,
        emotion_counts=dict(emotion_counter),
        recent_sentences=[sentence.sentence_text for sentence in sentences[:5]],
        insight=_build_insight(
            total_selections=len(logs),
            total_sentences=len(sentences),
            top_words=top_words,
            average_sentence_length=average_sentence_length,
        ),
    )


def _escape_pdf_text(text: str) -> str:
    return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def _make_simple_pdf(lines: list[str]) -> bytes:
    y = 780
    line_commands: list[str] = []
    for line in lines:
        safe_line = _escape_pdf_text(line)
        line_commands.append(f"1 0 0 1 50 {y} Tm ({safe_line}) Tj")
        y -= 18
    stream = "BT /F1 12 Tf " + " ".join(line_commands) + " ET"
    stream_bytes = stream.encode("ascii", errors="ignore")

    objects = [
        b"1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj",
        b"2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj",
        b"3 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Resources << /Font << /F1 5 0 R >> >> /Contents 4 0 R >> endobj",
        f"4 0 obj << /Length {len(stream_bytes)} >> stream\n".encode("ascii") + stream_bytes + b"\nendstream endobj",
        b"5 0 obj << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> endobj",
    ]

    header = b"%PDF-1.4\n"
    body = bytearray(header)
    offsets = [0]
    for obj in objects:
        offsets.append(len(body))
        body.extend(obj)
        body.extend(b"\n")

    xref_pos = len(body)
    body.extend(f"xref\n0 {len(offsets)}\n".encode("ascii"))
    body.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        body.extend(f"{offset:010d} 00000 n \n".encode("ascii"))
    body.extend(
        (
            f"trailer << /Size {len(offsets)} /Root 1 0 R >>\n"
            f"startxref\n{xref_pos}\n%%EOF"
        ).encode("ascii")
    )
    return bytes(body)


@router.get(
    "/{baby_id}",
    response_model=SuccessResponse[ReportSummaryData],
    summary="발달 리포트 조회",
    responses={404: {"description": "아동 정보를 찾을 수 없습니다."}},
)
async def get_report(
    baby_id: int,
    days: int = Query(default=30, ge=1, le=365),
    db: Session = Depends(get_db),
):
    report = _report_payload(baby_id, days, db)

    # 규칙기반 insight → GPT 자연어 해석으로 교체(실패 시 규칙기반 유지)
    stats = {
        "period_days": report.period_days,
        "total_selections": report.total_selections,
        "unique_words": report.unique_words,
        "total_sentences": report.total_sentences,
        "average_sentence_length": report.average_sentence_length,
        "top_words": [{"text": w.text, "count": w.count} for w in report.top_words],
        "emotion_counts": report.emotion_counts,
        "recent_sentences": report.recent_sentences,
    }
    gpt_insight = await fetch_report_insight(stats)
    if gpt_insight:
        report.insight = gpt_insight

    return SuccessResponse(
        data=report,
        message="발달 리포트를 조회했습니다.",
    )


@router.get(
    "/{baby_id}/diary",
    response_model=SuccessResponse[EmotionDiaryData],
    summary="감정일기 (그날 사용 기록 기반)",
    responses={404: {"description": "아동 정보를 찾을 수 없습니다."}},
)
async def get_emotion_diary(
    baby_id: int,
    date: str = Query(default=None, description="YYYY-MM-DD (기본: 오늘)"),
    db: Session = Depends(get_db),
):
    baby = db.get(BabyBasicInformation, baby_id)
    if baby is None:
        raise HTTPException(status_code=404, detail="아동 정보를 찾을 수 없습니다.")

    # 대상 날짜(기본 오늘, UTC) 00:00~24:00
    try:
        day = datetime.strptime(date, "%Y-%m-%d") if date else datetime.utcnow()
    except ValueError:
        raise HTTPException(status_code=400, detail="date 형식은 YYYY-MM-DD 입니다.")
    start = day.replace(hour=0, minute=0, second=0, microsecond=0)
    end = start + timedelta(days=1)
    date_str = start.strftime("%Y-%m-%d")

    sentences = (
        db.query(SentenceMaster)
        .filter(
            SentenceMaster.baby_id == baby_id,
            SentenceMaster.created_at >= start,
            SentenceMaster.created_at < end,
        )
        .order_by(SentenceMaster.created_at.asc())
        .all()
    )
    logs = (
        db.query(BabyVocabLog)
        .filter(
            BabyVocabLog.baby_id == baby_id,
            BabyVocabLog.used_at >= start,
            BabyVocabLog.used_at < end,
        )
        .all()
    )

    sentence_texts = [s.sentence_text for s in sentences if s.sentence_text]
    word_counter = Counter(l.text_snapshot.strip() for l in logs if l.text_snapshot and l.text_snapshot.strip())
    emotions: Counter[str] = Counter()
    for l in logs:
        if isinstance(l.context_json, dict):
            e = l.context_json.get("emotion") or l.context_json.get("mood")
            if e:
                emotions[str(e)] += 1

    ai = await fetch_emotion_diary({
        "date": date_str,
        "sentences": sentence_texts,
        "top_words": [w for w, _ in word_counter.most_common(5)],
        "emotions": dict(emotions),
    })
    if not ai:
        ai = {"mood": "편안",
              "diary": "오늘은 조용한 하루였어요." if not sentence_texts
                       else "오늘 아이가 여러 표현으로 마음을 전했어요."}

    return SuccessResponse(
        data=EmotionDiaryData(
            baby_id=baby_id, date=date_str,
            mood=ai.get("mood", "차분"), diary=ai.get("diary", ""),
            sentences=sentence_texts[:5],
        ),
        message="감정일기를 생성했습니다.",
    )


@router.get(
    "/{baby_id}/pdf",
    summary="발달 리포트 PDF 다운로드",
    responses={404: {"description": "아동 정보를 찾을 수 없습니다."}},
)
def download_report_pdf(
    baby_id: int,
    days: int = Query(default=30, ge=1, le=365),
    db: Session = Depends(get_db),
):
    report = _report_payload(baby_id, days, db)
    lines = [
        "SoriSsack Report",
        f"Baby ID: {report.baby_id}",
        f"Period: last {report.period_days} days",
        f"Selections: {report.total_selections}",
        f"Unique words: {report.unique_words}",
        f"Sentences: {report.total_sentences}",
        f"Avg sentence length: {report.average_sentence_length}",
        "Top words:",
    ]
    for item in report.top_words:
        lines.append(f"- {item.text}: {item.count}")
    lines.append(f"Insight: {report.insight}")

    pdf_bytes = _make_simple_pdf(lines)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="sorissack-report-{baby_id}.pdf"'
        },
    )
