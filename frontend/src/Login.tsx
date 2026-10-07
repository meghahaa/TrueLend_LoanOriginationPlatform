import React, { useState } from 'react';
import { DEMO_TOKENS, UserSession } from './types';

interface LoginProps {
  onLogin: (session: UserSession) => void;
}

export const Login: React.FC<LoginProps> = ({ onLogin }) => {
  const [selectedToken, setSelectedToken] = useState<string>(DEMO_TOKENS[0].token);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const found = DEMO_TOKENS.find((t) => t.token === selectedToken);
    if (found) {
      onLogin({
        token: found.token,
        userId: found.userId,
        role: found.role,
      });
    }
  };

  return (
    <div className="login-container" data-testid="login-container">
      <div className="login-card">
        <h1 data-testid="login-title">TrueLend — Loan Origination</h1>
        <p className="login-subtitle">Select a demo actor / role to access the platform</p>
        <form onSubmit={handleSubmit} data-testid="login-form">
          <div className="form-group">
            <label htmlFor="token-select">Demo Role & Token:</label>
            <select
              id="token-select"
              data-testid="token-select"
              value={selectedToken}
              onChange={(e) => setSelectedToken(e.target.value)}
            >
              {DEMO_TOKENS.map((item) => (
                <option key={item.token} value={item.token}>
                  {item.label} (token: {item.token})
                </option>
              ))}
            </select>
          </div>
          <button type="submit" data-testid="login-submit-button" className="btn-primary">
            Sign In
          </button>
        </form>
      </div>
    </div>
  );
};
