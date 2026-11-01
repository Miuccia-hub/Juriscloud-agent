"""Concurrency regressions with fictional data; no live model/network requests."""
from threading import Barrier, Lock, get_ident
import pytest
from legal_agent.workflow import Workflow
from legal_agent.models import ReviewBatch, Critique, OmissionAudit, ReviewSynthesis
from legal_agent.errors import RunFailure
from legal_agent.research import retrieve
from tests.fixture_data import load_demo
from tests.test_core import FakeGateway


def test_review_overlaps_independent_checks_and_audits_without_losing_coverage():
    main, settings, intake, *_ = load_demo()
    intake.contract_type = 'employment agreement'
    caller = get_ident()
    check_gate, audit_gate = Barrier(3), Barrier(2)
    lock = Lock()
    assignments, finished = [], set()
    progress_threads = []

    class ConcurrentGateway(FakeGateway):
        def structured(self, stage, schema, payload, instruction):
            if schema is ReviewBatch:
                assert get_ident() != caller
                assert payload['documents']  # Full contract, not just keyword snippets.
                assert 'required_checks' not in payload  # No duplicate all-topic hints.
                with lock:
                    assignments.extend(item['id'] for item in payload['assigned_checks'])
                check_gate.wait(timeout=3)
            if schema in (Critique, OmissionAudit):
                if schema is OmissionAudit:
                    assert 'critique' not in payload
                    assert len(payload['required_checks']) == 17
                    assert payload['documents'] and payload['draft']
                audit_gate.wait(timeout=3)
            if schema is ReviewSynthesis:
                assert finished == {Critique, OmissionAudit}
                assert 'critique' in payload and 'omission_audit' in payload
            result = super().structured(stage, schema, payload, instruction)
            if schema in (Critique, OmissionAudit):
                with lock:
                    finished.add(schema)
            return result

    parallel = Workflow(ConcurrentGateway(), lambda _: progress_threads.append(get_ident()))
    report, *_ = parallel.review(main, [], settings, intake)
    sequential, *_ = Workflow(FakeGateway(), max_workers=1).review(main, [], settings, intake)
    assert len(assignments) == len(set(assignments)) == 17
    assert report.model_dump() == sequential.model_dump()
    assert report._review_checks == sequential._review_checks
    assert set(progress_threads) == {caller}


def test_failed_parallel_wave_is_drained_and_later_requests_do_not_start():
    gate = Barrier(3)
    lock = Lock()
    called, finished = [], []
    caller = get_ident()
    progress_threads = []

    class FailingGateway:
        def structured(self, stage, *args):
            with lock:
                called.append(stage)
            gate.wait(timeout=3)
            with lock:
                finished.append(stage)
            if stage == 'failure':
                raise RunFailure('rate_limit', stage)
            return stage

    workflow = Workflow(FailingGateway(), lambda _: progress_threads.append(get_ident()))
    jobs = [(stage, None, {}, '') for stage in ('first', 'failure', 'third', 'must-not-start')]
    with pytest.raises(RunFailure) as caught:
        workflow.parallel_calls(jobs)
    assert caught.value.stage == 'failure'
    assert set(called) == set(finished) == {'first', 'failure', 'third'}
    assert set(progress_threads) == {caller}


def test_parallel_source_reads_are_bounded_and_keep_ids_failures_and_allowlist():
    gate, lock = Barrier(3), Lock()
    active = peak = 0
    read_urls = []

    def fetcher(url, domains):
        nonlocal active, peak
        index = int(url.rsplit('/', 1)[-1])
        with lock:
            active += 1
            peak = max(peak, active)
            read_urls.append(url)
        try:
            if index < 3:
                gate.wait(timeout=3)
            if index == 1:
                raise ValueError('test-only body must not be recorded')
            return 'Fictional source text for concurrency checks. ' * 5, url
        finally:
            with lock:
                active -= 1

    urls = [f'https://www.hcourt.gov.au/{i}' for i in range(7)]
    discovered = [{'url': 'https://unlisted.example/blocked'}, {'url': urls[0]}]
    discovered += [{'url': url} for url in urls]  # Includes a duplicate.
    sources, notes = retrieve(discovered, '维多利亚州', [], fetcher=fetcher)
    assert peak == 3 and active == 0
    assert set(read_urls) == set(urls[:5])
    assert [source.id for source in sources] == ['S1', 'S2', 'S3', 'S4', 'S5']
    assert [source.url for source in sources] == urls[:5]
    assert sources[1].status == '正文未取得' and not sources[1].text
    assert 'test-only body' not in sources[1].warning
    assert any('五个' in note for note in notes)
