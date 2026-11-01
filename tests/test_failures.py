"""Provider response regressions; no network, keys or fabricated live results."""
import json
from types import SimpleNamespace
import pytest
from legal_agent.models import Intake,Report
from legal_agent.workflow import Gateway
from legal_agent.errors import RunFailure,classify,message
from tests.fixture_data import load_demo


def response(status="completed",text=None,reason=None,refusal=False):
    return SimpleNamespace(status=status,output_text=text,
        incomplete_details=SimpleNamespace(reason=reason),usage=SimpleNamespace(total_tokens=42),
        output=[SimpleNamespace(content=[SimpleNamespace(type="refusal" if refusal else "output_text")])],
        _request_id="req_test123")

@pytest.mark.parametrize("value,code",[
    (response("incomplete",'{"contract_type":',"max_output_tokens"),"incomplete_tokens"),
    (response("incomplete","{}","content_filter"),"incomplete"),
    (response(text="",refusal=True),"refusal"),
    (response(text=""),"empty_output"),
    (response(text='{"private_contract":"DO_NOT_EXPOSE"}'),"invalid_output"),
])
def test_invalid_response_has_specific_safe_error(monkeypatch,value,code):
    g=Gateway("test-not-real","test-model")
    monkeypatch.setattr(g.client.responses,"create",lambda **kw:value)
    with pytest.raises(RunFailure) as caught:
        g.structured("read materials",Intake,{},"")
    assert caught.value.code==code
    assert caught.value.stage=="read materials"
    assert "DO_NOT_EXPOSE" not in str(caught.value)
    assert len(g.calls)==1 and not g.calls[0].success
    assert g.calls[0].tokens==42


def test_completed_response_validates_schema_and_does_not_retry(monkeypatch):
    g=Gateway("test-not-real","test-model")
    expected=load_demo()[2]
    calls=[]
    def create(**kwargs):
        calls.append(kwargs)
        return response(text=expected.model_dump_json())
    monkeypatch.setattr(g.client.responses,"create",create)
    assert g.structured("read",Intake,{},"")==expected
    assert len(calls)==1 and g.calls[0].success
    assert calls[0]["text"]["format"]["strict"] is True
    assert calls[0]["store"] is False

@pytest.mark.parametrize("status,api_code,expected",[(401,None,"authentication"),(429,"insufficient_quota","quota"),(429,None,"rate_limit"),(404,None,"model_access"),(400,None,"request"),(503,None,"service")])
def test_provider_error_does_not_echo_key(status,api_code,expected):
    exc=Exception("sk-secret-test contract DO_NOT_EXPOSE")
    exc.status_code=status;exc.body={"code":api_code};exc.request_id="req_safe123"
    failure=classify(exc,"test stage")
    assert failure.code==expected
    assert "sk-secret" not in message(failure,"中文")
    assert "DO_NOT_EXPOSE" not in str(failure)
    assert failure.request_id=="req_safe123"


def test_file_failure_ui_reports_actual_cause():
    from pathlib import Path
    from tests.ui_helpers import workspace_app
    app=workspace_app(Path(__file__).resolve().parents[1]/"app.py").run()
    app.radio(key="input_mode").set_value("粘贴文本").run()
    app.button(key="send_initial").click().run()
    assert not app.exception
    assert any("材料未通过检查" in x.value for x in app.error)
    assert any("文件为空" in x.value for x in app.warning)
    assert app.session_state["last_failure"]["code"]=="input"
    assert app.session_state["last_failure"]["stage"]=="读取与检查文件"
    assert not any("ValueError" in x.value for x in app.error)


@pytest.mark.parametrize('cause,expected',[
    (__import__('httpx').ReadTimeout('PRIVATE_PAYLOAD'),'connection_read_timeout'),
    (__import__('ssl').SSLCertVerificationError('PRIVATE_PAYLOAD'),'connection_tls'),
    (__import__('socket').gaierror(-2,'PRIVATE_PAYLOAD'),'connection_dns'),
])
def test_connection_cause_is_specific_without_exposing_private_text(cause,expected):
    from openai import APIConnectionError
    import httpx
    exc=APIConnectionError(request=httpx.Request('POST','https://api.openai.com/v1/responses'))
    exc.__cause__=cause
    failure=classify(exc,'intake')
    assert failure.code==expected
    assert failure.stage=='intake'
    for language in ('中文','English'):
        assert 'PRIVATE_PAYLOAD' not in message(failure,language)
        assert 'https://' not in message(failure,language)


@pytest.mark.parametrize('kind,expected',[
    ('ConnectTimeout','connection_connect_timeout'),
    ('ReadTimeout','connection_read_timeout'),
    ('WriteTimeout','connection_write_timeout'),
    ('PoolTimeout','connection_pool_timeout'),
])
def test_timeout_phase_survives_openai_exception_wrapper(kind,expected):
    import httpx
    from openai import APITimeoutError
    exc=APITimeoutError(request=httpx.Request('POST','https://api.openai.com/v1/responses'))
    exc.__cause__=getattr(httpx,kind)('PRIVATE_KEY_AND_CONTRACT')
    failure=classify(exc,'read materials')
    assert failure.code==expected
    assert failure.stage=='read materials'
    assert 'PRIVATE_KEY_AND_CONTRACT' not in str(failure)
    for locale in ('中文','English'):
        assert 'PRIVATE_KEY_AND_CONTRACT' not in message(failure,locale)


@pytest.mark.parametrize('model,schema,effort',[
    ('gpt-5',Intake,'low'),
    ('gpt-5-2025-08-07',Intake,'low'),
    ('gpt-5',Report,'medium'),
    ('gpt-4o',Intake,None),
    ('gpt-4o-mini',Intake,None),
    ('gpt-6.1-sol',Intake,None),
    ('gpt-6-luna',Intake,None),
])
def test_gpt5_extracts_with_low_effort_but_review_preserves_reasoning(monkeypatch,model,schema,effort):
    from legal_agent.models import Report
    g=Gateway('test-not-real',model)
    expected=load_demo()[3 if schema is Report else 2]
    captured=[]
    def create(**kwargs):
        captured.append(kwargs)
        return response(text=expected.model_dump_json())
    monkeypatch.setattr(g.client.responses,'create',create)
    assert g.structured('read or review',schema,{'documents':'all supplied text'},'')==expected
    assert len(captured)==1
    request=captured[0]
    assert request['model']==model  # No hidden fallback to another model.
    assert request['store'] is False
    assert request['text']['format']['strict'] is True
    assert 'all supplied text' in request['input'][1]['content']
    if effort: assert request['reasoning']=={'effort':effort}
    else: assert 'reasoning' not in request
    assert g.client.timeout.connect==20
    assert g.client.timeout.read==600
    assert g.client.timeout.write==60
    assert g.client.timeout.pool==20
    assert g.client.max_retries==0


def test_connection_check_uses_real_structured_path_without_contract(monkeypatch):
    g=Gateway('test-not-real','gpt-5')
    captured=[]
    def create(**kwargs):
        captured.append(kwargs)
        return response(text='{"ok":true}')
    monkeypatch.setattr(g.client.responses,'create',create)
    assert g.check_connection() is True
    request=captured[0]
    assert request['model']=='gpt-5'
    assert json.loads(request['input'][1]['content'])=={'task':'connectivity_check'}
    assert request['text']['format']['strict'] is True
    assert request['text']['format']['schema']['additionalProperties'] is False
    assert request['reasoning']=={'effort':'low'}
    assert request['store'] is False
    assert g.calls[0].success


def test_connection_check_rejects_negative_result(monkeypatch):
    g=Gateway('test-not-real','gpt-5')
    monkeypatch.setattr(g.client.responses,'create',lambda **kw:response(text='{"ok":false}'))
    with pytest.raises(RunFailure) as caught:
        g.check_connection()
    assert caught.value.code=='invalid_output'


def test_connection_test_ui_only_runs_on_request_and_does_not_replace_materials(monkeypatch):
    from pathlib import Path
    from tests.ui_helpers import workspace_app
    import legal_agent.workflow as workflow
    calls=[]
    class ProbeGateway:
        def __init__(self,key,model,search_model):
            calls.append(('create',model))
            self.client=SimpleNamespace(close=lambda:calls.append(('close',)))
        def check_connection(self):
            calls.append(('check',))
            return True
    monkeypatch.setattr(workflow,'Gateway',ProbeGateway)
    app=workspace_app(Path(__file__).resolve().parents[1]/'app.py')
    main,settings,*_=load_demo()
    state=dict(main=main,settings=settings,review_trace=['timeout test fixture'],
        api_key='test-not-real',ui_language='English',original_question='PRIVATE_QUESTION',
        model='gpt-5',search_model='gpt-4o')
    for key,value in state.items(): app.session_state[key]=value
    app.run(timeout=15)
    assert not calls
    for key in ('model','search_model'):
        assert app.selectbox(key=key).options==['gpt-6-luna','gpt-6.1-sol']
        assert app.selectbox(key=key).value=='gpt-6-luna'
    app.button(key='test_model_connection').click().run(timeout=15)
    assert not app.exception
    assert calls==[('create','gpt-6-luna'),('check',),('close',)]
    assert any('connection test passed' in item.value for item in app.success)
    assert app.session_state['main']==main
    assert app.session_state['original_question']=='PRIVATE_QUESTION'
    assert app.session_state['review_trace']==['timeout test fixture']
