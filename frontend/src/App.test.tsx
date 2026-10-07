import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import App from './App';

describe('App Root Component', () => {
  it('renders login screen initially and switches to customer views upon login', async () => {
    render(<App />);

    expect(screen.getByTestId('login-container')).toBeInTheDocument();

    const submitBtn = screen.getByTestId('login-submit-button');
    await userEvent.click(submitBtn);

    // After login as demo-customer-1
    expect(screen.getByTestId('current-user-info')).toHaveTextContent('cust-001 (CUSTOMER)');
    expect(screen.getByTestId('nav-tab-apply')).toBeInTheDocument();
    expect(screen.getByTestId('nav-tab-track')).toBeInTheDocument();
    expect(screen.getByTestId('nav-tab-repay')).toBeInTheDocument();

    // Underwriter / Admin tabs should not be visible for customer
    expect(screen.queryByTestId('nav-tab-workbench')).not.toBeInTheDocument();
    expect(screen.queryByTestId('nav-tab-dashboard')).not.toBeInTheDocument();
  });

  it('renders underwriter workbench tabs when logged in as underwriter', async () => {
    render(<App />);

    const select = screen.getByTestId('token-select');
    await userEvent.selectOptions(select, 'demo-underwriter-1');

    const submitBtn = screen.getByTestId('login-submit-button');
    await userEvent.click(submitBtn);

    expect(screen.getByTestId('current-user-info')).toHaveTextContent('uw-001 (UNDERWRITER)');
    expect(screen.getByTestId('nav-tab-workbench')).toBeInTheDocument();
    expect(screen.queryByTestId('nav-tab-apply')).not.toBeInTheDocument();
  });

  it('renders admin dashboard and policy editor tabs when logged in as admin', async () => {
    render(<App />);

    const select = screen.getByTestId('token-select');
    await userEvent.selectOptions(select, 'demo-admin-1');

    const submitBtn = screen.getByTestId('login-submit-button');
    await userEvent.click(submitBtn);

    expect(screen.getByTestId('current-user-info')).toHaveTextContent('adm-001 (ADMIN)');
    expect(screen.getByTestId('nav-tab-dashboard')).toBeInTheDocument();
    expect(screen.getByTestId('nav-tab-policy-editor')).toBeInTheDocument();
    expect(screen.getByTestId('nav-tab-workbench')).toBeInTheDocument();
  });
});
