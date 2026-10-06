"""Validation-chain tests. Needs DATABASE_URL pointing at a DB loaded with schema.sql + seed.sql."""
import pytest

import db


def test_no_token():
    assert db.mark_attendance(None, "CS001")[0] == db.NO_TOKEN


def test_invalid_token():
    assert db.mark_attendance("nope", "CS001")[0] == db.INVALID_TOKEN


def test_closed_session():
    assert db.mark_attendance("seedtoken1", "CS001")[0] == db.CLOSED


def test_not_started():
    from datetime import datetime, timedelta, timezone
    now = datetime.now(timezone.utc)
    s = db.create_session("future", now + timedelta(hours=1), now + timedelta(hours=2))
    assert db.mark_attendance(s["token"], "CS001")[0] == db.NOT_STARTED


def test_unknown_roll():
    assert db.mark_attendance("seedopen", "NOPE999")[0] == db.UNKNOWN_ROLL


def test_ok_then_duplicate_and_normalization():
    assert db.mark_attendance("seedopen", " cs001 ")[0] == db.OK      # trimmed + upper-cased
    assert db.mark_attendance("seedopen", "CS001")[0] == db.ALREADY


def test_sql_injection_is_inert():
    assert db.mark_attendance("seedopen", "' OR '1'='1")[0] == db.UNKNOWN_ROLL
    assert db.mark_attendance("x' OR '1'='1", "CS001")[0] == db.INVALID_TOKEN
