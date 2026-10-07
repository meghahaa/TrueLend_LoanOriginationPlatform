import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { Apply } from './Apply';
import * as api from '../api';

vi.mock('../api');

const mockProducts: api.ProductCatalogResponse = {
  policy_version: 1,
  products: [
    {
      product_code: 'PERSONAL',
      display_name: 'Personal Loan',
      min_monthly_income: '25000.00',
      min_age: 21,
      max_age: 60,
      min_amount: '50000.00',
      max_amount: '1000000.00',
      min_tenure_months: 12,
      max_tenure_months: 60,
      annual_rate_percent: '12.50',
      approve_score: 720,
      reject_score: 550,
      max_foir: '0.50',
      required_documents: ['ID_PROOF', 'ADDRESS_PROOF', 'SALARY_SLIP', 'BANK_STATEMENT'],
    },
    {
      product_code: 'VEHICLE',
      display_name: 'Vehicle Loan',
      min_monthly_income: '30000.00',
      min_age: 21,
      max_age: 65,
      min_amount: '100000.00',
      max_amount: '2500000.00',
      min_tenure_months: 12,
      max_tenure_months: 84,
      annual_rate_percent: '9.50',
      approve_score: 700,
      reject_score: 520,
      max_foir: '0.55',
      required_documents: ['ID_PROOF', 'ADDRESS_PROOF', 'SALARY_SLIP', 'VEHICLE_QUOTATION'],
    },
  ],
};

describe('Apply View Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(api.fetchProducts).mockResolvedValue(mockProducts);
  });

  it('renders product catalog options and dynamic document requirements', async () => {
    render(<Apply token="demo-customer-1" onNavigateToTrack={vi.fn()} />);

    await waitFor(() => {
      expect(screen.getByTestId('product-select')).toBeInTheDocument();
    });

    expect(screen.getByText('Personal Loan')).toBeInTheDocument();
    expect(screen.getByText('Vehicle Loan')).toBeInTheDocument();

    // Verify required document checklist appears
    expect(screen.getByText('ID_PROOF')).toBeInTheDocument();
    expect(screen.getByText('ADDRESS_PROOF')).toBeInTheDocument();
    expect(screen.getByText('SALARY_SLIP')).toBeInTheDocument();
    expect(screen.getByText('BANK_STATEMENT')).toBeInTheDocument();
  });

  it('submits loan application and displays result', async () => {
    const mockAppResponse: api.ApplicationResponse = {
      id: 'app-999',
      product: 'PERSONAL',
      amount: '100000.00',
      tenure_months: 24,
      status: 'APPROVED',
      decision: 'AUTO_APPROVE',
      score: 740,
      reason_codes: ['SCORE_ABOVE_APPROVE'],
      policy_version: 1,
      masked_pan: 'XXXXXX1234',
      masked_aadhaar: 'XXXX0001',
      applicant_name: 'John Doe',
      documents: [
        { doc_type: 'ID_PROOF', status: 'UPLOADED', filename: 'id.pdf' },
      ],
    };

    vi.mocked(api.submitApplication).mockResolvedValue(mockAppResponse);

    render(<Apply token="demo-customer-1" onNavigateToTrack={vi.fn()} />);

    await waitFor(() => {
      expect(screen.getByTestId('applicant-name-input')).toBeInTheDocument();
    });

    await userEvent.type(screen.getByTestId('applicant-name-input'), 'John Doe');
    await userEvent.type(screen.getByTestId('applicant-age-input'), '30');
    await userEvent.type(screen.getByTestId('applicant-income-input'), '60000.00');
    await userEvent.type(screen.getByTestId('applicant-pan-input'), 'TESTP1234X');
    await userEvent.type(screen.getByTestId('applicant-aadhaar-input'), '999900000001');
    await userEvent.type(screen.getByTestId('loan-amount-input'), '100000.00');
    await userEvent.type(screen.getByTestId('loan-tenure-input'), '24');

    await userEvent.click(screen.getByTestId('apply-submit-button'));

    await waitFor(() => {
      expect(screen.getByTestId('apply-result-id')).toHaveTextContent('app-999');
    });

    expect(screen.getByTestId('apply-result-status')).toHaveTextContent('APPROVED');
    expect(screen.getByTestId('apply-result-decision')).toHaveTextContent('AUTO_APPROVE');
  });
});
