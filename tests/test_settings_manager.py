import pytest

import settings_manager


@pytest.fixture(autouse=True)
def settings_file(tmp_path, monkeypatch):
    path = tmp_path / "user_settings.json"
    monkeypatch.setattr(settings_manager, "SETTINGS_FILE", str(path))
    return path


def test_defaults_without_a_file():
    assert settings_manager.load_settings()["is_active"] is True


def test_defaults_are_not_shared():
    settings_manager.load_settings()["symbols"].clear()

    assert settings_manager.load_settings()["symbols"]


def test_save_and_load():
    settings_manager.save_settings({"is_active": False})

    assert settings_manager.load_settings()["is_active"] is False


def test_missing_keys_come_from_defaults():
    settings_manager.save_settings({"is_active": False})

    assert settings_manager.load_settings()["notification_times"] == ["09:00", "18:00"]


@pytest.mark.parametrize("content", ["{broken", "[1, 2]"])
def test_damaged_file_falls_back_to_defaults(settings_file, content):
    settings_file.write_text(content, encoding="utf-8")

    assert settings_manager.load_settings()["is_active"] is True


@pytest.mark.parametrize("text, expected", [
    ("09:00", "09:00"),
    ("9:05", "09:05"),
    ("18.30", "18:30"),
    ("0745", "07:45"),
    (" 23:59 ", "23:59"),
])
def test_parse_time(text, expected):
    assert settings_manager.parse_time(text) == expected


@pytest.mark.parametrize("text", ["24:00", "12:60", "abc", "9", "1:2:3", "-1:00", ""])
def test_parse_time_rejects_invalid(text):
    assert settings_manager.parse_time(text) is None
