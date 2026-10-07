import React, { useEffect, useState } from 'react';
import {
  ApplicationResponse,
  ApplicationSubmission,
  fetchProducts,
  Product,
  submitApplication,
} from '../api';

interface ApplyProps {
  token: string;
  onNavigateToTrack?: (id: string) => void;
}

export const Apply: React.FC<ApplyProps> = ({ token, onNavigateToTrack }) => {
  const [products, setProducts] = useState<Product[]>([]);
  const [selectedProductCode, setSelectedProductCode] = useState<string>('PERSONAL');
  const [amount, setAmount] = useState<string>('100000.00');
  const [tenureMonths, setTenureMonths] = useState<string>('24');

  // Applicant fields
  const [fullName, setFullName] = useState<string>('');
  const [age, setAge] = useState<string>('30');
  const [monthlyIncome, setMonthlyIncome] = useState<string>('60000.00');
  const [pan, setPan] = useState<string>('TESTP1234X');
  const [aadhaar, setAadhaar] = useState<string>('999900000001');
  const [creditHistory, setCreditHistory] = useState<string>('CLEAN');
  const [hasDefault, setHasDefault] = useState<boolean>(false);

  // Document filenames
  const [docUploads, setDocUploads] = useState<Record<string, string>>({});

  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<ApplicationResponse | null>(null);

  useEffect(() => {
    fetchProducts()
      .then((res) => {
        setProducts(res.products);
        if (res.products.length > 0) {
          setSelectedProductCode(res.products[0].product_code);
        }
      })
      .catch((err) => setError(err.message));
  }, []);

  const selectedProduct = products.find((p) => p.product_code === selectedProductCode);

  const handleDocChange = (docType: string, filename: string) => {
    setDocUploads((prev) => ({ ...prev, [docType]: filename }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setResult(null);

    const docs = selectedProduct?.required_documents
      .map((docType) => ({
        doc_type: docType,
        filename: docUploads[docType] || `${docType.toLowerCase()}_sample.pdf`,
      }))
      .filter((d) => d.filename);

    const payload: ApplicationSubmission = {
      product: selectedProductCode,
      amount,
      tenure_months: parseInt(tenureMonths, 10),
      applicant: {
        full_name: fullName,
        age: parseInt(age, 10),
        monthly_income: monthlyIncome,
        pan,
        aadhaar,
        credit_history: creditHistory,
        has_default: hasDefault,
      },
      documents: docs,
    };

    try {
      const res = await submitApplication(payload, token);
      setResult(res);
    } catch (err: any) {
      setError(err.message || 'Application submission failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="card" data-testid="apply-view">
      <h2>Apply for a Loan</h2>
      {error && <div className="badge badge-REJECTED" style={{ marginBottom: '1rem' }}>{error}</div>}

      {result ? (
        <div data-testid="apply-result" style={{ background: '#f8fafc', padding: '1rem', borderRadius: '8px' }}>
          <h3>Application Submitted Successfully!</h3>
          <p>
            <strong>Application ID: </strong>
            <span data-testid="apply-result-id">{result.id}</span>
          </p>
          <p>
            <strong>Status: </strong>
            <span data-testid="apply-result-status" className={`badge badge-${result.status}`}>
              {result.status}
            </span>
          </p>
          {result.decision && (
            <p>
              <strong>Decision: </strong>
              <span data-testid="apply-result-decision" className={`badge badge-${result.decision}`}>
                {result.decision}
              </span>
            </p>
          )}
          {result.reason_codes && result.reason_codes.length > 0 && (
            <p>
              <strong>Reason Codes: </strong>
              {result.reason_codes.join(', ')}
            </p>
          )}
          <div style={{ marginTop: '1rem' }}>
            {onNavigateToTrack && (
              <button
                type="button"
                className="btn-primary"
                onClick={() => onNavigateToTrack(result.id)}
              >
                Track This Application
              </button>
            )}
          </div>
        </div>
      ) : (
        <form onSubmit={handleSubmit} data-testid="apply-form">
          <div className="form-group">
            <label htmlFor="product-select">Select Loan Product:</label>
            <select
              id="product-select"
              data-testid="product-select"
              value={selectedProductCode}
              onChange={(e) => setSelectedProductCode(e.target.value)}
            >
              {products.map((p) => (
                <option key={p.product_code} value={p.product_code}>
                  {p.display_name} ({p.annual_rate_percent}% p.a.)
                </option>
              ))}
            </select>
          </div>

          <div className="form-row">
            <div className="form-group">
              <label>Applicant Full Name:</label>
              <input
                type="text"
                data-testid="applicant-name-input"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                required
              />
            </div>
            <div className="form-group">
              <label>Age (years):</label>
              <input
                type="number"
                data-testid="applicant-age-input"
                value={age}
                onChange={(e) => setAge(e.target.value)}
                required
              />
            </div>
          </div>

          <div className="form-row">
            <div className="form-group">
              <label>Monthly Income (INR):</label>
              <input
                type="text"
                data-testid="applicant-income-input"
                value={monthlyIncome}
                onChange={(e) => setMonthlyIncome(e.target.value)}
                required
              />
            </div>
            <div className="form-group">
              <label>Credit History:</label>
              <select
                data-testid="applicant-history-select"
                value={creditHistory}
                onChange={(e) => setCreditHistory(e.target.value)}
              >
                <option value="CLEAN">Clean (No defaults/delinquencies)</option>
                <option value="THIN">Thin File (Limited history)</option>
                <option value="LATE_PAYMENTS">Late Payments</option>
              </select>
            </div>
          </div>

          <div className="form-row">
            <div className="form-group">
              <label>Synthetic PAN (e.g. TESTP1234X):</label>
              <input
                type="text"
                data-testid="applicant-pan-input"
                value={pan}
                onChange={(e) => setPan(e.target.value)}
                required
              />
            </div>
            <div className="form-group">
              <label>Synthetic Aadhaar (e.g. 999900000001):</label>
              <input
                type="text"
                data-testid="applicant-aadhaar-input"
                value={aadhaar}
                onChange={(e) => setAadhaar(e.target.value)}
                required
              />
            </div>
          </div>

          <div className="form-row">
            <div className="form-group">
              <label>Requested Loan Amount (INR):</label>
              <input
                type="text"
                data-testid="loan-amount-input"
                value={amount}
                onChange={(e) => setAmount(e.target.value)}
                required
              />
            </div>
            <div className="form-group">
              <label>Tenure (Months):</label>
              <input
                type="number"
                data-testid="loan-tenure-input"
                value={tenureMonths}
                onChange={(e) => setTenureMonths(e.target.value)}
                required
              />
            </div>
          </div>

          <div className="form-group" style={{ marginTop: '0.5rem' }}>
            <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <input
                type="checkbox"
                data-testid="applicant-default-checkbox"
                checked={hasDefault}
                onChange={(e) => setHasDefault(e.target.checked)}
              />
              Has prior loan default
            </label>
          </div>

          {selectedProduct && selectedProduct.required_documents.length > 0 && (
            <div style={{ marginTop: '1rem', marginBottom: '1rem' }}>
              <h4>Required Documents for {selectedProduct.display_name}:</h4>
              {selectedProduct.required_documents.map((docType) => (
                <div key={docType} className="form-group" style={{ marginTop: '0.5rem' }}>
                  <label>{docType}:</label>
                  <input
                    type="text"
                    placeholder={`${docType.toLowerCase()}_file.pdf`}
                    value={docUploads[docType] || ''}
                    onChange={(e) => handleDocChange(docType, e.target.value)}
                  />
                </div>
              ))}
            </div>
          )}

          <button
            type="submit"
            className="btn-primary"
            data-testid="apply-submit-button"
            disabled={loading}
          >
            {loading ? 'Submitting...' : 'Submit Application'}
          </button>
        </form>
      )}
    </div>
  );
};
