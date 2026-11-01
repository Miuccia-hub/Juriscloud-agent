"""Exercise real SDK handshakes against a fake HTTP transport; no paid calls."""
import json
from types import SimpleNamespace
import httpx
import pytest
from legal_agent.pkulaw import PkulawClient, PkulawError, sources_from_result, SERVICES
from legal_agent.workflow import Workflow, requests_case_research
from legal_agent.models import Source
from tests.fixture_data import load_demo

SECRET = "test-only-secret-do-not-export"


def transport_for(seen, status=200, tool_error=False):
    def handle(request):
        assert request.url.host == "apim-gateway.pkulaw.com"
        assert request.headers["authorization"] == "Bearer " + SECRET
        if request.method == "POST":
            seen.append((request.url.path, json.loads(request.content)))
        if status != 200:
            return httpx.Response(status, text="unsafe provider body " + SECRET)
        if request.method != "POST":
            return httpx.Response(405)
        data = json.loads(request.content)
        method = data["method"]
        if method == "notifications/initialized":
            return httpx.Response(202)
        if method == "initialize":
            result = {"protocolVersion": data["params"]["protocolVersion"], "capabilities": {"tools": {}},
                      "serverInfo": {"name": "fictional-pku", "version": "1"}}
        elif method == "tools/list":
            tool = "search_case" if "case" in request.url.path else "search_article"
            result = {"tools": [{"name": tool, "inputSchema": {"type": "object", "properties": {
                "text": {"type": "string"}, "size": {"type": "integer", "maximum": 3}}, "required": ["text"]}}]}
        else:
            assert method == "tools/call"
            assert data["params"]["arguments"] == {"text": "违约金；采购合同", "size": 3}
            rows = [{"title": "虚构测试案例", "url": "https://www.pkulaw.com/pfnl/test.html",
                     "reason": "仅测试传输与来源标记，不是真实法律结论"}]
            result = {"isError": tool_error, "content": [{"type": "text", "text": json.dumps(rows)}]}
        return httpx.Response(200, json={"jsonrpc": "2.0", "id": data["id"], "result": result})
    return httpx.MockTransport(handle)


def test_connection_uses_sdk_initialize_and_tools_list_without_search_or_model():
    seen = []
    client = PkulawClient(SECRET, transport_for(seen))
    assert client.check_connection() == {"cases": "ok", "legislation": "ok"}
    assert sorted(x[1]["method"] for x in seen) == sorted(["initialize", "notifications/initialized", "tools/list"] * 2)
    assert SECRET not in json.dumps(seen)


def test_bounded_research_and_source_status_with_actual_sdk():
    seen = []
    client = PkulawClient(SECRET, transport_for(seen))
    sources, notes = client.research(["违约金", "采购合同", "不应发送的第三项"])
    assert len(sources) == 2
    assert {s.id for s in sources} == {"PKU-cases-1", "PKU-legislation-1"}
    assert all(s.status == "MCP检索片段已取得" and "未独立核验" in s.warning for s in sources)
    calls = [data for _, data in seen if data["method"] == "tools/call"]
    assert len(calls) == 2
    assert SECRET not in repr(sources) + repr(notes) + json.dumps(seen)


@pytest.mark.parametrize("status,code", [(401,"authentication"), (403,"permission"), (402,"credits"), (429,"rate_limit")])
def test_errors_do_not_expose_credentials_and_do_not_retry(status, code):
    seen = []
    client = PkulawClient(SECRET, transport_for(seen, status))
    assert set(client.check_connection().values()) == {code}
    assert len(seen) == 2  # one initialise attempt per service, no retry
    sources, notes = client.research(["违约金", "采购合同"])
    assert not sources
    assert len(seen) == 4
    assert all(code in n and SECRET not in n and "unsafe" not in n for n in notes)


def test_tool_error_is_not_promoted_to_evidence():
    sources, notes = PkulawClient(SECRET, transport_for([], tool_error=True)).research(["违约金", "采购合同"])
    assert not sources and all("tool_error" in n for n in notes)


def test_secret_redaction_and_source_link_boundary():
    result = SimpleNamespace(isError=False, structuredContent={"Data": [{"Title": "示例", "reason": SECRET,
        "url": "https://pkulaw.com.evil.test/private"}]}, content=[])
    source = sources_from_result(result, "cases", SECRET)[0]
    assert not source.url and SECRET not in source.text
    result.structuredContent = {"Message": "authentication failed " + SECRET}
    with pytest.raises(PkulawError, match="unexpected_result"):
        sources_from_result(result, "cases", SECRET)


def test_workflow_routes_only_mainland_and_keeps_token_out_of_settings(monkeypatch):
    _, settings, *_ = load_demo()
    settings.jurisdiction = "维多利亚州"
    called = []
    monkeypatch.setattr(PkulawClient, "research", lambda self, queries: (called.append(queries) or [], ["test marker"]))
    gateway = SimpleNamespace(search=lambda *args: [])
    workflow = Workflow(gateway, pkulaw_token=SECRET)
    plan = SimpleNamespace(public_search_queries=["违约金"])
    workflow.research(plan, settings, [], "R")
    assert not called  # Victoria fixture
    settings.jurisdiction = "中国大陆"
    _, notes = workflow.research(plan, settings, [], "R")
    assert called == [["违约金"]] and "test marker" in notes
    assert SECRET not in repr(settings)


@pytest.mark.parametrize("question,expected", [
    ("请帮我检索关于竞业限制的案例", True),
    ("查找相关判例", True),
    ("Find relevant case law", True),
    ("请全面审查这份合同", False),
    ("不要检索案例，只审查条款", False),
])
def test_explicit_case_research_request(question, expected):
    assert requests_case_research(question) is expected


def test_explicit_case_request_searches_pkulaw_first_then_public_judgment(monkeypatch):
    _, settings, *_ = load_demo()
    settings.jurisdiction = "中国大陆"
    settings.focus = "请帮我检索关于竞业限制的案例"
    events = []
    snippet = Source("PKU-cases-1", "法宝检索结果", "https://pkulaw.com/pfnl/example.html",
                     "检索片段", "MCP检索片段已取得", "2026-01-01", "北大法宝 MCP")
    monkeypatch.setattr(PkulawClient, "research", lambda self, queries:
                        (events.append("pkulaw") or [snippet], ["法宝返回片段"]))

    def public_search(queries, jurisdiction, case_focus=False):
        events.append(("public", case_focus))
        return [{"title": "公开裁判文书", "url": "https://www.court.gov.cn/judgment/example"}]

    workflow = Workflow(SimpleNamespace(search=public_search), pkulaw_token=SECRET,
                        fetcher=lambda url, domains: ("可核对的公开裁判正文。" * 10, url))
    sources, notes = workflow.research(SimpleNamespace(public_search_queries=["竞业限制 判例"]), settings, [], "Q1-")
    assert events == ["pkulaw", ("public", True)]
    assert {s.id for s in sources} == {"Q1-PKU-cases-1", "Q1-S1"}
    assert any("继续检索公开裁判来源" in note for note in notes)
    assert SECRET not in repr(sources) + repr(notes)


def test_verified_full_pku_case_avoids_public_fallback(monkeypatch):
    _, settings, *_ = load_demo()
    settings.jurisdiction = "中国大陆"
    settings.focus = "查找相关判例"
    full = Source("PKU-cases-1", "已核验裁判", "https://pkulaw.com/pfnl/example.html",
                  "完整裁判文书", "完整裁判文书已核验", "2026-01-01", "北大法宝 MCP")
    monkeypatch.setattr(PkulawClient, "research", lambda self, queries: ([full], []))
    workflow = Workflow(SimpleNamespace(search=lambda *args, **kwargs: pytest.fail("Unexpected public fallback")),
                        pkulaw_token=SECRET)
    sources, notes = workflow.research(SimpleNamespace(public_search_queries=["相关法律问题"]), settings, [], "R")
    assert [s.id for s in sources] == ["RPKU-cases-1"]
    assert not notes


@pytest.mark.parametrize("jurisdiction,token", [("中国大陆", ""), ("维多利亚州", SECRET)])
def test_case_request_without_mainland_pku_still_targets_public_cases(monkeypatch, jurisdiction, token):
    _, settings, *_ = load_demo()
    settings.jurisdiction = jurisdiction
    settings.focus = "Find relevant case law"
    monkeypatch.setattr(PkulawClient, "research", lambda self, queries: pytest.fail("Unexpected PKULAW call"))
    seen = []

    def public_search(queries, region, case_focus=False):
        seen.append((region, case_focus))
        return []

    workflow = Workflow(SimpleNamespace(search=public_search), pkulaw_token=token)
    _, notes = workflow.research(SimpleNamespace(public_search_queries=["restrictive covenants"]), settings, [], "R")
    assert seen == [(jurisdiction, True)]
    assert any("未取得可核对的裁判正文" in note for note in notes)
