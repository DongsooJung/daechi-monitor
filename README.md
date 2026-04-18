# 🏫 대치동 학원가 모니터링 대시보드

> **대치동 학원가 변화를 실시간으로 감지·추적하는 자동 스캔 시스템**
> Real-time monitoring dashboard for Daechi-dong private academy market

[![Live Dashboard](https://img.shields.io/badge/Live-Dashboard-10b981?style=flat-square)](https://dongsoojung.github.io/daechi-monitor/)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![Chart.js](https://img.shields.io/badge/Chart.js-4.4.1-FF6384?style=flat-square&logo=chart.js&logoColor=white)](https://www.chartjs.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow?style=flat-square)](LICENSE)

---

## 🎯 Problem

대치동 학원가는 한국 사교육 시장의 **최전선 선행지표(leading indicator)** 입니다. 학원 개·폐업, 커리큘럼 변경, 모집 공고, 수업료 조정이 분 단위로 일어나지만, 강사·운영자·학부모 누구도 **체계적으로 추적하지 못합니다**.

수동 서핑으로는:
- 100+ 학원 사이트를 모두 보는 것이 현실적으로 불가능
- 변경 시점을 놓치면 기회도 경쟁 리스크도 사후에 파악
- 키워드 트렌드(KOI/의대/영재원 등)의 **실시간 빈도 데이터**가 부재

## 💡 Solution

웹 스크래핑 + diff 감지 + 시각화 대시보드를 **GitHub Pages 정적 호스팅 + Actions 자동 실행**으로 결합한 무한 무료 모니터링 시스템.

```
  Target URLs          GitHub Actions (cron)      JSON store          GitHub Pages
 ┌────────────┐        ┌──────────────────┐      ┌──────────┐        ┌──────────────┐
 │ 학원사이트  │ ───▶  │  Python scanner  │ ───▶ │ runs.json│ ───▶  │ Chart.js UI  │
 │ 커뮤니티    │        │  (requests/diff) │      │ keywords │        │ (static SPA) │
 └────────────┘        └──────────────────┘      └──────────┘        └──────────────┘
```

## 📊 Dashboard Features

| 패널 | 내용 | 시각화 |
|------|------|--------|
| **Summary Cards** | 총 스캔 페이지 / 변경 감지 건수 / 키워드 매칭 / 오류 | Stat cards |
| **📈 스캔 이력** | 최근 15회 스캔의 변경·키워드 추이 | Chart.js Bar (dual) |
| **🔑 TOP 키워드** | 기간별 빈도 상위 키워드 (KOI, 의대, 영재원 등) | Ranked list |
| **📋 최근 변경사항** | 학원별 diff 로그 (URL + 타임스탬프) | Timeline |
| **📡 소스별 현황** | 도메인별 모니터링 건수·최신성 | Status table |

## 🛠 Tech Stack

- **Scraper**: Python 3.11+, `requests` (경량 HTTP), 변경분 해시 비교
- **Scheduler**: GitHub Actions cron (기본 6시간 간격)
- **Storage**: JSON 파일 저장 — 외부 DB·서버 없음
- **Frontend**: 단일 HTML 파일, Chart.js 4.4.1 (CDN), Tailwind-style 커스텀 CSS
- **Hosting**: GitHub Pages (무료, HTTPS 자동)

## 📂 Data Model

```jsonc
// runs.json (예시)
{
  "runs": [
    {
      "created_at": "2026-04-18T02:00:00Z",
      "scans": 127,
      "changes": 4,
      "keywords": 18,
      "errors": 0
    }
  ],
  "changes": [
    { "url": "...", "title": "학원 A — 2026 여름특강 개설", "detected_at": "..." }
  ],
  "keywords": [
    { "term": "KOI 대비", "count": 7 },
    { "term": "의대 논술", "count": 5 }
  ]
}
```

## 🚀 Quick Start

```bash
# 1. 리포지토리 클론
git clone https://github.com/DongsooJung/daechi-monitor.git
cd daechi-monitor

# 2. 의존성 설치 (스캐너 실행용)
pip install -r requirements.txt

# 3. 스캐너 실행 (로컬 테스트)
python scanner.py

# 4. 대시보드 로컬 프리뷰
python -m http.server 8000
# → http://localhost:8000
```

## 📅 Roadmap

- [x] 기본 대시보드 (4-panel 레이아웃 + Chart.js)
- [x] GitHub Pages 배포
- [ ] 타겟 URL 동적 설정 (`targets.yaml`)
- [ ] Telegram/Slack 알림 (변경·키워드 임계치 기반)
- [ ] 주간 자동 리포트 생성 (요약 + 주요 변경사항)
- [ ] 다른 학원가 확장 (목동, 중계동, 반포)

## 🎓 Author

**정동수 (Dongsoo Jung)** — Stargate Corporation CEO
- 대치동 KOI(수학정보올림피아드) 전문 강사
- SNU 스마트도시공학 박사 수료 · 공간계량/헤도닉 연구자
- [GitHub](https://github.com/DongsooJung) · [Website](https://stargate11.com)

## 📄 License

MIT License — 자유롭게 사용·수정 가능합니다.

---

> *"Show me the data, I'll show you the market."*
> 대치동이라는 한 동네의 움직임만 잘 추적해도, 대한민국 사교육 시장의 방향이 보입니다.
