from __future__ import annotations

from ludo.probe import Gpu, SteamStatus, SystemProfile


def make_profile(**overrides: object) -> SystemProfile:
    data = dict(
        distro_id="cachyos",
        distro_name="CachyOS",
        distro_like=("arch",),
        version="",
        kernel="6.18.0",
        desktop="KDE",
        session="wayland",
        package_manager="pacman",
        gpus=[Gpu(name="Navi", vendor="AMD", vendor_id="1002")],
        vulkan=True,
        steam=SteamStatus(installed=False),
        flatpak=True,
        gamemode=False,
        mangohud=False,
        gamescope=False,
        hostname="testbox",
        username="tester",
        cpu="Test CPU",
        memory_gb=16.0,
    )
    data.update(overrides)
    return SystemProfile(**data)  # type: ignore[arg-type]
