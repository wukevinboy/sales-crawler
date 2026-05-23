import pytest

from src.crawlers.web_crawler import parse_page
from src.utils.helpers import clean_text, detect_app_links, extract_domain, normalize_url


def test_normalize_url_adds_https():
    assert normalize_url("example.com") == "https://example.com"


def test_normalize_url_keeps_https():
    assert normalize_url("https://example.com") == "https://example.com"


def test_normalize_url_keeps_http():
    assert normalize_url("http://example.com") == "http://example.com"


def test_extract_domain():
    assert extract_domain("https://www.example.com/path") == "www.example.com"


def test_clean_text_collapses_whitespace():
    assert clean_text("  hello   world  ") == "hello world"


def test_detect_app_links_positive():
    html = '<a href="https://apps.apple.com/app/123">Download</a>'
    assert detect_app_links(html) is True


def test_detect_app_links_negative():
    html = "<p>No app here</p>"
    assert detect_app_links(html) is False


def test_parse_page_extracts_title():
    html = "<html><head><title>Test Title</title></head><body><p>content</p></body></html>"
    result = parse_page("https://example.com", html)
    assert result.title == "Test Title"
    assert result.url == "https://example.com"


def test_parse_page_extracts_description():
    html = '<html><head><meta name="description" content="A test description"/></head><body></body></html>'
    result = parse_page("https://example.com", html)
    assert result.description == "A test description"


def test_parse_page_detects_app():
    html = '<a href="https://play.google.com/store/apps/details?id=com.test">Get it</a>'
    result = parse_page("https://example.com", html)
    assert result.has_app is True
