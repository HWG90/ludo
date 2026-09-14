import asyncio

from ludo.app import LudoApp
from ludo.progress import Progress

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

    asyncio.run(scenario())
