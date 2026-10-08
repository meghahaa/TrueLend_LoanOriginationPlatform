export interface Product {
  product_code: string;
  display_name: string;
  min_monthly_income: string;
  min_age: number;
  max_age: number;
  min_amount: string;
  max_amount: string;
  min_tenure_months: number;
  max_tenure_months: number;
  annual_rate_percent: string;
  approve_score: number;
  reject_score: number;
  max_foir: string;
  required_documents: string[];
}

export interface ProductCatalogResponse {
  policy_version: number;
  products: Product[];
}

export interface ApplicationSubmission {
  product: string;
  amount: string;
  tenure_months: number;
  applicant: {
    full_name: string;
    age: number;
    monthly_income: string;
    pan: string;
    aadhaar: string;
    credit_history: string;
    has_default: boolean;
  };
  documents?: { doc_type: string; filename: string }[];
}

export interface ApplicationDocument {
  doc_type: string;
  filename?: string;
  status: 'MISSING' | 'UPLOADED' | 'VERIFIED' | 'REJECTED';
  rejection_reason?: string;
}

export interface ApplicationResponse {
  id: string;
  product: string;
  amount: string;
  tenure_months: number;
  status: string;
  decision?: string;
  score?: number;
  reason_codes?: string[];
  policy_version: number;
  masked_pan?: string;
  masked_aadhaar?: string;
  applicant_name?: string;
  documents: ApplicationDocument[];
  missing_documents?: string[];
}

export interface ScheduleRowDto {
  installment_number: number;
  due_date: string;
  opening_balance: string;
  principal_component: string;
  interest_component: string;
  emi_amount: string;
  remaining_balance: string;
}

export interface ScheduleResponse {
  application_id: string;
  emi_amount: string;
  total_principal: string;
  total_interest: string;
  total_payable: string;
  rows: ScheduleRowDto[];
}

export interface RepaymentResponse {
  application_id: string;
  amount_paid: string;
  paid_on: string;
  outstanding_principal: string;
  total_remaining_due: string;
  dpd: number;
  delinquency_bucket: string;
  allocations: {
    installment_number: number;
    interest_allocated: string;
    principal_allocated: string;
  }[];
}

export interface PolicyVersionDto {
  version: number;
  effective_from: string;
  created_by: string;
  change_note: string;
}

export const fetchProducts = async (): Promise<ProductCatalogResponse> => {
  const res = await fetch('/products');
  if (!res.ok) throw new Error('Failed to fetch products');
  return res.json();
};

export const submitApplication = async (
  data: ApplicationSubmission,
  token: string
): Promise<ApplicationResponse> => {
  const res = await fetch('/applications', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail ? JSON.stringify(err.detail) : 'Failed to submit application');
  }
  return res.json();
};

export const getApplication = async (id: string, token: string): Promise<ApplicationResponse> => {
  const res = await fetch(`/applications/${id}`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) throw new Error('Failed to fetch application');
  return res.json();
};

export const uploadDocument = async (
  id: string,
  doc_type: string,
  filename: string,
  token: string
): Promise<ApplicationResponse> => {
  const res = await fetch(`/applications/${id}/documents`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ doc_type, filename }),
  });
  if (!res.ok) throw new Error('Failed to upload document');
  return res.json();
};

export const getUnderwriterQueue = async (token: string): Promise<ApplicationResponse[]> => {
  const res = await fetch('/underwriter/queue', {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) throw new Error('Failed to fetch underwriter queue');
  return res.json();
};

export const verifyDocument = async (
  applicationId: string,
  docType: string,
  status: 'VERIFIED' | 'REJECTED',
  reason: string,
  token: string
): Promise<void> => {
  const res = await fetch(`/applications/${applicationId}/documents/${docType}/verify`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ status, reason }),
  });
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || 'Failed to verify document');
  }
};

export const decideApplication = async (
  applicationId: string,
  action: 'APPROVE' | 'REJECT',
  reason_code: string,
  comment: string,
  token: string
): Promise<void> => {
  const res = await fetch(`/applications/${applicationId}/decision`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ action, reason_code, comment }),
  });
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || 'Failed to decide application');
  }
};

export const getSchedule = async (id: string, token: string): Promise<ScheduleResponse> => {
  const res = await fetch(`/applications/${id}/schedule`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) throw new Error('Failed to fetch schedule');
  return res.json();
};

export const postRepayment = async (
  id: string,
  amount: string,
  paid_on: string,
  token: string
): Promise<RepaymentResponse> => {
  const res = await fetch(`/applications/${id}/repayments`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ amount, paid_on }),
  });
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || 'Failed to post repayment');
  }
  return res.json();
};

export const listPolicies = async (token: string): Promise<PolicyVersionDto[]> => {
  const res = await fetch('/admin/policies', {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) throw new Error('Failed to fetch policies');
  return res.json();
};

export const publishPolicy = async (
  data: { products?: Record<string, any>; change_note: string },
  token: string
): Promise<{ version: number }> => {
  const res = await fetch('/admin/policies', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail ? JSON.stringify(err.detail) : 'Failed to publish policy');
  }
  return res.json();
};

export const getAdminApplications = async (
  token: string,
  filter?: { status?: string; product?: string }
): Promise<ApplicationResponse[]> => {
  const params = new URLSearchParams();
  if (filter?.status) params.set('status', filter.status);
  if (filter?.product) params.set('product', filter.product);
  const res = await fetch(`/admin/applications?${params.toString()}`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) throw new Error('Failed to fetch admin applications');
  const data = await res.json();
  if (Array.isArray(data)) {
    return data;
  }
  if (data && Array.isArray(data.items)) {
    return data.items;
  }
  return [];
};

export const overrideApplication = async (
  id: string,
  reason_code: string,
  comment: string,
  token: string
): Promise<void> => {
  const res = await fetch(`/admin/applications/${id}/override`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ reason_code, comment }),
  });
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || 'Failed to override application');
  }
};
