import json
from legal_agent.credentials import backend_pkulaw_token, save_backend_pkulaw_token


def test_server_token_env_precedence_and_local_fallback(tmp_path, monkeypatch):
    path = tmp_path / "private.json"
    path.write_text(json.dumps({"token": "local-test-only"}))
    monkeypatch.delenv("PKULAW_TOKEN", raising=False)
    assert backend_pkulaw_token(path) == "local-test-only"
    monkeypatch.setenv("PKULAW_TOKEN", "Bearer env-test-only")
    assert backend_pkulaw_token(path) == "env-test-only"


def test_bad_config_or_header_cannot_be_used(tmp_path, monkeypatch):
    path = tmp_path / "private.json"
    monkeypatch.delenv("PKULAW_TOKEN", raising=False)
    assert not backend_pkulaw_token(path)
    for value in ("broken-json", "[]", '{"token":123}', '{"token":"a\\nb"}'):
        path.write_text(value)
        assert not backend_pkulaw_token(path)
    monkeypatch.setenv("PKULAW_TOKEN", "a\nb")
    assert not backend_pkulaw_token(path)


def test_server_credential_is_not_rendered_in_widgets_or_session(monkeypatch):
    from pathlib import Path
    from streamlit.testing.v1 import AppTest
    monkeypatch.setenv("PKULAW_TOKEN", "fixture-server-token-not-real")
    app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / "app.py"), default_timeout=15)
    app.session_state["page"] = "workspace"
    app.run()
    assert not app.exception
    assert not any(w.key == "pkulaw_token" for w in app.text_input)
    assert app.checkbox(key="pkulaw_enabled").value is True
    assert "pkulaw_token" not in app.session_state
    assert "fixture-server-token-not-real" not in repr([(w.label, w.value) for w in app.text_input])
    app.button(key="new_chat").click().run()
    assert not app.exception and "pkulaw_token" not in app.session_state


def test_local_save_permissions_and_reuse_without_disclosing_token(tmp_path, monkeypatch):
    monkeypatch.delenv("PKULAW_TOKEN", raising=False)
    path=tmp_path / "private.json"
    save_backend_pkulaw_token("fixture-persisted-only", path)
    assert path.stat().st_mode & 0o777 == 0o600
    assert backend_pkulaw_token(path) == "fixture-persisted-only"
    assert list(tmp_path.iterdir()) == [path]


def test_one_time_admin_save_then_hide_input(tmp_path, monkeypatch):
    from pathlib import Path
    from streamlit.testing.v1 import AppTest
    from legal_agent import credentials
    monkeypatch.delenv("PKULAW_TOKEN", raising=False)
    path=tmp_path / "server.json"
    monkeypatch.setattr(credentials,"PKULAW_SECRET_FILE",path)
    app=AppTest.from_file(str(Path(__file__).resolve().parents[1]/"app.py"), default_timeout=15)
    app.session_state["page"]="workspace"
    app.run()
    app.text_input(key="pkulaw_token").set_value("fixture-admin-once").run()
    app.button(key="save_pkulaw_backend").click().run()
    assert not app.exception
    assert backend_pkulaw_token(path)=="fixture-admin-once"
    assert not any(w.key=="pkulaw_token" for w in app.text_input)
    assert "pkulaw_token" not in app.session_state
