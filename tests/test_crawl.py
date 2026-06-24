"""
daechi-monitor 단위 테스트
"""
import os
import json
import sys
from unittest import TestCase, mock
from pathlib import Path

# 현재 디렉토리를 sys.path에 추가 (모듈 import용)
sys.path.insert(0, str(Path(__file__).parent.parent))

from crawl_and_update import (
    analyze_keywords,
    validate_env_vars,
    retry,
)


class TestAnalyzeKeywords(TestCase):
    """키워드 분석 함수 테스트"""

    def test_empty_text(self):
        """빈 텍스트 처리"""
        result = analyze_keywords("")
        self.assertEqual(result, [])

    def test_no_keywords(self):
        """키워드 없는 텍스트"""
        result = analyze_keywords("이것은 아무 키워드도 없는 텍스트입니다.")
        self.assertEqual(result, [])

    def test_single_keyword(self):
        """단일 키워드 매칭"""
        text = "대치동 수학학원에서 수능 준비를 합니다."
        result = analyze_keywords(text)

        # 수학, 수능이 포함되어야 함
        keywords = [r["keyword"] for r in result]
        self.assertIn("수학", keywords)
        self.assertIn("수능", keywords)

    def test_keyword_count(self):
        """키워드 중복 카운트"""
        text = "코딩 코딩 코딩 알고리즘"
        result = analyze_keywords(text)

        coding_match = next((r for r in result if r["keyword"] == "코딩"), None)
        self.assertIsNotNone(coding_match)
        self.assertEqual(coding_match["match_count"], 3)

    def test_keyword_group(self):
        """키워드 그룹 분류"""
        text = "KOI 정보올림피아드 알고리즘"
        result = analyze_keywords(text)

        for r in result:
            if r["keyword"] in ["KOI", "정보올림피아드", "알고리즘"]:
                self.assertEqual(r["keyword_group"], "정보_코딩")

    def test_context_extraction(self):
        """컨텍스트 추출 테스트"""
        text = "앞의 문맥입니다. 수학 뒤의 문맥입니다."
        result = analyze_keywords(text)

        math_match = next((r for r in result if r["keyword"] == "수학"), None)
        self.assertIsNotNone(math_match)
        self.assertIn("수학", math_match["context"])


class TestValidateEnvVars(TestCase):
    """환경 변수 검증 테스트"""

    def test_missing_env_vars(self):
        """필수 환경 변수 누락"""
        with mock.patch.dict(os.environ, {}, clear=True):
            result = validate_env_vars()
            self.assertFalse(result)

    def test_missing_firecrawl_key(self):
        """Firecrawl API 키 누락"""
        with mock.patch.dict(
            os.environ,
            {"SUPABASE_SERVICE_KEY": "test_key"},
            clear=True
        ):
            result = validate_env_vars()
            self.assertFalse(result)

    def test_missing_supabase_key(self):
        """Supabase 키 누락"""
        with mock.patch.dict(
            os.environ,
            {"FIRECRAWL_API_KEY": "test_key"},
            clear=True
        ):
            result = validate_env_vars()
            self.assertFalse(result)

    def test_all_vars_present(self):
        """모든 환경 변수 존재"""
        with mock.patch.dict(
            os.environ,
            {
                "FIRECRAWL_API_KEY": "test_key1",
                "SUPABASE_SERVICE_KEY": "test_key2"
            },
            clear=True
        ):
            result = validate_env_vars()
            self.assertTrue(result)


class TestRetryDecorator(TestCase):
    """재시도 데코레이터 테스트"""

    def test_retry_success_on_first_attempt(self):
        """첫 시도 성공"""
        @retry(max_attempts=3, backoff_factor=0.1)
        def success_func():
            return "success"

        result = success_func()
        self.assertEqual(result, "success")

    def test_retry_success_on_second_attempt(self):
        """두 번째 시도 성공"""
        call_count = 0

        @retry(max_attempts=3, backoff_factor=0.1)
        def eventually_success():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                import requests
                raise requests.RequestException("First attempt fails")
            return "success"

        result = eventually_success()
        self.assertEqual(result, "success")
        self.assertEqual(call_count, 2)

    def test_retry_exhaustion(self):
        """재시도 횟수 초과"""
        @retry(max_attempts=2, backoff_factor=0.1)
        def always_fails():
            import requests
            raise requests.RequestException("Always fails")

        with self.assertRaises(Exception):
            always_fails()

    def test_retry_with_args_and_kwargs(self):
        """인자와 키워드 인자 전달"""
        @retry(max_attempts=1, backoff_factor=0.1)
        def func_with_args(a, b, c=0):
            return a + b + c

        result = func_with_args(1, 2, c=3)
        self.assertEqual(result, 6)


class TestSupabaseInsert(TestCase):
    """Supabase 삽입 함수 테스트"""

    @mock.patch("crawl_and_update.SUPABASE_KEY", "test_key")
    @mock.patch("crawl_and_update.requests.post")
    def test_insert_success(self, mock_post):
        """삽입 성공"""
        from crawl_and_update import supabase_insert

        mock_response = mock.Mock()
        mock_response.status_code = 201
        mock_post.return_value = mock_response

        rows = [{"id": 1, "name": "test"}]
        supabase_insert("test_table", rows)

        mock_post.assert_called_once()
        call_args = mock_post.call_args
        self.assertIn("test_table", call_args[0][0])

    @mock.patch.dict(os.environ, {}, clear=True)
    def test_insert_no_key(self):
        """API 키 없을 때"""
        from crawl_and_update import supabase_insert

        rows = [{"id": 1}]
        # API 키가 없으면 경고만 출력하고 반환
        supabase_insert("test_table", rows)
        # 예외 발생 없음

    def test_insert_empty_rows(self):
        """빈 행 리스트"""
        from crawl_and_update import supabase_insert

        # 빈 리스트는 조기 반환
        supabase_insert("test_table", [])
        # 예외 발생 없음


class TestFirecrawlScrape(TestCase):
    """Firecrawl 스크래핑 함수 테스트"""

    @mock.patch("crawl_and_update.FIRECRAWL_API_KEY", "test_key")
    @mock.patch("crawl_and_update.requests.post")
    def test_scrape_success(self, mock_post):
        """스크래핑 성공"""
        from crawl_and_update import firecrawl_scrape

        mock_response = mock.Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "success": True,
            "data": {"markdown": "# Test Content"}
        }
        mock_post.return_value = mock_response

        result = firecrawl_scrape("https://example.com")
        self.assertEqual(result, "# Test Content")

    @mock.patch("crawl_and_update.FIRECRAWL_API_KEY", "test_key")
    @mock.patch("crawl_and_update.requests.post")
    def test_scrape_empty_content(self, mock_post):
        """빈 응답"""
        from crawl_and_update import firecrawl_scrape

        mock_response = mock.Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "success": True,
            "data": {"markdown": ""}
        }
        mock_post.return_value = mock_response

        result = firecrawl_scrape("https://example.com")
        self.assertEqual(result, "")

    @mock.patch.dict(os.environ, {}, clear=True)
    def test_scrape_no_key(self):
        """API 키 없을 때"""
        from crawl_and_update import firecrawl_scrape

        result = firecrawl_scrape("https://example.com")
        self.assertEqual(result, "")


if __name__ == "__main__":
    import unittest
    unittest.main()
