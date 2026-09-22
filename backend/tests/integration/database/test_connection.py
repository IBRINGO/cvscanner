"""Proves Django can open a connection and run a query against whatever
DATABASES['default'] points at (SQLite in-memory for the test settings;
PostgreSQL when run against config.settings.development/production).
"""
import pytest
from django.db import connection


@pytest.mark.django_db
def test_database_connection_executes_a_query():
    with connection.cursor() as cursor:
        cursor.execute("SELECT 1")
        result = cursor.fetchone()

    assert result == (1,)
