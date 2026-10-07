import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { Dashboard } from './Dashboard';
import * as api from '../api';

vi.mock('../api');

const mockApplications: api.ApplicationResponse[] = [
  {
    id: 'app-501',
    product: 'PERSONAL',
    amount: '300000.00',
    tenure_months: 36,
    status: 'REJECTED',
    decision: 'AUTO_REJECT',
    score: 510,
    reason_codes: ['SCORE_BELOW_REJECT'],
    policy_version: 1,
    applicant_name: 'Bob Jones',
    documents: [],
  },
  {
    id: 'app-502',
    product: 'VEHICLE',
    amount: '500000.00',
    tenure_months: 48,
    status: 'APPROVED',
    decision: 'AUTO_APPROVE',
    score: 750,
    reason_codes: ['SCORE_ABOVE_APPROVE'],
    policy_version: 1,
    applicant_name: 'Carol White',
    documents: [],
  },
];

describe('Admin Dashboard Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders application portfolio list and summary metrics', async () => {
    vi.mocked(api.getAdminApplications).mockResolvedValue(mockApplications);

    render(<Dashboard token="demo-admin-1" />);

    await waitFor(() => {
      expect(screen.getByTestId('admin-app-app-501')).toBeInTheDocument();
    });

    expect(screen.getByTestId('admin-app-app-502')).toBeInTheDocument();
    expect(screen.getByTestId('metric-total-apps')).toHaveTextContent('2');
  });

  it('executes admin override on an auto-rejected application', async () => {
    vi.mocked(api.getAdminApplications).mockResolvedValue(mockApplications);
    vi.mocked(api.overrideApplication).mockResolvedValue();

    render(<Dashboard token="demo-admin-1" />);

    await waitFor(() => {
      expect(screen.getByTestId('override-button-app-501')).toBeInTheDocument();
    });

    // Click override on app-501
    await userEvent.click(screen.getByTestId('override-button-app-501'));

    expect(screen.getByTestId('override-modal')).toBeInTheDocument();

    await userEvent.type(screen.getByTestId('override-comment-input'), 'Senior risk officer approved exception');
    await userEvent.click(screen.getByTestId('override-submit-button'));

    await waitFor(() => {
      expect(api.overrideApplication).toHaveBeenCalledWith(
        'app-501',
        'ADMIN_OVERRIDE',
        'Senior risk officer approved exception',
        'demo-admin-1'
      );
    });
  });
});
