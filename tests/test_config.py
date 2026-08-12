# tests/test_config.py
import main


def test_load_config_defaults(tmp_path):
    main.CONFIG_FILE = str(tmp_path / "config.json")
    config = main.load_config()
    assert config["language"] == "en"
    assert config["theme"] == "dark_theme.qss"
    assert config["port"] == 8000
    assert config["allow_upload"] is False


def test_save_and_load_config_round_trip(tmp_path):
    config_path = tmp_path / "config.json"
    main.CONFIG_FILE = str(config_path)
    config = main.load_config()
    config["port"] = 9123
    config["allow_upload"] = True
    main.save_config(config)

    reloaded = main.load_config()
    assert reloaded["port"] == 9123
    assert reloaded["allow_upload"] is True


def test_load_existing_config_missing_keys_get_defaults(tmp_path):
    config_path = tmp_path / "config.json"
    config_path.write_text('{"language": "en", "theme": "dark_theme.qss"}', encoding="utf-8")
    main.CONFIG_FILE = str(config_path)
    config = main.load_config()
    assert config["port"] == 8000
    assert config["allow_upload"] is False
