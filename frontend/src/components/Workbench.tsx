import React, { useEffect, useState } from 'react';
import {
  ApplicationResponse,
  decideApplication,
  getUnderwriterQueue,
  verifyDocument,
} from '../api';

interface WorkbenchProps {
  token: string;
}

export const Workbench: React.FC<WorkbenchProps> = ({ token }) => {
  const [queue, setQueue] = useState<ApplicationResponse[]>([]);
  const [selectedApp, setSelectedApp] = useState<ApplicationResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  // Decision & rejection reason state
  const [decisionComment, setDecisionComment] = useState<string>('Verified all required information');
  const [rejectReason, setRejectReason] = useState<string>('Document quality does not meet standards');

  const fetchQueue = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getUnderwriterQueue(token);
      setQueue(data);
      if (selectedApp) {
        const refreshed = data.find((a) => a.id === selectedApp.id);
        setSelectedApp(refreshed || null);
      }
    } catch (err: any) {
      setError(err.message || 'Failed to load underwriter queue');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchQueue();
  }, [token]);

  const handleVerifyDoc = async (docType: string, status: 'VERIFIED' | 'REJECTED') => {
    if (!selectedApp) return;
    setError(null);
    setSuccessMsg(null);
    const reason = status === 'REJECTED' ? rejectReason : 'Verified valid and authentic';
    try {
      await verifyDocument(selectedApp.id, docType, status, reason, token);
      setSuccessMsg(`Document ${docType} marked as ${status}`);
      // Refresh local app state
      const updatedDocs = selectedApp.documents.map((d) =>
        d.doc_type === docType ? { ...d, status, rejection_reason: status === 'REJECTED' ? reason : undefined } : d
      );
      setSelectedApp({ ...selectedApp, documents: updatedDocs });
      fetchQueue();
    } catch (err: any) {
      setError(err.message || `Failed to mark ${docType} as ${status}`);
    }
  };

  const handleDecision = async (action: 'APPROVE' | 'REJECT') => {
    if (!selectedApp) return;
    setError(null);
    setSuccessMsg(null);
    const reasonCode = action === 'APPROVE' ? 'MANUAL_APPROVED' : 'MANUAL_REJECTED';
    try {
      await decideApplication(selectedApp.id, action, reasonCode, decisionComment, token);
      setSuccessMsg(`Application ${selectedApp.id} manually ${action === 'APPROVE' ? 'approved' : 'rejected'}`);
      fetchQueue();
    } catch (err: any) {
      setError(err.message || `Failed to submit manual decision`);
    }
  };

  return (
    <div className="card" data-testid="workbench-view">
      <h2>Underwriter Workbench & Document Queue</h2>

      {error && <div className="badge badge-REJECTED" style={{ marginBottom: '1rem' }}>{error}</div>}
      {successMsg && (
        <div className="badge badge-APPROVED" style={{ marginBottom: '1rem' }}>
          {successMsg}
        </div>
      )}

      {loading && <p>Loading underwriting queue...</p>}

      {!loading && queue.length === 0 && (
        <p>No applications currently waiting in the underwriter queue.</p>
      )}

      <table className="responsive-cards" data-testid="queue-table">
        <thead>
          <tr>
            <th>App ID</th>
            <th>Applicant</th>
            <th>Product</th>
            <th>Amount</th>
            <th>Status</th>
            <th>Decision</th>
            <th>Action</th>
          </tr>
        </thead>
        <tbody>
          {queue.map((app) => (
            <tr key={app.id} data-testid={`workbench-app-${app.id}`}>
              <td data-label="App ID"><strong>{app.id}</strong></td>
              <td data-label="Applicant">{app.applicant_name || 'N/A'}</td>
              <td data-label="Product">{app.product}</td>
              <td data-label="Amount">INR {app.amount}</td>
              <td data-label="Status">
                <span className={`badge badge-${app.status}`}>{app.status}</span>
              </td>
              <td data-label="Decision">
                <span className={`badge badge-${app.decision || 'NONE'}`}>{app.decision || 'N/A'}</span>
              </td>
              <td data-label="Action">
                <button
                  type="button"
                  className="btn-secondary"
                  onClick={() => setSelectedApp(app)}
                  data-testid={`inspect-button-${app.id}`}
                  style={{ padding: '0.3rem 0.6rem', fontSize: '0.85rem' }}
                >
                  Review
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      {selectedApp && (
        <div
          className="card"
          data-testid="selected-app-details"
          style={{ marginTop: '1.5rem', background: '#f8fafc', border: '2px solid var(--primary)' }}
        >
          <h3>
            Reviewing Application: <span data-testid="selected-app-id">{selectedApp.id}</span>
          </h3>
          <div className="form-row" style={{ marginTop: '0.75rem' }}>
            <div>
              <strong>Applicant: </strong>
              <span>{selectedApp.applicant_name || 'N/A'}</span>
            </div>
            <div>
              <strong>Product: </strong>
              <span>{selectedApp.product}</span>
            </div>
            <div>
              <strong>Requested: </strong>
              <span>INR {selectedApp.amount} ({selectedApp.tenure_months}m)</span>
            </div>
            <div>
              <strong>Score: </strong>
              <span>{selectedApp.score || 'N/A'}</span>
            </div>
            <div>
              <strong>Status: </strong>
              <span className={`badge badge-${selectedApp.status}`}>{selectedApp.status}</span>
            </div>
          </div>

          <h4 style={{ marginTop: '1.5rem' }}>Uploaded Documents Verification</h4>
          <div className="form-group" style={{ marginTop: '0.5rem', maxWidth: '400px' }}>
            <label>Rejection Reason (if rejecting a document):</label>
            <input
              type="text"
              value={rejectReason}
              onChange={(e) => setRejectReason(e.target.value)}
              placeholder="e.g. Blurry or expired document"
              data-testid="document-reject-reason-input"
            />
          </div>

          <table className="responsive-cards" style={{ marginTop: '0.5rem' }}>
            <thead>
              <tr>
                <th>Doc Type</th>
                <th>Filename</th>
                <th>Status</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {selectedApp.documents.map((doc) => (
                <tr key={doc.doc_type}>
                  <td data-label="Doc Type"><strong>{doc.doc_type}</strong></td>
                  <td data-label="Filename">{doc.filename || 'Not provided'}</td>
                  <td data-label="Status">
                    <span className={`badge badge-${doc.status}`}>{doc.status}</span>
                  </td>
                  <td data-label="Actions">
                    {doc.status === 'UPLOADED' && (
                      <div style={{ display: 'flex', gap: '0.5rem' }}>
                        <button
                          type="button"
                          className="btn-primary"
                          onClick={() => handleVerifyDoc(doc.doc_type, 'VERIFIED')}
                          data-testid={`verify-doc-${doc.doc_type}`}
                          style={{ padding: '0.3rem 0.6rem', fontSize: '0.85rem' }}
                        >
                          Verify
                        </button>
                        <button
                          type="button"
                          className="btn-danger"
                          onClick={() => handleVerifyDoc(doc.doc_type, 'REJECTED')}
                          data-testid={`reject-doc-${doc.doc_type}`}
                          style={{ padding: '0.3rem 0.6rem', fontSize: '0.85rem' }}
                        >
                          Reject
                        </button>
                      </div>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>

          <div style={{ marginTop: '1.5rem', borderTop: '1px solid var(--border)', paddingTop: '1rem' }}>
            <h4>Underwriter Decision & Comment</h4>
            <div className="form-group" style={{ marginTop: '0.5rem' }}>
              <label>Decision Notes / Audit Comment:</label>
              <textarea
                value={decisionComment}
                onChange={(e) => setDecisionComment(e.target.value)}
                data-testid="decision-comment-input"
                rows={2}
              />
            </div>
            <div style={{ display: 'flex', gap: '0.75rem' }}>
              <button
                type="button"
                className="btn-primary"
                onClick={() => handleDecision('APPROVE')}
                data-testid="decision-approve-button"
              >
                Approve Application
              </button>
              <button
                type="button"
                className="btn-danger"
                onClick={() => handleDecision('REJECT')}
                data-testid="decision-reject-button"
              >
                Reject Application
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
