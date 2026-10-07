import React, { useEffect, useState } from 'react';
import { listPolicies, PolicyVersionDto, publishPolicy } from '../api';

interface PolicyEditorProps {
  token: string;
}

export const PolicyEditor: React.FC<PolicyEditorProps> = ({ token }) => {
  const [versions, setVersions] = useState<PolicyVersionDto[]>([]);
  const [selectedProduct, setSelectedProduct] = useState<string>('PERSONAL');

  // Product thresholds
  const [minIncome, setMinIncome] = useState<string>('25000.00');
  const [minAge, setMinAge] = useState<string>('21');
  const [maxAge, setMaxAge] = useState<string>('60');
  const [minAmount, setMinAmount] = useState<string>('50000.00');
  const [maxAmount, setMaxAmount] = useState<string>('1000000.00');
  const [minTenure, setMinTenure] = useState<string>('12');
  const [maxTenure, setMaxTenure] = useState<string>('60');
  const [annualRate, setAnnualRate] = useState<string>('12.50');
  const [approveScore, setApproveScore] = useState<string>('720');
  const [rejectScore, setRejectScore] = useState<string>('550');
  const [maxFoir, setMaxFoir] = useState<string>('0.50');

  const [changeNote, setChangeNote] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(false);
  const [publishing, setPublishing] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [newVersionResult, setNewVersionResult] = useState<number | null>(null);

  const fetchVersions = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await listPolicies(token);
      setVersions(data);
    } catch (err: any) {
      setError(err.message || 'Failed to load policy versions');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchVersions();
  }, [token]);

  const handlePublish = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!changeNote.trim()) {
      setError('Change note is mandatory');
      return;
    }
    setPublishing(true);
    setError(null);
    setNewVersionResult(null);

    const payload = {
      products: {
        [selectedProduct]: {
          min_monthly_income: minIncome,
          min_age: parseInt(minAge, 10),
          max_age: parseInt(maxAge, 10),
          min_amount: minAmount,
          max_amount: maxAmount,
          min_tenure_months: parseInt(minTenure, 10),
          max_tenure_months: parseInt(maxTenure, 10),
          annual_rate_percent: annualRate,
          approve_score: parseInt(approveScore, 10),
          reject_score: parseInt(rejectScore, 10),
          max_foir: maxFoir,
        },
      },
      change_note: changeNote,
    };

    try {
      const res = await publishPolicy(payload, token);
      setNewVersionResult(res.version);
      setChangeNote('');
      fetchVersions();
    } catch (err: any) {
      setError(err.message || 'Failed to publish new policy version');
    } finally {
      setPublishing(false);
    }
  };

  return (
    <div className="card" data-testid="policy-editor-view">
      <h2>Loan Policy Management & Versioning</h2>

      {error && <div className="badge badge-REJECTED" style={{ marginBottom: '1rem' }}>{error}</div>}

      {newVersionResult && (
        <div
          data-testid="publish-result"
          style={{
            marginBottom: '1rem',
            padding: '1rem',
            background: '#f0fdf4',
            borderRadius: 'var(--radius)',
            border: '1px solid #bbf7d0',
          }}
        >
          <h4>Policy Version Published!</h4>
          <p>
            Successfully generated policy version <strong>v00<span data-testid="publish-result-version">{newVersionResult}</span></strong> (immutable, append-only).
          </p>
        </div>
      )}

      <div className="card" style={{ background: '#f8fafc', marginBottom: '1.5rem' }}>
        <h3>Policy Version History</h3>
        {loading && <p>Loading versions...</p>}
        <table className="responsive-cards" style={{ marginTop: '0.5rem' }}>
          <thead>
            <tr>
              <th>Version</th>
              <th>Effective From</th>
              <th>Created By</th>
              <th>Change Note</th>
            </tr>
          </thead>
          <tbody>
            {versions.map((v) => (
              <tr key={v.version} data-testid={`policy-version-${v.version}`}>
                <td data-label="Version"><strong>v00{v.version}</strong></td>
                <td data-label="Effective From">{v.effective_from}</td>
                <td data-label="Created By">{v.created_by}</td>
                <td data-label="Change Note">{v.change_note}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="card">
        <h3>Publish New Policy Version</h3>
        <p className="login-subtitle">
          Threshold updates create an append-only, immutable new version file (e.g., loan_policy.v002.json).
        </p>

        <form onSubmit={handlePublish} style={{ marginTop: '1rem' }}>
          <div className="form-group">
            <label>Product to Configure:</label>
            <select
              value={selectedProduct}
              onChange={(e) => setSelectedProduct(e.target.value)}
              data-testid="product-configure-select"
            >
              <option value="PERSONAL">Personal Loan (PERSONAL)</option>
              <option value="VEHICLE">Vehicle Loan (VEHICLE)</option>
              <option value="EDUCATION">Education Loan (EDUCATION)</option>
            </select>
          </div>

          <div className="form-row">
            <div className="form-group">
              <label>Min Monthly Income (INR):</label>
              <input
                type="text"
                value={minIncome}
                onChange={(e) => setMinIncome(e.target.value)}
                data-testid="min-income-input"
                required
              />
            </div>
            <div className="form-group">
              <label>Annual Interest Rate (%):</label>
              <input
                type="text"
                value={annualRate}
                onChange={(e) => setAnnualRate(e.target.value)}
                data-testid="annual-rate-input"
                required
              />
            </div>
          </div>

          <div className="form-row">
            <div className="form-group">
              <label>Min Age (years):</label>
              <input
                type="number"
                value={minAge}
                onChange={(e) => setMinAge(e.target.value)}
                data-testid="min-age-input"
                required
              />
            </div>
            <div className="form-group">
              <label>Max Age (years):</label>
              <input
                type="number"
                value={maxAge}
                onChange={(e) => setMaxAge(e.target.value)}
                data-testid="max-age-input"
                required
              />
            </div>
          </div>

          <div className="form-row">
            <div className="form-group">
              <label>Min Tenure (months):</label>
              <input
                type="number"
                value={minTenure}
                onChange={(e) => setMinTenure(e.target.value)}
                data-testid="min-tenure-input"
                required
              />
            </div>
            <div className="form-group">
              <label>Max Tenure (months):</label>
              <input
                type="number"
                value={maxTenure}
                onChange={(e) => setMaxTenure(e.target.value)}
                data-testid="max-tenure-input"
                required
              />
            </div>
          </div>

          <div className="form-row">
            <div className="form-group">
              <label>Min Amount (INR):</label>
              <input
                type="text"
                value={minAmount}
                onChange={(e) => setMinAmount(e.target.value)}
                data-testid="min-amount-input"
                required
              />
            </div>
            <div className="form-group">
              <label>Max Amount (INR):</label>
              <input
                type="text"
                value={maxAmount}
                onChange={(e) => setMaxAmount(e.target.value)}
                data-testid="max-amount-input"
                required
              />
            </div>
          </div>

          <div className="form-row">
            <div className="form-group">
              <label>Auto-Approve Score Threshold:</label>
              <input
                type="number"
                value={approveScore}
                onChange={(e) => setApproveScore(e.target.value)}
                data-testid="approve-score-input"
                required
              />
            </div>
            <div className="form-group">
              <label>Auto-Reject Score Threshold:</label>
              <input
                type="number"
                value={rejectScore}
                onChange={(e) => setRejectScore(e.target.value)}
                data-testid="reject-score-input"
                required
              />
            </div>
          </div>

          <div className="form-row">
            <div className="form-group">
              <label>Max FOIR (0.00 - 1.00):</label>
              <input
                type="text"
                value={maxFoir}
                onChange={(e) => setMaxFoir(e.target.value)}
                data-testid="max-foir-input"
                required
              />
            </div>
          </div>

          <div className="form-group" style={{ marginTop: '0.5rem' }}>
            <label>Audit Change Note (Mandatory):</label>
            <input
              type="text"
              placeholder="e.g. Rate adjustment for Q2 risk policy update"
              value={changeNote}
              onChange={(e) => setChangeNote(e.target.value)}
              data-testid="change-note-input"
              required
            />
          </div>

          <button
            type="submit"
            className="btn-primary"
            data-testid="publish-policy-button"
            disabled={publishing}
            style={{ marginTop: '0.5rem' }}
          >
            {publishing ? 'Publishing Version...' : 'Publish Policy Version'}
          </button>
        </form>
      </div>
    </div>
  );
};
