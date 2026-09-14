# Graphics drivers that actually matter

Games on Linux speak **Vulkan** (and sometimes OpenGL). Proton translates DirectX into Vulkan. If Vulkan is missing, everything else is decoration.

## AMD — easy mode

Mesa is in your distro. You almost certainly already have it. Keep the system updated. That is the driver story.

The kernel plus Mesa plus a recent Proton will run the same cards people buy for Windows. Features like Anti-Lag and AFMF are catching up; the basics (VRR, high refresh, ray tracing on recent cards) are real.

## Intel — also Mesa

Great for desktops and lighter games. Arc cards are far more usable than they were at launch. Still Mesa, still updates with the OS.

## NVIDIA — the one with extra steps

You want the **proprietary NVIDIA driver** from your distro, not a `.run` file from a browser download.

- Arch / CachyOS: `nvidia` or `nvidia-open` depending on GPU generation — CachyOS often documents this on the welcome screen
- Fedora: RPM Fusion `akmod-nvidia`
- Ubuntu: Additional Drivers, or the `nvidia-driver-XXX` package

Reboot after the first install. `nvidia-smi` in a terminal should show the card. If it does not, you are still on Nouveau (the reverse-engineered driver) or a broken DKMS build.

Wayland + NVIDIA is viable in 2026 on current drivers. If something specific is broken (a capture path, an overlay), X11 is the fallback, not a lifestyle.

## Hybrid laptops (Intel/AMD iGPU + NVIDIA)

This is "Optimus." Use your distro's story: `supergfxctl`, `envycontrol`, NVIDIA's `prime-run`, or the DE's "launch with discrete GPU." Steam can be set to start on the dGPU so you are not debugging the wrong chip.

## Confirm it worked

Ludo's checkup looks for Vulkan ICDs. You can also run:

```bash
vulkaninfo --summary
```

You want an ICD that matches your vendor, not an empty error.

## If you remember one thing

AMD/Intel: update the system. NVIDIA: install the distro's NVIDIA package and reboot. Do not stack three different driver guides from three different years on the same machine.
