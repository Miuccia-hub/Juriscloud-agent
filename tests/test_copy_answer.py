"""Answer-copy integration using fictional answers, with no clipboard/model access."""
from pathlib import Path
from legal_agent.models import Report
from legal_agent.presentation import report_copy_text
from legal_agent.i18n import translate
from tests.fixture_data import load_demo
from tests.ui_helpers import workspace_app


def test_copy_text_preserves_findings_citations_and_limits_for_one_answer():
    _, _, _, report, _ = load_demo()
    text = report_copy_text(report, lambda value: translate(value, 'English'))
    assert text.startswith(report.summary)
    for risk in report.risks:
        assert risk.explanation in text and risk.action in text and risk.impact in text
        assert all(anchor in text for anchor in risk.clause_ids + risk.source_ids)
    assert all(value in text for value in report.limitations)
    answer = Report(summary='Only this follow-up: quotation “text” and 中文.',
        coverage=[], assumptions=[], risks=[], suggestions=[],
        next_steps=['Obtain the missing policy.'], limitations=['No live research performed.'])
    copied = report_copy_text(answer)
    assert answer.summary in copied and answer.next_steps[0] in copied
    assert report.summary not in copied


def test_initial_and_followup_have_independent_copy_actions_and_localised_feedback(monkeypatch):
    import legal_agent.interactions as interactions
    copied = []
    monkeypatch.setattr(interactions, 'copy_answer', lambda text, language, key: copied.append((text, language, key)))
    main, settings, intake, report, choices = load_demo()
    report.summary = 'FICTIONAL INITIAL ANSWER — clipboard QA only.'
    answer = Report(summary='FICTIONAL FOLLOW-UP — only answer this question.',
        coverage=[], assumptions=[], risks=[], suggestions=[], next_steps=[], limitations=['Test fixture only.'])
    app = workspace_app(Path(__file__).resolve().parents[1] / 'app.py')
    for key, value in dict(main=main, settings=settings, intake=intake, report=report, choices=choices,
        sources=[], answers=[('A fictional follow-up?', answer)], messages=[], supplements=[],
        api_key='PRIVATE_TEST_KEY_NOT_FOR_CLIPBOARD').items():
        app.session_state[key] = value
    app.run()
    assert not app.exception
    assert [row[2] for row in copied] == ['copy_review', 'copy_answer_0']
    assert report.summary in copied[0][0] and answer.summary not in copied[0][0]
    assert answer.summary in copied[1][0] and report.summary not in copied[1][0]
    assert all('PRIVATE_TEST_KEY_NOT_FOR_CLIPBOARD' not in row[0] for row in copied)
    assert all(row[1] == '中文' for row in copied)
    copied.clear()
    app.selectbox(key='ui_language').set_value('English').run()
    assert not app.exception
    assert all(row[1] == 'English' for row in copied)
    assert 'Impact:' in copied[0][0]
    assert report.summary in copied[0][0] and answer.summary in copied[1][0]
