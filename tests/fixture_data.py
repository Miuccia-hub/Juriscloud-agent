"""Explicit static interface demonstration, not AI output or a legal opinion."""
from legal_agent.models import Intake, Report, Risk, ProposedEdit, EditChoice, Settings
from legal_agent.documents import extract
from pathlib import Path


def load_demo():
    path = Path(__file__).resolve().parent.parent / "examples" / "T01_采购合同.txt"
    main = extract(path.name,path.read_bytes())
    settings = Settings("中国大陆","中文","甲方 / 买方","全面审查","","采购合同")
    intake = Intake(contract_type="采购合同",parties=["甲方：云杉科技有限公司","乙方：晨光设备有限公司"],
                    governing_law="中国大陆",summary="20 套设备采购；全部预付款。虚构界面样例。",key_dates=["2026-11-20"],
                    jurisdiction_mismatch=False,critical_questions=[],local_gaps=["型号及验收标准未确定"],conflicts=[])
    clause = next(c for c in main.clauses if "及时验收" in c.text)
    risks = [Risk(id="DEMO-R1",title="验收期限和起算条件不明确",clause_ids=[clause.id],category="完整一致",severity="中",
                  action="建议修改",explanation="“及时”“逾期”缺少具体期限及判断标准。",impact="双方可能对验收是否完成产生分歧。",
                  source_ids=[],verification="文本或商业判断",missing_facts=["需要双方确定验收天数与标准"]),
             Risk(id="DEMO-R2",title="全部预付款带来履约敞口",clause_ids=["D1-P5"],category="商业风险",severity="高",
                  action="优先协商",explanation="示例：付款全部发生于交付之前。此处仅展示商业风险标签，不判断违法。",
                  impact="买方在交付前支付全部款项。",source_ids=[],verification="文本或商业判断",missing_facts=[])]
    edit = ProposedEdit(id="DEMO-E1",risk_id="DEMO-R1",clause_id=clause.id,original="及时验收",
                        replacement="在收到全部设备及约定验收资料后十个工作日内，按双方书面确认的标准完成验收",
                        reason="示例修改：明确期限及条件；具体天数须协商，并补充缺陷处理机制。",source_ids=[],bilingual_note="")
    report = Report(summary="这是静态界面示例：帮助你体验原文定位、风险筛选和修订导出。未调用 AI，也未检索法律。",
                    coverage=["仅演示验收和付款两个问题；不是完整合同审查"],assumptions=["全部内容虚构"],risks=risks,suggestions=[edit],
                    next_steps=["上传你自己的材料并输入 API key，才能运行真实分析。"],limitations=["静态示例，不构成 AI 审查结果或法律意见。"])
    return main,settings,intake,report,[EditChoice(edit,replacement=edit.replacement)]
