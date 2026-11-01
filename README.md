# ☁️ Juriscloud

A Streamlit agent for reviewing commercial contracts and researching related cases in a continuing conversation. Choose **Victoria, Australia** or **mainland China** independently. The interface defaults to English and can be switched to Chinese; answer language and review perspective are separate settings.

**Deployment URL: pending — this repository is not yet a deployed app.** See [deployment instructions](docs/DEPLOYMENT.md) and the [assignment checklist](docs/ASSIGNMENT_CHECKLIST.md) before submission.

## What the agent does

1. Accepts a DOCX, text-based PDF or pasted contract, supporting materials and a question.
2. Identifies the contract and builds a general plus contract-specific coverage checklist.
3. Reviews checklist topics, researches legal sources and checks quotations against retrieved text.
4. Independently challenges the draft and checks omissions before producing a risk table and coverage record.
5. Answers follow-ups about a clause, related cases or an earlier answer using the contract and conversation context. A follow-up uses five structured AI calls: plan, evidence, draft answer, critique and final answer. Initial reviews also exceed five calls; the count varies with the checklist, with additional search requests.

Each successful analysis run therefore has at least five AI calls. Validation or provider failures can stop a run before completion. The visible Activity panel shows execution status and source checks, not private model reasoning.

For mainland-China case requests, optional PKULAW MCP research runs first. Incomplete evidence triggers public-source research. Victoria uses public sources. Case links are displayed when a source returns a valid URL; the agent must not invent a link. Research currently requires an uploaded or pasted contract; there is no independent case-search mode.

The workbench supports multi-turn questions, copying answers, a unified amendment list, Word/PDF reports and supported Word tracked changes. Suggested amendments require user selection before insertion into a revised contract. The product does not contain static assignment demonstration answers.

## Run locally

Use Python 3.11 or 3.12 (development tests used 3.12).

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
streamlit run app.py
```

Open **Get started → Settings → Model & connection**, enter your own model API key and test the connection. The analysis model needs Responses structured output; the search model also needs `web_search`. The two model dropdowns contain `gpt-6-luna` and `gpt-6.1-sol`, as requested for this project. Your endpoint and account must actually provide these models. A successful models-list request is not a full analysis test. A compatible alternative endpoint can be configured by the deployment administrator through `OPENAI_BASE_URL`; never commit credentials.

Choose interface language, answer language, jurisdiction and your perspective in Settings. Changing interface language does not translate the original contract. Attach the contract with **+**, enter a question and send. After a report, use the compact input at the bottom to continue the conversation.

Without a model key, the app allows input preparation but does not generate simulated answers. Contracts and keys remain in the current app session; there is no account or cloud conversation-history database. Contracts and necessary research excerpts are sent to the model provider. Only authorised materials should be uploaded.

## Three live test cases and evidence

The [English live-test report](evaluation/english-live-tests-2026-11-01/README.md) records three real sequential runs completed on **1 November 2026**, with expected results, observed answers and limitations:

| Test | Input / prompt | Evidence and outcome |
|---|---|---|
| TC01 | Upload a Chinese used-car contract; ask for a comprehensive English review | Fourteen contract issues and ten coverage checks; real upload, question and report screenshots |
| TC02 | Ask for cases concerning refund deadlines, expenses and return arrangements | Focused case answer; observed PKULAW-first activity and public-source follow-up |
| TC03 | Ask whether courts generally order return of both vehicle and price | Direct, qualified answer retaining the contract context rather than repeating the initial table |

Download the [English Word report with screenshots](evaluation/english-live-tests-2026-11-01/Juriscloud%20Live%20English%20Functional%20Tests.docx). [Prompts](evaluation/english-live-tests-2026-11-01/prompts.json), [selected answer text](evaluation/english-live-tests-2026-11-01/actual-responses.md), observations and nine original screenshots are included. Selected text records are not complete verbatim transcripts.

**Input artifact outstanding:** the exact filled used-car contract used in these screenshots must still be supplied. The locally available same-named file is a different employment agreement, so it has deliberately not been substituted. The synthetic [examples](examples/) are runnable supplementary fixtures, not the inputs for those live screenshots.

Functional execution is not a legal-accuracy certification. TC01 recorded quotation matches of 0/0; TC02 recorded 5/6; TC03 could not reverify an earlier case from its current evidence set. Some Activity labels remained Chinese under English UI. Full judgments, subsequent treatment and current law were not independently verified. The live evidence predates the final case-link presentation update; fixture tests cover that update.

## Automated verification

```bash
python -m pip install pytest
python -m pytest -q
```

The current source has **133 passing local tests**. These cover parsing, workflow calls, follow-up relevance guards, coverage, source handling, PKULAW integration with simulated transport, exports, UI helpers and credential isolation. Test doubles do not prove legal correctness or live-provider availability. `evaluation/benchmark_latency.py` uses simulated I/O and is not a real-provider speed benchmark.

## Optional PKULAW configuration

The backend reads `PKULAW_TOKEN` from the environment, otherwise `.streamlit/pkulaw.local.json`. Both credentials and the local file are excluded from this repository. The local administrator setup can save a backend token; session-only entry is also supported when no backend token exists. Configure the cloud token privately through deployment secrets; never put it in code or a screenshot.

The connection check initialises the two services and lists tools without performing paid case research. Actual searches need a valid subscription and quota. Returned excerpts can be incomplete and do not establish complete judgment access. Retrieved material is sent to the analysis model. PKULAW is optional; a failed connection is reported and public-source research remains available.

## Limits

- Text PDF and DOCX only; no OCR, encrypted PDF, legacy `.doc`, existing tracked revisions or embedded-object documents. Single-file limit: 8 MB; combined extracted-text limits are enforced.
- Checklist coverage and a second AI review reduce omissions but cannot guarantee completeness.
- Source quotation matching checks text correspondence, not legal applicability, currency or correctness. At most five public sources are read per research step; long sources use relevant excerpts.
- Follow-ups retain conversational and contract context, but do not automatically rebuild the initial coverage checklist or preserve every earlier research source. Re-run full review for a new comprehensive assessment.
- Complex Word structures may prevent a particular tracked amendment. PDF/text contracts are reconstructed for Word export; unsupported additions remain suggestions.
- Session data and generated-file links can be lost on restart. Export work before ending the session.

## Repository map

- `app.py`, `legal_agent/`: Streamlit application and agent workflow.
- `assets/`: bilingual frontend, animation, upload, export and copy components; bundled font license included.
- `tests/`: reproducible automated tests and explicitly labelled fixtures.
- `examples/`, `scripts/make_samples.py`: synthetic supplementary inputs.
- `evaluation/english-live-tests-2026-11-01/`: final live English test report and screenshots.
- `PRD.md`, `DESIGN.md`, `THIRD_PARTY.md`: product/design records and external references. Historical plans are not claims that every proposed feature was implemented.
- `docs/`: deployment and submission checklist.

## Assignment-specific outstanding requirements

The specified API Credentials module at `https://github.com/stoneman-mls/openai_credentials` returned 404 during preparation. The current custom Settings/sidebar credential input is temporary and is **not claimed to satisfy the specified-module requirement**. Obtain the correct module or instructor confirmation before submission.

The repository remains private. Teacher access has not been granted because the teacher's GitHub username is unavailable. A real Streamlit Cloud URL must be added after successful deployment. Do not alter the submitted repository after the formal submission date unless permitted by the instructor.
