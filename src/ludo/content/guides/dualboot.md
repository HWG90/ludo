# Keeping Windows around

You can dual-boot. You can put Linux on a second drive and pick it in the firmware boot menu. You can keep Windows in a VM for one tax app. All of these are adult choices. Wiping the only disk on impulse is not.

## Second drive is the calm option

Install Linux on its own SSD. In UEFI, pick the disk to boot. No shared bootloader drama, no "Windows Update ate GRUB" week. Unplug the Windows drive during the Linux install if you want to be extra boring (then plug it back in).

## Same drive dual-boot

Shrink Windows in Windows (`diskmgmt.msc`), *never* from a half-awake installer if you can help it. Leave the Windows EFI partition alone. Install Linux next to it. Learn how to get into the UEFI boot menu on *this* motherboard (a key at power-on, not a prayer).

BitLocker will complain if you poke partitions. Have the recovery key. Fast Startup in Windows is a fake shutdown and it makes the Windows partition look "dirty" to Linux — turn it off.

## NTFS Steam libraries

It looks tempting: one `D:\Games` for both operating systems. It is a trap.

NTFS on Linux does not do POSIX permissions, executable bits, or file locking the way Proton expects. You get mysterious missing redistributables, games that update forever, and prefixes that corrupt.

Keep:

- Windows games on NTFS, played from Windows
- Linux Steam on ext4, btrfs, or xfs

Copy installed games across if you must; do not share the library folder.

## Firmware, Secure Boot, TPM

Secure Boot can work (especially on Ubuntu/Fedora). On Arch-family gaming distros it is often more hassle than it is worth unless you know why you need it. NVIDIA + Secure Boot means signing kernel modules. Save that fight for week four.

## If you remember one thing

Two operating systems can share a computer. They should not share a Steam library on NTFS. A second drive is the dual-boot with the least lore.
