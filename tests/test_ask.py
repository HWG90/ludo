from ludo.ask import answer_question
from ludo.probe import SteamStatus

from tests.helpers import make_profile


def test_proton_points_at_guide() -> None:
    answer = answer_question("what is Proton", make_profile())
    assert answer.guide_id == "steam-proton"
    assert "Proton" in answer.text or "proton" in answer.text.lower()


def test_ipconfig_translates() -> None:
    answer = answer_question("ipconfig", make_profile())
    assert answer.source == "command"
    assert "ip addr" in answer.text


def test_task_manager_glossary() -> None:
    answer = answer_question("task manager", make_profile())
    assert answer.source == "glossary"
    assert "btop" in answer.text or "System Monitor" in answer.text


def test_steam_installed_uses_this_pc() -> None:
    profile = make_profile(steam=SteamStatus(installed=True, native=True, proton_ge=True))
    answer = answer_question("is steam installed", profile)
    assert answer.source == "machine"
    assert "Steam" in answer.text


def test_help() -> None:
    answer = answer_question("help")
    assert answer.source == "help"


def test_unknown_is_honest() -> None:
    answer = answer_question("how do I overclock a toaster")
    assert answer.source == "miss"
