"""Bounded official PKULAW MCP client. Credentials never enter model payloads."""
from __future__ import annotations

import asyncio
import json
from datetime import datetime, timezone, timedelta
from urllib.parse import urlsplit, parse_qsl, unquote

import httpx
from jsonschema import validate
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client
from .models import Source

SERVICES = {
    "cases": ("https://apim-gateway.pkulaw.com/mcp-case-search-service", "search_case"),
    "legislation": ("https://apim-gateway.pkulaw.com/mcp-law-search-service", "search_article"),
}


class PkulawError(Exception):
    """Safe, fixed error codes only; never expose provider response bodies."""


def safe_pkulaw_url(value, token=""):
    """Keep vendor-supplied public links, never authentication or invented URLs."""
    if not isinstance(value, str) or not value.strip():
        return ""
    value = value.strip()
    try:
        p = urlsplit(value)
        host = (p.hostname or "").lower()
        if (any(c.isspace() or ord(c) < 32 for c in value)
                or p.scheme != "https" or p.username or p.password
                or p.port not in (None, 443)
                or not (host == "pkulaw.com" or host.endswith(".pkulaw.com"))
                or (token and token in unquote(value))):
            return ""
        # Retain only ordinary reading/navigation parameters, never signed access links.
        if p.fragment or any(k.casefold() not in {"way", "type", "from", "source", "search_mode"}
                             for k, _ in parse_qsl(p.query, keep_blank_values=True)):
            return ""
        return value
    except (ValueError, TypeError):
        return ""


def result_url(item, token):
    fields = {str(k).casefold(): v for k, v in item.items()}
    for name in ("url", "link", "caseurl", "detailurl", "href", "lawurl"):
        url = safe_pkulaw_url(fields.get(name), token)
        if url:
            return url
    return ""


def error_code(exc):
    children = getattr(exc, "exceptions", ())
    if children:
        codes = [error_code(child) for child in children]
        return next((c for c in codes if c != "connection"), "connection")
    if isinstance(exc, PkulawError):
        return str(exc)
    if isinstance(exc, httpx.HTTPStatusError):
        return {401: "authentication", 403: "permission", 402: "credits", 429: "rate_limit"}.get(exc.response.status_code, "service")
    if isinstance(exc, (TimeoutError, httpx.TimeoutException)):
        return "timeout"
    return "connection"


def sources_from_result(result, kind, token):
    if result.isError:
        raise PkulawError("tool_error")
    payload = result.structuredContent
    if payload is None:
        texts = [block.text for block in result.content if block.type == "text"]
        if not texts:
            raise PkulawError("empty_result")
        try:
            payload = json.loads("\n".join(texts))
        except ValueError:
            # Unrecognised prose may be an error, not a legal source.
            raise PkulawError("unexpected_result") from None
    if isinstance(payload, dict):
        if payload.get("isError") or payload.get("success") is False:
            raise PkulawError("tool_error")
        payload = payload.get("Data", payload.get("data", payload.get("results", payload)))
    if isinstance(payload, dict):
        payload = payload.get("items", payload.get("list", [payload]))
    if not isinstance(payload, list):
        raise PkulawError("unexpected_result")
    sources = []
    for item in payload[:3]:
        if not isinstance(item, dict):
            continue
        title = item.get("title") or item.get("Title")
        if not isinstance(title, str) or not title.strip():
            continue
        body = json.dumps(item, ensure_ascii=False).replace(token, "[REDACTED]")
        url = result_url(item, token)
        sources.append(Source(f"PKU-{kind}-{len(sources)+1}", title.replace(token, "[REDACTED]"), url,
            body[:18000], "MCP检索片段已取得", datetime.now(timezone.utc).isoformat(),
            "北大法宝 MCP", "检索返回片段，未独立核验完整正文、时效、后续裁判或适用性。"))
    if payload and not sources:
        raise PkulawError("unexpected_result")
    return sources


class PkulawClient:
    def __init__(self, token, transport=None):
        self._token = token.strip().removeprefix("Bearer ").strip()
        self._transport = transport

    async def _exchange(self, kind, query=None):
        if not self._token or any(c in self._token for c in "\r\n"):
            raise PkulawError("authentication")
        url, tool = SERVICES[kind]
        # Fixed vendor URLs only, no redirects, retries, cookies or subprocesses.
        async with httpx.AsyncClient(headers={"Authorization": "Bearer " + self._token},
                timeout=httpx.Timeout(60, connect=15), follow_redirects=False,
                trust_env=False, transport=self._transport) as client:
            async with streamable_http_client(url, http_client=client) as (read, write, _):
                async with ClientSession(read, write, read_timeout_seconds=timedelta(seconds=60)) as session:
                    await session.initialize()
                    tools = await session.list_tools()
                    selected = next((t for t in tools.tools if t.name == tool), None)
                    if selected is None:
                        raise PkulawError("missing_tool")
                    if query is None:
                        return []  # tools/list only, not a paid research call.
                    arguments = {"text": query[:1200], "size": 3}
                    validate(arguments, selected.inputSchema)
                    result = await session.call_tool(tool, arguments)
                    return sources_from_result(result, kind, self._token)

    async def _bounded(self, kind, query=None):
        try:
            return await asyncio.wait_for(self._exchange(kind, query), timeout=75)
        except Exception as exc:
            raise PkulawError(error_code(exc)) from None

    def check_connection(self):
        async def check():
            # Check each entitlement independently, without calling search tools.
            results = await asyncio.gather(*(self._bounded(k) for k in SERVICES), return_exceptions=True)
            return {k: error_code(r) if isinstance(r, Exception) else "ok" for k, r in zip(SERVICES, results)}
        return asyncio.run(check())

    def research(self, queries):
        query = "；".join(q.strip() for q in queries[:2] if isinstance(q, str) and q.strip())[:1200]
        if not query:
            return [], ["北大法宝 MCP：没有研究问题，未调用。"]
        async def run():
            return await asyncio.gather(*(self._bounded(k, query) for k in SERVICES), return_exceptions=True)
        sources, notes = [], []
        for kind, result in zip(SERVICES, asyncio.run(run())):
            if isinstance(result, Exception):
                notes.append(f"北大法宝 MCP {kind}: {error_code(result)}；未取得可用依据，无自动重试。")
            else:
                sources.extend(result)
                notes.append(f"北大法宝 MCP {kind}: 返回 {len(result)} 条检索片段；非穷尽检索。")
        return sources, notes
