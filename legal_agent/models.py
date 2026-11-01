from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, PrivateAttr


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ConnectionCheck(StrictModel):
    ok: bool


class Intake(StrictModel):
    contract_type: str
    parties: list[str]
    governing_law: str
    summary: str
    key_dates: list[str]
    jurisdiction_mismatch: bool
    critical_questions: list[str]
    local_gaps: list[str]
    conflicts: list[str]


class Plan(StrictModel):
    scope: list[str]
    issues: list[str]
    public_search_queries: list[str] = Field(description="At most 4 generic legal queries; NO party names or contract secrets")
    missing_information: list[str]


class Finding(StrictModel):
    source_id: str
    proposition: str
    exact_quote: str
    pinpoint: str
    applicability: str
    currency_limit: str


class Evidence(StrictModel):
    findings: list[Finding]
    limitations: list[str]


class Risk(StrictModel):
    id: str
    title: str
    clause_ids: list[str]
    category: Literal["法律效力", "完整一致", "商业风险", "待核实"]
    severity: Literal["高", "中", "低"]
    action: str
    explanation: str
    impact: str
    source_ids: list[str]
    verification: Literal["有原文支持，适用性仍需复核", "待核实", "文本或商业判断"]
    missing_facts: list[str]


class ProposedEdit(StrictModel):
    id: str
    risk_id: str
    clause_id: str
    original: str = Field(description="Exact contiguous original text from this clause, non-empty; never paraphrase")
    replacement: str
    reason: str
    source_ids: list[str]
    bilingual_note: str


class Report(StrictModel):
    _review_checks: list[dict] = PrivateAttr(default_factory=list)
    summary: str
    coverage: list[str]
    assumptions: list[str]
    risks: list[Risk]
    suggestions: list[ProposedEdit]
    next_steps: list[str]
    limitations: list[str]


class FollowupAnswer(StrictModel):
    answered_question: str = Field(description="Copy the current user question exactly; never the initial review request")
    direct_answer: str = Field(description="Answer this question first, not a summary of the entire contract")
    contract_analysis: str = Field(description="Relevant contract wording, omissions and cross-references only, using clause IDs")
    legal_analysis: str = Field(description="Relevant supported legal analysis with source IDs; disclose unavailable support")
    next_steps: list[str]
    limitations: list[str]
    suggestions: list[ProposedEdit]


class Critique(StrictModel):
    defects: list[str]
    unsupported_risk_ids: list[str]
    conflicting_edit_ids: list[str]
    corrections: list[str]


@dataclass
class Clause:
    id: str
    text: str
    location: str
    paragraph_index: int | None = None


@dataclass
class Material:
    id: str
    name: str
    role: str
    clauses: list[Clause]
    data: bytes = b""
    kind: str = "text"
    warnings: list[str] = field(default_factory=list)

    @property
    def text(self):
        return "\n".join(f"[{c.id}] {c.text}" for c in self.clauses)


@dataclass
class Source:
    id: str
    title: str
    url: str
    text: str
    status: str
    retrieved_at: str
    kind: str = "公开来源"
    warning: str = "未完成法律时效及后续处理核验"


@dataclass
class Settings:
    jurisdiction: str
    language: str
    stance: str
    mode: str
    focus: str
    contract_type: str
    confirmations: str = ""


@dataclass
class Call:
    stage: str
    kind: str
    success: bool
    seconds: float
    tokens: int = 0


@dataclass
class EditChoice:
    edit: ProposedEdit
    state: str = "未决定"
    replacement: str = ""
    origin: str = "首次审查"
    needs_reconfirmation: bool = False


class CoverageQuote(StrictModel):
    clause_id: str
    quote: str


class CoverageCheck(StrictModel):
    check_id: str
    status: Literal["已分析","发现问题","未找到明确约定","资料不足","不适用"]
    assessment: str
    quotes: list[CoverageQuote]
    concern: bool
    priority: Literal["高","中","低"]
    next_step: str


class ReviewBatch(StrictModel):
    checks: list[CoverageCheck]
    reviewed_clause_ids: list[str]


class OmissionAudit(StrictModel):
    corrected_checks: list[CoverageCheck]
    missed_issues: list[str]
    limitations: list[str]


class CheckLink(StrictModel):
    check_id: str
    risk_ids: list[str]


class ReviewSynthesis(Report):
    check_links: list[CheckLink]
