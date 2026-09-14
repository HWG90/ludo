import json

from ludo.cli import main
from ludo.content.installs import STEAM, pick

from tests.helpers import make_profile


def test_guides_cli(capsys) -> None:
    assert main(["guides"]) == 0
    out = capsys.readouterr().out
    assert "steam-proton" in out
    assert "welcome" in out


def test_translate_cli(capsys) -> None:
    assert main(["translate", "dir"]) == 0
    assert "ls" in capsys.readouterr().out


def test_glossary_cli(capsys) -> None:
    assert main(["glossary", "task manager"]) == 0
    assert "btop" in capsys.readouterr().out or "System Monitor" in capsys.readouterr().out


def test_glossary_miss() -> None:
    assert main(["glossary", "no-such-windows-feature-xyz"]) == 1


def test_checkup_json(capsys) -> None:
    assert main(["checkup", "--json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert "distro_name" in payload
    assert "recommendations" in payload


def test_pick_steam_for_arch() -> None:
    assert "pacman" in pick(STEAM, make_profile())
