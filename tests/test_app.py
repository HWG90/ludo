import asyncio

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
    missing = OllamaStatus(binary=None, running=False, model_present=False, model="qwen2.5:1.5b")
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
