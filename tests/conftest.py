import pytest

from app.main import create_app
from app.inputs import sample
from app.pipeline import inspect


@pytest.fixture
def archive_app(tmp_path):
    return create_app(tmp_path / 'track.sqlite')


@pytest.fixture
def client(archive_app):
    return archive_app.test_client()


@pytest.fixture(scope='session')
def dirty():
    return inspect(sample('dirty'))
