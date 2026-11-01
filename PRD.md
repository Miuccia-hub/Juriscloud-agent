> 2026-10-29 Latest interface requirements (take precedence over earlier descriptions): implement the chat workspace according to the user's Mike screenshots P1/P2/P4. Analysis proceeds continuously after upload and submission, without P3-style item-by-item confirmation forms; unconfirmed facts and conflicts become conditions and limitations that can be supplemented in later conversation. Show actual execution records, a brief direct answer and a two-column risk table. Acceptance of contract amendments remains a separate operation, not a prerequisite for receiving analysis. Retain light sky blue and separate Chinese/English interfaces.

> 2026-10-26 Revision: this supplement takes precedence over the earlier interface descriptions below. The product displays no static examples or preset answers; the three assignment cases are separate repository materials and must record actual inputs, questions, answers and screenshots. Chinese/English UI is displayed separately; answer language is selected independently or follows the question. The main layout draws on Mike's left navigation, central conversation and input, and on-demand right document panel; retain light sky blue. See juriscloud-contracts/BUILD_STATUS.md for implementation and unverified items.

# Commercial Contract Review and Legal Research Agent — Product Requirements Document

Version: 1.1  
Date: 26 October 2026  
Status: Compiled from requirements interviews as the basis for initial design and development  
Working product name: Juriscloud Agent (

## 1 Product Goals

Provide lawyers, in-house counsel and law students with a commercial contract review tool combining original contract text, transaction context and traceable legal authorities. After uploading a contract and confirming scope and perspective, users receive a risk list, legal analysis and replacement clauses; they can then ask multi-turn questions about specific clauses, select amendments individually, and export a review report and a Word contract with tracked changes.

The initial release targets classroom submission and demonstration while retaining practical value as an assistive tool. Quality work focuses on contract understanding, genuine research, citation verification, amendment consistency and file export; accounts, cloud history and team collaboration are outside the initial release.

The product's primary task is commercial contract review. Case and legislation research, clause questions and amendment suggestions serve that task; the product does not expand into a general litigation representative for every kind of case.

### 1.1 Product Success Criteria

- Users can complete the entire path from contract upload to review, follow-up, amendment selection and export.
- Every risk has a clear original-text location; a missing clause includes a suggested insertion location.
- Substantive legal conclusions are traceable to materials actually obtained; judgment is expressly reserved where support is insufficient.
- Users can understand the nature, level, impact and handling priority of each risk.
- The revised version contains only accepted amendments, which can be individually accepted or rejected in Word.
- The application runs through a Streamlit Cloud link, with visitors supplying their own OpenAI API key.

## 2 Target Users and Use Cases

| User | Main Needs | Product Support |
|---|---|---|
| Lawyer | Locate issues, check authorities and prepare amendment advice | Clause locations, issue analysis, original quotations and replacement text |
| In-house counsel | Identify performance and commercial risks from a transaction perspective | User perspective, background-material comparison, risk levels and amendment list |
| Law student | Understand review steps and legal application | Research steps, sources, applicability reasons and uncertainty |

Typical uses include procurement contracts, cooperation agreements, consulting services, technology development and intellectual property arrangements, confidentiality agreements, and checks of tax/financial service contracts and tax/financial clauses in general commercial contracts.

## 3 Initial Release Scope

### 3.1 Confirmed Scope

| Dimension | Initial Release Requirement |
|---|---|
| Legal systems | Victoria and mainland China, selected by the user and reviewed independently each time |
| Australian law coverage | Victoria as the review scope, while identifying relevant federal law and necessary connections with other laws |
| Contract types | Commercial contracts including procurement, cooperation, consulting, technology development, confidentiality, intellectual property and tax/financial services |
| Tax/financial scope | Tax/financial service contracts and arrangements concerning taxes, invoices and tax-inclusive prices in commercial contracts |
| Review perspective | Represent a user-selected party or conduct a neutral review |
| Review dimensions | Compliance and validity, completeness and consistency, commercial risks, amendment suggestions and replacement clauses |
| Input language | Chinese, English and bilingual Chinese/English contracts |
| Output language | Chinese, English or bilingual Chinese/English, selected independently by the user |
| Interface language | Chinese or English, switched independently without changing the contract, report language or current review state |
| Input methods | DOCX, PDF with a text layer and pasted text |
| Supporting materials | Legislation, judgments, legal opinions and research notes; transaction materials such as attachments, email text, quotations and technical requirements |
| Review modes | Comprehensive review and focused review |
| Focus selection | Clause selection, risk-topic selection and free-text description, in combination |
| Research strategy | Layered research using public sources and user-supplied materials |
| Interaction | Multi-turn follow-up within the contract context |
| Amendments | Unified suggestion list with individual acceptance, rejection or adjustment |
| Output files | Review report in DOCX/PDF; contract DOCX with tracked changes |
| Data retention | Current session only, without login or a cloud history database |

### 3.2 Outside the Initial Release

- Comprehensive resolution of cross-border conflict-of-laws issues or parallel comparative review under both jurisdictions. Disclose scope limits when relevant connections arise.
- Scanned PDFs, contract photographs and OCR of user materials.
- Accounts, historical session recovery, team permissions, multi-user collaboration and matter management.
- Default integration using accounts, passwords or session cookies for Westlaw, Jade or other paid databases.
- Automatically sending contracts externally, negotiating, signing, filing or submitting legal documents on the user's behalf.
- Guarantees of complete contractual compliance or exhaustive case research, or unverified win rates and risk probabilities.
- Independent specialist tasks such as complete tax filing, tax calculation, financial auditing or full patent searches.

Scanned user contracts are unsupported; a candidate research component's OCR capability does not expand the input scope. Legacy .doc is not supported by default; users should be prompted to convert it to DOCX.

## 4 Core User Journey

1. Enter an OpenAI API key in the sidebar and select jurisdiction and output language.
2. Upload one main contract or paste its text; optionally upload multiple supporting materials and label their types.
3. The tool identifies contract type, parties, governing law, key dates and clause structure.
4. The user confirms or corrects extracted information and selects perspective and comprehensive/focused mode.
5. Clarify information gaps or legal-scope differences that affect the overall analysis first.
6. Start phased review with actual progress; conduct legal and case research based on identified risks.
7. View contract and risks side by side, select an issue to locate the original text, and expand authorities and suggestions.
8. Select a clause or risk for follow-up; the system continues research using the current contract, conversation and new facts.
9. Add new suggestions to the unified list; the user accepts, rejects or adjusts them individually.
10. Check conflicts and related effects among amendments, preview them, then export the report and revised contract.

Users can switch between results within the current session. Explicitly choosing “Clear current session” clears contracts, questions and answers, temporary indexes, amendment lists and key state under application control.

## 5 Functional Requirements

### F01 Material Import and Parsing

- Each review has one main contract and zero or more supporting materials. Contract attachments can be linked as supporting materials.
- Support DOCX, PDF with a text layer and pasted plain text; supporting materials use these formats in the initial release. Email text can be pasted or exported to a supported format; no direct mailbox connection is provided.
- Preserve paragraphs, clause numbers, headings, table contents and available original locations.
- DOCX uses paragraph/table positions as stable locations, without promising identical pagination in every Word environment; PDF uses file page numbers and text positions.
- Identify corresponding Chinese/English clauses; flag unreliable pairings for confirmation rather than forcing alignment.
- Distinguish main contract, attachment, legal authority, transaction background and research opinion roles; do not treat email statements as legal rules.
- For empty, encrypted, scanned, damaged or deployment-limit-exceeding files, explain the reason and practical remedies without silently truncating content.
- Determine file-size, total-text and attachment-count limits through deployment tests and display them before upload.

### F02 Information Confirmation and Review Settings

- Display identified contract type, parties, contractual governing law, key dates and information gaps, and allow user corrections.
- Let users select Victoria or mainland China, a represented party or neutrality, output language, and comprehensive or focused review.
- Focused review combines clause selection, topic selection and free text, and displays the resulting scope.
- If the selected jurisdiction differs from the contract's governing law, disclose the difference and obtain confirmation of the analysis scope before proceeding.
- A choice of court or arbitral institution is not automatically a choice of substantive governing law; extract them separately.
- Selecting Victoria does not exclude relevant federal law or limit research to Victorian courts.

### F03 Commercial Contract Review

General review covers parties and authority, definitions and document priority, subject matter and scope, price and payment, performance and acceptance, variations, liability and indemnities, confidentiality and data, intellectual property, term and termination, notices, governing law and dispute resolution, according to the contract's actual contents.

| Contract Category | Specialist Checks to Configure |
|---|---|
| Procurement | Specifications, quantity, delivery, acceptance, quality, payment and after-sales arrangements |
| Cooperation | Contributions, responsibilities, returns, decision-making, exit and joint outputs |
| Consulting | Service boundaries, deliverables, information dependencies, fees and use of outputs |
| Technology development | Requirements and variations, milestones, acceptance, source code, ownership of outputs and maintenance |
| Confidentiality | Information scope, exceptions, permitted disclosure, duration, return/destruction and liability |
| Intellectual property | Ownership, licence or assignment scope, use restrictions, third-party rights and post-termination treatment |
| Tax/financial | Service boundaries, information duties, tax allocation, pricing basis, invoicing and liability arrangements |

These topics are product checklists, not legal conclusions. Maintain separate legal rules and sources for each jurisdiction rather than mechanically translating another jurisdiction's rules.

Every report must distinguish four issue categories: legal compliance or validity, textual completeness or consistency, allocation of commercial interests, and other matters requiring verification. Do not equate “unfavourable” or “unclear” with “unlawful” or “invalid”.

Where specialist capability is not configured or the materials do not support a judgment, show the review gap explicitly. Comprehensive review means processing the full materials and related checks, not covering every potential legal, industry or tax/financial obligation.

### F04 Layered Legal Research and Verification

- Check principal authorities during the initial review and seek relevant cases for important legal risks.
- Conduct further research when follow-ups introduce new issues, legal application questions or changes in currency; verified materials may be reused with their dates stated.
- Research topics may arise from contract type, specific clauses, user concerns and identified risks.
- Search with issue summaries, necessary facts and de-identified keywords, avoiding transmission of the whole contract or irrelevant identity information to search services.
- Search summaries are for source discovery only; final legal conclusions must rest on text actually obtained or explicitly labelled excerpts.
- Record publisher, jurisdiction, document title, case name/citation or statutory location, text extracts, URL, retrieval time and verification status for important sources.
- Check the relevant time, version, commencement and transitional arrangements for legislation; do not simply substitute the latest version for the version applicable to the facts.
- Consider subsequent treatment, adverse views and factual differences in case research. Disclose separately when subsequent treatment cannot be checked.
- Record source existence, text retrieval, proposition support, scope and currency checks separately rather than replacing all checks with a single “verified” label.
- If no authority is found, retain the concern as requiring verification and explain research scope and gaps; never invent provisions, case names, paragraphs or links.
- Search unavailability, inaccessible text, no matching results and incomplete verification are different states and require separate messages.
- Preloaded or user-uploaded materials may supplement research, but must state origin, date and independent-check status; they cannot be presented as results of the current online search.

Design separate source hierarchies and case-analysis methods for mainland China and Victoria. Identify the type and reference value of mainland cases; assess Australian cases using court hierarchy, the legal issue and subsequent treatment, rather than replacing applicability analysis with a simple numeric ranking.

### F05 Risk Report

The report contains review scope, perspective, facts and assumptions, contract overview, coverage checklist, risk summary, itemised analysis, legal sources, matters requiring verification and next actions.

Each risk includes at least: identifier, original location and extract, issue category, risk level, recommended handling, reasoning, possible impact, legal basis and status, replacement text, related clauses and missing facts.

Risk levels are high/medium/low; handling recommendations use labels such as priority action, amendment recommended, note for attention and verification required. Assess these separately, and also distinguish severity from evidential sufficiency. An issue with potentially high impact but insufficient support may be presented as “potential high risk; conclusion requires verification”.

Combine issues spanning multiple clauses while retaining their relationships and avoiding duplicate counts. The initial release does not use uncalibrated overall contract-safety scores, legal-accuracy rates or probabilities.

### F06 Multi-turn Clause Follow-up

- Users can enter a conversation from a risk item or contract clause, or type a question directly.
- Each answer combines the current contract version, review perspective, relevant clauses, confirmed facts, earlier questions and answers, and valid sources.
- Automatically read related clauses when a question concerns other parts of the contract; do not interpret a selected paragraph in isolation.
- Label new user statements as user-supplied facts, separate from original text, inferences and confirmed facts.
- Answers include a direct response, contractual basis, legal basis and applicability analysis, and amendment or verification directions.
- Replacement clauses proposed in conversation can enter the unified amendment list, retaining their originating question and authorities.
- When new facts undermine earlier analysis, mark affected conclusions and suggestions for updating rather than silently retaining them.
- Maintain long-conversation context through structured fact records and summaries; summaries must not replace original contract text or quoted source text.

### F07 Insufficient Information and Conflicting Materials

Handle information gaps according to their effect: ask first about key information affecting the whole review; flag gaps affecting individual clauses in the report and limit the corresponding conclusions.

List material conflicts separately, showing both original texts, source locations, the conflict, possible effects and questions to confirm. For example, differing IP ownership statements in a contract and an email do not automatically establish priority for either document.

Affected judgments and amendments require user confirmation of facts or research assumptions for key conflicts; unaffected analysis may proceed. Confirming facts does not confirm a document's superior legal effect, which still requires separate analysis. Unresolved conflicts remain subject to verification, without definitive conclusions.

### F08 Unified Amendment List

- Manage initial-review and follow-up suggestions together, retaining origin and version.
- Show original text, replacement, reasons, authorities, effects and related amendments for each item.
- Users may accept, reject, edit or defer; only accepted items enter the revised contract.
- Mark replacement relationships when a new suggestion supersedes an old one; do not overwrite user-edited text.
- Prompt users to resolve mutually exclusive suggestions for the same text or effects on definitions, numbering and cross-references.
- Require reconfirmation before final export when new facts affect accepted suggestions.
- Clearly identify user-edited text and do not label it legally verified without review.
- Before export, show acceptance counts, unresolved conflicts and an amendment preview; unresolved amendment conflicts prevent the affected changes from being written.

### F09 Bilingual Processing

- Configure contract language, jurisdiction and output language independently.
- Support Chinese, English and bilingual reports and answers; retain legal quotations in their original language and distinguish translations.
- Check bilingual contracts for consistency of rights and obligations, amounts, periods, conditions, terminology and language-priority clauses.
- Replacement text follows the corresponding contract clause's language by default. Corresponding changes in a bilingual contract must be displayed and selected as pairs.
- Selecting a bilingual report for a monolingual contract does not automatically create a full bilingual contract; translations may appear in the report but are not inserted as new agreed text.

### F10 Export and Format Preservation

- Review reports support DOCX and PDF, containing selected language, risks, authorities, source status, limitations and an amendment-list snapshot.
- Revised contracts use DOCX with Word-recognised insertion/deletion revisions, not simulated changes using colour or strikethrough.
- Preserve DOCX headings, numbering, tables, headers, footers and other original layout as far as possible; locate amendments in the correct original text.
- PDF and pasted text require reconstructed Word layout, disclosed before export.
- Check cross-references after clause additions/deletions or numbering changes; flag manual handling where reliable updates are impossible.
- For existing revisions, complex tables, text boxes, embedded objects or imprecisely located passages, explain specific limitations first and prohibit misplaced edits or silent content loss.
- If tracked-change export cannot be completed reliably, a separate amendment list may be provided, but that run does not satisfy revised-contract acceptance criteria.
- Acceptance checks must confirm files open normally, revisions can be accepted/rejected, accepted results are correct and layout is readable.

## 6 Page and Interaction Design

### 6.1 Page Structure

Prioritise desktop browsers for the initial release. Use two main states: pre-review confirmation and the review workbench.

| Area | Content |
|---|---|
| Left settings sidebar | API Credentials module, jurisdiction, language, perspective, mode, material management and clear session |
| Pre-review main area | Upload/paste, supporting-material classification, extracted-information confirmation, focus settings and start button |
| Workbench left area | Original contract, contents, keyword search, selected clause and risk location |
| Workbench right area | Switchable risk list, clause follow-up and amendment suggestions |
| Top status area | Current contract, review scope, execution stage, completion and failure status |
| Export entry | Report download, amendment preview and revised-contract download |

Selecting a risk locates the original text on the left; selecting a clause enables follow-up. Clicking a legal citation opens source details, including extract, location, link, verification status and date. Narrow screens use a vertical layout or switchable views with the same interaction logic.

The initial release is session-only and must not display misleading entries such as “Historical projects” or “Permanently saved”.

### 6.2 Visual Direction

Provide independent Chinese/English switching across menus, buttons, settings, confirmation forms, workbench labels and status messages. Configure interface and report/answer languages separately; changing the interface does not call the model, discard the contract or amendment selections, or automatically translate existing legal analysis.

- Draw on Mike's document-review and conversation workflow while retaining Juriscloud's light sky blue, clouds and breathing loading animation.
- Use light sky-blue backgrounds, white documents/cards, dark blue-grey text and blue primary actions. Suggested starting tokens: background #F5F9FF, border #D9E7F7, dark text #17365F; refine through readability checks.
- Use cloud emoji for welcome, empty states and execution messages without taking space from body-text reading.
- Use gentle cloud breathing and content fades while respecting reduced-motion settings and providing an animation-off option.
- Express high/medium/low risks with text, icons and colour together, not colour alone.
- Show verifiable steps, research status and results; do not expose hidden model reasoning or fabricate research progress.

## 7 AI Workflow and Program Control

### 7.1 Initial Comprehensive Review

Use six model calls with distinct tasks and structured outputs. The steps below are the implementation plan; specific prompts and model choices require development validation.

| Call | Input and Task | Output Passed to the Next Step |
|---|---|---|
| 1 Understand materials | Contract, background and user settings; extract structure and identify gaps/conflicts | Contract map, fact record and gap/conflict list |
| 2 Plan review | User-confirmed information; identify four-dimensional risk candidates and research needs | Review coverage table, issues and research plan |
| 3 Organise authorities | Source text retrieved by the program; extract rules, relevance and applicability limits | Source evidence pack, supporting/adverse authorities and incomplete checks |
| 4 Apply and amend | Original contract, facts and evidence pack; analyse risks and draft replacements | Risks, clause suggestions and related effects |
| 5 Independent review | Draft and original evidence; check citation support, scope, contrary views and amendment conflicts | Defect list and correction requirements |
| 6 Correct and report | Prior results and review comments; correct or qualify unreliable conclusions | Structured final report, verification items and amendment list |

If confirmation is needed after call 1, pause and resume the same workflow after confirmation without repeating completed calls. Long contracts may require additional calls by section, with a whole-document coverage checklist and cross-clause checks.

Web searches, source-text retrieval and file parsing do not count as independent AI calls. Asking a model to write six steps inside one request does not count as six calls.

### 7.2 Follow-up Analysis

Organise substantive follow-ups into five independent calls: understand the issue and gaps, generate a research plan, read actual retrieved materials, analyse and propose suggestions, and review/correct the answer. Interface operations such as export, display-language switching or amendment selection do not mechanically trigger five calls.

Record actual call counts and stages. Parameter-validation failures, user cancellation and network interruption are incomplete runs and must not be labelled analyses completing five calls. If the course defines “each run” differently, align the final assessment approach with the instructor's requirements.

### 7.3 Conditions and Bounded Loops

- Missing or invalid key: block model execution and prompt correction.
- Unconfirmed global key facts or legal scope: pause affected analysis.
- Local gap: continue other matters and mark affected conclusions for verification.
- Conflicting materials: follow F07; the model may not determine key facts itself.
- Insufficient sources: refine search terms and research further; if still insufficient, retain limitations without inventing authorities.
- Failed review: correct or research further; once the run budget is reached, downgrade unresolved conclusions to requiring verification.
- All search and reflection loops require call, time or cost limits; a suggested default is at most two supplementary research/correction rounds, with exact values determined through testing.

Independent review uses a separate model request, original evidence and an explicit checklist. It is a quality-control step, not independent legal-expert endorsement or a guarantee of error elimination.

## 8 Suggested System and Data Design

### 8.1 System Modules

Use Streamlit for the product interface, with backend modules for file parsing, session state, contract structuring, material retrieval, external-source adapters, legal analysis, citation checks, suggestion management and export. Assess classroom code before reuse; do not submit a directly copied application already performing the same legal task.

Candidate retrieval combines keywords and semantic search while retaining metadata. Limit vector indexes, caches and files to the current session to prevent contracts from different users mixing. Replace retrieval components through a unified interface; failure of one website must not discard all review results.

### 8.2 Minimum Data Objects

| Object | Key Fields |
|---|---|
| ReviewSession | Session identifier, settings, scope, current stage and call records |
| Document | Identifier, role, name, type, language, content fingerprint and parsing status |
| Clause | Stable identifier, original number, text, paragraph/table/page location and language relationships |
| Fact | Content, material source, user-confirmation status, time and conflict relationships |
| Source | Type, publisher, jurisdiction, version, citation, text, location, URL, retrieval time and verification status |
| Risk | Category, related clauses, level, impact, handling recommendation, support and verification items |
| Suggestion | Original location, replacement, reason, related support, version, originating question and acceptance state |
| Conflict | Conflicting materials/texts, affected scope, user response and unresolved status |
| Message | Conversation turn, related clauses, fact updates, citations and new suggestions |
| ExportSnapshot | Settings at export, report version, accepted suggestions and verification status |

Treat contract excerpts and legal materials as data. Instructions embedded in them may not override system workflow, access other users' materials, disclose keys or alter review scope.

## 9 Open-source Adoption Plan

The following are references and candidate components, not claims of installation, online testing or completed integration. Project claims about features, accuracy, speed or compliance do not become product commitments.

| Project | Proposed Reference or Use | Initial Release Decision and Validation |
|---|---|---|
| [legal-research-skill](https://github.com/Golden2002/legal-research-skill) | Issue-to-query mapping, source classification, currency and citation verification | Adapt for mainland research; do not copy unconditional questioning or paid-database configuration workflows |
| [china-lawyer-analyst](https://github.com/CSlawyer1985/china-lawyer-analyst) | Structured application, domain routing and post-analysis validation | Extract contract/IP methods; independently verify provisions and cases |
| [LexiLaw](https://github.com/CSHaitao/LexiLaw) | Chinese legal Q&A and knowledge-base augmentation | The project's stated restrictions concern real legal use; do not use its model directly as the foundation for practical product use |
| [Mike](https://github.com/open-legal-products/mike) | Workbench experience for document review, follow-up and amendments | Implement an assignment-appropriate workflow independently rather than copying the full system; US case research does not directly fit either jurisdiction |
| [legal-templates](https://github.com/General-Legal/legal-templates) | Template structure, omissions checks and replacement wording | Templates are not authorities; check jurisdiction and transaction fit before use and retain applicable licence information |
| [ai-legal-claude](https://github.com/zubair-trabzada/ai-legal-claude) | Risk ordering, missing clauses and alternative wording | Do not adopt unverified promises about speed, amounts, accuracy or safety scores |
| [AustralianLegal](https://github.com/gordoncprice/AustralianLegal) | Jurisdiction identification, official-source planning, legal currency and independent review | Use as an Australian research-method reference, not a ready-made search engine; supplement commercial-contract rules |
| [auslaw-mcp](https://github.com/tealou/auslaw-mcp) | AustLII search, full-text retrieval and paragraph/citation locations | Candidate component; verify availability, source-access conditions, deployment compatibility and citation output |

### 9.1 Specific Constraints for Australian Components

- AustralianLegal is an instruction-based research workflow package without complete built-in online search. Use its jurisdiction/source methods within the confirmed product scope.
- auslaw-mcp is a TypeScript MCP service requiring adapter and runtime validation with Python Streamlit; adding it to the repository does not make it immediately usable.
- Its court-weight ranking is an engineering ordering, not a direct determination of binding authority on a Victorian issue.
- Parsing a citation, finding a link or locating a paragraph does not establish that a judgment supports a proposition, remains good law or applies to the contract.
- Assess public research routes first; do not make a route requiring user-supplied Jade session cookies an initial-release dependency.
- Official legislation and court text need independent source adapters; candidate-component coverage cannot replace all official checks.

### 9.2 Checks Before Adoption

Pin versions or commits and record referenced files, adaptations and licences. Mike identifies AGPL-3.0 and the template library CC0; other content depends on the specific version and subdirectory licence. Check dependencies, logging, external data transmission and access requirements before adopting code.

Only project descriptions and selected key files have been read so far. The first development milestone must execute representative searches, text retrieval and citation checks before marking a candidate component verified.

## 10 Data and Operational Requirements

- Users supply their own OpenAI key through the assignment-specified API Credentials sidebar module; no developer-funded key is embedded.
- Keys must not enter the repository, reports, logs, download packages or shared caches. Sensitive state is limited to the current user's session.
- Do not persist contracts or conversation history; explicitly clean temporary files and indexes rather than relying solely on browser-close events.
- Do not promise immediate deletion of all external data on browser closure. Model and research services may receive necessary content; explain actual data paths and third-party processing in the interface.
- Default logs record stages, duration, error categories and call counts, not contract text or secrets.
- Isolate originals, indexes, conversations and exports by session; shared caches may contain only public legal materials without user secrets.
- Show actual stages, timeouts and retryable errors; do not require indefinite waiting or repeating all completed work from the beginning.
- Where cost information is available, show actual obtainable usage or clearly labelled estimates; do not promise fixed cost or duration before testing.
- Support keyboard operation, visible focus, text contrast and reduced motion; decorative content must not obscure document reading.

## 11 Acceptance Criteria

| ID | Acceptance Condition |
|---|---|
| A01 | DOCX, text PDF and pasted text reach confirmation; unsupported inputs such as scans receive clear messages |
| A02 | Users can correct contract type, parties, agreed law, perspective and review scope |
| A03 | Differences between selected jurisdiction and contractual law are disclosed; affected formal analysis is withheld until confirmation |
| A04 | Every agreed commercial-contract category has visible general/specialist coverage status without concealed gaps |
| A05 | Reports distinguish four issue categories and show level, handling recommendation, reasoning and original location for each |
| A06 | A completed initial review has at least six independent model calls; substantive follow-ups follow at least five calls, with actual records |
| A07 | Reports link back to actual sources and paragraphs; unknown/insufficient support is marked for verification without fabricated citations |
| A08 | Key material conflicts are listed separately, with affected judgments made after user confirmation; other analysis can continue |
| A09 | Multi-turn follow-ups inherit the current contract and perspective; new facts cause affected earlier suggestions to be rechecked |
| A10 | Initial/follow-up suggestions are managed together; acceptance/rejection/editing works correctly and conflicting changes are not written together |
| A11 | Chinese, English and bilingual output are selectable; meaning differences in bilingual contracts are located and explained |
| A12 | Report DOCX/PDF files open normally; revised DOCX contains genuine revisions with correct individual acceptance/rejection results |
| A13 | Unaccepted suggestions are excluded from the revised contract; DOCX format preservation is visually checked and limits clearly displayed |
| A14 | Desktop side-by-side and narrow-screen switching work; cloud animation can be reduced or disabled and risk is not expressed by colour alone |
| A15 | Clearing the session makes its files, questions/answers and key state inaccessible through the app; sessions do not mix |
| A16 | The Streamlit Cloud URL works and the instructor can complete the submission tests using their own key |

Fluent answers alone do not establish a pass. Key checks include fact extraction, source existence and support, coverage, amendment placement and honest presentation of failures.

## 12 Three Submission Test Cases

The following are proposed fictional tests. Actual contracts, supporting materials and human-check sheets must accompany the repository. Describing a plan does not mean testing is complete.

### T01 Comprehensive Review of a Mainland-China Procurement Contract

Materials: Chinese procurement contract DOCX and quotation PDF. The user represents the buyer and selects Chinese output and comprehensive review. The contract includes payment, delivery, acceptance, quality and tax arrangements, with seeded issues such as ambiguous acceptance timing and conflicting attachment pricing bases.

Expected: identify the transaction/key clauses, distinguish commercial disadvantage from legal concerns, list the pricing conflict separately and request confirmation of key facts. After confirmation, complete research with traceable authorities. Export report and revised Word after partial acceptance, excluding unaccepted suggestions.

### T02 Focused Review and Follow-up on a Victorian Technology Development Contract

Materials: English technology development DOCX, technical requirements and text-readable email contents. The user represents the commissioning party, selects Victoria, focuses on ownership of outputs, acceptance and payment, and requests bilingual output.

Expected: link contract and background materials explicitly; include relevant federal and Victorian law rather than relying only on a vic filter. Read related definitions when the user asks about a liability clause and add new suggestions to the unified list. Simulate a new suggestion replacing an earlier one and verify reconfirmation and export placement.

### T03 Boundaries and Failure Handling for a Bilingual Cooperation Contract

Materials: bilingual Chinese/English cooperation contract in text PDF, containing confidentiality, IP and tax clauses, with a period or liability differing between language versions. The user selects mainland China and neutral review, while the contract chooses another governing law; an older user-supplied research document is also provided.

Expected: disclose the legal-scope difference and continue after confirmation; identify bilingual differences without automatically prioritising one text. Check the older material's currency. Use a repeatable test switch to simulate research timeout or unavailable text, displaying insufficient support and verification items without fabricated cases; never describe simulated status as genuine online success. Explain PDF-to-Word reconstruction limits.

Each case provides steps, inputs, human-annotated issues, expected behaviour and actual execution records. Call counts for initial research and follow-up must be inspectable. Live results may vary, so acceptance rests on verifiable behaviour and sources rather than exact matches to fixed answers.

## 13 Development and Delivery Sequence

| Phase | Deliverables | Condition for the Next Phase |
|---|---|---|
| 1 Technical validation | Confirm credential-module location, test candidate Australian research, check source availability in both jurisdictions and create a genuine Word revision sample | Critical deployment dependencies and export path are clear |
| 2 Core workflow | Import, information confirmation, six calls, structured risks and citations | One representative case completes end to end |
| 3 Research and interaction | Layered research, multi-turn follow-up, conflicting materials and unified amendment list | Sources/status propagate correctly without overwriting suggestions |
| 4 Files and interface | Side-by-side workbench, light-blue cloud visuals, bilingual support, report and revision exports | File and interaction acceptance checks pass |
| 5 Deployment and evaluation | Streamlit Cloud, three test cases, README and execution records | Instructor can independently access and run the app |

Starting with a representative category is a development sequence, not authority to remove other confirmed contract categories. If deployment resources or component validation cannot support the full scope, identify specific effects and let the user decide adjustments rather than silently downgrading scope.

## 14 Assignment Mapping and Submission Checklist

Based on the user-supplied “LAWS90286 - 2026 - A2 - Student Copy.docx”.

| Assignment Requirement | Product Mapping |
|---|---|
| One defined legal task | Commercial contract review, with research and Q&A as subprocesses |
| More than three independent steps | Material understanding, research, application, review, amendment and output |
| At least five AI calls per run | Six initially and five for substantive follow-up, with actual call records |
| User input | Contract, supporting materials, settings, questions and amendment choices |
| User output | Web report, conversation, authorities, amendment list and document downloads |
| Streamlit Cloud deployment | Runs at an accessible application URL |
| Specified credentials sidebar | Users supply their own OpenAI key |
| GitHub repository and README | App link, three cases, steps and test materials |

Required before submission:

- README states operation, dependencies, app URL, scope and three test cases.
- Include all fictional materials needed for the submission cases and their instructions.
- Give the instructor repository access; the app must not depend on the developer's personal paid key.
- Retain external-project reference records, licences and independent-implementation explanations.
- Check that repository and history contain no keys or real sensitive contracts.
- Record the final submission version and time. The assignment states that subsequent repository changes may change the effective submission date; do not continue changing code in the submitted repository after submission.

## 15 Implementation Items Requiring Validation

These do not change the confirmed product direction, but their outcomes must not be promised before validation:

1. The assignment-specified module link is https://github.com/stoneman-mls/openai_credentials . Earlier access returned 404; check classroom code or an updated address rather than assuming a normal input field is an acceptable substitute.
2. Actual online search, text retrieval, citation output and Streamlit Cloud execution for auslaw-mcp.
3. Programmatic access conditions, availability and text coverage of mainland-China public sources; verification of user-supplied materials.
4. Human validation of specialist commercial-contract checklists and maintenance of legal sources in both jurisdictions.
5. Preservation and export compatibility for complex DOCX, bilingual tables and existing revisions.
6. Establish file limits, run budgets, models, timeouts and performance targets after testing, without promising accuracy or fixed speed beforehand.
7. Leave future adapter points for Westlaw and other paid databases, subject to API, institutional-licence and model-transmission permissions.
8. The formal product name remains undecided; this does not block initial development.

## 16 Future Extensions

After completing the initial release and assessing real feedback, consider accounts/history, project import/export, OCR, additional contracts and industry rules, authorised paid sources, version comparison, collaboration and a Word add-in. New capabilities must not be assumed to exist in the initial release.


## 2026-10-29 Completeness Implementation Supplement
Add topic batches (six items per batch) and an independent omissions review to the original minimum-six-call initial workflow. Ten general topics are supplemented by procurement, cooperation, consulting services, development, confidentiality, IP, tax/financial services or employment checklists according to classification; unknown types explicitly receive general checks only. Current employment/procurement examples each use ten structured requests plus separate search requests. Preserve each item's status, reasoning, verifiable quotations and next actions independently so they do not disappear when the main risk table contains fewer items; insufficient and unrecorded passages must be shown. The checklist includes model judgments and claims neither exhaustive legal coverage nor expert verification; legal quality and actual model omission rates still require real-case evaluation.
