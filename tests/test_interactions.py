"""Real export/state integration with fictional material, without any model calls."""
from contextlib import contextmanager
from pathlib import Path
from types import SimpleNamespace
from io import BytesIO
from zipfile import ZipFile
import pytest
from legal_agent.interactions import analysis_activity, consume_export_request, export_action, pdf_preview_url
from tests.fixture_data import load_demo
from tests.ui_helpers import workspace_app


@pytest.mark.parametrize('raises',[False,True])
def test_cloud_clears_on_completion_and_error(raises):
    events=[]
    indicator=SimpleNamespace(markdown=lambda *a,**kw:events.append(a[0]),empty=lambda:events.append('cleared'))
    @contextmanager
    def block(*a,**kw): yield SimpleNamespace()
    ui=SimpleNamespace(container=block,empty=lambda:indicator,status=block)
    try:
        with analysis_activity(ui,lambda v:v,True):
            assert 'motion-paused' in events[0]
            assert '💭' in events[0]
            if raises: raise RuntimeError('test failure')
    except RuntimeError:
        assert raises
    assert events[-1]=='cleared'


def test_export_click_is_consumed_once_and_busy_ignores_duplicate():
    session={}
    assert not consume_export_request(session,None)
    assert not consume_export_request(session,{'action':'generate','nonce':42})
    assert consume_export_request(session,{'action':'generate','nonce':'first'})
    assert session['export_state']=='generating'
    assert not consume_export_request(session,{'action':'generate','nonce':'second'})
    session['export_state']='ready'
    assert not consume_export_request(session,{'action':'generate','nonce':'first'})
    session['export_state']='error'
    assert consume_export_request(session,{'action':'generate','nonce':'retry'})


def test_pdf_only_passed_to_ready_component(monkeypatch):
    import legal_agent.interactions as interactions
    sent=[]
    monkeypatch.setattr(interactions,'_export',lambda **kw:sent.append(kw))
    registered=[]
    monkeypatch.setattr(interactions,'pdf_preview_url',lambda data:registered.append(data) or '/media/test.pdf')
    pdf=b'%PDF-FICTIONAL-TEST'
    export_action('generating','English',True,pdf)
    assert sent[-1]['pdf_url'] is None and not registered
    export_action('ready','English',True,pdf)
    assert sent[-1]['pdf_url']=='/media/test.pdf' and registered==[pdf]
    assert sent[-1]['english'] and sent[-1]['reduce_motion']


def test_preview_uses_inline_session_media_with_deployment_base_path(monkeypatch):
    from streamlit import runtime,config
    registered=[]
    manager=SimpleNamespace(add=lambda *args,**kw:registered.append((args,kw)) or '/media/fixture.pdf')
    monkeypatch.setattr(runtime,'exists',lambda:True)
    monkeypatch.setattr(runtime,'get_instance',lambda:SimpleNamespace(media_file_mgr=manager))
    monkeypatch.setattr(config,'get_option',lambda key:'legal')
    assert pdf_preview_url(b'%PDF-fixture')=='/legal/media/fixture.pdf'
    args,kwargs=registered[0]
    assert args[:2]==(b'%PDF-fixture','application/pdf')
    assert kwargs=={'file_name':'review-preview.pdf','is_for_static_download':False}


def export_app():
    app=workspace_app(Path(__file__).resolve().parents[1]/'app.py')
    main,settings,intake,report,choices=load_demo()
    for key,value in dict(main=main,settings=settings,intake=intake,report=report,choices=choices,
        view='带走审查结果 / Export your work',sources=[],answers=[],messages=[],supplements=[]).items():
        app.session_state[key]=value
    return app


def test_export_ready_only_after_real_word_and_pdf_generated(monkeypatch):
    import legal_agent.interactions as interactions
    import legal_agent.exports as exports
    event={};seen=[];calls=[]
    def render(state,*args):
        seen.append(state)
        return dict(event)
    original=exports.report_pdf
    def pdf(sections):
        calls.append('pdf')
        return original(sections)
    monkeypatch.setattr(interactions,'export_action',render)
    monkeypatch.setattr(exports,'report_pdf',pdf)
    app=export_app().run(timeout=15)
    assert 'exports' not in app.session_state
    event.update(action='generate',nonce='actual-export')
    app.run(timeout=15)
    assert not app.exception
    assert 'generating' in seen and seen[-1]=='ready'
    out=app.session_state['exports']
    assert out['report_pdf'].startswith(b'%PDF-')
    with ZipFile(BytesIO(out['report_docx'])) as archive:
        assert 'word/document.xml' in archive.namelist()
    app.run(timeout=15)
    assert calls==['pdf']  # A persisted component event never generates twice.


def test_failed_export_stops_loading_keeps_review_and_can_retry(monkeypatch):
    import legal_agent.interactions as interactions
    import legal_agent.exports as exports
    event={'action':'generate','nonce':'broken'}
    monkeypatch.setattr(interactions,'export_action',lambda *a:dict(event))
    original=exports.report_pdf
    def broken(_): raise RuntimeError('PRIVATE_CONTRACT_DO_NOT_ECHO')
    monkeypatch.setattr(exports,'report_pdf',broken)
    app=export_app().run(timeout=15)
    assert not app.exception
    assert app.session_state['export_state']=='error'
    assert 'exports' not in app.session_state
    assert 'report' in app.session_state
    assert any('报告文件生成失败' in x.value for x in app.error)
    assert all('PRIVATE_CONTRACT_DO_NOT_ECHO' not in x.value for x in app.error)
    monkeypatch.setattr(exports,'report_pdf',original)
    event['nonce']='retry'
    app.run(timeout=15)
    assert not app.exception
    assert app.session_state['export_state']=='ready'
