import React, { useEffect, useState } from 'react';
import { ApplicationResponse, getAdminApplications, overrideApplication } from '../api';

interface DashboardProps {
  token: string;
}

export const Dashboard: React.FC<DashboardProps> = ({ token }) => {
  const [applications, setApplications] = useState<ApplicationResponse[]>([]);
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [productFilter, setProductFilter] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  // Override modal state
  const [overrideApp, setOverrideApp] = useState<ApplicationResponse | null>(null);
  const [overrideReasonCode, setOverrideReasonCode] = useState<string>('ADMIN_OVERRIDE');
  const [overrideComment, setOverrideComment] = useState<string>('');
  const [overriding, setOverriding] = useState<boolean>(false);

  const fetchApplications = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getAdminApplications(token, {
        status: statusFilter || undefined,
        product: productFilter || undefined,
      });
      setApplications(data);
    } catch (err: any) {
      setError(err.message || 'Failed to load admin applications');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchApplications();
  }, [token, statusFilter, productFilter]);

  const handleOverrideSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!overrideApp) return;
    if (!overrideComment.trim()) {
      setError('Audit comment is mandatory for admin override');
      return;
    }
    setOverriding(true);
    setError(null);
    setSuccessMsg(null);
    try {
      await overrideApplication(overrideApp.id, overrideReasonCode, overrideComment, token);
      setSuccessMsg(`Application ${overrideApp.id} successfully overridden to APPROVED.`);
      setOverrideApp(null);
      setOverrideComment('');
      fetchApplications();
    } catch (err: any) {
      setError(err.message || 'Failed to execute admin override');
    } finally {
      setOverriding(false);
    }
  };

  // Metrics
  const appList = Array.isArray(applications) ? applications : [];
  const totalApps = appList.length;
  const approvedCount = appList.filter((a) => a.status === 'APPROVED' || a.status === 'DISBURSED').length;
  const rejectedCount = appList.filter((a) => a.status === 'REJECTED').length;
  const reviewCount = appList.filter((a) => a.status === 'MANUAL_REVIEW').length;

  return (
    <div className="card" data-testid="dashboard-view">
      <h2>Admin Portfolio & Application Management</h2>

      {error && <div className="badge badge-REJECTED" style={{ marginBottom: '1rem' }}>{error}</div>}
      {successMsg && <div className="badge badge-APPROVED" style={{ marginBottom: '1rem' }}>{successMsg}</div>}
      {loading && <p>Loading application portfolio...</p>}

      {/* Metrics Row */}
      <div className="form-row" style={{ marginBottom: '1.5rem' }}>
        <div className="card" style={{ textAlign: 'center', background: '#f8fafc' }}>
          <h3>Total Applications</h3>
          <p style={{ fontSize: '1.75rem', fontWeight: 'bold' }} data-testid="metric-total-apps">
            {totalApps}
          </p>
        </div>
        <div className="card" style={{ textAlign: 'center', background: '#dcfce7' }}>
          <h3>Approved / Disbursed</h3>
          <p style={{ fontSize: '1.75rem', fontWeight: 'bold', color: 'var(--success)' }}>
            {approvedCount}
          </p>
        </div>
        <div className="card" style={{ textAlign: 'center', background: '#fef9c3' }}>
          <h3>Manual Review</h3>
          <p style={{ fontSize: '1.75rem', fontWeight: 'bold', color: 'var(--warning)' }}>
            {reviewCount}
          </p>
        </div>
        <div className="card" style={{ textAlign: 'center', background: '#fee2e2' }}>
          <h3>Rejected</h3>
          <p style={{ fontSize: '1.75rem', fontWeight: 'bold', color: 'var(--danger)' }}>
            {rejectedCount}
          </p>
        </div>
      </div>

      {/* Filters */}
      <div className="card" style={{ background: '#f8fafc', marginBottom: '1rem' }}>
        <div className="form-row">
          <div className="form-group">
            <label>Filter by Status:</label>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              data-testid="filter-status-select"
            >
              <option value="">All Statuses</option>
              <option value="APPROVED">APPROVED</option>
              <option value="REJECTED">REJECTED</option>
              <option value="MANUAL_REVIEW">MANUAL_REVIEW</option>
              <option value="DISBURSED">DISBURSED</option>
            </select>
          </div>
          <div className="form-group">
            <label>Filter by Product:</label>
            <select
              value={productFilter}
              onChange={(e) => setProductFilter(e.target.value)}
              data-testid="filter-product-select"
            >
              <option value="">All Products</option>
              <option value="PERSONAL">PERSONAL</option>
              <option value="VEHICLE">VEHICLE</option>
              <option value="EDUCATION">EDUCATION</option>
            </select>
          </div>
        </div>
      </div>

      {/* Applications Table */}
      <table className="responsive-cards" data-testid="admin-applications-table">
        <thead>
          <tr>
            <th>App ID</th>
            <th>Applicant</th>
            <th>Product</th>
            <th>Amount</th>
            <th>Status</th>
            <th>Decision</th>
            <th>Score</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {appList.map((app) => (
            <tr key={app.id} data-testid={`admin-app-${app.id}`}>
              <td data-label="App ID"><strong>{app.id}</strong></td>
              <td data-label="Applicant">{app.applicant_name || (app as any).full_name || 'N/A'}</td>
              <td data-label="Product">{app.product}</td>
              <td data-label="Amount">INR {app.amount}</td>
              <td data-label="Status">
                <span className={`badge badge-${app.status}`}>{app.status}</span>
              </td>
              <td data-label="Decision">
                <span className={`badge badge-${app.decision || 'NONE'}`}>{app.decision || 'N/A'}</span>
              </td>
              <td data-label="Score">{app.score || 'N/A'}</td>
              <td data-label="Actions">
                {app.status === 'REJECTED' && app.decision === 'AUTO_REJECT' && (
                  <button
                    type="button"
                    className="btn-danger"
                    onClick={() => setOverrideApp(app)}
                    data-testid={`override-button-${app.id}`}
                    style={{ padding: '0.3rem 0.6rem', fontSize: '0.85rem' }}
                  >
                    Override
                  </button>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      {/* Override Modal */}
      {overrideApp && (
        <div
          data-testid="override-modal"
          style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            background: 'rgba(0,0,0,0.5)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 1000,
          }}
        >
          <div
            className="card"
            style={{ width: '90%', maxWidth: '500px', background: '#fff', padding: '2rem' }}
          >
            <h3>Admin Override: {overrideApp.id}</h3>
            <p className="login-subtitle">
              Overrides AUTO_REJECT decision and transitions application to APPROVED with an audit trail.
            </p>
            <form onSubmit={handleOverrideSubmit} style={{ marginTop: '1rem' }}>
              <div className="form-group">
                <label>Override Reason Code:</label>
                <select
                  value={overrideReasonCode}
                  onChange={(e) => setOverrideReasonCode(e.target.value)}
                  data-testid="override-reason-select"
                >
                  <option value="ADMIN_OVERRIDE">ADMIN_OVERRIDE (Executive Exception)</option>
                </select>
              </div>
              <div className="form-group">
                <label>Audit Comment (Mandatory):</label>
                <textarea
                  value={overrideComment}
                  onChange={(e) => setOverrideComment(e.target.value)}
                  data-testid="override-comment-input"
                  placeholder="State the justification and authorization for this override..."
                  rows={3}
                  required
                />
              </div>
              <div style={{ display: 'flex', gap: '0.75rem', marginTop: '1rem' }}>
                <button
                  type="submit"
                  className="btn-primary"
                  data-testid="override-submit-button"
                  disabled={overriding}
                >
                  {overriding ? 'Processing Override...' : 'Confirm Override'}
                </button>
                <button
                  type="button"
                  className="btn-secondary"
                  onClick={() => setOverrideApp(null)}
                >
                  Cancel
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
