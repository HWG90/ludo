# Steam, Proton, and Windows games

Valve did the hard part. **Proton** is Wine plus DXVK/VKD3D plus a pile of game-specific fixes, shipped inside Steam. You stay in your Steam library. You press Play.

## Install Steam, once

Prefer your distro's package or Flathub — not a random tarball. Enable **multilib** / 32-bit support if the installer asks; a surprising number of Windows games still drag 32-bit pieces along.

Log in. Let it download. Do not copy a Windows Steam folder on top of it.

## Enable Proton globally

Steam → Settings → Compatibility → **Enable Steam Play for all other titles**.

Pick a recent Proton version (or Experimental) as the default. Per-game overrides live in the game's Properties → Compatibility.

That checkbox is the whole magic trick. DirectX calls become Vulkan. Filesystem quirks get shims. You are not installing Windows in a window.

## Will *my* game run?

Search it on [ProtonDB](https://www.protondb.com). Gold/Platinum means "people are playing it." Silver means "tinker." Borked means "wait or refund."

Also check anti-cheat (next guide) for competitive online games.

Native Linux titles (many indies, plenty of Valve games, a growing AAA list) skip Proton entirely. Steam will say "Native" in the compatibility UI.

## Steam Linux Runtime vs "it launches and dies"

If a game fails instantly:

1. Properties → Compatibility → try Proton Experimental, then a numbered Proton, then Proton-GE
2. Check `~/.steam` logs, or launch Steam from a terminal and watch the scream
3. Verify the GPU guide (Vulkan must work)
4. Disable overlays one at a time (Discord, MangoHud) to see if they are the culprit

Proton-GE (GloriousEggroll) is a community Proton with extra codecs and fixes. Install it with **ProtonUp-Qt** or ProtonPlus, then select it per-game. It is not a distro, it is a compatibility version.

## Launch options you will actually use

In Properties → General → Launch Options:

```text
mangohud %command%
gamemoderun %command%
PROTON_USE_WINED3D=1 %command%     # emergency OpenGL fallback, slower
```

`%command%` is "the thing Steam was going to run anyway." You wrap it; you do not delete it.

## If you remember one thing

Enable Steam Play for all titles, keep GPU drivers healthy, and use ProtonDB before you spend an evening blaming Linux for a game whose anti-cheat publisher never opted in.
