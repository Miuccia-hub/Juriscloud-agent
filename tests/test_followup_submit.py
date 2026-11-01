"""Accepted sends clear before work; failed sends restore the exact draft."""
from pathlib import Path
import pytest
from streamlit import session_state
from legal_agent.interactions import queue_followup
from legal_agent.models import Report, Evidence, Critique
from tests.fixture_data import load_demo
from tests.ui_helpers import workspace_app
from tests.test_core import FakeGateway


def fixture_app(monkeypatch, followup):
    import legal_agent.workflow as workflow
    monkeypatch.setattr(workflow,'Gateway',lambda *args:FakeGateway())
    monkeypatch.setattr(workflow.Workflow,'followup',followup)
    main,settings,intake,report,choices=load_demo()
    app=workspace_app(Path(__file__).resolve().parents[1]/'app.py')
    for key,value in dict(main=main,settings=settings,intake=intake,report=report,choices=choices,
        sources=[],answers=[],messages=[],supplements=[],api_key='test-only-no-network',
        evidence=Evidence(findings=[],limitations=[])).items():
        app.session_state[key]=value
    return app.run()


def result():
    return (Report(summary='Fictional focused answer.',coverage=[],assumptions=[],risks=[],
                   suggestions=[],next_steps=[],limitations=[]),[],
            Evidence(findings=[],limitations=[]),Critique(defects=[],unsupported_risk_ids=[],conflicting_edit_ids=[],corrections=[]))


def test_send_clears_widgets_before_work_and_uses_captured_question_and_facts(monkeypatch):
    seen=[]
    def followup(self,main,supplements,settings,intake,report,messages,question,facts):
        assert session_state.question=='' and session_state.new_facts==''
        seen.append((question,facts))
        return result()
    app=fixture_app(monkeypatch,followup)
    app.text_area(key='question').set_value('Only explain the missing leave provision.').run()
    app.text_area(key='new_facts').set_value('Fictional new fact.').run()
    app.button(key='send_followup').click().run()
    assert not app.exception
    assert seen==[('Only explain the missing leave provision.','Fictional new fact.')]
    assert app.text_area(key='question').value==''
    assert app.session_state['answers'][0][0]==seen[0][0]
    assert app.session_state['messages'][0]['content']==seen[0][0]+'\n'+seen[0][1]
    app.run()
    assert len(seen)==1  # Rendering again never resubmits automatically.


def test_failed_send_restores_question_and_facts_and_manual_retry_uses_them(monkeypatch):
    calls=[]
    def followup(self,main,supplements,settings,intake,report,messages,question,facts):
        assert session_state.question=='' and session_state.new_facts==''
        calls.append((question,facts))
        if len(calls)==1:
            raise RuntimeError('PRIVATE_TEST_EXCEPTION_NOT_FOR_UI')
        return result()
    app=fixture_app(monkeypatch,followup)
    app.text_area(key='question').set_value('Retry this exact question.').run()
    app.text_area(key='new_facts').set_value('Keep the exact new facts.').run()
    app.button(key='send_followup').click().run()
    assert not app.exception and app.error
    assert all('PRIVATE_TEST_EXCEPTION_NOT_FOR_UI' not in error.value for error in app.error)
    assert app.text_area(key='question').value=='Retry this exact question.'
    assert app.text_area(key='new_facts').value=='Keep the exact new facts.'
    assert not app.session_state['answers'] and not app.session_state['messages']
    assert 'report' in app.session_state
    app.button(key='send_followup').click().run()
    assert not app.exception and len(calls)==2 and calls[0]==calls[1]
    assert not app.error and app.text_area(key='question').value==''
    assert len(app.session_state['answers'])==1


@pytest.mark.parametrize('overrides',[{'api_key':''},{'question':'  '},{'messages':[{}]*20}])
def test_invalid_send_does_not_clear_draft_or_queue_work(overrides):
    session={'question':'Keep this draft.','new_facts':'Keep these facts.','api_key':'test-only',
             'messages':[],**overrides}
    before=dict(session)
    assert not queue_followup(session)
    assert session==before
