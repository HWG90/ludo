from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Vertical, VerticalScroll
from textual.widgets import Label, Static

from ludo.content import installs
from ludo.format import steam_label, vulkan_label
from ludo.ui.widgets import GuideButton


class GamingView(VerticalScroll):
    def compose(self) -> ComposeResult:
        profile = self.app.profile
        yield Label("Gaming on Linux", classes="gold")
        yield Static(
            "Steam is still Steam. Proton is the compatibility layer Valve ships so Windows titles run. "
            "Check ProtonDB for a title before you spend an evening troubleshooting.",
            classes="muted",
        )
        with Vertical(classes="card"):
            yield Label("On this PC", classes="card-title")
            yield Static(f"Steam: {steam_label(profile.steam)}")
            yield Static(f"Vulkan: {vulkan_label(profile.vulkan)}")
            yield Static(f"GPU: {profile.primary_gpu.vendor if profile.primary_gpu else 'unknown'}")
            yield Static(
                f"MangoHud {'yes' if profile.mangohud else 'no'} · "
                f"GameMode {'yes' if profile.gamemode else 'no'} · "
                f"gamescope {'yes' if profile.gamescope else 'no'}",
                classes="muted",
            )
        with Vertical(classes="card"):
            yield Label("Install Steam", classes="card-title")
            yield Static(installs.pick(installs.STEAM, profile), classes="gold")
            yield Static("Or Flathub:", classes="muted")
            yield Static(installs.FLATPAK_STEAM)
            yield Static("Then: Steam → Settings → Compatibility → Enable Steam Play for all other titles.")
        with Vertical(classes="card"):
            yield Label("Useful extras", classes="card-title")
            yield Static("MangoHud (FPS overlay)")
            yield Static(installs.pick(installs.MANGOHUD, profile), classes="muted")
            yield Static("GameMode")
            yield Static(installs.pick(installs.GAMEMODE, profile), classes="muted")
            yield Static("Heroic (Epic / GOG)")
            yield Static(installs.pick(installs.HEROIC, profile), classes="muted")
        with Vertical(classes="card"):
            yield Label("Guides", classes="card-title")
            yield GuideButton("Steam and Proton", "steam-proton", classes="primary")
            yield GuideButton("GPU drivers", "gpu")
            yield GuideButton("Lutris, Heroic, overlays", "gaming-stack")
            yield GuideButton("Anti-cheat honesty", "anticheat")

    def on_button_pressed(self, event: GuideButton.Pressed) -> None:
        if isinstance(event.button, GuideButton):
            self.app.open_guide(event.button.guide_id)
