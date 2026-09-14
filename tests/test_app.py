import asyncio
from pathlib import Path

from ludo.app import LudoApp
from ludo.ollama_setup import OllamaStatus
from ludo.progress import Progress
from ludo.ui.setup import OllamaSetupScreen

from tests.helpers import make_profile


def test_app_navigation() -> None:
    async def scenario() -> None:
        app = LudoApp(profile=make_profile(), progress=Progress())
        async with app.run_test() as pilot:
            await pilot.pause()
            brand = app.query_one("#brand")
            assert "LUDO" in str(brand.content)
            await pilot.press("4")
            await pilot.pause()
            assert app.current_view == "gaming"
            await pilot.click("#nav-glossary")
            await pilot.pause()
            assert app.current_view == "glossary"
            await pilot.click("#nav-checkup")
            await pilot.pause()
            assert app.current_view == "checkup"
            await pilot.press("n")
            await pilot.pause()
            assert len(app.screen_stack) == 2
            await pilot.press("escape")
            await pilot.pause()
            ask = app.query_one("#ask-input")
            ask.value = "what is Proton"
            await ask.action_submit()
            await pilot.pause()
            assert app.current_view == "ask"
            assert app.chat[0].text == "what is Proton"
            assert "Proton" in app.chat[1].text or "proton" in app.chat[1].text.lower()

    asyncio.run(scenario())


def test_theme_changes_app_chrome() -> None:
    async def scenario() -> None:
        app = LudoApp(profile=make_profile(), progress=Progress())
        async with app.run_test() as pilot:
            await pilot.pause()
            assert app.theme == "ludo"
            sidebar = app.query_one("#sidebar")
            ludo_screen = app.screen.styles.background
            ludo_sidebar = sidebar.styles.background
            app.theme = "textual-light"
            await pilot.pause()
            assert app.screen.styles.background != ludo_screen
            assert sidebar.styles.background != ludo_sidebar

    asyncio.run(scenario())


def test_app_stops_ollama_on_exit(monkeypatch) -> None:
    stopped: list[bool] = []
    monkeypatch.setattr("ludo.app.stop_ludo_ollama", lambda: stopped.append(True))

    async def scenario() -> None:
        app = LudoApp(profile=make_profile(), progress=Progress())
        async with app.run_test() as pilot:
            await pilot.pause()
        assert stopped

    asyncio.run(scenario())


def test_ollama_setup_prompt(monkeypatch) -> None:
    monkeypatch.setenv("LUDO_LLM", "auto")
    missing = OllamaStatus(binary=None, running=False, model_present=False, model="qwen2.5:7b")
    monkeypatch.setattr("ludo.app.inspect_ollama", lambda: missing)

    async def scenario() -> None:
        app = LudoApp(profile=make_profile(), progress=Progress())
        async with app.run_test() as pilot:
            await pilot.pause()
            assert isinstance(app.screen, OllamaSetupScreen)
            await pilot.press("n")
            await pilot.pause()
            assert not isinstance(app.screen, OllamaSetupScreen)

    asyncio.run(scenario())


def test_no_ollama_setup_when_already_installed(monkeypatch) -> None:
    monkeypatch.setenv("LUDO_LLM", "auto")
    installed = OllamaStatus(
        binary=Path("/usr/bin/ollama"),
        running=False,
        model_present=True,
        model="qwen2.5:7b",
    )
    monkeypatch.setattr("ludo.app.inspect_ollama", lambda: installed)
    monkeypatch.setattr("ludo.ollama_setup.ensure_ready", lambda: installed)

    async def scenario() -> None:
        app = LudoApp(profile=make_profile(), progress=Progress())
        async with app.run_test() as pilot:
            await pilot.pause()
            assert not isinstance(app.screen, OllamaSetupScreen)

    asyncio.run(scenario())


def test_ollama_autostart_survives_update_check(monkeypatch) -> None:
    monkeypatch.setenv("LUDO_LLM", "auto")
    monkeypatch.setenv("LUDO_UPDATE", "auto")
    installed = OllamaStatus(
        binary=Path("/usr/bin/ollama"),
        running=False,
        model_present=True,
        model="qwen2.5:7b",
    )
    started: list[str] = []
    monkeypatch.setattr("ludo.app.inspect_ollama", lambda: installed)
    monkeypatch.setattr(
        "ludo.ollama_setup.ensure_ready",
        lambda: started.append("ollama") or installed,
    )
    monkeypatch.setattr(
        "ludo.update.check_for_update",
        lambda settings: started.append("update") or None,
    )

    async def scenario() -> None:
        app = LudoApp(profile=make_profile(), progress=Progress())
        async with app.run_test() as pilot:
            await pilot.pause()
            await pilot.pause()
            assert "ollama" in started
            assert "update" in started

    asyncio.run(scenario())


def test_saved_theme_is_restored() -> None:
    from ludo.settings import Settings, save_settings

    save_settings(Settings(theme="textual-light"))

    async def scenario() -> None:
        app = LudoApp(profile=make_profile(), progress=Progress())
        async with app.run_test() as pilot:
            await pilot.pause()
            assert app.theme == "textual-light"

    asyncio.run(scenario())


def test_theme_change_is_saved() -> None:
    from ludo.settings import load_settings

    async def scenario() -> None:
        app = LudoApp(profile=make_profile(), progress=Progress())
        async with app.run_test() as pilot:
            await pilot.pause()
            app.theme = "nord"
            await pilot.pause()

    asyncio.run(scenario())
    assert load_settings().theme == "nord"


def test_unknown_saved_theme_falls_back_to_ludo() -> None:
    from ludo.settings import Settings, save_settings

    save_settings(Settings(theme="not-a-real-theme"))

    async def scenario() -> None:
        app = LudoApp(profile=make_profile(), progress=Progress())
        async with app.run_test() as pilot:
            await pilot.pause()
            assert app.theme == "ludo"

    asyncio.run(scenario())


def test_chat_scrolls_to_latest() -> None:
    from ludo.ui.chat import ChatTurn

    async def scenario() -> None:
        app = LudoApp(profile=make_profile(), progress=Progress())
        async with app.run_test(size=(80, 18)) as pilot:
            await pilot.pause()
            for index in range(15):
                app.chat.append(ChatTurn("you", f"question {index}"))
                app.chat.append(
                    ChatTurn("ludo", "Proton runs the Windows game on Linux.\n" * 4)
                )
            app.switch_view("ask")
            await pilot.pause()
            log = app.query_one("#chat-log")
            assert log.max_scroll_y > 0
            assert log.scroll_offset.y == log.max_scroll_y

    asyncio.run(scenario())


def test_update_prompt_when_github_is_newer(monkeypatch) -> None:
    from ludo.ui.update import UpdateScreen
    from ludo.update import UpdateInfo

    monkeypatch.setenv("LUDO_UPDATE", "auto")
    info = UpdateInfo(local="0.1.0", remote="9.9.9", repo="HWG90/ludo")
    monkeypatch.setattr("ludo.update.check_for_update", lambda settings: info)

    async def scenario() -> None:
        app = LudoApp(profile=make_profile(), progress=Progress())
        async with app.run_test() as pilot:
            await pilot.pause()
            await pilot.pause()
            assert isinstance(app.screen, UpdateScreen)
            await pilot.press("n")
            await pilot.pause()
            assert not isinstance(app.screen, UpdateScreen)

    asyncio.run(scenario())
