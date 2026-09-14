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


def test_chitchat_skips_brain() -> None:
    class TrackingBrain:
        name = "fake"
        label = "fake"
        called = False

        def complete(self, question: str, context: str, history: list[tuple[str, str]]) -> str:
            TrackingBrain.called = True
            return "should not run"

    TrackingBrain.called = False
    answer = answer_question("lol", backend=TrackingBrain())
    assert answer.source == "chat"
    assert not TrackingBrain.called


def test_ludo_commands_use_notes() -> None:
    answer = answer_question("What are some commands for ludo", use_llm=False)
    assert answer.source == "ludo"
    assert "checkup" in answer.text
    assert "translate" in answer.text


def test_tiny_ollama_does_not_invent_on_a_miss() -> None:
    from ludo.llm import OllamaBrain

    called: list[str] = []

    class QuietOllama(OllamaBrain):
        def complete(self, question: str, context: str, history: list[tuple[str, str]]) -> str:
            called.append(question)
            return "- lspci\n- lspci\n- lspci"

    brain = QuietOllama(host="http://127.0.0.1:11434", model="qwen2.5:1.5b")
    answer = answer_question("how do I overclock a toaster", backend=brain)
    assert answer.source == "miss"
    assert called == []


def test_tiny_ollama_keeps_ludo_command_notes() -> None:
    from ludo.llm import OllamaBrain

    called: list[str] = []

    class QuietOllama(OllamaBrain):
        def complete(self, question: str, context: str, history: list[tuple[str, str]]) -> str:
            called.append(question)
            return "pacman lspci lsusb " * 20

    brain = QuietOllama(host="http://127.0.0.1:11434", model="qwen2.5:1.5b")
    answer = answer_question("What are some commands for ludo", backend=brain)
    assert answer.source == "ludo"
    assert "ludo checkup" in answer.text
    assert called == []


def test_system_name_uses_this_pc() -> None:
    answer = answer_question("What is my system name", make_profile(), use_llm=False)
    assert answer.source == "machine"
    assert "testbox" in answer.text
    assert "tester" in answer.text
    assert answer.guide_id is None


def test_tiny_ollama_keeps_hostname_facts() -> None:
    from ludo.llm import OllamaBrain

    called: list[str] = []

    class QuietOllama(OllamaBrain):
        def complete(self, question: str, context: str, history: list[tuple[str, str]]) -> str:
            called.append(question)
            return "Your computer name is /home/you on NTFS."

    brain = QuietOllama(host="http://127.0.0.1:11434", model="qwen2.5:1.5b")
    answer = answer_question("What is my system name", make_profile(), backend=brain)
    assert answer.source == "machine"
    assert "testbox" in answer.text
    assert called == []


def test_discord_install_uses_notes() -> None:
    answer = answer_question("Where do I get discord for linux", make_profile(), use_llm=False)
    assert answer.source == "app"
    assert "discord" in answer.text.lower()
    assert ".exe" in answer.text.lower()
    assert "pacman -S discord" in answer.text or "flathub com.discordapp.Discord" in answer.text


def test_tiny_qwen_does_not_paraphrase_guides() -> None:
    from ludo.llm import OllamaBrain

    called: list[str] = []

    class QuietOllama(OllamaBrain):
        def complete(self, question: str, context: str, history: list[tuple[str, str]]) -> str:
            called.append(question)
            return "Download DiscordSetup.exe and use a proxy server."

    brain = QuietOllama(host="http://127.0.0.1:11434", model="qwen2.5:1.5b")
    answer = answer_question("Where do I get discord", make_profile(), backend=brain)
    assert answer.source == "app"
    assert called == []
    assert "proxy" not in answer.text.lower()
