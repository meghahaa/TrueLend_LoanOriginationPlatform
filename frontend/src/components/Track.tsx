import React, { useEffect, useState } from 'react';
import { ApplicationResponse, getApplication, uploadDocument } from '../api';

interface TrackProps {
  token: string;
  initialAppId?: string;
  onNavigateToRepay?: (id: string) => void;
}

export const Track: React.FC<TrackProps> = ({ token, initialAppId = '', onNavigateToRepay }) => {
  const [appId, setAppId] = useState<string>(initialAppId);
  const [application, setApplication] = useState<ApplicationResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const [uploadFilenames, setUploadFilenames] = useState<Record<string, string>>({});
  const [uploadingDoc, setUploadingDoc] = useState<string | null>(null);

  const fetchApp = async (id: string) => {
    if (!id.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const data = await getApplication(id.trim(), token);
      setApplication(data);
    } catch (err: any) {
      setError(err.message || 'Application not found');
      setApplication(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (initialAppId) {
      fetchApp(initialAppId);
    }
  }, [initialAppId]);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    fetchApp(appId);
  };

  const handleUpload = async (docType: string) => {
    const filename = uploadFilenames[docType] || `${docType.toLowerCase()}_uploaded.pdf`;
    if (!application) return;
    setUploadingDoc(docType);
    try {
      const updated = await uploadDocument(application.id, docType, filename, token);
      setApplication(updated);
      setUploadFilenames((prev) => ({ ...prev, [docType]: '' }));
    } catch (err: any) {
      setError(err.message || 'Failed to upload document');
    } finally {
      setUploadingDoc(null);
    }
  };

  return (
    <div className="card" data-testid="track-view">
      <h2>Track Loan Application</h2>

      <form onSubmit={handleSearch} style={{ display: 'flex', gap: '0.5rem', marginBottom: '1.5rem' }}>
        <input
          type="text"
          placeholder="Enter Application ID (e.g. app-100)"
          value={appId}
          onChange={(e) => setAppId(e.target.value)}
          data-testid="track-input-app-id"
          style={{ flex: 1 }}
          required
        />
        <button type="submit" className="btn-primary" data-testid="track-search-button">
          {loading ? 'Searching...' : 'Track'}
        </button>
      </form>

      {error && <div className="badge badge-REJECTED" style={{ marginBottom: '1rem' }}>{error}</div>}

      {application && (
        <div data-testid="track-details">
          <div className="card" style={{ background: '#f8fafc' }}>
            <p>
              <strong>Application ID: </strong>
              <span data-testid="track-app-id">{application.id}</span>
            </p>
            <p>
              <strong>Product: </strong>
              <span>{application.product}</span>
            </p>
            <p>
              <strong>Requested Amount: </strong>
              <span>INR {application.amount}</span> ({application.tenure_months} months)
            </p>
            <p>
              <strong>Status: </strong>
              <span data-testid="track-status" className={`badge badge-${application.status}`}>
                {application.status}
              </span>
            </p>
            {application.decision && (
              <p>
                <strong>Decision: </strong>
                <span className={`badge badge-${application.decision}`}>{application.decision}</span>
              </p>
            )}
            {application.score && (
              <p>
                <strong>Credit Score: </strong>
                <span>{application.score}</span>
              </p>
            )}
            {application.reason_codes && application.reason_codes.length > 0 && (
              <p>
                <strong>Reason Codes: </strong>
                <span>{application.reason_codes.join(', ')}</span>
              </p>
            )}
            <p>
              <strong>Masked PAN: </strong>
              <span data-testid="track-masked-pan">{application.masked_pan || 'XXXXXX1234'}</span>
            </p>
            <p>
              <strong>Masked Aadhaar: </strong>
              <span data-testid="track-masked-aadhaar">{application.masked_aadhaar || 'XXXX0001'}</span>
            </p>

            {(application.status === 'APPROVED' || application.status === 'DISBURSED') && onNavigateToRepay && (
              <div style={{ marginTop: '1rem' }}>
                <button
                  type="button"
                  className="btn-primary"
                  onClick={() => onNavigateToRepay(application.id)}
                  data-testid="track-repay-button"
                >
                  View Repayment Schedule & Pay
                </button>
              </div>
            )}
          </div>

          <h3 style={{ marginTop: '1.5rem' }}>Document Verification Checklist</h3>
          <table className="responsive-cards" data-testid="track-documents-table">
            <thead>
              <tr>
                <th>Document Type</th>
                <th>Status</th>
                <th>Filename / Reason</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {application.documents.map((doc) => (
                <tr key={doc.doc_type}>
                  <td data-label="Document Type"><strong>{doc.doc_type}</strong></td>
                  <td data-label="Status">
                    <span data-testid={`doc-status-${doc.doc_type}`} className={`badge badge-${doc.status}`}>
                      {doc.status}
                    </span>
                  </td>
                  <td data-label="Filename / Reason">
                    {doc.filename && <div>File: {doc.filename}</div>}
                    {doc.rejection_reason && (
                      <div style={{ color: 'var(--danger)', fontSize: '0.85rem' }}>
                        Reason: {doc.rejection_reason}
                      </div>
                    )}
                  </td>
                  <td data-label="Action">
                    {(doc.status === 'MISSING' || doc.status === 'REJECTED') && (
                      <div style={{ display: 'flex', gap: '0.25rem' }}>
                        <input
                          type="text"
                          placeholder="file_upload.pdf"
                          value={uploadFilenames[doc.doc_type] || ''}
                          onChange={(e) =>
                            setUploadFilenames({ ...uploadFilenames, [doc.doc_type]: e.target.value })
                          }
                          data-testid={`upload-input-${doc.doc_type}`}
                          style={{ width: '130px', padding: '0.3rem' }}
                        />
                        <button
                          type="button"
                          className="btn-secondary"
                          onClick={() => handleUpload(doc.doc_type)}
                          disabled={uploadingDoc === doc.doc_type}
                          data-testid={`upload-button-${doc.doc_type}`}
                          style={{ padding: '0.3rem 0.6rem', fontSize: '0.85rem' }}
                        >
                          {uploadingDoc === doc.doc_type ? 'Uploading...' : 'Upload'}
                        </button>
                      </div>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};
