"""Citation links use retrieved fixtures only; no model or paid research calls."""
from pathlib import Path
from types import SimpleNamespace
import pytest
from legal_agent.models import Source, Report
from legal_agent.pkulaw import sources_from_result, safe_pkulaw_url
from legal_agent.presentation import pkulaw_case_links_text, report_copy_text
from legal_agent.exports import report_sections
from legal_agent.i18n import translate
from tests.fixture_data import load_demo
from tests.ui_helpers import workspace_app

URL='https://www.pkulaw.com/pfnl/fictional-test.html?way=textBasic'


def answer(text):
    return Report(summary=text,coverage=[],assumptions=[],risks=[],suggestions=[],next_steps=[],limitations=[])


def source(id='Q1-PKU-cases-1',url=URL):
    return Source(id,'Fictional case for testing',url,'Fixture snippet','MCP检索片段已取得','2026-11-01','北大法宝 MCP')


@pytest.mark.parametrize('field',['url','URL','Url','link','CaseUrl','detailUrl','href'])
def test_vendor_link_fields_preserve_public_document_url(field):
    result=SimpleNamespace(isError=False,structuredContent={'data':[{'title':'Fixture',field:URL}]},content=[])
    assert sources_from_result(result,'cases','fixture-secret')[0].url==URL


@pytest.mark.parametrize('url',[
    'javascript:alert(1)','https://pkulaw.com.evil.test/case',
    'https://user:password@www.pkulaw.com/pfnl/example.html',
    'https://www.pkulaw.com/pfnl/example.html?token=fixture-secret',
    'https://www.pkulaw.com/pfnl/example.html?access_token=hidden',
    'https://www.pkulaw.com/pfnl/example.html?way=fixture%2Dsecret',
    'https://www.pkulaw.com:8080/pfnl/example.html',
])
def test_credentials_and_nonpublic_urls_never_become_case_links(url):
    assert safe_pkulaw_url(url,'fixture-secret')==''


def test_per_answer_links_copy_and_export_exclude_unrelated_cases():
    report=answer('Case comparison [Q1-PKU-cases-1], plus Q1-PKU-cases-2.')
    sources=[source(),source('Q1-PKU-cases-2',''),source('Q1-PKU-cases-10')]
    tx=lambda x:translate(x,'English')
    text=report_copy_text(report,tx,sources)
    assert URL in text and 'PKULAW case links' in text
    assert 'PKULAW did not return a usable case link.' in text
    assert 'Q1-PKU-cases-10' not in text
    assert 'Full text may require a PKULAW account' in text
    _,settings,*_=load_demo()
    sections=report_sections(answer('Initial report without cases'),sources,[],settings,[('Find cases',report)])
    linked=[body for title,body in sections if title=='北大法宝案例链接 / PKULAW case links']
    assert len(linked)==1 and URL in linked[0]
    assert not pkulaw_case_links_text(answer('No case citations'),sources)


def test_case_link_visible_below_followup_and_missing_url_explicit():
    main,settings,intake,report,choices=load_demo()
    app=workspace_app(Path(__file__).resolve().parents[1]/'app.py')
    followup=answer('Compare Q1-PKU-cases-1 with Q1-PKU-cases-2.')
    for key,value in dict(main=main,settings=settings,intake=intake,report=report,choices=choices,
        supplements=[],messages=[],answers=[('Find cases',followup)],
        sources=[source(),source('Q1-PKU-cases-2','')]).items():
        app.session_state[key]=value
    app.run()
    assert not app.exception
    assert any(x.label=='在北大法宝打开案例' for x in app.get('link_button'))
    assert any('北大法宝未返回可用的案例链接' in x.value for x in app.caption)
    app.selectbox(key='ui_language').set_value('English').run()
    assert not app.exception
    assert any(x.label=='Open case on PKULAW' for x in app.get('link_button'))
    assert any('PKULAW did not return' in x.value for x in app.caption)
