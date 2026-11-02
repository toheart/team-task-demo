import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it, vi } from 'vitest';
import { Home } from './Home';
import { fetchSamples } from '../services/api';
import type { SampleItem } from '../types/sample';

vi.mock('../services/api', () => ({ fetchSamples: vi.fn() }));

const sample: SampleItem = {
  id: 'sample-1',
  name: 'Contract response',
  summary: 'Data returned by the API service',
  category: 'backend',
  status: 'ready',
  updatedAt: '2026-10-09T00:00:00Z',
};

describe('首页数据交互', () => {
  // 断言来源：模板首页展示 API 数据的验收契约，不在组件层证明 HTTP 链路。
  it('展示服务层返回的数据', async () => {
    vi.mocked(fetchSamples).mockResolvedValueOnce([sample]);
    render(<Home />);

    expect(await screen.findByRole('heading', { name: sample.name })).toBeVisible();
    expect(screen.getByText(sample.summary)).toBeVisible();
  });

  // 断言来源：失败反馈与重试交互契约；验证用户动作后的可观察结果。
  it('失败后通过重试恢复数据展示', async () => {
    vi.mocked(fetchSamples)
      .mockRejectedValueOnce(new Error('Service unavailable'))
      .mockResolvedValueOnce([sample]);
    const user = userEvent.setup();
    render(<Home />);

    expect(await screen.findByText('Request failed: Service unavailable')).toBeVisible();
    await user.click(screen.getByRole('button', { name: 'Try again' }));

    expect(await screen.findByRole('heading', { name: sample.name })).toBeVisible();
    expect(screen.queryByText('Request failed: Service unavailable')).not.toBeInTheDocument();
  });
});
