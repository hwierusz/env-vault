"""Tests for env_vault.badge."""
import pytest

from env_vault.badge import Badge, BadgeError, generate_badges, _score_color


# ---------------------------------------------------------------------------
# _score_color
# ---------------------------------------------------------------------------

def test_score_color_green():
    assert _score_color(100) == "green"
    assert _score_color(80) == "green"


def test_score_color_yellow():
    assert _score_color(79) == "yellow"
    assert _score_color(50) == "yellow"


def test_score_color_red():
    assert _score_color(49) == "red"
    assert _score_color(0) == "red"


# ---------------------------------------------------------------------------
# Badge helpers
# ---------------------------------------------------------------------------

def test_badge_to_dict():
    b = Badge(label="foo", message="bar", color="green")
    assert b.to_dict() == {"label": "foo", "message": "bar", "color": "green"}


def test_badge_to_shields_url_basic():
    b = Badge(label="vault health", message="95%", color="green")
    url = b.to_shields_url()
    assert url.startswith("https://img.shields.io/badge/")
    assert "green" in url


def test_badge_to_shields_url_replaces_spaces():
    b = Badge(label="my label", message="ok", color="blue")
    url = b.to_shields_url()
    assert " " not in url


# ---------------------------------------------------------------------------
# generate_badges
# ---------------------------------------------------------------------------

_VARS = {"DB_HOST": "localhost", "API_KEY": "secret", "PORT": "5432"}


def test_generate_badges_returns_three_items():
    badges = generate_badges(_VARS, score=90)
    assert len(badges) == 3


def test_generate_badges_health_score_present():
    badges = generate_badges(_VARS, score=75)
    labels = [b.label for b in badges]
    assert "vault health" in labels


def test_generate_badges_variable_count_correct():
    badges = generate_badges(_VARS, score=90)
    count_badge = next(b for b in badges if b.label == "variables")
    assert count_badge.message == str(len(_VARS))
    assert count_badge.color == "blue"


def test_generate_badges_no_empty_values_green():
    badges = generate_badges(_VARS, score=90)
    empty_badge = next(b for b in badges if b.label == "empty values")
    assert empty_badge.message == "none"
    assert empty_badge.color == "green"


def test_generate_badges_some_empty_values_yellow():
    vars_with_empty = {"A": "", "B": "val", "C": "val"}
    badges = generate_badges(vars_with_empty, score=70)
    empty_badge = next(b for b in badges if b.label == "empty values")
    assert empty_badge.message == "1"
    assert empty_badge.color == "yellow"


def test_generate_badges_many_empty_values_red():
    vars_with_many_empty = {"A": "", "B": "", "C": "", "D": ""}
    badges = generate_badges(vars_with_many_empty, score=30)
    empty_badge = next(b for b in badges if b.label == "empty values")
    assert empty_badge.color == "red"


def test_generate_badges_invalid_score_raises():
    with pytest.raises(BadgeError):
        generate_badges(_VARS, score=101)


def test_generate_badges_negative_score_raises():
    with pytest.raises(BadgeError):
        generate_badges(_VARS, score=-1)


def test_generate_badges_empty_vault():
    badges = generate_badges({}, score=100)
    count_badge = next(b for b in badges if b.label == "variables")
    assert count_badge.message == "0"
