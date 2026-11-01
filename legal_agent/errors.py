"""Actionable, bilingual failures without dumping provider payloads or credentials."""
from dataclasses import dataclass
import socket
import ssl
from pydantic import ValidationError

@dataclass
class RunFailure(Exception):
    code: str
    stage: str = ""
    request_id: str = ""

MESSAGES = {
    "export_failed": ("报告文件生成失败，已有审查结果仍保留。请重试导出。", "Report generation failed. Your review is preserved; retry the export."),
    "followup_mismatch": ("本轮回答没有对应当前追问，已阻止显示。问题与材料仍保留，请重试本轮追问。", "This answer did not match the current follow-up and was not displayed. Your question and materials are preserved; retry this question."),
    "incomplete_tokens": ("模型输出达到长度上限，本步骤没有完成。请缩小本次材料或重点范围后重试。", "The model reached its output limit. Narrow the materials or review scope and retry."),
    "refusal": ("模型未处理本次请求，没有生成可用结果。请调整问题后重试。", "The model declined this request. Adjust the question and retry."),
    "incomplete": ("模型响应未完成，本步骤没有可用结果。请稍后重试。", "The model response did not complete. Retry this step later."),
    "invalid_output": ("模型返回的数据不符合审查格式。请重试；若持续发生，请确认分析模型支持结构化输出。", "The model returned invalid review data. Retry; if it persists, confirm that the analysis model supports structured outputs."),
    "empty_output": ("模型完成响应，但没有返回可用的分析正文。请重试或检查所选模型。", "The model completed without usable analysis. Retry or check the selected model."),
    "authentication": ("接口密钥未通过验证。请重新填写有效密钥。", "The API key was not accepted. Enter a valid key."),
    "quota": ("接口账户额度不足。请检查该账户的账单与可用额度。", "The API account has insufficient quota. Check billing and available credit."),
    "rate_limit": ("接口请求过于频繁。请稍后再试。", "The API rate limit was reached. Retry later."),
    "model_access": ("所选模型不存在或当前账户无权使用。请检查分析模型名称与账户权限。", "The selected model is unavailable or inaccessible to this account. Check its name and account access."),
    "request": ("接口拒绝了请求参数。请检查模型是否支持结构化输出；检索模型还需支持联网搜索。", "The API rejected the request parameters. Check model support for structured outputs and web search."),
    "connection_timeout": ("模型请求超时，尚未取得本步骤结果。这不等于密钥错误；可稍后重试，或缩小材料与问题范围。", "The model request timed out before this step completed. This does not establish an invalid key. Retry later or narrow the materials and question."),
    "connection_connect_timeout": ("建立模型服务连接超时，尚不能判断模型是否可用。请检查网络或代理后重试。", "Connecting to the model service timed out. Model availability has not been established. Check the network or proxy and retry."),
    "connection_read_timeout": ("等待模型服务响应超时。可能是生成耗时、网络或代理中断；不能据此认定密钥或模型权限有误。", "Waiting for the model service response timed out. Generation latency, network issues or a proxy interruption may be responsible; this does not establish a key or model-access error."),
    "connection_write_timeout": ("向模型服务发送请求超时。请检查网络或代理后重试；本步骤尚未完成。", "Sending the request to the model service timed out. Check the network or proxy and retry; this step has not completed."),
    "connection_pool_timeout": ("等待可用网络连接超时。请稍后重试；本步骤尚未完成。", "Waiting for an available network connection timed out. Retry later; this step has not completed."),
    "connection_tls": ("连接模型服务时证书校验失败。请检查本机证书及网络代理配置，保留证书校验。", "Certificate verification failed when connecting to the model service. Check local certificates and proxy configuration; keep certificate verification enabled."),
    "connection_dns": ("无法解析模型服务域名。请检查当前网络及 DNS 配置。", "The model service hostname could not be resolved. Check the network and DNS configuration."),
    "connection": ("无法连接模型服务。请检查网络后重试。", "The model service could not be reached. Check the connection and retry."),
    "service": ("模型服务暂时不可用。请稍后重试。", "The model service is temporarily unavailable. Retry later."),
    "input": ("材料未通过检查，请根据下方原因调整文件后重试。", "The materials failed validation. Resolve the issue below and retry."),
    "unknown": ("本步骤未完成。请查看下方失败阶段和错误类型以定位问题。", "This step did not complete. Check the stage and error type below."),
}

def connection_code(exc):
    """Inspect exception types only, never expose exception text, URLs or payloads."""
    current=exc
    seen=set()
    timeout=False
    phase=""
    for _ in range(10):
        if not isinstance(current,BaseException) or id(current) in seen: break
        seen.add(id(current))
        if isinstance(current,ssl.SSLCertVerificationError): return "connection_tls"
        if isinstance(current,socket.gaierror): return "connection_dns"
        if not phase:
            phase={"ConnectTimeout":"connect", "ReadTimeout":"read",
                   "WriteTimeout":"write", "PoolTimeout":"pool"}.get(type(current).__name__,"")
        if isinstance(current,TimeoutError) or type(current).__name__ in {
            "APITimeoutError","ConnectTimeout","ReadTimeout","WriteTimeout","PoolTimeout"}:
            timeout=True
        current=current.__cause__ or current.__context__
    if phase: return "connection_"+phase+"_timeout"
    return "connection_timeout" if timeout else "connection"


def classify(exc, stage=""):
    if isinstance(exc,RunFailure): return exc
    if isinstance(exc,ValidationError): code="invalid_output"
    else:
        status=getattr(exc,"status_code",None)
        body=getattr(exc,"body",None)
        error=body.get("error",body) if isinstance(body,dict) else {}
        api_code=error.get("code") if isinstance(error,dict) else None
        name=type(exc).__name__
        if status==401: code="authentication"
        elif api_code=="insufficient_quota": code="quota"
        elif status==429: code="rate_limit"
        elif status in (403,404) or api_code=="model_not_found": code="model_access"
        elif status==400: code="request"
        elif status and status>=500: code="service"
        elif name in ("APIConnectionError","APITimeoutError","TimeoutError","ConnectError",
                      "ReadTimeout","WriteTimeout","ConnectTimeout","PoolTimeout") or isinstance(exc,(socket.gaierror,ssl.SSLCertVerificationError)):
            code=connection_code(exc)
        elif type(exc) is ValueError: code="input"
        else: code="unknown"
    request_id=getattr(exc,"request_id","") or ""
    # Only a provider-shaped reference, never arbitrary exception text.
    import re
    if not re.fullmatch(r"req_[A-Za-z0-9_-]{1,100}",request_id): request_id=""
    return RunFailure(code,stage,request_id)


def message(failure, language):
    return MESSAGES.get(failure.code,MESSAGES["unknown"])[language=="English"]
