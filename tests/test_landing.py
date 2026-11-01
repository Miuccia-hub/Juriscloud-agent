"""Landing navigation tests; no credentials, provider calls or legal output."""
from pathlib import Path
from streamlit.testing.v1 import AppTest
from tests.ui_helpers import workspace_app

APP=Path(__file__).resolve().parents[1]/'app.py'


def test_public_entry_renders_intro_without_workspace_or_model_request():
    app=AppTest.from_file(APP).run()
    assert not app.exception
    assert len(app.get('component_instance'))==1
    assert not app.text_input and not app.text_area
    assert 'gateway' not in app.session_state
    assert app.session_state['ui_language']=='English'


def test_get_started_keeps_locale_and_preferences(monkeypatch):
    import legal_agent.landing
    monkeypatch.setattr(legal_agent.landing,'render_landing',lambda *args:dict(
        action='start',language='English',reduce_motion=True,nonce=101))
    app=AppTest.from_file(APP).run()
    assert not app.exception
    assert app.session_state['page']=='workspace'
    assert app.selectbox(key='ui_language').value=='English'
    assert not any(widget.key=='reduce_motion' for widget in app.checkbox)
    assert app.text_area(key='initial_question')
    assert 'gateway' not in app.session_state


def test_back_home_and_return_preserves_unsent_contract(monkeypatch):
    import legal_agent.landing
    monkeypatch.setattr(legal_agent.landing,'render_landing',lambda *args:None)
    app=workspace_app(APP).run()
    app.radio(key='input_mode').set_value('粘贴文本').run()
    app.text_area(key='contract_text').set_value('Fictional unsent contract').run()
    app.text_area(key='initial_question').set_value('Check payment').run()
    app.button(key='back_home').click().run()
    assert app.session_state['page']=='home' and not app.exception
    # Streamlit cleans absent widget keys unless explicitly retained across views.
    assert app.session_state['contract_text']=='Fictional unsent contract'
    monkeypatch.setattr(legal_agent.landing,'render_landing',lambda *args:dict(
        action='start',language='中文',reduce_motion=False,nonce=102))
    app.run()
    assert not app.exception
    assert app.text_area(key='initial_question').value=='Check payment'
