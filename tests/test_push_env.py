import sys

from conftest import ROOT

sys.path.insert(0, str(ROOT / "tools"))


def test_dry_run_never_prints_secret_values(tmp_path, capsys):
    from push_vercel_env import main
    (tmp_path / "secrets.env").write_text("SESSION_SECRET=supergeheim123\nLINKEDIN_CLIENT_SECRET=topsecret456\n# X=1\n")
    (tmp_path / "pass.p12").write_bytes(b"\x00geheim")
    assert main(["--dir", str(tmp_path), "--dry-run"]) == 1   # fehlt noch etwas
    out = capsys.readouterr().out
    assert "supergeheim123" not in out and "topsecret456" not in out
    assert "SESSION_SECRET" in out and "APPLE_P12_BASE64" in out and "Fehlt noch" in out


def test_write_env_file_is_private(tmp_path, capsys):
    from push_vercel_env import main
    (tmp_path / "secrets.env").write_text("SESSION_SECRET=abc\n")
    main(["--dir", str(tmp_path), "--write-env"])
    f = tmp_path / "vercel-import.env"
    assert "SESSION_SECRET=abc" in f.read_text() and oct(f.stat().st_mode)[-3:] == "600"
    assert "abc" not in capsys.readouterr().out
