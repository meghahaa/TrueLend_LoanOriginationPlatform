import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { Login } from './Login';

describe('Login Component', () => {
  it('renders all demo tokens and roles as specified in specs/app_spec.md', () => {
    render(<Login onLogin={vi.fn()} />);

    expect(screen.getByTestId('login-title')).toHaveTextContent(/TrueLend/i);
    expect(screen.getByTestId('token-select')).toBeInTheDocument();

    const options = screen.getAllByRole('option');
    expect(options).toHaveLength(4);
    expect(options[0]).toHaveTextContent(/demo-customer-1/i);
    expect(options[0]).toHaveTextContent(/cust-001/i);
    expect(options[0]).toHaveTextContent(/CUSTOMER/i);

    expect(options[1]).toHaveTextContent(/demo-customer-2/i);
    expect(options[2]).toHaveTextContent(/demo-underwriter-1/i);
    expect(options[3]).toHaveTextContent(/demo-admin-1/i);
  });

  it('selects an underwriter token and logs in with underwriter credentials', async () => {
    const handleLogin = vi.fn();
    render(<Login onLogin={handleLogin} />);

    const select = screen.getByTestId('token-select');
    await userEvent.selectOptions(select, 'demo-underwriter-1');

    const submitBtn = screen.getByTestId('login-submit-button');
    await userEvent.click(submitBtn);

    expect(handleLogin).toHaveBeenCalledWith({
      token: 'demo-underwriter-1',
      userId: 'uw-001',
      role: 'UNDERWRITER',
    });
  });

  it('selects an admin token and logs in with admin credentials', async () => {
    const handleLogin = vi.fn();
    render(<Login onLogin={handleLogin} />);

    const select = screen.getByTestId('token-select');
    await userEvent.selectOptions(select, 'demo-admin-1');

    const submitBtn = screen.getByTestId('login-submit-button');
    await userEvent.click(submitBtn);

    expect(handleLogin).toHaveBeenCalledWith({
      token: 'demo-admin-1',
      userId: 'adm-001',
      role: 'ADMIN',
    });
  });
});
