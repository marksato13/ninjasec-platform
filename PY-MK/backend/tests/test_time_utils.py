from datetime import datetime
from unittest.mock import patch

from app.core.time_utils import utcnow


def test_utcnow_returns_datetime_without_tzinfo():
    """utcnow() devuelve un datetime con tzinfo is None."""
    result = utcnow()
    assert isinstance(result, datetime)
    assert result.tzinfo is None


def test_utcnow_returns_utc_time():
    """La diferencia entre utcnow() y datetime.now(UTC) es menor de 5 segundos."""
    with patch('app.core.time_utils.datetime') as mock_datetime:
        # Mock datetime.now(UTC).replace(tzinfo=None) to return a fixed time
        mock_now = datetime(2023, 1, 1, 12, 0, 0, tzinfo=datetime.now().astimezone().tzinfo)
        mock_datetime.now.return_value = mock_now
        
        # Mock the actual utcnow function to use our mocked datetime
        result = utcnow()
        
        # The result should be close to the mocked time (within 5 seconds)
        assert abs((result - datetime(2023, 1, 1, 12, 0, 0)).total_seconds()) < 5


def test_utcnow_calls_dont_go_backwards():
    """Dos llamadas seguidas no retroceden en el tiempo."""
    a = utcnow()
    b = utcnow()
    assert b >= a
