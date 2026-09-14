# Admin rights, updates, and not breaking things

UAC asked "Are you sure?" Linux asks you to type your password after `sudo`. Same idea: this command is allowed to change the whole machine.

## sudo is a scalpel

```bash
sudo pacman -S steam     # fine: install a system package
sudo rm -rf /            # famous last words
```

Rules of thumb:

- Installing software, editing `/etc`, updating the system → `sudo` is normal
- Anything inside your home folder → should **not** need sudo
- If a game or browser asks for sudo, that is a smell

You should not browse the web as root. You should not `sudo steam`. Proton does not get faster with admin rights.

## Updates are boring on purpose

A healthy week looks like:

1. Update when your distro tells you, or once or twice a week on purpose
2. Reboot if the kernel or NVIDIA driver moved
3. Carry on

Rolling distros (Arch, CachyOS, Tumbleweed) update frequently and are stable if you **do not mix random third-party repos and then ignore them for three months**. Ubuntu/Fedora point releases feel closer to Windows Update.

If an update warning looks apocalyptic, read it. If it is 400 packages named like libraries, that is a normal Friday on Arch.

## How people actually break installs

- Following a tutorial for the *wrong distro*
- Mixing Debian instructions into Arch, or Ubuntu PPAs into Mint without knowing
- Wiping the wrong disk in a partition tool
- Force-removing something that looks unused (`glibc` looks unused until the desktop vanishes)

Recovery is usually: boot a live USB, mount your disk, chroot, undo. That is a later skill. For now, avoid the situations.

## Backups without a lecture

Copy `/home/you` somewhere. That is 90% of "my Linux died." Timeshift / Snapper / btrfs snapshots are excellent if your distro set them up — use them before big experiments, not after.

## If you remember one thing

`sudo` is not a cheat code for "make it work." It is a declaration that you meant to change the system. Type slowly when you see it.
