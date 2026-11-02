import { describe, expect, it, vi } from 'vitest';
import { fetchSamples } from './api';

const { get } = vi.hoisted(() => ({ get: vi.fn() }));
vi.mock('axios', () => ({ default: { create: () => ({ get }) } }));

describe('API 响应契约', () => {
  // 断言来源：统一 envelope 的业务错误不能因 HTTP 请求成功而被视为成功数据。
  it('保留业务错误码、消息与详情', async () => {
    get.mockResolvedValueOnce({
      data: { code: 40001, message: 'Invalid filter', detail: { field: 'status' }, data: null },
    });

    await expect(fetchSamples()).rejects.toMatchObject({
      name: 'ApiClientError',
      code: 40001,
      message: 'Invalid filter',
      detail: { field: 'status' },
    });
  });
});
