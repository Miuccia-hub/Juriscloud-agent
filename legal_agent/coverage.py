"""Review topics and validation. Checklists guide examination, not statements of law."""
from dataclasses import dataclass
import re
from .models import CoverageCheck, Risk

@dataclass(frozen=True)
class Topic:
    id: str
    zh: str
    en: str
    terms: tuple[str,...]=()

BASE=[
 Topic('G01','当事人、权限与交易范围','Parties, authority and scope'),
 Topic('G02','期限、续期与生效条件','Term, renewal and commencement',('renew','term','期限','续期')),
 Topic('G03','价款、付款、发票与税费','Price, payment, invoices and taxes',('pay','invoice','tax','付款','税')),
 Topic('G04','履行标准、交付与验收','Performance, delivery and acceptance',('deliver','accept','验收','交付')),
 Topic('G05','违约、责任分配与赔偿','Breach, liability and indemnities',('liabil','indemn','违约','赔偿')),
 Topic('G06','终止、通知及终止后结算','Termination, notice and exit payments',('terminat','notice','终止','通知')),
 Topic('G07','知识产权、保密及数据处理','IP, confidentiality and data',('intellectual','confidential','data','知识产权','保密')),
 Topic('G08','适用法律、争议解决及地域联系','Governing law, disputes and territorial links',('governing','jurisdiction','法律','法院')),
 Topic('G09','定义、交叉引用与全文一致性','Definitions, cross-references and consistency'),
 Topic('G10','附件、外部文件与待确认事实','Attachments, external documents and unresolved facts',('schedule','policy','plan','附件','政策')),
]
PROFILES={
 'employment':('雇佣','Employment',r'employ|executive|劳动|雇佣|聘用|就业|雇用',[
  Topic('E01','岗位、工作地点及雇佣身份','Role, work location and employment status',('role','location','casual','岗位','工作地点')),
  Topic('E02','薪酬、奖金、股权与福利','Remuneration, bonuses, equity and benefits',('salary','bonus','equity','benefit','薪酬','福利')),
  Topic('E03','工时、加班与休息安排','Hours, overtime and breaks',('hours','overtime','工时','加班')),
  Topic('E04','年假及其他休假安排','Annual leave and other leave',('annual leave','vacation','paid time off','pto','年假','年休假','休假')),
  Topic('E05','试用、考核及职责变更','Probation, performance and changes to duties',('probation','duties','试用','职责')),
  Topic('E06','竞业、招揽限制与离职义务','Restraints, solicitation and post-employment duties',('restraint','compete','solicit','竞业','招揽')),
  Topic('E07','适用制度、政策与不可排除权利','Applicable instruments, policies and non-excludable rights',('award','enterprise agreement','statutory','法定','规章')),
 ]),
 'procurement':('采购','Procurement',r'procure|purchase|supply|sale of goods|采购|供货|买卖|销售',[
  Topic('P01','规格、数量及质量标准','Specifications, quantities and quality'),
  Topic('P02','交付、运输及风险转移','Delivery, transport and transfer of risk'),
  Topic('P03','验收、缺陷处理及保修','Acceptance, defects and warranty'),
  Topic('P04','付款节点、预付款与担保','Payment milestones, advances and security'),
  Topic('P05','变更、延期、退货及供应中断','Changes, delay, returns and supply interruption'),
 ]),
 'services':('咨询与服务','Consulting and services',r'consult|service|咨询|服务',[
  Topic('S01','服务边界、成果与验收','Scope, deliverables and acceptance'),
  Topic('S02','人员、分包及利益冲突','Personnel, subcontracting and conflicts'),
  Topic('S03','费用、工时及变更控制','Fees, time and change control'),
  Topic('S04','成果权利、依赖及责任限制','Deliverable rights, reliance and liability limits'),
 ]),
 'development':('技术开发','Development',r'develop|技术开发|研发|软件',[
  Topic('D01','技术需求、里程碑及测试','Requirements, milestones and testing'),
  Topic('D02','背景与新增知识产权归属','Background and newly developed IP'),
  Topic('D03','开源、第三方许可及侵权责任','Open-source, third-party licences and infringement'),
  Topic('D04','源代码、数据、维护及退出交接','Source code, data, maintenance and handover'),
 ]),
 'confidentiality':('保密','Confidentiality',r'non.disclosure|nda\b|confidentiality|保密',[
  Topic('N01','保密信息定义与例外','Confidential information and exclusions'),
  Topic('N02','允许用途、接收人及披露例外','Permitted use, recipients and disclosure exceptions'),
  Topic('N03','保密期限、返还及删除','Duration, return and deletion'),
  Topic('N04','知识产权保留及救济','IP reservation and remedies'),
 ]),
 'ip':('知识产权','Intellectual property',r'licen[cs]|intellectual property|知识产权|许可|授权|转让',[
  Topic('I01','权利范围、权属及授权链','Rights, title and chain of authority'),
  Topic('I02','地域、期限、独占及分许可','Territory, duration, exclusivity and sublicensing'),
  Topic('I03','费用、版税及审计','Fees, royalties and audit'),
  Topic('I04','改进成果、侵权及终止后使用','Improvements, infringement and post-termination use'),
 ]),
 'collaboration':('合作','Collaboration',r'collaborat|cooperat|joint venture|合作|合资',[
  Topic('C01','投入、职责及决策机制','Contributions, responsibilities and decisions'),
  Topic('C02','收益、费用及亏损分配','Revenue, expenses and loss allocation'),
  Topic('C03','成果归属、客户及利益冲突','Deliverables, customers and conflicts'),
  Topic('C04','退出、僵局及清算安排','Exit, deadlock and winding-up'),
 ]),
 'finance':('财税服务','Finance and tax services',r'account|financ|tax|财务|财税|税务|审计',[
  Topic('F01','服务边界、专业职责及申报授权','Scope, professional duties and filing authority'),
  Topic('F02','资料提供、准确性及期限','Information, accuracy and deadlines'),
  Topic('F03','费用、保密及记录保管','Fees, confidentiality and record keeping'),
  Topic('F04','责任边界、监管与后续处理','Liability boundaries, regulation and follow-up'),
 ]),
}


def checklist(contract_type):
    selected=[(key,value) for key,value in PROFILES.items() if re.search(value[2],contract_type,re.I)]
    topics=list(BASE)
    for _,profile in selected: topics.extend(profile[3])
    return topics,[key for key,_ in selected]


def topic_payload(topics,main,english=False):
    return [dict(id=t.id,topic=t.en if english else t.zh,
                 candidate_clauses=[dict(clause_id=c.id,text=c.text) for c in main.clauses
                    if any(term.casefold() in c.text.casefold() for term in t.terms)]) for t in topics]


def normalise_checks(items,topics,main,english=False):
    """No missing/duplicate result or fabricated quote may count as completed."""
    clauses={c.id:c.text for c in main.clauses}
    rows=[]
    for topic in topics:
        matches=[x for x in items if x.check_id==topic.id]
        if len(matches)!=1:
            rows.append(CoverageCheck(check_id=topic.id,status='资料不足',assessment=
                'No unique check result was returned.' if english else '未返回唯一的逐项检查结果，不能视为已完成。',
                quotes=[],concern=False,priority='中',next_step=
                'Manually check this topic against the full contract.' if english else '对照合同全文人工补查此项。'))
            continue
        row=matches[0].model_copy(deep=True)
        valid=[q for q in row.quotes if q.clause_id in clauses and q.quote.strip() and q.quote in clauses[q.clause_id]]
        bad=len(valid)!=len(row.quotes)
        row.quotes=valid
        if bad or (row.status in ('已分析','发现问题') and not valid):
            row.status='资料不足'
            row.assessment+=(' Evidence location/quotation could not be verified.' if english else ' 所引位置或原文未通过核对，保留待核实。')
        if not row.assessment.strip():
            row.status='资料不足'
            row.assessment='No rationale was returned.' if english else '未提供判断理由，不能视为已完成。'
        if row.status in ('发现问题','未找到明确约定'):row.concern=True
        if not row.next_step.strip() or row.next_step.strip().casefold() in {'审查','检查','建议修改','review','check','revise'}:
            row.next_step=(f'Check {topic.en} against the identified wording and obtain missing information before deciding on an amendment.' if english else
                f'针对“{topic.zh}”核对所引原文、补齐相关事实及附件，再确定需澄清或补充的具体安排。')
        rows.append(row)
    return rows


def attach_checks(report,checks,topics,main,scan_ids,links,english=False):
    risks_by_id={r.id:r for r in report.risks}
    checks_by_id={r.check_id:r for r in checks}
    mapped=set()
    for link in links:
        row=checks_by_id.get(link.check_id)
        if row is None:continue
        locations={q.clause_id for q in row.quotes}
        # An unsupported mapping to an unrelated risk cannot suppress an audit concern.
        if locations and any(r in risks_by_id and locations.intersection(risks_by_id[r].clause_ids) for r in link.risk_ids):
            mapped.add(link.check_id)
    catalog={t.id:t for t in topics}
    for row in checks:
        if row.concern and row.check_id not in mapped:
            topic=catalog[row.check_id]
            report.risks.append(Risk(id='AUDIT-'+row.check_id,title=topic.en if english else topic.zh,
                clause_ids=list(dict.fromkeys(q.clause_id for q in row.quotes)),category='待核实',severity=row.priority,
                action=row.next_step,explanation=row.assessment,impact=
                'A concern from the item-by-item check remains unresolved; this is not a finding of illegality.' if english else
                '逐项检查发现的事项仍待解决；此处不代表已经确认违法或无效。',source_ids=[],verification='待核实',missing_facts=[]))
    recorded=sum(c.id in scan_ids for c in main.clauses)
    report.coverage=[
        (f'{len(checks)} checklist records. These are model assessments, not independent verification.' if english else f'已形成 {len(checks)} 项清单记录；这些是模型判断，不等于独立核验。'),
        (f'The model recorded consideration of {recorded}/{len(main.clauses)} paragraphs.' if english else f'模型记录考虑过 {recorded}/{len(main.clauses)} 个段落。')]
    report._review_checks=[dict(check_id=r.check_id,topic=catalog[r.check_id].en if english else catalog[r.check_id].zh,**r.model_dump(exclude={'check_id'})) for r in checks]
    missing=[c.id for c in main.clauses if c.id not in scan_ids]
    if missing:report.limitations.append(('No recorded reading coverage for: ' if english else '未记录到阅读覆盖的段落：')+', '.join(missing))
    if any(r.status=='资料不足' for r in checks):report.limitations.append('Some checklist items remain unresolved.' if english else '部分检查项仍为资料不足，不能声称已全面完成。')
    return report
