from __future__ import annotations
from dataclasses import replace
from pathlib import Path
import hashlib
import html
import streamlit as _st
from legal_agent.documents import extract, validate_bundle
from legal_agent.models import Settings, EditChoice
from legal_agent.workflow import Gateway, Workflow
from legal_agent.edits import merge_choices, check_conflicts
from legal_agent.exports import report_sections, report_docx, report_pdf, revised_docx
from legal_agent.i18n import LocalizedUI, translate
from legal_agent.upload import upload_files
from legal_agent.landing import render_landing
from legal_agent.interactions import analysis_activity, export_action, consume_export_request, copy_answer, queue_followup
from legal_agent.presentation import answer_language, report_table, coverage_table, automatic_settings, apply_intake_limits, report_copy_text, cited_pkulaw_cases
from legal_agent.errors import RunFailure, classify, message
from legal_agent.pkulaw import PkulawClient, safe_pkulaw_url
from legal_agent.credentials import backend_pkulaw_token, save_backend_pkulaw_token

_st.set_page_config(page_title="Juriscloud",page_icon="☁️",layout="wide",initial_sidebar_state="expanded")
ss=_st.session_state
ss.setdefault("ui_language","English")
ss.setdefault("jurisdiction","中国大陆")
ss.setdefault("pkulaw_enabled",True)
st=LocalizedUI(_st,lambda:ss.get("ui_language","English"))
def tx(value): return translate(value,ss.get("ui_language","English"))
def go_home():
    ss.page="home"

def use_quick_prompt(prompt):
    ss.initial_question=tx(prompt)

def clear():
    preferences={k:ss[k] for k in ("ui_language","page") if k in ss}
    for key in list(ss): del ss[key]
    ss.update(preferences)
    ss.update(initial_question="",contract_text="",question="",new_facts="",api_key="",perspective="")
def gateway():
    signature=hashlib.sha256((api_key+model+search_model).encode()).hexdigest()
    if ss.get("gateway_signature")!=signature:
        ss.gateway=Gateway(api_key,model,search_model); ss.gateway_signature=signature
    return ss.gateway
def pkulaw_token():
    return (backend_pkulaw_token() or ss.get("pkulaw_token", "")) if ss.get("pkulaw_enabled", False) else ""
def fail(exc):
    failure=classify(exc,ss.get("active_stage",""))
    language=ss.get("ui_language","English")
    st.error(message(failure,language))
    if type(exc) is ValueError:
        # Local file-validation errors only; never show arbitrary API bodies.
        st.warning(tx(str(exc))[:600])
    if failure.stage: st.caption(tx("失败阶段：")+tx(failure.stage))
    st.caption(tx("错误编号：")+failure.code)
    if failure.request_id: st.caption(tx("请求编号：")+failure.request_id)
    st.info("已有输入与结果已保留；可修正设置后重试当前操作。")
    ss.last_failure={"code":failure.code,"stage":failure.stage,"request_id":failure.request_id}

def progress(status):
    def update(stage):
        ss.active_stage=stage
        ss.setdefault("active_trace",[]).append(stage)
        status.write(tx(stage))
    return update

def trace(items):
    if items:
        with st.expander("分析过程",expanded=False,icon=":material/format_list_bulleted:"):
            for item in items: st.caption(tx(item))

def render_report(report):
    st.write(report.summary)
    checks=getattr(report,"_review_checks",[])
    if checks:
        st.caption(tx("已记录 {total} 项检查，其中 {open} 项资料不足。").format(total=len(checks),open=sum(r["status"]=="资料不足" for r in checks)))
        st.caption(tx("逐项检查记录不等于独立法律合规保证；未找到明确约定也不等于不存在法定权利。"))
        with st.expander("完整检查清单",expanded=False):
            st.markdown(coverage_table(checks,tx),unsafe_allow_html=True)
    if report.risks:
        st.markdown(report_table(report,tx),unsafe_allow_html=True)
    cases=cited_pkulaw_cases(report,ss.get("sources",[]))
    if cases:
        st.markdown("**"+tx("北大法宝案例链接")+"**")
        for source in cases:
            st.write(source.id+" · "+source.title)
            url=safe_pkulaw_url(source.url)
            if url: _st.link_button(tx("在北大法宝打开案例"),url)
            else: st.caption(tx("北大法宝未返回可用的案例链接。"))
        st.caption(tx("打开全文可能需要北大法宝账号或机构权限；链接不代表已核验全文。"))
    with st.expander("覆盖、假设与局限 / Coverage & limits"):
        for label,items in [("覆盖",report.coverage),("假设",report.assumptions),("下一步",report.next_steps),("局限",report.limitations)]:
            if items:
                st.markdown("**"+tx(label)+"**")
                for item in dict.fromkeys(items): st.write("• "+item)

def run_review():
    if not api_key:
        st.error("请输入 API key。")
        return
    ss.active_trace=[]
    try:
        with st.chat_message("assistant",avatar="☁️"):
            with analysis_activity(st,tx,False) as status:
                workflow=Workflow(gateway(),progress(status),pkulaw_token=pkulaw_token())
                if "intake" not in ss:
                    ss.intake=workflow.intake(ss.main,ss.supplements,ss.settings)
                ss.settings=automatic_settings(ss.settings,ss.intake)
                report,sources,evidence,critique=workflow.review(ss.main,ss.supplements,ss.settings,ss.intake)
                apply_intake_limits(report,ss.intake)
                ss.update(report=report,sources=sources,evidence=evidence,critique=critique,
                    choices=[EditChoice(e,replacement=e.replacement) for e in report.suggestions],
                    review_trace=list(ss.active_trace))
                ss.pop("last_failure",None)
                status.update(label=tx("分析完成"),state="complete",expanded=False)
        st.rerun()
    except Exception as exc:
        ss.review_trace=list(ss.active_trace)
        fail(exc)

# Landing and workspace share a session; visiting the introduction never clears work.
if ss.get("page","home")=="home":
    # Detach hidden workspace controls from widget cleanup while on the intro.
    for saved_key in list(ss):
        if saved_key in {"ui_language","api_key","model","search_model","pkulaw_token","pkulaw_enabled",
                         "jurisdiction","language","perspective","initial_question","contract_text",
                         "question","new_facts","input_mode","view","selected_clause","document_search"} or saved_key.startswith(("role_","replace_","decision_")):
            ss[saved_key]=ss[saved_key]
    st.markdown("""<style>
    [data-testid="stSidebar"],[data-testid="stHeader"]{display:none!important}
    .block-container{padding:0!important;max-width:none!important}
    html,body{overflow-x:clip}
    iframe[title="legal_agent.landing.juriscloud_landing"]{display:block;border:0}
    </style>""",unsafe_allow_html=True)
    action=render_landing(ss.get("ui_language","English"),False)
    if isinstance(action,dict) and action.get("nonce")!=ss.get("_landing_event"):
        ss._landing_event=action.get("nonce")
        if action.get("language") in ("中文","English"):
            ss.ui_language=action["language"]
        if action.get("action")=="start":
            ss.page="workspace"
            st.rerun()
        if action.get("action")=="language":
            st.rerun()
    st.stop()

if ss.pop("_clear_followup",False):
    ss.question="";ss.new_facts=""
restored_followup=ss.pop("_restore_followup",None)
if restored_followup:
    ss.question=restored_followup["question"]
    ss.new_facts=restored_followup["facts"]
st.markdown('<style>'+ (Path(__file__).parent/'assets/workspace.css').read_text()+'</style>',unsafe_allow_html=True)
with st.sidebar:
    st.markdown('<div class="wordmark"><span aria-hidden="true">☁️</span> Juriscloud</div>',unsafe_allow_html=True)
    st.button("返回首页",key="back_home",use_container_width=True,on_click=go_home)
    if st.button("新对话",icon=":material/add:",use_container_width=True,key="new_chat"):
        prefs={k:ss[k] for k in ("ui_language","page","api_key","model","search_model","pkulaw_token","pkulaw_enabled","jurisdiction","language","perspective") if k in ss}
        clear();ss.update(prefs);st.rerun()
    view=st.radio("工作区",(["对话","修改清单 / Edits","带走审查结果 / Export your work"] if "report" in ss else ["对话"]),key="view",label_visibility="collapsed")
    if "main" in ss:
        st.caption(ss.main.name)
    with st.container(key="sidebar_settings"):
        with st.popover("设置",icon=":material/tune:",use_container_width=True):
            st.subheader("设置")
            st.selectbox("界面语言",["中文","English"],key="ui_language")
            jurisdiction=st.selectbox("司法区域 / Jurisdiction",["维多利亚州","中国大陆"],key="jurisdiction")
            language=st.selectbox("输出语言 / Output",["自动（跟随问题）","中文","English","中英双语"],key="language")
            perspective=st.text_input("审查立场",value="",placeholder="按问题判断，未指定时中立",key="perspective")
            with st.expander("模型与接入 / Connection"):
                api_key=st.text_input("接口密钥",type="password",key="api_key",help="仅当前会话；不写入仓库和下载报告。")
                model_options=["gpt-6-luna","gpt-6.1-sol"]
                for model_key in ("model","search_model"):
                    if ss.get(model_key) not in model_options:
                        ss[model_key]="gpt-6-luna"
                model=st.selectbox("分析模型 / Model",model_options,key="model")
                search_model=st.selectbox("联网模型 / Search model",model_options,key="search_model")
                st.caption("可用性以接口和账户权限为准；联网模型还需支持网页检索。")
                st.caption("连接等待上限 20 秒；读取响应等待上限 10 分钟。网络或代理可能更早中断。")
                st.caption("连接测试仅发送固定测试文字，验证分析模型的结构化请求，不发送合同。")
                if st.button("测试分析模型连接",key="test_model_connection"):
                    if not api_key:
                        st.error("请输入 API key。")
                    else:
                        check_gateway=None
                        try:
                            with st.spinner("正在测试模型连接…"):
                                check_gateway=Gateway(api_key,model,search_model)
                                check_gateway.check_connection()
                            st.success(tx("分析模型连接测试通过：")+model)
                        except Exception as exc:
                            failure=classify(exc,"模型连接测试")
                            st.error(message(failure,ss.get("ui_language","English")))
                            st.caption(tx("错误编号：")+failure.code)
                            if failure.request_id: st.caption(tx("请求编号：")+failure.request_id)
                        finally:
                            if check_gateway is not None: check_gateway.client.close()
            with st.expander("北大法宝 MCP"):
                backend_token = backend_pkulaw_token()
                if backend_token:
                    ss.pop("pkulaw_token", None)
                    st.caption("已由服务器配置北大法宝，无需填写 Token。")
                    ss.setdefault("pkulaw_enabled", True)
                else:
                    st.text_input("北大法宝 Token",type="password",key="pkulaw_token",help="仅当前会话；不写入仓库和下载报告。")
                    st.caption("管理员首次配置：保存后由服务器统一提供，使用者无需再填写。")
                    if st.button("保存到本地后端",key="save_pkulaw_backend"):
                        try:
                            save_backend_pkulaw_token(ss.get("pkulaw_token", ""))
                            ss.pkulaw_enabled=True
                            st.rerun()
                        except (ValueError, OSError):
                            st.error("保存失败，请检查 Token 或本地配置目录权限。")
                st.checkbox("启用中国大陆法律检索",key="pkulaw_enabled")
                st.caption("仅中国大陆：每轮最多两次检索，可能消耗法宝积分。向法宝发送研究问题，不发送合同原文；返回片段会交给分析模型。")
                st.caption("Token 与模型 API Key 不同；获取 Token 后仍需订阅对应 MCP 服务。")
                if st.button("测试法宝连接（不执行检索）",key="test_pkulaw_connection"):
                    with st.spinner("正在检查法宝工具权限…"):
                        checks=PkulawClient(backend_token or ss.get("pkulaw_token", "")).check_connection()
                    for kind, code in checks.items():
                        label=tx("案例检索") if kind=="cases" else tx("法规检索")
                        if code=="ok":
                            st.success(label+" · "+tx("认证及工具列表通过；尚未执行检索。"))
                        else:
                            st.warning(label+" · "+tx("连接未通过，请检查 Token、服务订阅或网络。"))
                            st.caption(tx("错误编号：")+code)
            with st.expander("会话设置"):
                st.caption("不保存云端历史。合同与必要资料会发送给模型服务；公开检索使用研究问题。清除会话不撤回第三方已处理的数据。")
                if st.button("清除当前会话 / Clear session"): clear();st.rerun()

if "main" not in ss:
    st.markdown('<div class="welcome"><span class="cloud" aria-hidden="true">☁️</span><h1>'+tx("你好，今天想审查什么？")+'</h1></div>',unsafe_allow_html=True)
    with st.container(key="quick_prompts"):
        quick_columns=st.columns(3,gap="small")
        quick_options=[
            ("📄 审查这份合同","请全面审查这份合同，识别法律效力、条款严密性、商业风险及重要遗漏，并以表格列出风险、依据和修改建议。"),
            ("🔎 检索条款相关判例","请结合上传合同和所选司法区域，检索与关键风险条款相关的判例及法律规定，并说明其适用性与来源。"),
            ("⚖️ 评估知识产权条款","请评估这份合同中的知识产权条款，重点分析成果归属、许可范围、背景知识产权和侵权责任，并提出修改建议。"),
        ]
        for i,(label,prompt) in enumerate(quick_options):
            with quick_columns[i]:
                st.button(label,key=f"quick_prompt_{i}",use_container_width=True,on_click=use_quick_prompt,args=(prompt,))
    with st.container(border=True,key="initial_composer"):
        initial_question=st.text_area("你的问题",placeholder=tx("有什么可以帮你？"),key="initial_question",height=95,label_visibility="collapsed")
        attach,space,send=st.columns([1,7,1],vertical_alignment="bottom")
        with attach:
            with st.popover("＋",help=tx("添加合同与资料")):
                input_mode=st.radio("合同来源 / Contract input",["上传文件","粘贴文本"],horizontal=True,key="input_mode")
                uploaded=upload_files("main_upload",tx("主合同 / Main contract"),ss.get("ui_language","English"),1) if input_mode=="上传文件" else []
                text=st.text_area("合同正文 / Contract text",height=170,key="contract_text") if input_mode=="粘贴文本" else ""
                files=upload_files("support_upload",tx("补充资料"),ss.get("ui_language","English"),6)
                roles={i:st.selectbox(f"{f.name} 的用途",["交易背景材料","法律研究材料","合同附件"],key=f"role_{i}_{f.name}") for i,f in enumerate(files)}
                st.caption("支持文字版 PDF、Word 和文本文件；每份最多 8 MB。")
        with space:
            names=[f.name for f in uploaded]+[f.name for f in files]
            if text.strip(): names.insert(0,tx("已添加合同文本"))
            for name in names: st.markdown('<span class="attachment">▤ '+html.escape(name)+'</span>',unsafe_allow_html=True)
        with send: submitted=st.button("↑",help=tx("发送并分析"),type="primary",key="send_initial")
    st.caption("上传合同后直接提问，分析完成后可以继续追问。")
    if submitted:
        try:
            ss.active_stage="读取与检查文件"
            if input_mode=="上传文件" and not uploaded: raise ValueError("请上传合同。")
            main=extract(uploaded[0].name,uploaded[0].getvalue()) if uploaded else extract("contract.txt",text.encode())
            supplements=[extract(f.name,f.getvalue(),f"D{i+2}",roles[i]) for i,f in enumerate(files)]
            validate_bundle(main,supplements)
            if not api_key: st.error("请输入 API key。")
            else:
                settings=Settings(jurisdiction,answer_language(language,initial_question,ss.get("ui_language","English")),
                    perspective.strip() or "按问题中的立场；未指定时中立", "全面审查",initial_question,"自动识别")
                ss.update(main=main,supplements=supplements,settings=settings,
                    original_question=initial_question or tx("请审查这份合同。"),messages=[],answers=[],choices=[],sources=[])
                st.rerun()
        except Exception as exc: fail(exc)
else:
    main=ss.main
    if view=="对话":
        with st.chat_message("user"):
            st.write(ss.get("original_question",tx("请审查这份合同。")))
            st.markdown('<span class="attachment">▤ '+html.escape(main.name)+'</span>',unsafe_allow_html=True)
        if "report" not in ss:
            if ss.get("review_trace"): trace(ss.review_trace)
            if not ss.get("review_trace"):
                run_review()
            elif st.button("重试分析",type="primary"):
                if api_key: run_review()
                else: st.error("请输入 API key。")
        else:
            with st.chat_message("assistant",avatar="☁️"):
                trace(ss.get("review_trace",[]))
                render_report(ss.report)
                with st.expander("合同原文 / Document"):
                    ids=[c.id for c in main.clauses]
                    selected_clause=st.selectbox("定位条款 / Clause",["",*ids],key="selected_clause",format_func=lambda v,locale=ss.ui_language:translate("整份合同",locale) if not v else v)
                    search=st.text_input("搜索原文 / Search",key="document_search")
                    for c in main.clauses:
                        if search and search.casefold() not in c.text.casefold(): continue
                        st.markdown(f'<div class="clause"><div class="location">{html.escape(c.id)}</div>{html.escape(c.text)}</div>',unsafe_allow_html=True)
                with st.expander("法律来源与核验 / Sources"):
                    if not ss.sources: st.info("没有可展示的检索来源；不能据此给出已核验的法律结论。")
                    for source in ss.sources:
                        st.markdown('**'+html.escape(source.id+' '+source.title)+'**')
                        st.caption(tx(source.status)); st.write(source.warning)
                        # External links have no widget state/key in Streamlit 1.50.
                        # Translate directly so existing sessions also recover without a server restart.
                        if source.url: _st.link_button(tx("查看原始来源 / Open source"),source.url)
                        for evidence in ss.get("all_evidence",[ss.get("evidence")]):
                            if evidence:
                                for finding in evidence.findings:
                                    if finding.source_id==source.id:
                                        st.write(finding.proposition); st.code(finding.exact_quote,language=None)
                copy_answer(report_copy_text(ss.report,tx,ss.sources),ss.ui_language,key="copy_review")
            for i,(question,answer) in enumerate(ss.answers):
                with st.chat_message("user"): st.write(question)
                with st.chat_message("assistant",avatar="☁️"):
                    trace(ss.get("answer_traces",[[]]*len(ss.answers))[i])
                    render_report(answer)
                    copy_answer(report_copy_text(answer,tx,ss.sources),ss.ui_language,key=f"copy_answer_{i}")
            if ss.get("_followup_failure"):
                fail(ss._followup_failure)
            with st.container(border=True,key="followup_composer"):
                opts,entry,send=st.columns([1,14,1],vertical_alignment="center",gap="small")
                with opts:
                    with st.popover("＋",help=tx("补充事实")):
                        new_facts=st.text_area("补充或修正事实 / New facts",height=90,key="new_facts")
                with entry:
                    question=st.text_area("继续提问",placeholder=tx("针对上方审查结果继续提问…"),key="question",height=68,label_visibility="collapsed")
                with send: ask=st.button("↑",help=tx("发送"),type="primary",key="send_followup",
                                       on_click=queue_followup,args=(ss,))
            pending_followup=ss.pop("_pending_followup",None)
            if ask or pending_followup:
                if pending_followup:
                    question=pending_followup["question"]
                    new_facts=pending_followup["facts"]
                if not api_key or not question.strip(): st.error("请输入 API key 和问题。")
                elif len(ss.messages)>=20: st.warning("本次会话已达到 10 轮研究上限，请导出后开始新审查。")
                else:
                    ss.active_trace=[]
                    try:
                        with st.chat_message("user"): st.write(question)
                        with st.chat_message("assistant",avatar="☁️"):
                            with analysis_activity(st,tx,False) as status:
                                selected=(pending_followup or {}).get("clause",ss.get("selected_clause",""))
                                context=("["+selected+"] ") if selected else ""
                                answer,sources,evidence,critique=Workflow(gateway(),progress(status),pkulaw_token=pkulaw_token()).followup(main,ss.supplements,
                                    replace(ss.settings,language=answer_language(language,question)),ss.intake,ss.report,ss.messages,context+question,new_facts)
                                status.update(label=tx("分析完成"),state="complete",expanded=False)
                        ss.messages.extend([{"role":"user","content":question+("\n"+new_facts if new_facts else "")},
                            {"role":"assistant","content":answer.model_dump_json()}])
                        ss.answers.append((question,answer)); ss.sources.extend(sources)
                        ss.setdefault("answer_traces",[[]]*(len(ss.answers)-1)).append(list(ss.active_trace))
                        ss.setdefault("all_evidence",[ss.evidence]).append(evidence)
                        merge_choices(ss.choices,answer.suggestions,f"追问 {len(ss.answers)}",bool(new_facts.strip()))
                        ss.pop("exports",None);ss.pop("last_failure",None)
                        ss.pop("_followup_failure",None)
                        st.rerun()
                    except Exception as exc:
                        ss._followup_failure=classify(exc,ss.get("active_stage",""))
                        ss._restore_followup=pending_followup or {"question":question,"facts":new_facts}
                        st.rerun()
    elif "report" in ss:
        report,settings=ss.report,ss.settings
        if view=="修改清单 / Edits":
            st.caption("仅采纳项进入修订合同。修改文字后需重新确认；关联建议和替代建议不自动覆盖。")
            for choice in ss.choices:
                e=choice.edit
                with st.expander(f"{e.id} · {e.clause_id} · {tx(choice.state)}"):
                    st.caption(choice.origin)
                    st.write("**原文 / Original**"); st.code(e.original,language=None)
                    st.write(e.reason)
                    if e.bilingual_note:
                        st.info(e.bilingual_note)
                    replacement=st.text_area("替代文本 / Replacement",value=choice.replacement,key=f"replace_{e.id}")
                    if replacement!=choice.replacement:
                        choice.replacement=replacement; choice.needs_reconfirmation=True; ss.pop("exports",None)
                    state=st.radio("处理 / Decision",["未决定","采纳","拒绝"],index=["未决定","采纳","拒绝"].index(choice.state),horizontal=True,key=f"decision_{e.id}")
                    if state!=choice.state:
                        choice.state=state; ss.pop("exports",None)
                    if choice.needs_reconfirmation:
                        st.warning("新事实、新建议或手动改文影响此项；手动文本未自动完成法律复核。")
                        if st.button("确认当前版本 / Reconfirm",key=f"reconfirm_{e.id}"):
                            choice.needs_reconfirmation=False; ss.pop("exports",None); st.rerun()
            errors=check_conflicts(main,ss.choices)
            for error in errors:
                st.warning(error)
            if not ss.choices:
                st.info("暂无可精确定位的替代文本；缺失条款请参照报告的后续行动。")
        else:
            st.subheader("带走审查结果 / Export your work")
            st.caption("仅当前会话保留。导出前请核对引用、双语对应、关联条款及所有已采纳修改。")
            if ss.get("export_state")=="ready" and "exports" not in ss:
                ss.export_state="idle"
            state=ss.get("export_state","ready" if "exports" in ss else "idle")
            event=export_action(state,ss.get("ui_language","English"),False,
                ss.get("exports",{}).get("report_pdf"))
            if consume_export_request(ss,event): st.rerun()
            if ss.get("export_state")=="generating":
                ss.active_stage="导出报告"
                out={};warnings=[]
                try:
                    sections=report_sections(report,ss.sources,ss.choices,settings,ss.answers)
                    out["report_docx"]=report_docx(sections)
                    out["report_pdf"]=report_pdf(sections)
                    if any(c.state=="采纳" for c in ss.choices):
                        try:
                            out["revision"]=revised_docx(main,ss.choices)
                        except ValueError as exc:
                            warnings.append("修订合同未生成："+str(exc))
                    ss.exports=out
                    ss.export_warnings=warnings
                    ss.export_state="ready"
                except Exception as exc:
                    ss.export_state="error"
                    ss.export_error=RunFailure("export_failed","导出报告")
                st.rerun()
            if ss.get("export_state")=="error" and ss.get("export_error"):
                fail(ss.export_error)
            if "exports" in ss:
                st.caption("点击打开可预览 PDF，也可以下载以下文件。")
                for warning in ss.get("export_warnings",[]): st.warning(tx(warning))
                columns=st.columns(3)
                for i,(key,label,name,mime) in enumerate([
                    ("report_docx","审查报告 · Word","review-report.docx","application/vnd.openxmlformats-officedocument.wordprocessingml.document"),
                    ("report_pdf","审查报告 · PDF","review-report.pdf","application/pdf"),
                    ("revision","修订合同 · Word","contract-redline.docx","application/vnd.openxmlformats-officedocument.wordprocessingml.document")]):
                    if key in ss.exports:
                        columns[i].download_button(label,ss.exports[key],file_name=name,mime=mime,use_container_width=True)

ss._rendered_ui_language=ss.get("ui_language","English")
