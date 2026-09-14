from ludo.settings import Settings
from ludo.update import (
    UpdateInfo,
    apply_update,
    check_for_update,
    is_newer,
    parse_pyproject_version,
    prompt_copy,
    should_offer,
    version_parts,
)


def test_version_compare() -> None:
    assert is_newer("0.2.0", "0.1.0")
    assert is_newer("v0.1.1", "0.1.0")
    assert not is_newer("0.1.0", "0.1.0")
    assert not is_newer("0.1.0", "0.2.0")
    assert version_parts("0.2") == (0, 2, 0)
    assert version_parts("v1.0.0") == (1, 0, 0)


def test_parse_pyproject_version() -> None:
    text = "[build-system]\nrequires = []\n\n[project]\nname = \"ludo-linux\"\nversion = \"0.3.1\"\n"
    assert parse_pyproject_version(text) == "0.3.1"


def test_should_offer_skips_this_version() -> None:
    settings = Settings(skip_update="0.2.0")
    assert not should_offer(settings, "0.1.0", "0.2.0")
    assert should_offer(settings, "0.1.0", "0.3.0")
    assert not should_offer(Settings(), "0.2.0", "0.2.0")
    assert should_offer(Settings(), "0.1.0", "0.2.0")


def test_check_disabled(monkeypatch) -> None:
    monkeypatch.setenv("LUDO_UPDATE", "off")
    assert check_for_update(Settings(), local="0.1.0") is None


def test_check_for_update_when_newer(monkeypatch) -> None:
    monkeypatch.setenv("LUDO_UPDATE", "auto")
    monkeypatch.setattr("ludo.update.fetch_remote_version", lambda timeout=4.0: "9.9.9")
    info = check_for_update(Settings(), local="0.1.0")
    assert info is not None
    assert info.remote == "9.9.9"
    assert info.local == "0.1.0"


def test_check_for_update_when_current(monkeypatch) -> None:
    monkeypatch.setenv("LUDO_UPDATE", "auto")
    monkeypatch.setattr("ludo.update.fetch_remote_version", lambda timeout=4.0: "0.1.0")
    assert check_for_update(Settings(), local="0.1.0") is None


def test_fetch_falls_back_to_pyproject(monkeypatch) -> None:
    monkeypatch.setenv("LUDO_UPDATE", "auto")

    def fake_json(url: str, *, timeout: float) -> dict:
        raise OSError("no releases")

    def fake_text(url: str, *, timeout: float) -> str:
        assert "pyproject.toml" in url
        return '[project]\nversion = "1.4.0"\n'

    monkeypatch.setattr("ludo.update._get_json", fake_json)
    monkeypatch.setattr("ludo.update._get_text", fake_text)
    from ludo.update import fetch_remote_version

    assert fetch_remote_version() == "1.4.0"


def test_apply_update_uses_install_kind(monkeypatch) -> None:
    monkeypatch.setattr("ludo.update.install_kind", lambda: "pipx")
    monkeypatch.setattr("ludo.update.git_url", lambda: "https://github.com/HWG90/ludo.git")
    ran: list[list[str]] = []
    monkeypatch.setattr("ludo.update._run", lambda command: ran.append(command))
    apply_update()
    assert ran[0][:3] == ["pipx", "install", "--force"]
    assert ran[0][3].startswith("git+")


def test_prompt_copy_mentions_versions() -> None:
    copy = prompt_copy(UpdateInfo(local="0.1.0", remote="0.2.0", repo="HWG90/ludo"))
    assert "0.2.0" in copy
    assert "0.1.0" in copy
    assert "Yes, update now" in copy


def test_install_kind_detects_uv_without_following_python_symlink(monkeypatch) -> None:
    import sys

    from ludo.update import install_kind

    monkeypatch.setattr(sys, "executable", "/home/me/.local/share/uv/tools/ludo-linux/bin/python")
    monkeypatch.setattr(sys, "argv", ["ludo"])
    monkeypatch.setattr("ludo.update.shutil.which", lambda name: None)
    monkeypatch.setattr("ludo.update.source_repo", lambda: None)
    assert install_kind() == "uv"


def test_install_kind_detects_pipx_from_unresolved_path(monkeypatch) -> None:
    import sys

    from ludo.update import install_kind

    monkeypatch.setattr(sys, "executable", "/home/me/.local/share/pipx/venvs/ludo-linux/bin/python")
    monkeypatch.setattr(sys, "argv", ["ludo"])
    monkeypatch.setattr("ludo.update.shutil.which", lambda name: None)
    monkeypatch.setattr("ludo.update.source_repo", lambda: None)
    assert install_kind() == "pipx"


def test_install_kind_detects_uv_from_ludo_script(monkeypatch) -> None:
    import sys

    from ludo.update import install_kind

    monkeypatch.setattr(sys, "executable", "/usr/bin/python3")
    monkeypatch.setattr(sys, "argv", ["/home/me/.local/bin/ludo"])
    monkeypatch.setattr(
        "ludo.update.shutil.which",
        lambda name: "/home/me/.local/share/uv/tools/ludo-linux/bin/ludo" if name == "ludo" else None,
    )
    monkeypatch.setattr("ludo.update.source_repo", lambda: None)
    assert install_kind() == "uv"
