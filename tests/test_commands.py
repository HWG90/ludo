from ludo.content.commands import translate_command


def test_dir() -> None:
    hits = translate_command("dir")
    assert hits[0].linux.startswith("ls")


def test_ipconfig() -> None:
    hits = translate_command("ipconfig")
    assert any("ip addr" in entry.linux for entry in hits)


def test_taskkill() -> None:
    hits = translate_command("taskkill")
    assert hits[0].linux == "kill"


def test_unknown() -> None:
    assert translate_command("definitely-not-a-command-xyz") == []


def test_empty_lists_all() -> None:
    assert len(translate_command("")) > 10
