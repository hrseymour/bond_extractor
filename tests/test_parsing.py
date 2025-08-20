import pytest
from src.utils import normalize_date, parse_frequency, safe_json_loads

def test_normalize_date_formats():
    assert normalize_date('2025-01-02') == '2025-01-02'
    assert normalize_date('01/02/2025') == '2025-01-02'
    assert normalize_date('Feb 1, 2025') == '2025-02-01'

def test_parse_frequency():
    assert parse_frequency('semi-annual') == 2.0
    assert parse_frequency('quarterly') == 4.0
    assert parse_frequency('monthly') == 12.0
    assert parse_frequency('annual') == 1.0
    assert parse_frequency(6) == 6.0

def test_safe_json_loads():
    blob = "Here is JSON: {\"bonds\":[{\"interest_rate\":0.05}]} Thanks"
    data = safe_json_loads(blob)
    assert 'bonds' in data and isinstance(data['bonds'], list)
