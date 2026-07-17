#!/usr/bin/env python3
"""
출판 상위 100개 시각화용 데이터 생성기
=====================================

`publications.json`을 재현 가능(seed 고정)하게 생성한다.

⚠️  주의: 여기서 만드는 매출(억원)·출판책 수 값은 **시각화 데모용 예시(sample)
데이터**이며, 실제 각 출판사의 재무·발행 실적이 아니다. 실제 데이터로 교체하려면
아래 PUBLISHERS 리스트를 크롤링/API 결과로 대체하면 된다.

데이터 모델 (publications.json):
{
  "generated_at": "ISO8601",
  "is_sample": true,
  "unit": {"revenue": "억원", "titles": "권(누적 발행 종수)"},
  "publications": [
    {"rank": 1, "name": "출판사", "category": "교육", "revenue": 1234.5, "titles": 3200}
  ]
}
"""
import json
import math
from datetime import datetime, timezone

# ─── 상위권: 실재하는 한국 주요 출판/교육기업명 (값은 예시) ───
KNOWN = [
    ("웅진씽크빅", "교육"), ("대교", "교육"), ("교원", "교육"),
    ("미래엔", "교육"), ("천재교육", "교육"), ("비상교육", "교육"),
    ("메가스터디교육", "교육"), ("YBM", "어학"), ("NE능률", "어학"),
    ("좋은책신사고", "교육"), ("지학사", "교육"), ("EBS미디어", "교육"),
    ("해커스어학원", "어학"), ("시원스쿨", "어학"), ("다락원", "어학"),
    ("넥서스", "어학"), ("김영사", "단행본"), ("민음사", "단행본"),
    ("창비", "단행본"), ("문학동네", "단행본"), ("위즈덤하우스", "단행본"),
    ("북이십일", "단행본"), ("다산북스", "단행본"), ("쌤앤파커스", "단행본"),
    ("한빛미디어", "IT/실용"), ("길벗", "IT/실용"), ("시공사", "단행본"),
    ("열린책들", "단행본"), ("웅진주니어", "아동"), ("사회평론", "학습"),
    ("이투스북", "교육"), ("마더텅", "교육"), ("아이스크림에듀", "교육"),
    ("대성마이맥", "교육"), ("재능교육", "교육"), ("을유문화사", "단행본"),
    ("휴머니스트", "단행본"), ("책세상", "단행본"), ("돌베개", "단행본"),
    ("길벗스쿨", "아동"),
]

# ─── 하위권 롱테일: 합성 출판사명 (형용사 + 명사 + 접미사 조합) ───
# 접두 어휘 × 접미 어휘의 곱으로 충분한 고유 조합을 확보한다(현재 45×8=360).
_ADJ = ["한빛", "새움", "푸른", "밝은", "열림", "다온", "온새미", "가온",
        "이든", "라온", "해솔", "미리내", "너울", "예솔", "보름", "다솜",
        "슬기", "누리", "든해", "아라", "청람", "도담", "여울", "소담",
        "한결", "빛솔", "나래", "초록", "물결", "바람", "구름", "은하",
        "새벽", "노을", "단비", "샘터", "옹달", "너른", "포근", "고운",
        "맑음", "차오름", "이룸", "펴는", "지음"]
_SUF = ["출판", "미디어", "북스", "에듀", "프레스", "문화사", "컬처", "랩"]
_CATS = ["교육", "어학", "단행본", "아동", "IT/실용", "학습"]


def _synth_names(n, start_idx, exclude=()):
    exclude = set(exclude)
    out = []
    seen = set()
    i = start_idx
    limit = len(_ADJ) * len(_SUF)
    while len(out) < n and i < start_idx + limit:
        adj = _ADJ[i % len(_ADJ)]
        suf = _SUF[(i // len(_ADJ)) % len(_SUF)]
        name = f"{adj}{suf}"
        if name not in seen and name not in exclude:
            out.append(name)
            seen.add(name)
        i += 1
    if len(out) < n:
        raise ValueError(f"합성 이름 부족: {len(out)}/{n} — _ADJ/_SUF 풀을 늘리세요.")
    return out


def build(total=100):
    names = list(KNOWN)
    known_names = {nm for nm, _ in KNOWN}
    synth = _synth_names(total - len(KNOWN), 0, exclude=known_names)
    for j, nm in enumerate(synth):
        names.append((nm, _CATS[j % len(_CATS)]))
    names = names[:total]

    pubs = []
    for i, (name, cat) in enumerate(names):
        rank = i + 1
        # 매출: 완만한 멱법칙 분포 (1위 ≈ 6,800억 → 100위 ≈ 40억)
        revenue = round(6800 * math.pow(rank, -0.72), 1)
        # 출판책 수: 순위·카테고리 영향 + 결정적 변주 (권당 매출이 카테고리마다 다르게)
        base_titles = 5200 * math.pow(rank, -0.45)
        cat_factor = {
            "교육": 1.15, "학습": 1.1, "어학": 0.95, "아동": 1.25,
            "단행본": 1.0, "IT/실용": 0.8,
        }.get(cat, 1.0)
        wobble = 1 + 0.18 * math.sin(rank * 1.7)  # 결정적 변주
        titles = int(round(base_titles * cat_factor * wobble / 10) * 10)
        titles = max(titles, 30)
        pubs.append({
            "rank": rank,
            "name": name,
            "category": cat,
            "revenue": revenue,
            "titles": titles,
            "rev_per_title": round(revenue * 100 / titles, 2),  # 백만원/권
        })
    return pubs


def main():
    pubs = build(300)
    data = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "is_sample": True,
        "unit": {
            "revenue": "억원",
            "titles": "권(누적 발행 종수)",
            "rev_per_title": "백만원/권",
        },
        "note": "매출·발행 종수는 시각화 데모용 예시(sample) 값이며 실제 실적이 아님.",
        "publications": pubs,
    }
    with open("publications.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"✅ publications.json 생성 완료 — {len(pubs)}개 출판사")
    print(f"   1위 {pubs[0]['name']} 매출 {pubs[0]['revenue']}억 / {pubs[0]['titles']}권")
    print(f"   {len(pubs)}위 {pubs[-1]['name']} 매출 {pubs[-1]['revenue']}억 / {pubs[-1]['titles']}권")


if __name__ == "__main__":
    main()
