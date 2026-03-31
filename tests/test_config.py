"""Configuration tests."""
from backend.config import _parse_cors_origins


def test_parse_cors_origins_defaults_to_wildcard():
    assert _parse_cors_origins(None) == ["*"]


def test_parse_cors_origins_splits_and_trims_values():
    origins = _parse_cors_origins("https://a.example, https://b.example ,, http://localhost:3000 ")

    assert origins == [
        "https://a.example",
        "https://b.example",
        "http://localhost:3000",
    ]
