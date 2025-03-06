import os
import sys
from unittest.mock import MagicMock

import pytest

# Add parent directory to path to allow imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.database import db
from services.flask_route import server


@pytest.fixture(scope="function")
def app():
    """Create application for the tests."""
    app = server
    app.config.update(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        }
    )

    # Create context
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture(scope="function")
def client(app):
    """Test client for the application."""
    return app.test_client()


@pytest.fixture
def mock_stop_data():
    """Sample stop data for tests."""
    return [
        {
            "id": 1,
            "stop_id": "101N",
            "stop_name": "Test Station North",
            "stop_desc": "North Platform",
            "stop_lat": 40.7128,
            "stop_lon": -74.0060,
        },
        {
            "id": 2,
            "stop_id": "101S",
            "stop_name": "Test Station South",
            "stop_desc": "South Platform",
            "stop_lat": 40.7129,
            "stop_lon": -74.0061,
        },
    ]


@pytest.fixture
def mock_stop_objects(mock_stop_data):
    """Create mock Stop objects from test data."""
    mock_stops = []
    for stop_data in mock_stop_data:
        mock_stop = MagicMock()
        for key, value in stop_data.items():
            setattr(mock_stop, key, value)
        mock_stops.append(mock_stop)
    return mock_stops
