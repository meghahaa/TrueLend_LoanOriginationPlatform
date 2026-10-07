import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { Track } from './Track';
import * as api from '../api';

vi.mock('../api');

const mockApp: api.ApplicationResponse = {
  id: 'app-100',
  product: 'PERSONAL',
  amount: '300000.00',
  tenure_months: 36,
  status: 'MANUAL_REVIEW',
  decision: 'MANUAL_REVIEW',
  score: 650,
  reason_codes: ['SCORE_IN_REVIEW_BAND'],
  policy_version: 1,
  masked_pan: 'XXXXXX1234',
  masked_aadhaar: 'XXXX0001',
  applicant_name: 'Jane Doe',
  documents: [
    { doc_type: 'ID_PROOF', status: 'VERIFIED', filename: 'id.pdf' },
    { doc_type: 'SALARY_SLIP', status: 'REJECTED', filename: 'slip.pdf', rejection_reason: 'Blurry' },
    { doc_type: 'ADDRESS_PROOF', status: 'MISSING' },
  ],
  missing_documents: ['ADDRESS_PROOF'],
};

describe('Track View Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('fetches and displays application details, masked identifiers, and document statuses', async () => {
    vi.mocked(api.getApplication).mockResolvedValue(mockApp);

    render(<Track token="demo-customer-1" initialAppId="app-100" />);

    await waitFor(() => {
      expect(screen.getByTestId('track-app-id')).toHaveTextContent('app-100');
    });

    expect(screen.getByTestId('track-status')).toHaveTextContent('MANUAL_REVIEW');
    expect(screen.getByTestId('track-masked-pan')).toHaveTextContent('XXXXXX1234');
    expect(screen.getByTestId('track-masked-aadhaar')).toHaveTextContent('XXXX0001');

    // Document statuses
    expect(screen.getByTestId('doc-status-ID_PROOF')).toHaveTextContent('VERIFIED');
    expect(screen.getByTestId('doc-status-SALARY_SLIP')).toHaveTextContent('REJECTED');
    expect(screen.getByTestId('doc-status-ADDRESS_PROOF')).toHaveTextContent('MISSING');
  });

  it('allows uploading a replacement or missing document', async () => {
    vi.mocked(api.getApplication).mockResolvedValue(mockApp);
    vi.mocked(api.uploadDocument).mockResolvedValue({
      ...mockApp,
      documents: [
        { doc_type: 'ID_PROOF', status: 'VERIFIED', filename: 'id.pdf' },
        { doc_type: 'SALARY_SLIP', status: 'UPLOADED', filename: 'new_slip.pdf' },
        { doc_type: 'ADDRESS_PROOF', status: 'MISSING' },
      ],
    });

    render(<Track token="demo-customer-1" initialAppId="app-100" />);

    await waitFor(() => {
      expect(screen.getByTestId('track-app-id')).toHaveTextContent('app-100');
    });

    const uploadInput = screen.getByTestId('upload-input-SALARY_SLIP');
    await userEvent.type(uploadInput, 'new_slip.pdf');

    const uploadBtn = screen.getByTestId('upload-button-SALARY_SLIP');
    await userEvent.click(uploadBtn);

    await waitFor(() => {
      expect(api.uploadDocument).toHaveBeenCalledWith('app-100', 'SALARY_SLIP', 'new_slip.pdf', 'demo-customer-1');
    });
  });
});
