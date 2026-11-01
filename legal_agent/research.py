"""Bounded public-source discovery and retrieval. Never fetch model-invented URLs."""
from __future__ import annotations

from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor
from io import BytesIO
from urllib.parse import urlsplit
import ipaddress
import socket
import re
import httpx
from bs4 import BeautifulSoup
from pypdf import PdfReader
from .models import Source, Material

DOMAINS = {
    "维多利亚州": ["legislation.vic.gov.au", "legislation.gov.au", "hcourt.gov.au", "fedcourt.gov.au", "supremecourt.vic.gov.au", "austlii.edu.au", "accc.gov.au", "ato.gov.au", "ipaustralia.gov.au"],
    "中国大陆": ["npc.gov.cn", "gov.cn", "court.gov.cn", "chinatax.gov.cn", "cnipa.gov.cn", "samr.gov.cn"],
}


def allowed_url(url: str, domains: list[str]) -> bool:
    try:
        p = urlsplit(url)
        host = (p.hostname or "").lower().rstrip(".")
        return (p.scheme == "https" and not p.username and not p.password and p.port in (None, 443)
                and any(host == d or host.endswith("." + d) for d in domains))
    except ValueError:
        return False


def safe_fetch(url: str, domains: list[str]) -> tuple[str, str]:
    """No cookies; restricted HTTPS hosts; redirects revalidated; size/time bounded."""
    with httpx.Client(timeout=12, follow_redirects=False, trust_env=False) as client:
        for _ in range(4):
            if not allowed_url(url, domains):
                raise ValueError("来源不在公开法律站点白名单。")
            host = urlsplit(url).hostname
            addresses = socket.getaddrinfo(host, 443, type=socket.SOCK_STREAM)
            if any(not ipaddress.ip_address(a[4][0]).is_global for a in addresses):
                raise ValueError("来源解析为非公网地址。")
            with client.stream("GET", url, headers={"User-Agent": "JuriscloudResearch/0.1 (educational; low-volume)"}) as response:
                if response.status_code in (301, 302, 303, 307, 308):
                    url = str(response.url.join(response.headers.get("location", "")))
                    continue
                response.raise_for_status()
                raw = bytearray()
                for chunk in response.iter_bytes():
                    raw.extend(chunk)
                    if len(raw) > 3_000_000:
                        raise ValueError("来源正文超过 3 MB 上限。")
                content_type = response.headers.get("content-type", "")
                if "pdf" in content_type or raw[:4] == b"%PDF":
                    reader = PdfReader(BytesIO(raw))
                    text = "\n".join(f"[PDF page {i+1}] {p.extract_text() or ''}" for i,p in enumerate(reader.pages))
                else:
                    soup = BeautifulSoup(bytes(raw), "html.parser")
                    for el in soup(["script", "style", "nav", "header", "footer"]):
                        el.decompose()
                    text = soup.get_text("\n", strip=True)
                if len(text.strip()) < 100:
                    raise ValueError("无法取得足够正文，可能需要登录或脚本加载。")
                return text, url
    raise ValueError("来源重定向次数过多。")


def relevant_excerpt(text: str, queries: list[str], limit=18000) -> tuple[str, bool]:
    if len(text) <= limit:
        return text, False
    tokens = set(re.findall(r"[a-zA-Z]{4,}|[\u4e00-\u9fff]{2,4}", " ".join(queries).lower()))
    windows = [(i, text[i:i+2400]) for i in range(0, len(text), 2100)]
    ranked = sorted(windows, key=lambda pair: sum(t in pair[1].lower() for t in tokens), reverse=True)
    selected = sorted(ranked[:6], key=lambda pair: pair[0])
    return "\n".join(f"[正文字符位置 {i}]\n{body}" for i,body in selected), True


def retrieve(discovered: list[dict], jurisdiction: str, queries: list[str], fetcher=safe_fetch, max_workers=3):
    notes, seen, selected = [], set(), []
    for item in discovered:
        url = item.get("url", "")
        if url in seen or not allowed_url(url, DOMAINS[jurisdiction]):
            continue
        seen.add(url)
        if len(selected) >= 5:
            notes.append("本轮最多读取五个公开来源；非穷尽检索。")
            break
        selected.append(item)

    def read_source(index_item):
        index, item = index_item
        url = item["url"]
        try:
            text, final_url = fetcher(url, DOMAINS[jurisdiction])
            excerpt, partial = relevant_excerpt(text, queries)
            return Source(f"S{index+1}", item.get("title") or final_url, final_url, excerpt,
                                  "正文片段已取得" if partial else "正文已取得",
                                  datetime.now(timezone.utc).isoformat(), warning=("长文已选取相关片段，未将全文提供给模型；" if partial else "") + "法律时效、适用性与后续处理仍须复核")
        except Exception as exc:
            # Avoid logging server bodies or user credentials.
            return Source(f"S{index+1}", item.get("title") or url, url, "", "正文未取得",
                                  datetime.now(timezone.utc).isoformat(), warning=f"{type(exc).__name__}：不能作为已核验依据")

    # Preserve discovery order/IDs even when reads complete out of order. Each
    # safe_fetch owns its client; URL/DNS/redirect/size checks stay unchanged.
    workers=max(1,min(3,int(max_workers)))
    if workers == 1 or len(selected) < 2:
        sources=[read_source(item) for item in enumerate(selected)]
    else:
        with ThreadPoolExecutor(max_workers=workers) as pool:
            sources=list(pool.map(read_source,enumerate(selected)))
    if not sources:
        notes.append("本轮没有取得公开来源正文，相关法律结论必须保留待核实。")
    return sources, notes


def supplemental_sources(materials: list[Material]):
    return [Source(f"U-{m.id}", m.name, "", m.text, "用户提供，未经独立核验",
                   datetime.now(timezone.utc).isoformat(), "用户法律资料")
            for m in materials if m.role == "法律研究材料"]


def normalise(s):
    return re.sub(r"\s+", "", s).casefold()


def quote_exists(quote: str, source: Source) -> bool:
    return len(normalise(quote)) >= 12 and normalise(quote) in normalise(source.text)
