#!/usr/bin/env python3
"""
대치동 학원가 모니터링 - Cloud Crawler
GitHub Actions에서 실행, Firecrawl + Supabase 연동

개선사항:
- 타입 힌트 추가
- 로깅 시스템 도입
- 환경 변수 검증
- 재시도 로직 (지수 백오프)
- 향상된 에러 처리
"""
import os
import json
import hashlib
import time
import logging
from datetime import datetime, timezone
from functools import wraps
from typing import Dict, List, Optional, Any

import requests

# ─── 로깅 설정 ───
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


# ─── 환경 변수 검증 ───
def validate_env_vars() -> bool:
    """필수 환경 변수 검증"""
    required = ["FIRECRAWL_API_KEY", "SUPABASE_SERVICE_KEY"]
    missing = []

    for var in required:
        if not os.environ.get(var):
            missing.append(var)

    if missing:
        logger.error(f"❌ 필수 환경 변수 누락: {', '.join(missing)}")
        return False

    logger.info("✅ 환경 변수 검증 완료")
    return True


# ─── 재시도 데코레이터 ───
def retry(max_attempts: int = 3, backoff_factor: float = 2.0):
    """지수 백오프를 사용한 재시도 데코레이터"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            attempt = 1
            while attempt <= max_attempts:
                try:
                    return func(*args, **kwargs)
                except requests.RequestException as e:
                    if attempt == max_attempts:
                        logger.error(f"❌ {func.__name__} 최대 재시도 횟수 초과: {e}")
                        raise

                    wait_time = backoff_factor ** (attempt - 1)
                    logger.warning(
                        f"⚠️ {func.__name__} 실패 (시도 {attempt}/{max_attempts}). "
                        f"{wait_time}초 후 재시도... 오류: {str(e)[:100]}"
                    )
                    time.sleep(wait_time)
                    attempt += 1
        return wrapper
    return decorator


# ─── 설정 ───
FIRECRAWL_API_KEY = os.environ.get("FIRECRAWL_API_KEY", "")
SUPABASE_URL = os.environ.get(
    "SUPABASE_URL",
    "https://inftexpcnfinglwlrvsj.supabase.co"
)
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_KEY", "")

TARGETS: Dict[str, Dict[str, Any]] = {
    "dschool": {
        "name": "디스쿨 (대치동 학원정보)",
        "urls": ["https://www.dschool.co.kr/"],
    },
    "gangmom": {
        "name": "강남엄마",
        "urls": ["https://www.gangmom.kr/"],
    },
    "data_go_kr": {
        "name": "공공데이터포털 - 학원교습소",
        "urls": ["https://www.data.go.kr/data/15096277/standard.do"],
    },
    "sen_go_kr": {
        "name": "서울시교육청",
        "urls": ["https://www.sen.go.kr/"],
    },
    "naver_search": {
        "name": "네이버 검색 - 대치동 학원",
        "urls": [
            "https://search.naver.com/search.naver?query=대치동+수학학원+2026",
            "https://search.naver.com/search.naver?query=대치동+정보올림피아드+KOI+2026",
            "https://search.naver.com/search.naver?query=대치동+코딩학원+2026",
        ],
    },
}

KEYWORDS: Dict[str, List[str]] = {
    "수학_입시": ["수학", "수능", "내신", "수리논술", "KMO", "수학올림피아드", "AMC"],
    "정보_코딩": ["정보올림피아드", "KOI", "코딩", "알고리즘", "USACO"],
    "AI_SW": ["AI", "인공지능", "SW", "머신러닝", "딥러닝"],
    "입시_정보": ["입시", "수시", "정시", "학생부", "대입"],
    "학원_동향": ["수강료", "개원", "폐원", "신규", "이전"],
}


# ─── 대시보드 HTML 템플릿 (placeholder 치환 방식) ───
_DASHBOARD_TEMPLATE = """<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>대치동 학원가 모니터링 대시보드</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.min.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Segoe UI', -apple-system, sans-serif; background: #0f172a; color: #e2e8f0; min-height: 100vh; }
        .header { background: linear-gradient(135deg, #1e3a5f 0%, #0f172a 100%); padding: 24px 32px; border-bottom: 1px solid #334155; }
        .header h1 { font-size: 24px; background: linear-gradient(90deg, #60a5fa, #a78bfa); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
        .header .subtitle { color: #94a3b8; margin-top: 4px; font-size: 14px; }
        .container { max-width: 1400px; margin: 0 auto; padding: 24px; }
        .stats-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-bottom: 24px; }
        .stat-card { background: #1e293b; border-radius: 12px; padding: 20px; border: 1px solid #334155; }
        .stat-card .label { color: #94a3b8; font-size: 13px; }
        .stat-card .value { font-size: 32px; font-weight: 700; margin-top: 8px; }
        .stat-card .value.blue { color: #60a5fa; }
        .stat-card .value.green { color: #4ade80; }
        .stat-card .value.yellow { color: #fbbf24; }
        .stat-card .value.red { color: #f87171; }
        .grid-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 24px; margin-bottom: 24px; }
        .panel { background: #1e293b; border-radius: 12px; padding: 24px; border: 1px solid #334155; }
        .panel h2 { font-size: 16px; margin-bottom: 16px; color: #f1f5f9; }
        table { width: 100%; border-collapse: collapse; font-size: 13px; }
        th { text-align: left; color: #94a3b8; padding: 8px; border-bottom: 1px solid #334155; }
        td { padding: 8px; border-bottom: 1px solid #1e293b; }
        tr:hover { background: #334155; }
        .badge { display: inline-block; padding: 2px 8px; border-radius: 999px; font-size: 11px; font-weight: 600; }
        .badge-new { background: #065f46; color: #6ee7b7; }
        .badge-modified { background: #713f12; color: #fde047; }
        .kw-bar { display: flex; align-items: center; gap: 8px; margin-bottom: 6px; }
        .kw-bar .bar { height: 20px; background: linear-gradient(90deg, #3b82f6, #8b5cf6); border-radius: 4px; min-width: 4px; }
        .kw-bar .name { min-width: 120px; font-size: 13px; }
        .kw-bar .count { font-size: 12px; color: #94a3b8; }
        .chart-container { position: relative; height: 250px; }
        @media (max-width: 768px) { .stats-grid { grid-template-columns: repeat(2, 1fr); } .grid-2 { grid-template-columns: 1fr; } }
    </style>
</head>
<body>
    <div class="header">
        <h1>🏫 대치동 학원가 모니터링 대시보드</h1>
        <div class="subtitle">Firecrawl + Supabase 자동 크롤링 · 변경 감지 · 키워드 트래킹 | 갱신: __NOW__</div>
        <div style="margin-top:10px;font-size:13px;">📚 <a href="publications.html" style="color:#7cc0ff;text-decoration:none;">2025 한국 출판생산 통계 — 발행 종수·부수 시각화 →</a></div>
    </div>
    <div class="container">
        <div class="stats-grid" id="statsGrid"></div>
        <div class="grid-2">
            <div class="panel"><h2>📈 스캔 이력</h2><div class="chart-container"><canvas id="runChart"></canvas></div></div>
            <div class="panel"><h2>🔑 TOP 키워드</h2><div id="topKeywords"></div></div>
        </div>
        <div class="grid-2">
            <div class="panel"><h2>📋 최근 변경사항</h2>
                <table><thead><tr><th>소스</th><th>유형</th><th>요약</th><th>시각</th></tr></thead><tbody id="changesTable"></tbody></table>
            </div>
            <div class="panel"><h2>📡 소스별 현황</h2>
                <table><thead><tr><th>소스</th><th>변경</th><th>최근</th></tr></thead><tbody id="sourceTable"></tbody></table>
            </div>
        </div>
    </div>
    <script>
        const changes = __CHANGES_JSON__;
        const runStats = __RUN_STATS_JSON__;
        const topKeywords = __TOP_KEYWORDS_JSON__;
        const sourceStats = __SOURCE_STATS_JSON__;

        const totalScans = runStats.reduce((s, r) => s + (r.pages||0), 0);
        const totalChanges = runStats.reduce((s, r) => s + (r.changes||0), 0);
        const totalKeywords = runStats.reduce((s, r) => s + (r.keywords||0), 0);
        const totalErrors = runStats.reduce((s, r) => s + (r.errors||0), 0);

        document.getElementById('statsGrid').innerHTML = `
            <div class="stat-card"><div class="label">총 스캔 페이지</div><div class="value blue">${totalScans}</div></div>
            <div class="stat-card"><div class="label">변경 감지</div><div class="value green">${totalChanges}</div></div>
            <div class="stat-card"><div class="label">키워드 매칭</div><div class="value yellow">${totalKeywords}</div></div>
            <div class="stat-card"><div class="label">오류</div><div class="value red">${totalErrors}</div></div>
        `;

        document.getElementById('changesTable').innerHTML = changes.slice(0, 20).map(c => `
            <tr>
                <td>${c.source_key}</td>
                <td><span class="badge ${c.change_type === 'new' ? 'badge-new' : 'badge-modified'}">${c.change_type}</span></td>
                <td>${(c.summary || '').substring(0, 50)}</td>
                <td>${(c.created_at || '').substring(0, 16)}</td>
            </tr>
        `).join('');

        document.getElementById('sourceTable').innerHTML = sourceStats.map(s => `
            <tr>
                <td>${s.name || s.key}</td>
                <td>${s.changes || 0}</td>
                <td>${(s.last_scan || '').substring(0, 16)}</td>
            </tr>
        `).join('');

        const maxKw = topKeywords.length > 0 ? topKeywords[0].count : 1;
        document.getElementById('topKeywords').innerHTML = topKeywords.map(k => `
            <div class="kw-bar">
                <div class="name">${k.keyword}</div>
                <div class="bar" style="width: ${(k.count / maxKw * 200)}px"></div>
                <div class="count">${k.count}</div>
            </div>
        `).join('');

        if (runStats.length > 0) {
            const ctx = document.getElementById('runChart').getContext('2d');
            new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: runStats.slice(0, 15).reverse().map(r => (r.created_at||'').substring(5, 16)),
                    datasets: [
                        { label: '변경', data: runStats.slice(0, 15).reverse().map(r => r.changes), backgroundColor: '#4ade80', borderRadius: 4 },
                        { label: '키워드', data: runStats.slice(0, 15).reverse().map(r => r.keywords), backgroundColor: '#fbbf24', borderRadius: 4 }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        x: { ticks: { color: '#94a3b8', font: { size: 10 } }, grid: { display: false } },
                        y: { ticks: { color: '#94a3b8' }, grid: { color: '#334155' } }
                    },
                    plugins: { legend: { labels: { color: '#e2e8f0' } } }
                }
            });
        }
    </script>
</body>
</html>"""


# ─── Supabase 헬퍼 ───
@retry(max_attempts=3, backoff_factor=1.5)
def supabase_insert(table: str, rows: List[Dict[str, Any]]) -> None:
    """Supabase REST API로 데이터 삽입 (재시도 포함)"""
    if not rows:
        return

    if not SUPABASE_KEY:
        logger.warning(f"⚠️ Supabase 키 없음, {table} 삽입 스킵")
        return

    url = f"{SUPABASE_URL}/rest/v1/{table}"
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=minimal",
    }

    try:
        resp = requests.post(url, json=rows, headers=headers, timeout=30)
        if resp.status_code not in (200, 201):
            logger.warning(
                f"⚠️ Supabase insert {table}: {resp.status_code} "
                f"{resp.text[:200]}"
            )
        else:
            logger.debug(f"✅ Supabase insert {table}: {len(rows)} 행")
    except requests.RequestException as e:
        logger.error(f"❌ Supabase insert {table} 오류: {e}")
        raise


@retry(max_attempts=3, backoff_factor=1.5)
def supabase_select(
    table: str,
    params: Dict[str, str]
) -> List[Dict[str, Any]]:
    """Supabase REST API로 데이터 조회 (재시도 포함)"""
    if not SUPABASE_KEY:
        logger.warning(f"⚠️ Supabase 키 없음, {table} 조회 스킵")
        return []

    url = f"{SUPABASE_URL}/rest/v1/{table}"
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
    }

    try:
        resp = requests.get(url, params=params, headers=headers, timeout=30)
        if resp.status_code == 200:
            logger.debug(f"✅ Supabase select {table}: {len(resp.json())} 행")
            return resp.json()
        else:
            logger.warning(f"⚠️ Supabase select {table}: {resp.status_code}")
            return []
    except requests.RequestException as e:
        logger.error(f"❌ Supabase select {table} 오류: {e}")
        raise


# ─── Firecrawl 스크래핑 ───
@retry(max_attempts=3, backoff_factor=2.0)
def firecrawl_scrape(url: str) -> str:
    """Firecrawl API v1로 페이지 스크래핑 (재시도 포함)"""
    if not FIRECRAWL_API_KEY:
        logger.warning(f"⚠️ Firecrawl 키 없음, {url} 스크래핑 스킵")
        return ""

    api_url = "https://api.firecrawl.dev/v1/scrape"
    headers = {
        "Authorization": f"Bearer {FIRECRAWL_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "url": url,
        "formats": ["markdown"],
        "onlyMainContent": True,
        "timeout": 30000,
    }

    try:
        resp = requests.post(api_url, json=payload, headers=headers, timeout=60)
        if resp.status_code == 200:
            data = resp.json()
            if data.get("success"):
                content = data.get("data", {}).get("markdown", "")
                if not content:
                    logger.warning(f"⚠️ Firecrawl {url}: 빈 응답")
                    return ""
                logger.debug(f"✅ Firecrawl {url}: {len(content)} 자")
                return content

        logger.warning(f"⚠️ Firecrawl {url}: {resp.status_code}")
    except requests.RequestException as e:
        logger.error(f"❌ Firecrawl {url} 오류: {e}")
        raise

    return ""


# ─── 키워드 분석 ───
def analyze_keywords(text: str) -> List[Dict[str, Any]]:
    """텍스트에서 키워드 매칭"""
    if not text:
        return []

    results = []
    text_lower = text.lower()

    for group, keywords in KEYWORDS.items():
        for kw in keywords:
            count = text_lower.count(kw.lower())
            if count > 0:
                # 컨텍스트 추출
                idx = text_lower.find(kw.lower())
                start = max(0, idx - 50)
                end = min(len(text), idx + len(kw) + 50)
                context = text[start:end].replace("\n", " ").strip()

                results.append({
                    "keyword": kw,
                    "keyword_group": group,
                    "match_count": count,
                    "context": context[:200],
                })

    logger.debug(f"🔍 키워드 분석: {len(results)}개 매칭")
    return results


# ─── 메인 크롤링 ───
def run_crawl() -> Dict[str, Any]:
    """메인 크롤링 프로세스"""
    run_id = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    logger.info(f"🚀 크롤링 시작: {run_id}")
    start_time = time.time()

    total_pages = 0
    total_changes = 0
    total_keywords = 0
    total_errors = 0
    all_keyword_matches = []
    all_change_logs = []

    for source_key, source_config in TARGETS.items():
        logger.info(f"📡 [{source_key}] {source_config['name']}")

        for url in source_config["urls"]:
            total_pages += 1
            logger.info(f"  🕷️ 스캔: {url[:60]}...")

            try:
                # Firecrawl 스크래핑
                content = firecrawl_scrape(url)

                if not content:
                    total_errors += 1
                    logger.warning(f"  ⚠️ 빈 응답")
                    continue

                content_hash = hashlib.md5(content.encode()).hexdigest()

                # 이전 스냅샷 비교
                prev = supabase_select("page_snapshots", {
                    "source_key": f"eq.{source_key}",
                    "url": f"eq.{url}",
                    "order": "created_at.desc",
                    "limit": "1",
                })

                if prev and prev[0].get("content_hash") == content_hash:
                    change_type = "unchanged"
                    summary = "변경 없음"
                elif prev:
                    change_type = "modified"
                    summary = f"컨텐츠 변경 감지 (이전: {prev[0].get('content_length', 0)} → 현재: {len(content)} 자)"
                    total_changes += 1
                else:
                    change_type = "new"
                    summary = "최초 스캔 - 기준 스냅샷 저장"
                    total_changes += 1

                logger.info(f"  ✅ {change_type}: {summary}")

                # 스냅샷 저장
                supabase_insert("page_snapshots", [{
                    "source_key": source_key,
                    "url": url,
                    "content_hash": content_hash,
                    "content_length": len(content),
                    "change_type": change_type,
                    "summary": summary,
                }])

                # 키워드 분석
                kw_results = analyze_keywords(content)
                for kw in kw_results:
                    total_keywords += kw["match_count"]
                    all_keyword_matches.append({
                        "run_id": run_id,
                        "source_key": source_key,
                        "url": url,
                        **kw,
                    })

                if change_type != "unchanged":
                    all_change_logs.append({
                        "run_id": run_id,
                        "source_key": source_key,
                        "url": url,
                        "change_type": change_type,
                        "summary": summary,
                        "keywords": json.dumps([k["keyword"] for k in kw_results]),
                    })

                logger.info(
                    f"  🔑 키워드: {len(kw_results)}개 그룹, "
                    f"{sum(k['match_count'] for k in kw_results)}회 매칭"
                )
            except Exception as e:
                total_errors += 1
                logger.error(f"  ❌ {url} 처리 중 오류: {e}")
                continue

            time.sleep(1)  # Rate limit

    duration = time.time() - start_time

    # 결과 저장
    try:
        supabase_insert("crawl_runs", [{
            "run_id": run_id,
            "pages": total_pages,
            "changes": total_changes,
            "keywords": total_keywords,
            "errors": total_errors,
            "duration": round(duration, 2),
        }])

        # 키워드 매칭 결과 저장 (배치)
        if all_keyword_matches:
            for i in range(0, len(all_keyword_matches), 50):
                supabase_insert("keyword_matches", all_keyword_matches[i:i+50])

        # 변경 로그 저장
        if all_change_logs:
            supabase_insert("change_logs", all_change_logs)
    except Exception as e:
        logger.error(f"❌ 결과 저장 중 오류: {e}")

    logger.info(f"✅ 크롤링 완료")
    logger.info(
        f"  📊 실행시간: {duration:.1f}초 | "
        f"페이지: {total_pages} | 변경: {total_changes} | "
        f"키워드: {total_keywords} | 오류: {total_errors}"
    )

    return {
        "run_id": run_id,
        "pages": total_pages,
        "changes": total_changes,
        "keywords": total_keywords,
        "errors": total_errors,
        "duration": duration,
    }


# ─── 대시보드 생성 ───
def generate_dashboard() -> None:
    """Supabase 데이터 기반 대시보드 HTML 생성"""
    logger.info("📊 대시보드 생성 중...")

    try:
        # 최근 실행 이력
        run_stats = supabase_select("crawl_runs", {
            "order": "created_at.desc",
            "limit": "30",
        })

        # 최근 변경사항
        changes = supabase_select("change_logs", {
            "order": "created_at.desc",
            "limit": "30",
        })

        # 키워드 집계 (최근 7일)
        kw_raw = supabase_select("keyword_matches", {
            "order": "created_at.desc",
            "limit": "500",
        })

        # 키워드 TOP 집계
        kw_counts = {}
        for k in kw_raw:
            key = k.get("keyword", "")
            if key not in kw_counts:
                kw_counts[key] = {
                    "keyword": key,
                    "group": k.get("keyword_group", ""),
                    "count": 0
                }
            kw_counts[key]["count"] += k.get("match_count", 1)

        top_keywords = sorted(
            kw_counts.values(),
            key=lambda x: x["count"],
            reverse=True
        )[:20]

        # 소스별 집계
        source_map = {}
        for c in changes:
            sk = c.get("source_key", "")
            if sk not in source_map:
                source_map[sk] = {
                    "key": sk,
                    "name": TARGETS.get(sk, {}).get("name", sk),
                    "scans": 0,
                    "changes": 0,
                    "last_scan": ""
                }
            source_map[sk]["changes"] += 1
            if (not source_map[sk]["last_scan"] or
                c.get("created_at", "") > source_map[sk]["last_scan"]):
                source_map[sk]["last_scan"] = c.get("created_at", "")[:16]

        for r in run_stats:
            for sk in TARGETS:
                if sk not in source_map:
                    source_map[sk] = {
                        "key": sk,
                        "name": TARGETS[sk]["name"],
                        "scans": 0,
                        "changes": 0,
                        "last_scan": ""
                    }
                source_map[sk]["scans"] += 1

        source_stats = list(source_map.values())

        now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")

        changes_json = json.dumps(changes, ensure_ascii=False, default=str)
        run_stats_json = json.dumps(run_stats, ensure_ascii=False, default=str)
        top_keywords_json = json.dumps(top_keywords, ensure_ascii=False, default=str)
        source_stats_json = json.dumps(source_stats, ensure_ascii=False, default=str)

        html = (
            _DASHBOARD_TEMPLATE
            .replace("__NOW__", now)
            .replace("__CHANGES_JSON__", changes_json)
            .replace("__RUN_STATS_JSON__", run_stats_json)
            .replace("__TOP_KEYWORDS_JSON__", top_keywords_json)
            .replace("__SOURCE_STATS_JSON__", source_stats_json)
        )

        with open("index.html", "w", encoding="utf-8") as f:
            f.write(html)

        logger.info(f"✅ 대시보드 생성 완료 ({len(html)} bytes)")
    except Exception as e:
        logger.error(f"❌ 대시보드 생성 중 오류: {e}")


# ─── 카카오톡 알림 ───
KAKAO_NOTIFY_URL = os.environ.get(
    "KAKAO_NOTIFY_URL",
    "https://inftexpcnfinglwlrvsj.supabase.co/functions/v1/kakao-notify?action=send",
)


def send_kakao_notification(result: Dict[str, Any]) -> None:
    """크롤링 결과를 카카오톡으로 전송"""
    now_kst = datetime.now(timezone.utc).strftime("%m/%d %H:%M")
    msg_lines = [
        f"📊 대치동 모니터링 리포트",
        f"⏰ {now_kst} UTC",
        f"",
        f"📄 스캔: {result['pages']}페이지",
        f"🔄 변경: {result['changes']}건",
        f"🔑 키워드: {result['keywords']}회 매칭",
    ]

    if result["errors"] > 0:
        msg_lines.append(f"⚠️ 오류: {result['errors']}건")

    if result["changes"] > 0:
        msg_lines.append(f"\n✅ 변경 감지됨! 대시보드를 확인하세요.")
    else:
        msg_lines.append(f"\n✅ 모든 소스 정상 (변경 없음)")

    message = "\n".join(msg_lines)

    try:
        resp = requests.post(
            KAKAO_NOTIFY_URL,
            json={"message": message},
            headers={"Content-Type": "application/json"},
            timeout=15,
        )

        if resp.status_code == 200:
            data = resp.json()
            if data.get("success"):
                logger.info("✅ 카카오톡 알림 전송 성공!")
            else:
                logger.warning(f"⚠️ 카카오톡 알림 실패: {data}")
        else:
            logger.warning(
                f"⚠️ 카카오톡 알림 HTTP {resp.status_code}: "
                f"{resp.text[:200]}"
            )
    except Exception as e:
        logger.error(f"❌ 카카오톡 알림 오류: {e}")


def main() -> None:
    """메인 진입점"""
    if not validate_env_vars():
        logger.error("❌ 필수 환경 변수가 없어 실행할 수 없습니다.")
        return

    result = run_crawl()
    generate_dashboard()
    send_kakao_notification(result)

    logger.info(f"✨ 최종 결과: {json.dumps(result)}")


if __name__ == "__main__":
    main()
