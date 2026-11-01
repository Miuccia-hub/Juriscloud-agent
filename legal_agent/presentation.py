"""Output preference resolution does not mutate original documents or old answers."""
import re

def answer_language(preference, question, fallback="中文"):
    if preference in ("中文", "English", "中英双语"):
        return preference
    if question.strip():
        return "中文" if re.search(r"[\u3400-\u9fff]", question) else "English"
    return fallback


def automatic_settings(settings, intake):
    """An unresolved question is a limitation, never an affirmative confirmation."""
    from dataclasses import replace
    return replace(settings,contract_type=intake.contract_type,confirmations=
        "No factual confirmations were obtained. Missing documents, conflicting terms and questions "
        "remain unresolved. Analyse available text conditionally; never infer a yes, consent or waiver. "
        "The selected jurisdiction defines research scope, not a finding of governing law. "
        "Respond directly from the perspective in the user's question; otherwise remain neutral.")


def apply_intake_limits(report, intake):
    report.limitations=list(dict.fromkeys(report.limitations+intake.critical_questions+intake.conflicts+intake.local_gaps))
    return report


def report_table(report, tx=lambda v:v):
    """Accessible, escaped report table. The model cannot inject markup."""
    from html import escape
    e=lambda v:escape(str(v)).replace("\n","<br>")
    rows=[]
    for risk in report.risks:
        anchors=" / ".join(risk.clause_ids+risk.source_ids)
        rows.append('<tr><th scope="row">'+e(risk.title)+'<span class="risk-meta">'+e(tx(risk.severity))+" · "+e(tx(risk.category))+'</span></th><td>'+
            e(risk.explanation)+'<p><strong>'+e(tx("影响"))+': </strong>'+e(risk.impact)+'</p><p><strong>'+e(tx("建议"))+': </strong>'+e(risk.action)+
            '</p><span class="risk-meta">'+e(tx(risk.verification))+(" / "+e(anchors) if anchors else "")+'</span></td></tr>')
    return '<div class="review-table-wrap"><table class="review-table"><thead><tr><th>'+e(tx("问题"))+'</th><th>'+e(tx("风险分析与处理建议"))+'</th></tr></thead><tbody>'+''.join(rows)+'</tbody></table></div>'



def coverage_table(rows, tx=lambda v:v):
    """Render locally validated check records, without executing model markup."""
    from html import escape
    e=lambda v:escape(str(v)).replace('\n','<br>')
    body=[]
    for row in rows:
        quotes='<br>'.join(e(q['clause_id'])+': '+e(q['quote']) for q in row['quotes'])
        body.append('<tr><th scope="row">'+e(row['topic'])+'</th><td>'+e(tx(row['status']))+'</td><td>'+e(row['assessment'])+
            ('<p>'+quotes+'</p>' if quotes else '')+'</td><td>'+e(row['next_step'])+'</td></tr>')
    return '<div class="coverage-table-wrap"><table class="coverage-table"><thead><tr>'+''.join('<th>'+e(tx(x))+'</th>' for x in ('检查主题','检查状态','判断与原文','后续处理'))+'</tr></thead><tbody>'+''.join(body)+'</tbody></table></div>'


def cited_pkulaw_cases(report, sources):
    """Resolve only case IDs actually cited in this answer to retrieved records."""
    content = report.model_dump_json()
    seen = set()
    result = []
    for source in sources:
        if (source.id not in seen and re.search(r"(?:^|-)PKU-cases-\d+$", source.id)
                and re.search(r"(?<![\w-])" + re.escape(source.id) + r"(?![\w-])", content)):
            seen.add(source.id)
            result.append(source)
    return result


def pkulaw_case_links_text(report, sources, tx=lambda value:value):
    from .pkulaw import safe_pkulaw_url
    cases = cited_pkulaw_cases(report, sources)
    if not cases:
        return ""
    lines = [tx("北大法宝案例链接")]
    for source in cases:
        url = safe_pkulaw_url(source.url)
        lines.append(source.id + " · " + source.title + "\n" +
                     (url or tx("北大法宝未返回可用的案例链接。")))
    lines.append(tx("打开全文可能需要北大法宝账号或机构权限；链接不代表已核验全文。"))
    return "\n\n".join(lines)


def report_copy_text(report, tx=lambda value:value, sources=()):
    """Readable text for this answer only; no contract, credentials or internal trace."""
    parts=[report.summary]
    checks=getattr(report,"_review_checks",[])
    if checks:
        parts.append(tx("完整检查清单"))
        parts.append(tx("逐项检查记录不等于独立法律合规保证；未找到明确约定也不等于不存在法定权利。"))
        for row in checks:
            parts.append(" · ".join([row["check_id"],row["topic"],tx(row["status"])]))
            parts.append(row["assessment"])
            parts.extend(q["clause_id"]+": "+q["quote"] for q in row["quotes"])
            parts.append(tx("后续处理")+": "+row["next_step"])
    for risk in report.risks:
        parts.append(risk.title+" ("+tx(risk.severity)+" · "+tx(risk.category)+")")
        parts.append(risk.explanation)
        parts.append(tx("影响")+": "+risk.impact)
        parts.append(tx("建议")+": "+risk.action)
        parts.append(" / ".join([tx(risk.verification),*risk.clause_ids,*risk.source_ids]))
    parts.append(pkulaw_case_links_text(report, sources, tx))
    for label,items in [("覆盖",report.coverage),("假设",report.assumptions),("下一步",report.next_steps),("局限",report.limitations)]:
        if items:
            parts.append(tx(label))
            parts.extend("• "+item for item in dict.fromkeys(items))
    return "\n\n".join(part for part in parts if part.strip())
