from ludo.probe import Gpu, SteamStatus
from ludo.recommend import recommend

from tests.helpers import make_profile


def test_missing_steam_suggests_guide() -> None:
    items = recommend(make_profile())
    titles = [item.title for item in items]
    assert any("Steam" in title for title in titles)
    assert any(item.guide_id == "steam-proton" for item in items)


def test_nvidia_without_vulkan_warns() -> None:
    profile = make_profile(
        gpus=[Gpu(name="RTX", vendor="NVIDIA", vendor_id="10de")],
        vulkan=False,
        steam=SteamStatus(installed=True, native=True, proton_official=True),
    )
    items = recommend(profile)
    assert any(item.level == "warn" and item.guide_id == "gpu" for item in items)


def test_healthy_box_has_goods() -> None:
    profile = make_profile(
        steam=SteamStatus(installed=True, native=True, proton_official=True, proton_ge=True),
        mangohud=True,
        gamemode=True,
        gamescope=True,
    )
    items = recommend(profile)
    assert any(item.level == "good" for item in items)
    assert not any("Optional gaming tools" in item.title for item in items)
