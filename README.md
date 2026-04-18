# 🏫 대치동 학원가 모니터링 대시보드

> **Firecrawl × Supabase 기반 자동 크롤링 · 변경 감지 · 키워드 트래킹 시스템**
>
> 서울 강남구 대치동 학원가의 학원 홈페이지·모집 공고·수강료 변동을 실시간 추적하여, KOI(수학·정보올림피아드) 전문 교육 시장의 동향을 데이터로 포착합니다.

[![Stack](https://img.shields.io/badge/Stack-Firecrawl%20%2B%20Supabase-3ECF8E?style=flat-square)](https://firecrawl.dev)
[![Visualization](https://img.shields.io/badge/Chart-Chart.js%204.4-FF6384?style=flat-square&logo=chartdotjs&logoColor=white)](https://www.chartjs.org/)
[![Deploy](https://img.shields.io/badge/Deploy-GitHub%20Pages-181717?style=flat-square&logo=github&logoColor=white)](https://dongsoojung.github.io/daechi-monitor/)
[![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)](LICENSE)

---

## 🎯 Problem

대치동 학원가는 KOI·수학올림피아드·내신 시장에서 **매주 수강료·개강일·프로그램이 갱신**됩니다. 개별 모니터링은 비효율적이고, 경쟁 학원의 변화를 놓치면 **포지셔닝·가격 경쟁력 저하**로 직결됩니다.

## ✨ Solution

이 대시보드는 **헤드리스 크롤링 + 변경 감지 + 키워드 집계** 3단 파이프라인으로 학원가를 자동 감시합니다.

```
Firecrawl API → 대치동 주요 학원 URL 스캔
    ↓
Supabase (diff 저장) → 이전 스냅샷과 비교하여 변경 라인만 추출
    ↓
Chart.js 대시보드 → 시계열 스캔 이력 · TOP 키워드 · 소스별 상태
```

## 📊 대시보드 구성

| 패널 | 내용 |
|------|------|
| **📈 스캔 이력** | 일자별 크롤링 시도·성공·변경 감지 건수 시계열 |
| **🔑 TOP 키워드** | 추출 본문에서 빈도 급증 키워드 (신규/증가율 기준) |
| **📋 최근 변경사항** | URL별 diff 라인 — `NEW` / `MODIFIED` 배지 구분 |
| **📡 소스별 현황** | 각 학원 사이트의 최근 응답 상태·오류율 |

상단 4개 통계 카드: `총 스캔 페이지` · `변경 감지` · `키워드 매칭` · `오류`

## 🛠 Tech Stack

- **크롤링**: [Firecrawl](https://firecrawl.dev) — JS 렌더링 포함, 대규모 학원 사이트 대응
- **저장소**: [Supabase](https://supabase.com) — 변경 diff 시계열 + Row Level Security
- **프론트**: Vanilla HTML + Chart.js 4.4 (UMD CDN) — GitHub Pages 정적 호스팅
- **트리거**: GitHub Actions cron (주 1회 자동 갱신)
- **디자인**: 다크 모드 (slate-900 베이스), blue-400 / purple-400 그라디언트 포인트

## 🚀 Live Demo

**▶ https://dongsoojung.github.io/daechi-monitor/**

## 📂 프로젝트 구조

```
daechi-monitor/
├── index.html          # 대시보드 단일 페이지 (Chart.js 통합)
├── requirements.txt    # Firecrawl·Supabase 파이썬 클라이언트
└── README.md
```

## 🎓 활용 맥락

본 대시보드는 **[Stargate Corporation](https://stargate11.com)**의 교육 사업(대치동 KOI 전문 강의) 의사결정을 지원합니다. 경쟁 학원 가격·개강일·프로그램 변동을 정량적으로 포착하여, 수강료 포지셔닝 및 커리큘럼 차별화 전략을 데이터 기반으로 수립합니다.

## 📄 License

MIT © 2026 Dongsoo Jung / Stargate Corporation

---

<p align="center">
  <sub>Built for <a href="https://stargate11.com">Stargate Corp</a> · 대치동 KOI 전문 교육 · AI-powered market intelligence</sub>
</p>
