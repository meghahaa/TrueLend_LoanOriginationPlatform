import React, { useEffect, useState } from 'react';
import { getSchedule, postRepayment, RepaymentResponse, ScheduleResponse } from '../api';

interface RepayProps {
  token: string;
  initialAppId?: string;
}

export const Repay: React.FC<RepayProps> = ({ token, initialAppId = '' }) => {
  const [appId, setAppId] = useState<string>(initialAppId);
  const [schedule, setSchedule] = useState<ScheduleResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  // Repayment form
  const [repayAmount, setRepayAmount] = useState<string>('');
  const [paidOn, setPaidOn] = useState<string>(new Date().toISOString().split('T')[0]);
  const [repayResult, setRepayResult] = useState<RepaymentResponse | null>(null);
  const [posting, setPosting] = useState<boolean>(false);

  const fetchScheduleData = async (id: string) => {
    if (!id.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const data = await getSchedule(id.trim(), token);
      setSchedule(data);
      if (data.emi_amount) {
        setRepayAmount(data.emi_amount);
      }
    } catch (err: any) {
      setError(err.message || 'Repayment schedule not found');
      setSchedule(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (initialAppId) {
      fetchScheduleData(initialAppId);
    }
  }, [initialAppId]);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    fetchScheduleData(appId);
  };

  const handlePostRepayment = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!schedule) return;
    setPosting(true);
    setError(null);
    try {
      const res = await postRepayment(schedule.application_id, repayAmount, paidOn, token);
      setRepayResult(res);
    } catch (err: any) {
      setError(err.message || 'Repayment posting failed');
    } finally {
      setPosting(false);
    }
  };

  return (
    <div className="card" data-testid="repay-view">
      <h2>Loan Repayment & Amortization Schedule</h2>

      <form onSubmit={handleSearch} style={{ display: 'flex', gap: '0.5rem', marginBottom: '1.5rem' }}>
        <input
          type="text"
          placeholder="Enter Application ID (e.g. app-300)"
          value={appId}
          onChange={(e) => setAppId(e.target.value)}
          data-testid="repay-input-app-id"
          style={{ flex: 1 }}
          required
        />
        <button type="submit" className="btn-primary" data-testid="repay-search-button">
          {loading ? 'Loading...' : 'Load Schedule'}
        </button>
      </form>

      {error && <div className="badge badge-REJECTED" style={{ marginBottom: '1rem' }}>{error}</div>}

      {schedule && (
        <div>
          <div className="card" style={{ background: '#f8fafc' }}>
            <div className="form-row">
              <div>
                <strong>Application ID: </strong>
                <span>{schedule.application_id}</span>
              </div>
              <div>
                <strong>Monthly EMI: </strong>
                <span>INR </span>
                <span data-testid="schedule-emi-amount">{schedule.emi_amount}</span>
              </div>
              <div>
                <strong>Total Principal: </strong>
                <span>INR </span>
                <span data-testid="schedule-total-principal">{schedule.total_principal}</span>
              </div>
              <div>
                <strong>Total Interest: </strong>
                <span>INR {schedule.total_interest}</span>
              </div>
              <div>
                <strong>Total Payable: </strong>
                <span>INR </span>
                <span data-testid="schedule-total-payable">{schedule.total_payable}</span>
              </div>
            </div>
          </div>

          {/* Repayment posting form */}
          <div className="card" style={{ marginTop: '1rem', border: '2px solid var(--primary)' }}>
            <h3>Post a Loan Repayment</h3>
            <form onSubmit={handlePostRepayment} style={{ marginTop: '0.75rem' }}>
              <div className="form-row">
                <div className="form-group">
                  <label>Payment Amount (INR):</label>
                  <input
                    type="text"
                    value={repayAmount}
                    onChange={(e) => setRepayAmount(e.target.value)}
                    data-testid="repayment-amount-input"
                    required
                  />
                </div>
                <div className="form-group">
                  <label>Payment Date:</label>
                  <input
                    type="date"
                    value={paidOn}
                    onChange={(e) => setPaidOn(e.target.value)}
                    data-testid="repayment-date-input"
                    required
                  />
                </div>
              </div>
              <button
                type="submit"
                className="btn-primary"
                data-testid="repayment-submit-button"
                disabled={posting}
                style={{ marginTop: '0.5rem' }}
              >
                {posting ? 'Posting Payment...' : 'Post Repayment'}
              </button>
            </form>

            {repayResult && (
              <div
                data-testid="repayment-result"
                style={{
                  marginTop: '1rem',
                  padding: '1rem',
                  background: '#f0fdf4',
                  borderRadius: 'var(--radius)',
                  border: '1px solid #bbf7d0',
                }}
              >
                <h4>Repayment Processed Successfully!</h4>
                <p>
                  <strong>Outstanding Principal: </strong>
                  INR <span data-testid="repay-outstanding-principal">{repayResult.outstanding_principal}</span>
                </p>
                <p>
                  <strong>Total Remaining Due: </strong>
                  INR <span>{repayResult.total_remaining_due}</span>
                </p>
                <p>
                  <strong>Days Past Due (DPD): </strong>
                  <span data-testid="repay-dpd">{repayResult.dpd}</span>
                </p>
                <p>
                  <strong>Delinquency Bucket: </strong>
                  <span
                    data-testid="repay-delinquency-bucket"
                    className={`badge badge-${repayResult.delinquency_bucket}`}
                  >
                    {repayResult.delinquency_bucket}
                  </span>
                </p>
              </div>
            )}
          </div>

          <h3 style={{ marginTop: '1.5rem' }}>Full Amortization Schedule</h3>
          <table className="responsive-cards" data-testid="schedule-table">
            <thead>
              <tr>
                <th>#</th>
                <th>Due Date</th>
                <th>Opening Balance</th>
                <th>Principal</th>
                <th>Interest</th>
                <th>EMI Amount</th>
                <th>Remaining Balance</th>
              </tr>
            </thead>
            <tbody>
              {schedule.rows.map((row) => (
                <tr key={row.installment_number}>
                  <td data-label="#">{row.installment_number}</td>
                  <td data-label="Due Date">{row.due_date}</td>
                  <td data-label="Opening Balance">{row.opening_balance}</td>
                  <td data-label="Principal">
                    <span data-testid={`row-principal-${row.installment_number}`}>
                      {row.principal_component}
                    </span>
                  </td>
                  <td data-label="Interest">
                    <span data-testid={`row-interest-${row.installment_number}`}>
                      {row.interest_component}
                    </span>
                  </td>
                  <td data-label="EMI Amount">
                    <strong data-testid={`row-emi-${row.installment_number}`}>
                      {row.emi_amount}
                    </strong>
                  </td>
                  <td data-label="Remaining Balance">{row.remaining_balance}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};
