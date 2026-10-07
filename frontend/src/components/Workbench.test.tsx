import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { Workbench } from './Workbench';
import * as api from '../api';

vi.mock('../api');

const mockQueue: api.ApplicationResponse[] = [
  {
    id: 'app-201',
    product: 'PERSONAL',
    amount: '200000.00',
    tenure_months: 24,
    status: 'MANUAL_REVIEW',
    decision: 'MANUAL_REVIEW',
    score: 660,
    reason_codes: ['SCORE_IN_REVIEW_BAND'],
    policy_version: 1,
    applicant_name: 'Alice Smith',
    documents: [
      { doc_type: 'ID_PROOF', status: 'UPLOADED', filename: 'id.pdf' },
      { doc_type: 'SALARY_SLIP', status: 'UPLOADED', filename: 'slip.pdf' },
    ],
  },
];

describe('Underwriter Workbench Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders queue items and allows underwriter to inspect and verify document', async () => {
    vi.mocked(api.getUnderwriterQueue).mockResolvedValue(mockQueue);
    vi.mocked(api.verifyDocument).mockResolvedValue();

    render(<Workbench token="demo-underwriter-1" />);

    await waitFor(() => {
      expect(screen.getByTestId('workbench-app-app-201')).toBeInTheDocument();
    });

    // Click to inspect app-201
    await userEvent.click(screen.getByTestId('inspect-button-app-201'));

    expect(screen.getByTestId('selected-app-id')).toHaveTextContent('app-201');

    // Click verify on ID_PROOF
    const verifyBtn = screen.getByTestId('verify-doc-ID_PROOF');
    await userEvent.click(verifyBtn);

    await waitFor(() => {
      expect(api.verifyDocument).toHaveBeenCalledWith(
        'app-201',
        'ID_PROOF',
        'VERIFIED',
        expect.any(String),
        'demo-underwriter-1'
      );
    });
  });

  it('submits manual underwriting decision', async () => {
    vi.mocked(api.getUnderwriterQueue).mockResolvedValue(mockQueue);
    vi.mocked(api.decideApplication).mockResolvedValue();

    render(<Workbench token="demo-underwriter-1" />);

    await waitFor(() => {
      expect(screen.getByTestId('workbench-app-app-201')).toBeInTheDocument();
    });

    await userEvent.click(screen.getByTestId('inspect-button-app-201'));

    const approveBtn = screen.getByTestId('decision-approve-button');
    await userEvent.click(approveBtn);

    await waitFor(() => {
      expect(api.decideApplication).toHaveBeenCalledWith(
        'app-201',
        'APPROVE',
        'MANUAL_APPROVED',
        expect.any(String),
        'demo-underwriter-1'
      );
    });
  });
});
