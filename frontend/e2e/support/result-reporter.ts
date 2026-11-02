import { mkdirSync, writeFileSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import type { FullConfig, FullResult, Reporter, Suite } from '@playwright/test/reporter';

type BusinessResult =
  | 'PASS'
  | 'FAIL'
  | 'HANDOFF_PENDING'
  | 'DIAGNOSTIC_ONLY'
  | 'NOT_RUN'
  | 'NOT_APPLICABLE'
  | 'CLEANUP_FAILED';

function classify(status: string, annotations: ReadonlyArray<{ type: string }>): BusinessResult {
  const has = (type: string) => annotations.some((item) => item.type === type);
  if (status === 'failed' && has('cleanup-only')) return 'CLEANUP_FAILED';
  if (status === 'failed' || status === 'timedOut') return 'FAIL';
  if (has('cleanup-failed')) return 'CLEANUP_FAILED';
  if (has('handoff')) return 'HANDOFF_PENDING';
  if (has('diagnostic-only')) return 'DIAGNOSTIC_ONLY';
  if (status === 'skipped' && has('not-applicable')) return 'NOT_APPLICABLE';
  return status === 'passed' ? 'PASS' : 'NOT_RUN';
}

/** 收集命令不覆盖执行证据；业务结果不把 skip 或人工接管算成通过。 */
export default class ResultReporter implements Reporter {
  private suite?: Suite;
  private outputFile = resolve('e2e/artifacts/system/results.json');
  private environment: unknown;

  onBegin(config: FullConfig, suite: Suite): void {
    this.suite = suite;
    this.environment = config.metadata.environment;
    this.outputFile = resolve(
      config.configFile ? dirname(config.configFile) : config.rootDir,
      'artifacts/system/results.json',
    );
  }

  onEnd(result: FullResult): { status: FullResult['status'] } {
    if (process.argv.includes('--list')) return { status: result.status };

    const tests = (this.suite?.allTests() ?? []).map((test) => {
      const last = test.results.at(-1);
      const annotations = last?.annotations ?? test.annotations;
      return {
        title: test.titlePath().join(' > '),
        file: test.location.file,
        status: classify(last?.status ?? 'not-run', annotations),
        playwrightStatus: last?.status ?? 'not-run',
        annotations,
        errors: last?.errors.map((error) => error.message) ?? [],
        attachments: last?.attachments.map(({ name, path }) => ({ name, path })) ?? [],
      };
    });
    const counts: Partial<Record<BusinessResult, number>> = {};
    for (const test of tests) counts[test.status] = (counts[test.status] ?? 0) + 1;

    const passed = result.status === 'passed'
      && tests.some((test) => test.status === 'PASS')
      && tests.every((test) => test.status === 'PASS' || test.status === 'NOT_APPLICABLE');
    const status = passed ? result.status : 'failed';
    mkdirSync(dirname(this.outputFile), { recursive: true });
    writeFileSync(this.outputFile, JSON.stringify({ environment: this.environment, status, passed, counts, tests }, null, 2));
    return { status };
  }
}
