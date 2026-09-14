from pathlib import Path

from ludo.probe import SystemProfile, read_os_release


def test_read_os_release(tmp_path: Path) -> None:
    path = tmp_path / "os-release"
    path.write_text(
        'NAME="CachyOS Linux"\n'
        "ID=cachyos\n"
        'ID_LIKE="arch"\n'
        'PRETTY_NAME="CachyOS"\n'
        "# comment\n",
        encoding="utf-8",
    )
    data = read_os_release(path)
    assert data["ID"] == "cachyos"
    assert data["PRETTY_NAME"] == "CachyOS"
    assert data["ID_LIKE"] == "arch"


def test_read_os_release_missing(tmp_path: Path) -> None:
    assert read_os_release(tmp_path / "nope") == {}


def test_family_arch() -> None:
    assert SystemProfile(distro_id="cachyos", distro_like=("arch",)).family == "arch"


def test_family_debian() -> None:
    assert SystemProfile(distro_id="linuxmint", distro_like=("ubuntu", "debian")).family == "debian"


def test_family_fedora() -> None:
    assert SystemProfile(distro_id="nobara", distro_like=("fedora",)).family == "fedora"


def test_clean_lspci_name() -> None:
    from ludo.probe import _clean_lspci_name

    assert (
        _clean_lspci_name("NVIDIA Corporation GB202 [GeForce RTX 5090] [10de:2b85] (rev a1)")
        == "NVIDIA Corporation GB202 [GeForce RTX 5090]"
    )
