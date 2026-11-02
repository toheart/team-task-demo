import { test } from '@playwright/test';

type RemotePath = 'read-only' | 'draft' | 'human-handoff' | 'confirmed-write' | 'not-configured';

interface CaseContract {
  id: string;
  dev: string;
  remote: { path: RemotePath; assertions: string };
}

/** 为当前测试记录环境断言范围；登记与执行结果分别判定。 */
export function declareCase(contract: CaseContract): void {
  const environment = process.env.E2E_ENV ?? 'dev';
  const info = test.info();
  info.annotations.push({ type: 'case-id', description: contract.id });
  info.annotations.push({
    type: 'environment-coverage',
    description: `dev=${contract.dev}; remote=${contract.remote.path}: ${contract.remote.assertions}`,
  });

  if (environment === 'remote' && contract.remote.path === 'not-configured') {
    info.annotations.push({ type: 'not-applicable', description: 'Remote path is not configured' });
    test.skip(true, `Remote path is not configured for ${contract.id}`);
  }
}

/** 远程写入只接受本轮对当前 Case ID 的显式确认。 */
export function requireRemoteWrite(caseId: string): void {
  if ((process.env.E2E_ENV ?? 'dev') === 'remote' && process.env.E2E_REMOTE_CONFIRM !== caseId) {
    throw new Error(`Remote write requires E2E_REMOTE_CONFIRM=${caseId}`);
  }
}
