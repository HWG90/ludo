# There is no C: drive

Windows taught you that storage is a row of letters. Linux taught the rest of the industry that storage is a tree. Everything starts at `/` (root). Other disks are *mounted* — attached as folders.

## The rooms you will actually use

| Path | Windows muscle memory |
| --- | --- |
| `/home/you` | `C:\Users\you` |
| `~/Downloads` | Downloads |
| `~/Desktop` | Desktop |
| `~/.config` | AppData/Roaming |
| `~/.local/share` | AppData/Local |
| `/usr` | Program Files (system) |
| `/etc` | System-wide settings |
| `/tmp` | Temp |
| `/mnt` or `/run/media/you` | Extra disks, USB drives |

`~` means home. It is not a cute emoji. It is a real path.

## Case sensitivity

`Steam` and `steam` are different names. `Photo.jpg` and `photo.jpg` are different files. This bites people who grew up on NTFS being "mostly case-insensitive."

## Permissions, not just ownership

Every file has a user, a group, and bits for read/write/execute. That is why an AppImage can sit in Downloads and refuse to launch until `chmod +x`. It is also why your user can wreck `/home/you` freely and cannot wreck `/usr` without `sudo`.

## USB drives and the Windows partition

Plug in a stick — it appears in the file manager sidebar. Eject it there before you yank it. The Windows disk from a dual-boot shows up the same way. You can copy files off it. Do not use it as your Linux Steam library (see the dual-boot guide).

## Hidden files

Names starting with `.` are hidden. `ls -a` shows them. `Ctrl+H` in most file managers toggles them. That is where Firefox, Steam, and your shell keep their brains.

## If you remember one thing

Your stuff lives in `/home/you`. If you never leave home except through the software store, you can daily-drive Linux without ever thinking about `/usr`. When something breaks, "is it in my home folder or is it a system package?" is the right first question.
