import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { Repay } from './Repay';
import * as api from '../api';

vi.mock('../api');

const mockSchedule: api.ScheduleResponse = {
  application_id: 'app-300',
  emi_amount: '10036.09',
  total_principal: '300000.00',
  total_interest: '61299.12',
  total_payable: '361299.12',
  rows: [
    {
      installment_number: 1,
      due_date: '2026-02-01',
      opening_balance: '300000.00',
      principal_component: '6911.09',
      interest_component: '3125.00',
      emi_amount: '10036.09',
      remaining_balance: '293088.91',
    },
    {
      installment_number: 2,
      due_date: '2026-03-01',
      opening_balance: '293088.91',
      principal_component: '6983.08',
      interest_component: '3053.01',
      emi_amount: '10036.09',
      remaining_balance: '286105.83',
    },
  ],
};

const mockRepayResult: api.RepaymentResponse = {
  application_id: 'app-300',
  amount_paid: '10036.09',
  paid_on: '2026-02-01',
  outstanding_principal: '293088.91',
  total_remaining_due: '351263.03',
  dpd: 0,
  delinquency_bucket: 'CURRENT',
  allocations: [
    {
      installment_number: 1,
      interest_allocated: '3125.00',
      principal_allocated: '6911.09',
    },
  ],
};

describe('Repay View Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders amortization schedule table and total summary', async () => {
    vi.mocked(api.getSchedule).mockResolvedValue(mockSchedule);

    render(<Repay token="demo-customer-1" initialAppId="app-300" />);

    await waitFor(() => {
      expect(screen.getByTestId('schedule-total-payable')).toHaveTextContent('361299.12');
    });

    expect(screen.getByTestId('schedule-emi-amount')).toHaveTextContent('10036.09');
    expect(screen.getByTestId('schedule-total-principal')).toHaveTextContent('300000.00');

    // Check installment rows
    expect(screen.getByTestId('row-emi-1')).toHaveTextContent('10036.09');
    expect(screen.getByTestId('row-principal-1')).toHaveTextContent('6911.09');
    expect(screen.getByTestId('row-interest-1')).toHaveTextContent('3125.00');
  });

  it('posts repayment and updates delinquency bucket and outstanding principal', async () => {
    vi.mocked(api.getSchedule).mockResolvedValue(mockSchedule);
    vi.mocked(api.postRepayment).mockResolvedValue(mockRepayResult);

    render(<Repay token="demo-customer-1" initialAppId="app-300" />);

    await waitFor(() => {
      expect(screen.getByTestId('repayment-amount-input')).toBeInTheDocument();
    });

    await userEvent.clear(screen.getByTestId('repayment-amount-input'));
    await userEvent.type(screen.getByTestId('repayment-amount-input'), '10036.09');
    await userEvent.click(screen.getByTestId('repayment-submit-button'));

    await waitFor(() => {
      expect(screen.getByTestId('repay-outstanding-principal')).toHaveTextContent('293088.91');
    });

    expect(screen.getByTestId('repay-delinquency-bucket')).toHaveTextContent('CURRENT');
    expect(screen.getByTestId('repay-dpd')).toHaveTextContent('0');
  });
});
