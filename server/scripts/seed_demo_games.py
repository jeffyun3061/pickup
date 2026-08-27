"""개발용 데모 데이터 시드: GamePickup 후보 게임 카탈로그 + 깨진 시드 한글 복구.

실행: .\\.venv\\Scripts\\python scripts\\seed_demo_games.py
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.db import SessionLocal  # noqa: E402
from app.models.entities import Content, Game  # noqa: E402
from app.schemas.common import GameCreate  # noqa: E402
from app.services.admin_service import AdminService  # noqa: E402

DEMO_GAMES = [
    ("g_honkai_star_rail", "붕괴: 스타레일", "붕", "턴제 RPG", "#4B4A80", 11800),
    ("g_genshin_impact", "원신", "원", "오픈월드 액션", "#3E6B86", 10900),
    ("g_blue_archive", "블루 아카이브", "블", "학원 RPG", "#2563A6", 12850),
    ("g_nikke", "니케", "니", "건슈팅 RPG", "#6B294D", 9420),
    ("g_seven_knights", "세븐나이츠", "세", "수집형 RPG", "#6A3D28", 8100),
    ("g_pokemon_go", "포켓몬 GO", "포", "AR 액션", "#2F5E9A", 7540),
    ("g_girls_frontline_2", "소녀전선 2", "소", "전략 RPG", "#374B68", 6100),
    ("g_ihwan", "이환", "이", "액션 RPG", "#433B62", 4980),
    ("g_epic_seven", "에픽세븐", "에", "수집형 RPG", "#5D3A6E", 4620),
    ("g_trickcal_revive", "트릭컬 리바이브", "트", "볼따구 RPG", "#6B4D38", 4200),
    ("g_arknights", "명일방주", "명", "전략 RPG", "#3B454B", 3980),
    ("g_umamusume", "우마무스메", "우", "육성 시뮬레이션", "#7A3F58", 3650),
]

DEMO_FALLBACK_KEYS = {
    "g_honkai_star_rail": "gameHonkai",
    "g_genshin_impact": "gameGenshin",
    "g_blue_archive": "gameBlueArchive",
    "g_nikke": "gameNikke",
    "g_seven_knights": "gameSevenKnights",
    "g_pokemon_go": "gamePokemonGo",
    "g_girls_frontline_2": "gameGirlsFrontline2",
    "g_ihwan": "gameIhwan",
    "g_epic_seven": "gameEpicSeven",
    "g_trickcal_revive": "gameTrickcal",
    "g_arknights": "gameArknights",
    "g_umamusume": "gameUmamusume",
}

# 카탈로그에서 제외한 예전 데모 게임은 기록을 삭제하지 않고 비활성화한다.
# 기존 콘텐츠/구독 이력은 보존하면서 공개 목록에서만 사라지게 하는 운영 원칙이다.
LEGACY_GAME_IDS = {
    *(f"g_demo_{index:02d}" for index in range(1, 11)),
    "g_733a59c0d9a8",
}

# 사용자가 권리 검토 후 추가하기로 한 게임. 데이터·구독 이력은 보존하고
# 공개 카탈로그에서만 비활성화한다.
# 권리 검토 전 보류: 젠레스 존 제로·명조. wuthering은 명조의 구 ID다.
REMOVED_GAME_IDS = {"g_zenless_zone_zero", "g_mingchao", "g_wuthering_waves"}


def main() -> None:
    db = SessionLocal()
    try:
        service = AdminService(db)
        created = 0
        for game_id, name, initial, genre, color, interest in DEMO_GAMES:
            existing = db.get(Game, game_id)
            if existing:
                existing.fallback_image_key = DEMO_FALLBACK_KEYS[game_id]
                continue
            service.create_game(
                GameCreate(
                    id=game_id,
                    name=name,
                    initial=initial,
                    genre=genre,
                    color=color,
                    interest_count=interest,
                    fallback_image_key=DEMO_FALLBACK_KEYS[game_id],
                )
            )
            created += 1

        deactivated = 0
        for legacy_id in LEGACY_GAME_IDS | REMOVED_GAME_IDS:
            legacy_game = db.get(Game, legacy_id)
            if legacy_game and legacy_game.is_active:
                legacy_game.is_active = False
                deactivated += 1

        # 이전 콘솔 인코딩 문제로 '??'로 저장된 초기 시드 복구
        fixed = 0
        legacy = db.get(Game, "g_733a59c0d9a8")
        if legacy and "?" in (legacy.genre or ""):
            legacy.genre = "사이버펑크 러너"
            fixed += 1
        for content in db.query(Content).all():
            if "?" in (content.title or ""):
                content.title = "1.2 업데이트 사전 안내"
                content.summary_points_json = json.dumps(
                    ["신규 지역 추가", "밸런스 조정", "접속 보상 지급"],
                    ensure_ascii=False,
                )
                fixed += 1

        db.commit()
        print(
            f"created={created} deactivated={deactivated} fixed={fixed} "
            f"total_games={db.query(Game).count()}"
        )
    finally:
        db.close()


if __name__ == "__main__":
    main()
