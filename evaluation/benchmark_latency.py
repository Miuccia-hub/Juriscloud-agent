"""Local scheduling benchmark: fictional material and artificial I/O delays only.

Run: python -m evaluation.benchmark_latency
Not a model-latency, legal-quality, or live-network benchmark.
"""
from copy import deepcopy
from json import dumps
from statistics import median
from time import perf_counter, sleep
from legal_agent.workflow import Workflow
from tests.fixture_data import load_demo
from tests.test_core import FakeGateway

MODEL_DELAY = 0.08
SOURCE_DELAY = 0.04

class DelayedGateway(FakeGateway):
    def structured(self, *args):
        sleep(MODEL_DELAY)
        return super().structured(*args)

    def search(self, *args):
        sleep(MODEL_DELAY)
        return [{'url': f'https://www.hcourt.gov.au/benchmark-{i}'} for i in range(5)]


def fetcher(url, domains):
    sleep(SOURCE_DELAY)
    return 'Fictional source text. No legal propositions or live research. ' * 5, url


def run(workers):
    main, settings, *_ = load_demo()
    settings.jurisdiction = "维多利亚州"
    gateway = DelayedGateway()
    workflow = Workflow(gateway, fetcher=fetcher, max_workers=workers)
    start = perf_counter()
    intake = workflow.intake(main, [], settings)
    intake.contract_type = 'employment agreement'
    report, sources, *_ = workflow.review(main, [], settings, intake)
    assert len(sources) == 5 and len(report._review_checks) == 17
    return {'seconds': round(perf_counter() - start, 4),
            'structured_requests': len(gateway.calls), 'source_records': len(sources),
            'check_records': len(report._review_checks)}, deepcopy(report)


def main():
    # Warm schema/fixture caches so startup imports don't inflate either mode.
    run(3)
    results = {1: [], 3: []}
    reports = []
    for _ in range(3):
        for workers in (1, 3):
            result, report = run(workers)
            results[workers].append(result)
            reports.append(report)
    assert all(report.model_dump() == reports[0].model_dump() for report in reports)
    assert all(report._review_checks == reports[0]._review_checks for report in reports)
    serial = median(row['seconds'] for row in results[1])
    parallel = median(row['seconds'] for row in results[3])
    print(dumps({'kind': 'synthetic_delays_only_no_live_model_or_network',
                 'model_delay_seconds': MODEL_DELAY, 'source_delay_seconds': SOURCE_DELAY,
                 'runs': results, 'serial_median_seconds': serial,
                 'parallel_median_seconds': parallel,
                 'reduction_percent': round((1 - parallel / serial) * 100, 1),
                 'fictional_report_and_check_records_equal': True}, indent=2))

if __name__ == '__main__':
    main()
