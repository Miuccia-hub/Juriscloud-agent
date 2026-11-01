from dataclasses import replace
from tests.fixture_data import load_demo
from legal_agent.presentation import report_table,automatic_settings,apply_intake_limits
from legal_agent.i18n import translate


def test_table_escapes_document_and_model_text_and_localises_headers():
    report=load_demo()[3].model_copy(deep=True)
    report.risks[0].title='<script>alert("x")</script>'
    report.risks[0].explanation='<img src=x onerror="x">'
    table=report_table(report,lambda x:translate(x,"English"))
    assert '<script>' not in table and '<img' not in table
    assert '&lt;script&gt;' in table
    assert '<th>Issue</th>' in table and 'Risk analysis and suggested action' in table
    assert 'scope="row"' in table
    assert table.count('<tr>')==len(report.risks)+1


def test_automatic_review_keeps_unresolved_facts_and_scope_conditional():
    _,settings,intake,report,_=load_demo()
    intake.critical_questions=["Missing attachment"]
    intake.conflicts=["Conflicting law"]
    intake.local_gaps=["Undefined term"]
    updated=automatic_settings(settings,intake)
    assert updated.jurisdiction==settings.jurisdiction
    assert updated.stance==settings.stance
    assert 'No factual confirmations' in updated.confirmations
    assert 'not a finding of governing law' in updated.confirmations
    apply_intake_limits(report,intake)
    assert all(item in report.limitations for item in ('Missing attachment','Conflicting law','Undefined term'))
    before=list(report.limitations)
    apply_intake_limits(report,intake)
    assert report.limitations==before


def test_new_chat_clears_draft_but_preserves_connection_preferences():
    from pathlib import Path
    from tests.ui_helpers import workspace_app
    app=workspace_app(Path(__file__).resolve().parents[1]/"app.py").run()
    app.text_area(key="initial_question").set_value("Unsent question").run()
    app.text_input(key="api_key").set_value("test-only-key").run()
    app.button(key="new_chat").click().run()
    assert not app.exception
    assert app.text_area(key="initial_question").value==""
    assert app.text_input(key="api_key").value=="test-only-key"
    assert "main" not in app.session_state


def test_external_link_localises_without_unsupported_widget_key():
    from legal_agent.i18n import LocalizedUI
    class LinkTarget:
        def link_button(self, label, url):
            return label, url
    ui=LocalizedUI(LinkTarget(),lambda: 'English')
    assert ui.link_button('查看原始来源 / Open source','https://example.com') == ('Open original source','https://example.com')


def test_report_with_external_sources_keeps_followup_available():
    from pathlib import Path
    from tests.ui_helpers import workspace_app
    from legal_agent.models import Source
    main,settings,intake,report,choices=load_demo()
    app=workspace_app(Path(__file__).resolve().parents[1]/'app.py')
    state=dict(main=main,settings=settings,intake=intake,report=report,choices=choices,
               supplements=[],messages=[],answers=[],original_question='Review this contract',
               sources=[Source('RS1','Public source','https://www.legislation.gov.au/','',
                               '正文片段已取得','2026-10-29')])
    for key,value in state.items(): app.session_state[key]=value
    app.run()
    assert not app.exception
    assert app.text_area(key='question').placeholder=='针对上方审查结果继续提问…'
    assert len(app.get('link_button'))==1
    app.text_area(key='question').set_value('请进一步解释付款风险').run()
    assert not app.exception
    assert app.button(key='send_followup')
    app.selectbox(key='ui_language').set_value('English').run()
    assert not app.exception
    assert app.text_area(key='question').value=='请进一步解释付款风险'
    assert app.text_area(key='question').placeholder=='Ask a follow-up about the review above…'


def test_followup_question_reaches_every_stage_and_overrides_initial_scope():
    """Checks propagation through the real workflow; the gateway is a test double."""
    from copy import deepcopy
    from legal_agent.workflow import Workflow
    from legal_agent.models import Plan,Evidence,Critique,Report,FollowupAnswer
    main,settings,intake,report,_=load_demo()
    settings.focus='Review the whole contract for all risks'
    question='no Paid Time Off clauses'
    history=[{'role':'user','content':'Earlier question'}, {'role':'assistant','content':'Earlier answer'}]
    class RecordingGateway:
        def __init__(self): self.requests=[]
        def structured(self,stage,schema,payload,instruction):
            self.requests.append((schema,deepcopy(payload),instruction))
            if schema is Plan:return Plan(scope=['paid time off omission'],issues=['leave'],public_search_queries=['leave contract omission'],missing_information=[])
            if schema is Evidence:return Evidence(findings=[],limitations=['No live research in this test'])
            if schema is Critique:return Critique(defects=[],unsupported_risk_ids=[],conflicting_edit_ids=[],corrections=[])
            return FollowupAnswer(answered_question=question,direct_answer='Focused test answer to the leave question.',contract_analysis='Only leave-related text.',legal_analysis='No live legal research.',suggestions=[],next_steps=[],limitations=[])
        def search(self,*args):return []
    gateway=RecordingGateway()
    answer,*_=Workflow(gateway).followup(main,[],settings,intake,report,history,question,'Employment status is not confirmed')
    assert len(gateway.requests)==5
    for schema,payload,instruction in gateway.requests:
        assert payload['current_question']==question
        assert payload['settings']['focus']==question
        assert payload['settings']['mode']=='重点审查'
        assert payload['new_user_assertions']=='Employment status is not confirmed'
        assert 'current_question' in instruction
        assert 'documents' in payload
    assert gateway.requests[0][1]['history']==history
    assert gateway.requests[0][1]['prior_review_context']['summary']==report.summary
    assert settings.focus=='Review the whole contract for all risks' and settings.mode=='全面审查'
    assert answer.summary!='' and answer.summary!=report.summary
    assert not answer.risks  # A focused prose answer need not repeat the original risk table.


def test_followup_blocks_original_summary_or_wrong_question():
    """A provider response cannot silently re-label the initial review as a new answer."""
    import pytest
    from legal_agent.models import Plan,Evidence,Critique,FollowupAnswer
    from legal_agent.workflow import Workflow
    from legal_agent.errors import RunFailure
    main,settings,intake,initial,_=load_demo()
    question='好像也没提到年假'
    class WrongGateway:
        def __init__(self,wrong_question): self.wrong_question=wrong_question
        def search(self,*args):return []
        def structured(self,stage,schema,payload,instruction):
            if schema is Plan:return Plan(scope=['leave only'],issues=['leave'],public_search_queries=[],missing_information=[])
            if schema is Evidence:return Evidence(findings=[],limitations=[])
            if schema is Critique:return Critique(defects=['Answer is unrelated'],unsupported_risk_ids=[],conflicting_edit_ids=[],corrections=['Answer current question'])
            return FollowupAnswer(answered_question='Review jurisdiction' if self.wrong_question else question,
                direct_answer='Unrelated answer' if self.wrong_question else initial.summary,
                contract_analysis='',legal_analysis='',next_steps=[],limitations=[],suggestions=[])
    for wrong_question in (True,False):
        with pytest.raises(RunFailure) as caught:
            Workflow(WrongGateway(wrong_question)).followup(main,[],settings,intake,initial,[],question,'')
        assert caught.value.code=='followup_mismatch'
