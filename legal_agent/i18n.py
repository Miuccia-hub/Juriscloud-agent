"""Presentation-only localisation. Widget values and legal-output language stay separate."""
from hashlib import sha256
import re

EN = {
"管理员首次配置：保存后由服务器统一提供，使用者无需再填写。":"First-time administrator setup: save once to provide server credentials for all users.",
"保存到本地后端":"Save to local backend",
"保存失败，请检查 Token 或本地配置目录权限。":"Save failed. Check the Token or local configuration directory permissions.",
"已由服务器配置北大法宝，无需填写 Token。":"PKULAW is configured by the server. No Token entry is required.",
"北大法宝 MCP":"PKULAW MCP",
"北大法宝案例链接":"PKULAW case links",
"在北大法宝打开案例":"Open case on PKULAW",
"北大法宝未返回可用的案例链接。":"PKULAW did not return a usable case link.",
"打开全文可能需要北大法宝账号或机构权限；链接不代表已核验全文。":"Full text may require a PKULAW account or institutional access. A link does not establish full-text verification.",
"MCP检索片段已取得":"MCP research excerpts retrieved",
"检索返回片段，未独立核验完整正文、时效、后续裁判或适用性。":"Search excerpts only; full text, currency, subsequent treatment and applicability have not been independently verified.",
"北大法宝 Token":"PKULAW Token",
"启用中国大陆法律检索":"Enable mainland China legal research",
"仅中国大陆：每轮最多两次检索，可能消耗法宝积分。向法宝发送研究问题，不发送合同原文；返回片段会交给分析模型。":"Mainland China only: up to two searches per round, which may use PKULAW credits. Research queries are sent to PKULAW, without the original contract; returned excerpts are sent to the analysis model.",
"Token 与模型 API Key 不同；获取 Token 后仍需订阅对应 MCP 服务。":"This Token is separate from your model API key. The corresponding MCP services must also be subscribed to.",
"测试法宝连接（不执行检索）":"Test PKULAW connection (no search)",
"正在检查法宝工具权限…":"Checking PKULAW tool access…",
"案例检索":"Case research","法规检索":"Legislation research",
"认证及工具列表通过；尚未执行检索。":"Authentication and tool listing passed; no search performed.",
"连接未通过，请检查 Token、服务订阅或网络。":"Connection check failed. Check the Token, service subscription or network.",
"检索北大法宝 MCP（案例与法规）":"Search PKULAW MCP (cases and legislation)",
"导出报告":"Export report",
"点击打开可预览 PDF，也可以下载以下文件。":"Open the PDF preview, or download the files below.",
"连接等待上限 20 秒；读取响应等待上限 10 分钟。网络或代理可能更早中断。":"Connection wait: up to 20 seconds. Response read wait: up to 10 minutes. Networks or proxies may interrupt sooner.",
"连接测试仅发送固定测试文字，验证分析模型的结构化请求，不发送合同。":"The connection test sends fixed test text to check the analysis model's structured response, without contract data.",
"测试分析模型连接":"Test analysis model connection",
"正在测试模型连接…":"Testing model connection…",
"分析模型连接测试通过：":"Analysis model connection test passed: ",
"模型连接测试":"Model connection test",
"已记录 {total} 项检查，其中 {open} 项资料不足。":"{total} checks recorded; {open} have insufficient information.",
"完整检查清单":"Full checklist",
"检查主题":"Topic","检查状态":"Status","判断与原文":"Assessment and original text","后续处理":"Next action",
"已分析":"Analysed","发现问题":"Concern identified","未找到明确约定":"No explicit provision found","资料不足":"Insufficient information","不适用":"Not applicable",
"逐项检查记录不等于独立法律合规保证；未找到明确约定也不等于不存在法定权利。":"These model check records are not independent legal assurance. Contractual silence does not establish an absence of statutory rights.",
"理解合同与材料":"Read contract and materials","规划四维审查与检索":"Plan review and research","独立查找遗漏":"Independently check omissions","修正并形成报告":"Revise and prepare report",
"返回首页":"Back to home",
"可用性以接口和账户权限为准；联网模型还需支持网页检索。":"Availability depends on the API and your account access. The search model must also support web search.",
"针对上方审查结果继续提问…":"Ask a follow-up about the review above…",
"📄 审查这份合同":"📄 Review this contract",
"🔎 检索条款相关判例":"🔎 Research relevant cases",
"⚖️ 评估知识产权条款":"⚖️ Assess IP clauses",
"请全面审查这份合同，识别法律效力、条款严密性、商业风险及重要遗漏，并以表格列出风险、依据和修改建议。":"Review this contract comprehensively for legal effect, drafting precision, commercial risks and material omissions. Present the risks, supporting grounds and suggested changes in a table.",
"请结合上传合同和所选司法区域，检索与关键风险条款相关的判例及法律规定，并说明其适用性与来源。":"Using the uploaded contract and selected jurisdiction, research cases and legislation relevant to key risk clauses. Explain their applicability and cite sources.",
"请评估这份合同中的知识产权条款，重点分析成果归属、许可范围、背景知识产权和侵权责任，并提出修改建议。":"Assess the contract's intellectual property clauses, focusing on ownership of deliverables, licence scope, background IP and infringement liability. Suggest amendments.",
"### ☁️ Juriscloud\n商业合同审查工作台":"### ☁️ Juriscloud\nCommercial contract workspace",
"CURRENT SESSION · 当前会话":"CURRENT SESSION",
"司法区域 / Jurisdiction":"Jurisdiction", "输出语言 / Output":"Report & answer language",
"清除当前会话 / Clear session":"Clear session",
"模型与接入 / Connection":"Model & connection", "分析模型 / Model":"Analysis model", "联网模型 / Search model":"Search model",
"仅当前会话；不写入仓库和下载报告。":"Current session only. Never included in the repository or exports.",
"模型需支持 Responses 结构化输出；联网模型还需支持 web_search。可填写你账户可用的模型。":"The analysis model needs Responses structured outputs; the search model also needs web_search. Enter models available to your account.",
"作业指定的凭证模块地址目前返回 404。此处为临时密钥输入，提交前须替换或由教师确认。":"The assignment's credentials-module URL returns 404. This temporary key input must be replaced or approved by the teacher before submission.",
"不保存云端历史。合同与必要资料会发送给模型服务；公开检索使用研究问题。清除会话不撤回第三方已处理的数据。":"No cloud history. Contracts and necessary materials are sent to the model provider; public searches use research queries. Clearing this session does not withdraw data already processed by third parties.",
"开始一份审查 / Start a review":"Start a review", "合同来源 / Contract input":"Contract input",
"上传文件":"Upload file", "粘贴文本":"Paste text", "主合同 / Main contract":"Main contract",
"合同正文 / Contract text":"Contract text", "补充资料 / Supporting documents · 最多 6 份":"Supporting documents · up to 6",
"交易背景材料":"Transaction background", "法律研究材料":"Legal research materials", "合同附件":"Contract attachment",
"单文件 8 MB，合计 60,000 字符。扫描件、加密文件、已有修订或复杂嵌入对象需先转换。重新读取材料会清除本次审查结果。":"8 MB per file; 60,000 characters in total. Convert scans, encrypted files, existing tracked changes or embedded objects first. Reading new materials replaces the current review.",
"读取并识别合同 / Read contract":"Read contract", "请先在侧边栏输入自己的 API key，或使用右侧静态示例。":"Enter your API key in the sidebar, or explore the static sample.",
"请上传合同。":"Upload a contract first.", "粘贴合同.txt":"Pasted contract.txt",
"☁️ 理解材料…":"☁️ Reading your materials…", "材料已识别，请确认信息":"Materials ready. Please confirm the details.",
"你的审查路径":"Your review journey",
"**01　确认材料与立场**\n\n**02　四维审查与法律检索**\n\n**03　围绕条款继续追问**\n\n**04　选择修改并导出**":"**01　Confirm materials & perspective**\n\n**02　Review risks & research the law**\n\n**03　Ask follow-up questions**\n\n**04　Choose edits & export**",
"体验静态示例 / Explore sample":"Explore static sample", "下载三个虚构测试材料":"Download fictional test materials",
"确认审查信息 / Confirm before review":"Confirm before review", "合同类型 / Type":"Contract type", "当事人 / Parties":"Parties",
"合同约定法律 / Governing law":"Contractual governing law", "审查立场 / Perspective":"Review perspective",
"中立审查":"Neutral", "其他（在关注点中说明）":"Other (describe in your instructions)",
"审查模式 / Mode":"Review mode", "全面审查":"Full review", "重点审查":"Focused review",
"关注主题 / Topics":"Focus topics", "重点条款 / Focus clauses":"Focus clauses", "关注点 / Instructions":"Your instructions",
"付款与发票":"Payment & invoicing", "履行与验收":"Performance & acceptance", "责任与赔偿":"Liability & indemnities",
"终止":"Termination", "知识产权":"Intellectual property", "保密与数据":"Confidentiality & data", "财税":"Tax & finance", "争议解决":"Disputes",
"例如：重点检查成果归属和验收后付款风险。":"For example: focus on ownership of deliverables and payment after acceptance.",
"确认并开始审查 / Confirm & review":"Confirm & start review",
"请逐项回应关键缺口和材料冲突；无法确认时请明确说明，相关结论将保持待核实。":"Respond to each critical gap and conflict. If you cannot confirm a fact, say so; affected conclusions must remain provisional.",
"请确认本次法律分析范围。":"Confirm the legal scope for this review.",
"重点审查需要至少指定一个条款、主题或关注点。":"Select a clause or topic, or describe a focus for the review.",
"请输入 API key。":"Enter your API key.", "☁️ 审查进行中…":"☁️ Reviewing your contract…", "审查已完成":"Review complete",
"静态示例 / STATIC SAMPLE：未调用 AI，未联网检索，不是法律审查结果。清除会话后可运行真实审查。":"STATIC SAMPLE: no AI calls or web research. This is not a legal review. Clear the session to start a real review.",
"当前结果仍按上方已确认的设置生成。更改侧边栏不会重新解释旧结果，请新建审查以使用新设置。":"These results use the confirmed settings above. Sidebar changes do not reinterpret existing results. Start a new review to use different settings.",
"发现问题 / Issues":"Issues", "优先关注 / High":"High priority", "修改建议 / Edits":"Suggested edits", "来源 / Sources":"Sources",
"合同原文 / Document":"Contract document", "定位条款 / Clause":"Go to paragraph", "搜索原文 / Search":"Search contract", "搜索关键词…":"Search keywords…",
"选中段落置顶显示；段落标识用于定位，不代表合同自身条号。":"The selected paragraph is shown first. Location IDs are not the contract's clause numbers.",
"审查发现 / Review":"Review", "条款追问 / Ask":"Ask", "修改清单 / Edits":"Edits",
"风险筛选 / Severity":"Filter by severity", "高":"High", "中":"Medium", "低":"Low",
"法律效力":"Legal effect", "完整一致":"Clarity & consistency", "商业风险":"Commercial risk", "待核实":"Needs verification",
"覆盖、假设与局限 / Coverage & limits":"Coverage, assumptions & limitations", "法律来源与核验 / Sources":"Legal sources & verification",
"覆盖":"Coverage", "假设":"Assumptions", "下一步":"Next steps", "局限":"Limitations",
"没有可展示的检索来源；不能据此给出已核验的法律结论。":"No research sources are available. Legal conclusions cannot be treated as verified.",
"查看原始来源 / Open source":"Open original source", "**影响 / Impact：** ":"**Impact:** ",
"针对条款提问 / Ask about this clause":"Ask about this clause", "补充或修正事实 / New facts":"Add or correct facts",
"新事实会使已采纳修改需要重新确认。":"New facts require previously accepted edits to be reconfirmed.",
"☁️ 检索并回答 / Research & answer":"☁️ Research & answer", "静态示例不生成回答。请清除会话并上传材料运行真实分析。":"The static sample does not generate answers. Clear the session and upload materials for real analysis.",
"请输入 API key 和问题。":"Enter your API key and a question.", "本次会话已达到 10 轮研究上限，请导出后开始新审查。":"This session has reached the 10-question research limit. Export your work and start a new review.",
"☁️ 深入研究…":"☁️ Researching your question…", "追问研究已完成":"Follow-up research complete",
"仅采纳项进入修订合同。修改文字后需重新确认；关联建议和替代建议不自动覆盖。":"Only accepted edits enter the revised contract. Reconfirm after editing text. Related or alternative suggestions never overwrite each other automatically.",
"**原文 / Original**":"**Original wording**", "替代文本 / Replacement":"Replacement wording", "处理 / Decision":"Decision",
"未决定":"Undecided", "采纳":"Accept", "拒绝":"Reject",
"新事实、新建议或手动改文影响此项；手动文本未自动完成法律复核。":"New facts, suggestions or manual changes affect this edit. Manually edited text has not automatically received legal verification.",
"确认当前版本 / Reconfirm":"Reconfirm this version", "暂无可精确定位的替代文本；缺失条款请参照报告的后续行动。":"No precisely anchored replacements are available. See next steps for proposed missing clauses.",
"带走审查结果 / Export your work":"Export your work",
"仅当前会话保留。导出前请核对引用、双语对应、关联条款及所有已采纳修改。":"Current session only. Check citations, bilingual alignment, related clauses and all accepted edits before export.",
"准备下载文件 / Prepare downloads":"Prepare downloads", "审查报告 · Word":"Review report · Word", "审查报告 · PDF":"Review report · PDF", "修订合同 · Word":"Revised contract · Word",
"运行记录与产品说明 / Run details":"Run details & product status",
"公开检索：OpenAI web_search + 白名单正文读取。澳洲与大陆研究方法参考开源项目，auslaw-mcp 尚未接入。当前是开发版本，凭证模块及真实密钥联网端到端验收仍待完成。":"Public research uses OpenAI web_search plus allowlisted document retrieval. Research methods draw on open-source references; auslaw-mcp is not integrated. This is a development build. The assignment credentials module and live end-to-end model verification remain pending.",
"维多利亚州":"Victoria, Australia", "中国大陆":"Mainland China", "中文":"Chinese", "中英双语":"Chinese + English",
"法律效力":"Legal effect", "首次审查":"Initial review", "文本或商业判断":"Textual or commercial assessment", "有原文支持，适用性仍需复核":"Quotation matched; applicability still needs review",
"正文已取得":"Document retrieved", "正文片段已取得":"Document excerpts retrieved", "正文未取得":"Document not retrieved",
"用户提供，未经独立核验":"User supplied; not independently verified",
"不支持加密 PDF，请先提供未加密副本。":"Encrypted PDFs are not supported. Please provide a decrypted copy.",
"没有识别到正文。":"No readable content was found.", "这不是有效的 DOCX 文件。":"This is not a valid DOCX document.",
"文件为空或超过 8 MB。请拆分或转换后上传。":"The file is empty or exceeds 8 MB. Split or convert it before uploading.",
"材料超过 60,000 字符，请缩小本次材料范围；系统未截断正文。":"The material exceeds 60,000 characters. Reduce the scope; no text was silently truncated.",
"全部材料合计超过 60,000 字符。请减少材料，系统未截断内容。":"The materials exceed 60,000 characters in total. Reduce the materials; no text was truncated.",
"最多上传六份补充材料。":"Up to six supporting documents are supported.",
"原文件已有修订。请先在 Word 中处理修订并保存副本再上传，避免覆盖既有记录。":"The document contains tracked changes. Resolve them in Word and upload a clean copy to preserve existing records.",
"检测到文本框或嵌入对象。请转换为普通段落或文本 PDF，以免遗漏内容。":"Text boxes or embedded objects were detected. Convert them into ordinary paragraphs or a text PDF to avoid omissions.",
"模型未返回有效结构化结果；运行尚未完成。":"The model did not return a valid structured result; the run is incomplete.",
}


EN.update({
"关键日期：":"Key dates: ",
"商业合同审查工作台":"Commercial contract workspace", "工作区":"Workspace", "对话":"Conversation", "新建审查":"New review", "新审查":"New review",
"接口密钥":"API key", "会话设置":"Session settings", "查看材料":"View materials",
"自动（跟随问题）":"Auto (follow question)", "完成审查后，即可查看修改并导出结果。":"Complete a review to manage edits and export your results.",
"今天需要审查什么？":"What would you like to review?", "上传合同，告诉我你关心的问题。":"Attach a contract and tell me what you would like to check.",
"你的问题":"Your question", "例如：付款条件与知识产权归属存在哪些风险？":"For example: what risks arise from the payment terms and IP ownership?",
"补充资料":"Supporting documents", "支持文字版 PDF、Word 和文本文件；每份最多 8 MB。":"Text-based PDF, Word and text files; up to 8 MB each.",
"发送并识别材料":"Send & read materials", "当前条款：":"Current paragraph: ",
"原文保持原始顺序；选定条款用于追问。":"Original order is preserved. The selected paragraph provides context for questions.",
"实际模型请求：":"Actual model requests: ", "成功":"Succeeded", "失败":"Failed",
"请上传 Word、PDF 或文本文件。":"Upload a Word, PDF or text file.",
"未识别":"Not identified", "未完成法律时效及后续处理核验":"Currency and subsequent treatment have not been verified.",
"首次审查":"Initial review",
})

EN.update({
"DOCX 解压后过大，无法安全解析。":"The expanded DOCX is too large to parse safely.",
"不支持包含外部声明的文档。":"Documents containing external declarations are not supported.",
"含超链接或域的段落可阅读，自动写入修订时将拒绝复杂片段。":"Paragraphs containing links or fields can be read; complex replacements cannot be applied automatically.",
"PDF 会重新生成 Word 排版，不能保留原 PDF 版式。":"PDF input is rebuilt as Word; the original PDF layout cannot be retained.",
"文本输入将使用标准 Word 排版。":"Text input uses standard Word formatting.",
"支持 DOCX、文本 PDF 和 UTF-8 TXT；不支持 .doc 或扫描件。":"Use DOCX, text-based PDF or UTF-8 TXT. Legacy .doc files and scans are unsupported.",
"请先采纳至少一项修改。":"Accept at least one edit first.",
})
ERROR_SUFFIXES={
" 受新事实或新建议影响，请重新确认。":" is affected by new facts or suggestions. Reconfirm it.",
" 无法唯一定位。":" cannot be uniquely located.",
" 是页眉、页脚或无法定位的内容，请人工处理。":" is a header, footer or unlocatable section; edit it manually.",
" 包含超链接、书签或复杂域，已停止导出以保护原文件。":" contains links, bookmarks or complex fields. Export stopped to protect the original.",
" 含域、图片或特殊字符结构，请人工处理。":" contains fields, images or special character structures; edit it manually.",
" 原文校验失败，未写入修订。":" failed original-text validation; no revision was written.",
}

EN.update({
"上次失败：":"Last failure: ","失败阶段：":"Failed stage: ","错误编号：":"Error code: ","请求编号：":"Request ID: ",
"读取与检查文件":"Read and validate files",
"已有输入与结果已保留；可修正设置后重试当前操作。":"Your inputs and existing results are preserved. Adjust the settings and retry the current action.",
})

EN.update({
"＋ 新对话":"＋ New chat","审查偏好":"Review preferences","审查立场":"Perspective",
"按问题判断，未指定时中立":"Follow the question; neutral if unspecified",
"你好，今天想审查什么？":"Hello, what would you like to review?",
"有什么可以帮你？":"How can I help?", "添加合同与资料":"Attach contract and materials",
"已添加合同文本":"Contract text attached", "发送并分析":"Send & analyse",
"上传合同后直接提问，分析完成后可以继续追问。":"Attach a contract and ask a question. Continue the conversation after the review.",
"请审查这份合同。":"Please review this contract.","正在分析…":"Working…","分析完成":"Analysis complete",
"分析过程":"Activity","重试分析":"Retry analysis","继续提问":"Follow-up question",
"整份合同":"Whole contract","补充事实":"Add facts","发送":"Send",
"问题":"Issue","风险分析与处理建议":"Risk analysis and suggested action","影响":"Impact","建议":"Suggested action",
})

EN.update({"界面语言":"Interface language","设置":"Settings","新对话":"New chat","一起理清这份合同。":"Let’s look at your contract."})

PREFIXES={
"需要确认：":"Please clarify: ", "局部信息缺口（可继续并保留相关判断）：":"Local gaps (review may proceed conditionally): ",
"识别的适用法律：":"Detected governing law: ", " · 关键日期：":" · Key dates: ",
"依据 / Source：":"Source: ", "当前上下文 / Context：":"Current context: ",
"定位 ":"Go to ", "修订合同未生成：":"Revised contract was not generated: ",
}


def translate(text,language):
    if not isinstance(text,str): return text
    if language!="English":
        if text=="English": return "英文"
        if text=="请输入 API key。": return "请输入接口密钥。"
        if text=="请输入 API key 和问题。": return "请输入接口密钥和问题。"
        if text.startswith("**影响 / Impact：** "): return "**影响：** "+text[len("**影响 / Impact：** "):]
        if text.startswith("依据 / Source："): return "依据："+text[len("依据 / Source："): ]
        if text=="补充资料 / Supporting documents · 最多 6 份": return "补充资料（最多六份）"
        if text in EN and " / " in text:
            suffix="**" if text.endswith("**") else ""
            return text.split(" / ",1)[0]+suffix
        return text
    if text in EN:
        return EN[text]
    if text.startswith(("✓ ","✕ ")): return text[:2]+translate(text[2:],language)
    if text.startswith("公开来源读取结果："):
        numbers=re.findall(r"\d+",text)
        return f"Source retrieval: {numbers[0]} records; {numbers[1]} with readable text"
    if text.startswith("逐项检查合同（"):return "Check contract topics ("+text.split("（",1)[1].replace("）",")")
    if text.startswith("引文原文匹配："): return "Quotation matches: "+text.split("：",1)[1]
    for suffix,replacement in ERROR_SUFFIXES.items():
        if text.endswith(suffix): return text[:-len(suffix)]+replacement
    match=re.fullmatch(r"(.+) 与 (.+) 修改范围重叠，请只采纳其中一项。",text)
    if match: return f"{match[1]} and {match[2]} overlap. Accept only one."
    match=re.fullmatch(r"第 (\d+) 页缺少可读文本，可能是扫描件；首版不支持 OCR。",text)
    if match: return f"Page {match[1]} has insufficient readable text. Scans and OCR are not supported."
    if text.startswith("**") and text.endswith("**"):
        return "**"+translate(text[2:-2],language)+"**"
    if text.startswith("**影响 / Impact：** "):
        return "**Impact:** "+text[len("**影响 / Impact：** "): ]
    if text.startswith("<div class=\"note\">"):
        return '<div class="note">☁️ For legal professionals. Distinguish legal effect, drafting issues and commercial risks. Unsupported conclusions remain provisional.</div>'
    for prefix,replacement in PREFIXES.items():
        if text.startswith(prefix):
            return replacement+translate(text[len(prefix):],language)
    if text.startswith("追问 "): return "Follow-up "+text[3:]
    if text.endswith(" 的用途"):
        return "Material type: "+text[:-4]
    if text.startswith("我确认按 "):
        return "I confirm the selected legal scope. Differences from contractual governing law remain subject to review."
    if text.startswith("实际模型请求 "):
        return re.sub(r"实际模型请求 (\d+) · 成功 (\d+)。静态示例不产生调用。",r"Actual model requests: \1 · Successful: \2. Static samples make no calls.",text)
    if text.startswith("运行未完成（"):
        kind=text.split("（",1)[1].split("）",1)[0]
        return f"Run incomplete ({kind}). Check your key, model access, network or file format. Existing results are preserved."
    if " · " in text and text.split(" · ")[0] in {"1 / 6","2 / 6","1 / 5","2","3","4","5","6"}:
        stage,detail=text.split(" · ",1)
        stages={"理解合同与材料":"Read contract and materials","规划四维审查与检索":"Plan review and research",
                "理解追问并规划研究":"Understand question and plan research","阅读与核对法律依据":"Read and check legal materials",
                "分析风险并拟修改":"Assess risks and draft edits","独立复核":"Independent verification","修正并形成报告":"Revise and prepare report"}
        return stage+" · "+stages.get(detail,detail)
    if text=="检索公开来源并读取正文": return "Search public sources and retrieve documents"
    return text


class LocalizedUI:
    """Wrap presentation labels only; leave widget values stable across language changes."""
    WIDGETS={"text_input","text_area","selectbox","radio","multiselect","checkbox","button","file_uploader","download_button","form_submit_button","link_button"}
    TEXT={"markdown","write","caption","subheader","header","title","info","warning","error","success","expander","status","metric","text","update","popover"}
    CONTEXTS={"container","form","expander","status","chat_message","spinner","popover"}

    def __init__(self,target,language):
        self.target=target; self.language=language

    def __enter__(self):
        self.target.__enter__(); return self

    def __exit__(self,*args):
        return self.target.__exit__(*args)

    def __getattr__(self,name):
        original=getattr(self.target,name)
        if name=="sidebar": return LocalizedUI(original,self.language)
        if not callable(original): return original
        def wrapped(*args,**kwargs):
            lang=self.language()
            args=list(args)
            label=args[0] if args and isinstance(args[0],str) else kwargs.get("label","")
            if name in self.WIDGETS and name not in {"form_submit_button","link_button"} and "key" not in kwargs:
                kwargs["key"]="ui_"+sha256((name+label).encode()).hexdigest()[:16]
            if name in self.WIDGETS|self.TEXT|{"spinner"}:
                if args and isinstance(args[0],str): args[0]=translate(args[0],lang)
                for k in ("label","help","placeholder"):
                    if k in kwargs: kwargs[k]=translate(kwargs[k],lang)
            if name in {"selectbox","radio","multiselect"}:
                formatter=kwargs.get("format_func",str)
                kwargs["format_func"]=lambda v:translate(formatter(v),lang)
            # Explicit session state wins over defaults, including when a locale
            # changes Streamlit 1.50's widget identity. Avoid duplicate-default warnings.
            if name in {"text_input","text_area","selectbox","radio","multiselect","checkbox"}:
                import streamlit as raw_st
                key=kwargs.get("key")
                if key in raw_st.session_state:
                    previous=raw_st.session_state[key]
                    options=args[1] if len(args)>1 else kwargs.get("options",[])
                    if name=="multiselect": previous=[v for v in previous if v in options]
                    elif name in {"selectbox","radio"} and previous not in options: previous=options[0]
                    raw_st.session_state[key]=previous
                    for default in ("value","index","default"): kwargs.pop(default,None)
            if name=="tabs":
                args[0]=[translate(v,lang) for v in args[0]]
            result=original(*args,**kwargs)
            if name in {"columns","tabs"}: return [LocalizedUI(r,self.language) for r in result]
            if name in self.CONTEXTS: return LocalizedUI(result,self.language)
            return result
        return wrapped

