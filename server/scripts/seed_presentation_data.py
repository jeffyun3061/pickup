"""발표용 목업 카탈로그와 테스트 초안을 넣는 멱등 시드.

실행 예:
    python scripts/seed_presentation_data.py

운영 DB에서 실행할 때는 관리자 화면 대신 Railway 서비스 셸에서
DATABASE_URL이 주입된 상태로 한 번만 실행한다. 게임 이름·자체 제작 폴백
이미지만 넣고, 외부 게임 이미지나 원문을 복제하지 않는다.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.db import SessionLocal  # noqa: E402
from app.models.entities import Content, Game  # noqa: E402
from app.schemas.common import ContentCreate, GameCreate  # noqa: E402
from app.services.admin_service import AdminService  # noqa: E402
from seed_demo_games import DEMO_FALLBACK_KEYS, DEMO_GAMES  # noqa: E402


TEST_GAMES = [
    ("g_test_01", "테스트 1", "1", "알림 테스트", "#6B4D38", "coverTactical"),
    ("g_test_02", "테스트 2", "2", "알림 테스트", "#3E6B86", "feedNeon"),
    ("g_test_03", "테스트 3", "3", "알림 테스트", "#4B4A80", "rankCyber"),
    ("g_test_04", "테스트 4", "4", "알림 테스트", "#433B62", "rankGrid"),
]

# 게임별로 한 건씩 전체 소식에 노출할 샘플이다. popup/goods만 발행해
# 시드 실행 순간 기존 설치에 업데이트 푸시가 쏟아지지 않게 한다.
GLOBAL_FEED_MOCKS = [
    ("c_demo_feed_01", "g_honkai_star_rail", "popup", "붕괴: 스타레일 개발자 노트 팝업", ["신규 지역과 캐릭터 관련 안내", "발표용 카드 목업"]),
    ("c_demo_feed_02", "g_genshin_impact", "goods", "원신 시즌 굿즈 출시 소식", ["한정 굿즈 라인업 공개", "공식 판매 링크를 연결할 수 있어요"]),
    ("c_demo_feed_03", "g_blue_archive", "popup", "블루 아카이브 오프라인 행사 안내", ["현장 이벤트와 참여 방법", "장소·예약 정보 입력 예시"]),
    ("c_demo_feed_04", "g_nikke", "goods", "니케 업데이트 기념 굿즈 안내", ["업데이트 테마 상품 공개", "전체 소식 카드 표시 예시"]),
    ("c_demo_feed_05", "g_seven_knights", "popup", "세븐나이츠 공식 방송 일정", ["신규 영웅 공개 방송", "방송 시간과 원문 링크 확인"]),
    ("c_demo_feed_06", "g_pokemon_go", "goods", "포켓몬 GO 시즌 상품 소식", ["시즌 한정 아이템 안내", "공식 판매처를 확인하세요"]),
    ("c_demo_feed_07", "g_girls_frontline_2", "popup", "소녀전선 2 개발자 인터뷰", ["다음 업데이트 방향 공개", "개발자 코멘트 카드 예시"]),
    ("c_demo_feed_08", "g_ihwan", "goods", "이환 콜라보 굿즈 소식", ["한정 콜라보 상품 안내", "판매 기간을 확인하세요"]),
    ("c_demo_feed_09", "g_epic_seven", "popup", "에픽세븐 특별 방송 안내", ["신규 영웅 공개 예정", "방송 일정 카드 예시"]),
    ("c_demo_feed_10", "g_trickcal_revive", "goods", "트릭컬 리바이브 기념 상품", ["시즌 기념 상품 공개", "공식 원문 링크 자리"]),
    ("c_demo_feed_11", "g_arknights", "popup", "명일방주 오프라인 전시 안내", ["전시 기간과 장소 안내", "예약 링크를 연결할 수 있어요"]),
    ("c_demo_feed_12", "g_umamusume", "goods", "우마무스메 한정 상품 안내", ["기간 한정 상품 공개", "전체 소식 카드 표시 예시"]),
    ("c_demo_feed_13", "g_test_01", "popup", "테스트 1 발표용 팝업 소식", ["전체 소식 화면 목업", "푸시를 만들지 않는 popup 샘플"]),
    ("c_demo_feed_14", "g_test_02", "goods", "테스트 2 굿즈 카드 샘플", ["카드형 요약과 이미지 폴백 확인", "운영 전용 샘플 데이터"]),
    ("c_demo_feed_15", "g_test_03", "popup", "테스트 3 행사 카드 샘플", ["장소와 예약 링크 입력 UI 확인", "운영 전용 샘플 데이터"]),
    ("c_demo_feed_16", "g_test_04", "goods", "테스트 4 상품 카드 샘플", ["전체 소식 목록 노출 확인", "운영 전용 샘플 데이터"]),
]

# 사용자가 직접 검수→발행해 푸시를 확인할 수 있는 초안. 실제 12개 게임과
# 테스트 1~4 모두 준비해 두므로 원하는 게임 하나만 선택해 바로 시험한다.
TEST_NEWS_DRAFTS = [
    ("c_test_news_01", "g_honkai_star_rail", "붕괴: 스타레일 업데이트 알림 테스트", ["새 패치 요약과 딥링크를 확인하세요", "관리자에서 발행하면 선택 기기에 알림"]),
    ("c_test_news_02", "g_genshin_impact", "원신 신규 캐릭터 출시 알림 테스트", ["신규 캐릭터 소식 카드 예시", "발행 후 푸시 제목을 확인하세요"]),
    ("c_test_news_03", "g_blue_archive", "블루 아카이브 이벤트 시작 알림 테스트", ["기간 이벤트 소식 카드 예시", "선택 게임 대상만 알림을 받습니다"]),
    ("c_test_news_04", "g_nikke", "니케 핫픽스 알림 테스트", ["긴급 공지 요약 카드 예시", "발행 후 딥링크를 확인하세요"]),
    ("c_test_news_05", "g_seven_knights", "세븐나이츠 업데이트 알림 테스트", ["밸런스 조정 요약", "선택 게임 알림을 확인하세요"]),
    ("c_test_news_06", "g_pokemon_go", "포켓몬 GO 이벤트 시작 알림 테스트", ["이벤트 기간과 핵심 보상 요약"]),
    ("c_test_news_07", "g_girls_frontline_2", "소녀전선 2 신규 인형 출시 테스트", ["신규 캐릭터와 획득 방법 요약"]),
    ("c_test_news_08", "g_ihwan", "이환 업데이트 알림 테스트", ["업데이트 핵심 변경점 요약"]),
    ("c_test_news_09", "g_epic_seven", "에픽세븐 신규 영웅 출시 테스트", ["신규 영웅 출시 소식 요약"]),
    ("c_test_news_10", "g_trickcal_revive", "트릭컬 리바이브 이벤트 알림 테스트", ["기간 이벤트 핵심 보상 요약"]),
    ("c_test_news_11", "g_arknights", "명일방주 업데이트 알림 테스트", ["신규 작전과 보상 요약"]),
    ("c_test_news_12", "g_umamusume", "우마무스메 픽업 시작 알림 테스트", ["기간 한정 픽업 소식 요약"]),
    ("c_test_news_13", "g_test_01", "테스트 1 알림 확인용 소식", ["테스트 1을 선택한 기기에 알림을 보냅니다", "발행 후 알림 큐에서 전송하세요"]),
    ("c_test_news_14", "g_test_02", "테스트 2 알림 확인용 소식", ["테스트 2의 푸시 제목과 딥링크를 확인하세요"]),
    ("c_test_news_15", "g_test_03", "테스트 3 알림 확인용 소식", ["여러 게임 선택 시 대상 분리를 확인하세요"]),
    ("c_test_news_16", "g_test_04", "테스트 4 알림 확인용 소식", ["알림 권한과 기기 토큰 등록을 확인하세요"]),
]


def ensure_game(service: AdminService, db, game_id: str, name: str, initial: str, genre: str, color: str, fallback: str) -> bool:
    if db.get(Game, game_id):
        return False
    service.create_game(
        GameCreate(
            id=game_id,
            name=name,
            initial=initial,
            genre=genre,
            color=color,
            fallback_image_key=fallback,
            image_rights_status="unverified",
            is_active=True,
        )
    )
    return True


def ensure_content(service: AdminService, db, content_id: str, game_id: str, kind: str, title: str, points: list[str], status: str) -> bool:
    if db.get(Content, content_id):
        return False
    service.create_content(
        ContentCreate(
            id=content_id,
            game_id=game_id,
            kind=kind,
            title=title,
            summary_points=points,
            official_url=f"https://example.com/gamepickup-demo/{content_id}",
            status=status,
        )
    )
    return True


def main() -> None:
    db = SessionLocal()
    try:
        service = AdminService(db)
        games_created = 0
        for game_id, name, initial, genre, color, _interest in DEMO_GAMES:
            if ensure_game(service, db, game_id, name, initial, genre, color, DEMO_FALLBACK_KEYS[game_id]):
                games_created += 1
        for game_id, name, initial, genre, color, fallback in TEST_GAMES:
            if ensure_game(service, db, game_id, name, initial, genre, color, fallback):
                games_created += 1

        published_created = 0
        for content_id, game_id, kind, title, points in GLOBAL_FEED_MOCKS:
            if ensure_content(service, db, content_id, game_id, kind, title, points, "published"):
                published_created += 1

        drafts_created = 0
        for content_id, game_id, title, points in TEST_NEWS_DRAFTS:
            if ensure_content(service, db, content_id, game_id, "update", title, points, "draft"):
                drafts_created += 1

        db.commit()
        print(
            f"games_created={games_created} published_feed_created={published_created} "
            f"test_drafts_created={drafts_created} total_games={db.query(Game).count()} "
            f"total_contents={db.query(Content).count()}"
        )
    finally:
        db.close()


if __name__ == "__main__":
    main()
