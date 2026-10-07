export type Role = 'CUSTOMER' | 'UNDERWRITER' | 'ADMIN';

export interface UserSession {
  token: string;
  userId: string;
  role: Role;
}

export interface DemoTokenOption {
  token: string;
  userId: string;
  role: Role;
  label: string;
}

export const DEMO_TOKENS: DemoTokenOption[] = [
  {
    token: 'demo-customer-1',
    userId: 'cust-001',
    role: 'CUSTOMER',
    label: 'Customer 1 (cust-001) - CUSTOMER',
  },
  {
    token: 'demo-customer-2',
    userId: 'cust-002',
    role: 'CUSTOMER',
    label: 'Customer 2 (cust-002) - CUSTOMER',
  },
  {
    token: 'demo-underwriter-1',
    userId: 'uw-001',
    role: 'UNDERWRITER',
    label: 'Underwriter 1 (uw-001) - UNDERWRITER',
  },
  {
    token: 'demo-admin-1',
    userId: 'adm-001',
    role: 'ADMIN',
    label: 'Admin 1 (adm-001) - ADMIN',
  },
];
