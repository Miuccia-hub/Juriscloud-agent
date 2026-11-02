# ☁️ Juriscloud

Juriscloud is a Streamlit AI agent for commercial contract review and clause-based legal research. It accepts a contract and a question, produces a structured review, and supports follow-up questions within the same conversation. The two supported jurisdictions are mainland China and Victoria, Australia.

**Live application:** [juriscloud-agent.streamlit.app](https://juriscloud-agent.streamlit.app/)

The interface defaults to English, with a Chinese option. New sessions default to mainland China and enable PKULAW research; both settings can be changed. Interface language, answer language and review perspective are configured independently.

## Agent workflow

1. **Read the materials.** Accept a DOCX, text-based PDF or pasted contract, optional supporting documents and the user's question.
2. **Plan the review.** Identify the contract type and prepare a general and contract-specific coverage checklist.
3. **Analyse the contract.** Examine legal effect, drafting consistency, commercial risks, missing terms and facts requiring confirmation. Research relevant legal sources and compare quotations with retrieved text.
4. **Check the draft.** Conduct a separate critique and omission check before presenting a risk table, recommendations and a coverage record.
5. **Continue the conversation.** Answer questions about a clause, an identified risk or related cases using the contract and prior conversation. A follow-up comprises five structured AI calls: planning, evidence, draft answer, critique and final answer. The initial review also exceeds five calls, with the precise number determined by the checklist and research needs.

The Activity panel displays the execution stages and source checks. Case research concerning mainland China uses PKULAW MCP first when enabled and falls back to public sources if the available evidence is insufficient. Victorian research uses public sources. A case link appears only when the retrieved source supplies a valid URL. Research currently requires an uploaded or pasted contract.

The workbench also supports answer copying, a consolidated amendment list, Word/PDF report export and tracked changes for supported Word documents. Suggested amendments are selected before insertion into a revised contract.

## Using the application

1. Open the [live application](https://juriscloud-agent.streamlit.app/) and select **Get started**.
2. In **Settings**, select the jurisdiction, interface and answer languages, and review perspective. Under **Model & connection**, enter a model API key and run the connection check.
3. Use **+** to attach the contract and any supporting materials, enter a question, and send it for review.
4. Read the risk table and source information. Use the compact input below the answer for a follow-up question or related-case request, or export the report.

The model options are `gpt-6-luna` and `gpt-6.1-sol`; availability depends on the configured endpoint and account. Analysis requires Responses structured output, and public-source research requires `web_search`. The interface language does not alter the uploaded contract. Session data and generated-file links may be lost when the application restarts, so reports should be exported during the session.

## Three live test cases

The [English evaluation record](evaluation/english-live-tests-2026-11-01/README.md) documents three sequential runs completed on **1 November 2026**. It contains the prompts, observed outputs, limitations and nine screenshots of the running application.

| Test | Task | Observed result |
|---|---|---|
| TC01 | Upload a Chinese used-vehicle contract and request a comprehensive review in English. | Fourteen contract issues and ten coverage checks; screenshots record the upload, question and report. |
| TC02 | Request related cases on refund deadlines, expenses and vehicle-return arrangements. | A focused case-research answer, with PKULAW-first activity and subsequent public-source research. |
| TC03 | Ask whether courts generally require both the vehicle and the price to be returned. | A qualified answer addressing the new question in the context of the earlier contract review. |

The tests used the [original Chinese contract](evaluation/english-live-tests-2026-11-01/inputs/test%20contract.docx). An [English version](evaluation/english-live-tests-2026-11-01/inputs/Used%20Vehicle%20Sale%20and%20Purchase%20Agreement%20English.docx) is supplied as a reading aid; it was not the input for these recorded runs. The [input provenance note](evaluation/english-live-tests-2026-11-01/inputs/README.md) describes the files. The [Word evaluation report](evaluation/english-live-tests-2026-11-01/Juriscloud%20Live%20English%20Functional%20Tests.docx), [prompts](evaluation/english-live-tests-2026-11-01/prompts.json), [selected answer text](evaluation/english-live-tests-2026-11-01/actual-responses.md) and original screenshots provide the supporting evidence. The selected answer text is not a complete verbatim transcript.

These runs demonstrate functional execution, not legal accuracy. TC01 recorded quotation matches of 0/0; TC02 recorded 5/6; TC03 could not reverify an earlier case from its available evidence. Full judgments, subsequent treatment and current law were not independently verified. Some Activity labels remained Chinese under the English interface.

## Local setup and automated tests

Python 3.11 or 3.12 is supported; development tests used Python 3.12.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
streamlit run app.py
```

The model API key is entered in **Settings → Model & connection**. A compatible alternative endpoint can be configured with `OPENAI_BASE_URL`. Credentials are excluded from the repository.

```bash
python -m pip install pytest
python -m pytest -q
```

**133 local tests pass.** They cover document parsing, workflow calls, follow-up relevance, coverage checks, source handling, PKULAW integration with simulated transport, exports, UI helpers and credential isolation. Simulated transport does not establish live-provider availability or legal correctness. `evaluation/benchmark_latency.py` uses simulated I/O and does not measure live-provider latency.

## PKULAW configuration

The backend reads `PKULAW_TOKEN` from the environment and otherwise from `.streamlit/pkulaw.local.json`. The local token file and credential values are excluded from the repository. Streamlit Cloud uses a private application secret. A session-only token can be entered when no backend token is configured.

The connection check authenticates the case and legislation services and lists their available tools without conducting a paid search. Live searches require an active subscription and available quota. Retrieved excerpts may be incomplete and are sent to the analysis model. Public-source research remains available if PKULAW research fails.

## Scope and verification limits

- DOCX, text-based PDF and plain text are supported. OCR, encrypted PDFs, legacy `.doc` files, existing tracked revisions and embedded-object documents are unsupported. The single-file upload limit is 8 MB, with additional combined extracted-text limits.
- The coverage checklist and independent critique reduce omissions but do not guarantee completeness.
- Quotation matching establishes textual correspondence, not legal applicability, currency or correctness. Public research reads at most five sources per step, using relevant excerpts from long sources.
- Follow-ups retain the contract and conversation context but do not automatically rebuild the original coverage checklist or retain every earlier research source. A new comprehensive assessment requires another full review.
- Some complex Word structures cannot accept a tracked amendment. PDF and text inputs are reconstructed for Word export; unsupported amendments remain recommendations.
- The public Streamlit Cloud homepage, workbench, settings and English/Chinese interface switching were checked. On 2 November 2026, the configured PKULAW case and legislation services passed authentication and tool-list checks without a search. Live cloud model analysis, report export and actual PKULAW research have not yet been verified.

## Repository contents

- `app.py`, `legal_agent/`: Streamlit application and agent workflow.
- `assets/`: interface components, styling, animation, upload, export and copying.
- `tests/`: automated tests and labelled fixtures.
- `examples/`, `scripts/make_samples.py`: supplementary synthetic inputs.
- `evaluation/english-live-tests-2026-11-01/`: live evaluation record, inputs and screenshots.
- `PRD.md`, `DESIGN.md`, `THIRD_PARTY.md`: product and design documentation and external references.
- `docs/DEPLOYMENT.md`, `docs/ASSIGNMENT_CHECKLIST.md`: deployment details and assessment status.
