import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { PolicyEditor } from './PolicyEditor';
import * as api from '../api';

vi.mock('../api');

const mockVersions: api.PolicyVersionDto[] = [
  {
    version: 1,
    effective_from: '2026-01-01',
    created_by: 'seed',
    change_note: 'Initial synthetic policy',
  },
];

describe('PolicyEditor Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders policy version history and editor form', async () => {
    vi.mocked(api.listPolicies).mockResolvedValue(mockVersions);

    render(<PolicyEditor token="demo-admin-1" />);

    await waitFor(() => {
      expect(screen.getByTestId('policy-version-1')).toBeInTheDocument();
    });

    expect(screen.getByText('Initial synthetic policy')).toBeInTheDocument();
    expect(screen.getByTestId('change-note-input')).toBeInTheDocument();
    expect(screen.getByTestId('publish-policy-button')).toBeInTheDocument();
  });

  it('submits updated policy thresholds and displays new version', async () => {
    vi.mocked(api.listPolicies).mockResolvedValue(mockVersions);
    vi.mocked(api.publishPolicy).mockResolvedValue({ version: 2 });

    render(<PolicyEditor token="demo-admin-1" />);

    await waitFor(() => {
      expect(screen.getByTestId('change-note-input')).toBeInTheDocument();
    });

    await userEvent.clear(screen.getByTestId('annual-rate-input'));
    await userEvent.type(screen.getByTestId('annual-rate-input'), '13.50');

    await userEvent.type(screen.getByTestId('change-note-input'), 'Increase PERSONAL interest rate');
    await userEvent.click(screen.getByTestId('publish-policy-button'));

    await waitFor(() => {
      expect(screen.getByTestId('publish-result-version')).toHaveTextContent('2');
    });

    expect(api.publishPolicy).toHaveBeenCalledWith(
      expect.objectContaining({
        change_note: 'Increase PERSONAL interest rate',
      }),
      'demo-admin-1'
    );
  });
});
