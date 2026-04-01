"""Performance timing utility tests."""
from backend.perf import TimingCollector


def test_server_timing_header_single_span():
    collector = TimingCollector()
    collector.add_duration("db.sessions.summary", 12.3456)

    assert collector.as_header() == "db.sessions.summary;dur=12.35"


def test_server_timing_header_accumulates_repeated_spans():
    collector = TimingCollector()
    collector.add_duration("db.sessions.summary", 10)
    collector.add_duration("db.sessions.summary", 5.125)

    assert collector.as_dict()["db.sessions.summary"] == 15.12


def test_server_timing_header_multiple_spans_keep_order():
    collector = TimingCollector()
    collector.add_duration("request.total", 20)
    collector.add_duration("db.sessions.summary", 7.5)
    collector.add_duration("service.sessions.serialize", 1.25)

    assert collector.as_header() == (
        "request.total;dur=20.00, db.sessions.summary;dur=7.50, "
        "service.sessions.serialize;dur=1.25"
    )
