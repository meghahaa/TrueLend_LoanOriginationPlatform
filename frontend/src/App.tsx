import React, { useState } from 'react';
import { Login } from './Login';
import { Apply } from './components/Apply';
import { Track } from './components/Track';
import { Repay } from './components/Repay';
import { Workbench } from './components/Workbench';
import { PolicyEditor } from './components/PolicyEditor';
import { Dashboard } from './components/Dashboard';
import { UserSession } from './types';
import './styles.css';

export const App: React.FC = () => {
  const [session, setSession] = useState<UserSession | null>(null);
  const [activeTab, setActiveTab] = useState<string>('apply');
  const [targetAppId, setTargetAppId] = useState<string>('');

  const handleLogin = (userSession: UserSession) => {
    setSession(userSession);
    if (userSession.role === 'CUSTOMER') {
      setActiveTab('apply');
    } else if (userSession.role === 'UNDERWRITER') {
      setActiveTab('workbench');
    } else if (userSession.role === 'ADMIN') {
      setActiveTab('dashboard');
    }
  };

  const handleLogout = () => {
    setSession(null);
    setActiveTab('apply');
    setTargetAppId('');
  };

  const handleNavigateToTrack = (id: string) => {
    setTargetAppId(id);
    setActiveTab('track');
  };

  const handleNavigateToRepay = (id: string) => {
    setTargetAppId(id);
    setActiveTab('repay');
  };

  if (!session) {
    return <Login onLogin={handleLogin} />;
  }

  return (
    <div className="app-container" data-testid="app-container">
      <header>
        <div className="brand-title">TrueLend Platform</div>
        <div className="user-badge">
          <span data-testid="current-user-info">
            User: <strong>{session.userId}</strong> (
            <span className={`badge badge-${session.role}`}>{session.role}</span>)
          </span>
          <button
            type="button"
            className="btn-secondary"
            onClick={handleLogout}
            data-testid="logout-button"
            style={{ padding: '0.3rem 0.6rem', fontSize: '0.85rem' }}
          >
            Logout
          </button>
        </div>
      </header>

      <nav data-testid="app-navigation">
        {session.role === 'CUSTOMER' && (
          <>
            <button
              type="button"
              className={activeTab === 'apply' ? 'active' : ''}
              onClick={() => setActiveTab('apply')}
              data-testid="nav-tab-apply"
            >
              Apply for Loan
            </button>
            <button
              type="button"
              className={activeTab === 'track' ? 'active' : ''}
              onClick={() => setActiveTab('track')}
              data-testid="nav-tab-track"
            >
              Track Application
            </button>
            <button
              type="button"
              className={activeTab === 'repay' ? 'active' : ''}
              onClick={() => setActiveTab('repay')}
              data-testid="nav-tab-repay"
            >
              Repayment & Schedule
            </button>
          </>
        )}

        {session.role === 'UNDERWRITER' && (
          <button
            type="button"
            className={activeTab === 'workbench' ? 'active' : ''}
            onClick={() => setActiveTab('workbench')}
            data-testid="nav-tab-workbench"
          >
            Underwriter Workbench
          </button>
        )}

        {session.role === 'ADMIN' && (
          <>
            <button
              type="button"
              className={activeTab === 'dashboard' ? 'active' : ''}
              onClick={() => setActiveTab('dashboard')}
              data-testid="nav-tab-dashboard"
            >
              Portfolio Dashboard
            </button>
            <button
              type="button"
              className={activeTab === 'policy-editor' ? 'active' : ''}
              onClick={() => setActiveTab('policy-editor')}
              data-testid="nav-tab-policy-editor"
            >
              Policy Editor
            </button>
            <button
              type="button"
              className={activeTab === 'workbench' ? 'active' : ''}
              onClick={() => setActiveTab('workbench')}
              data-testid="nav-tab-workbench"
            >
              Underwriter Workbench
            </button>
          </>
        )}
      </nav>

      <main>
        {activeTab === 'apply' && session.role === 'CUSTOMER' && (
          <Apply token={session.token} onNavigateToTrack={handleNavigateToTrack} />
        )}
        {activeTab === 'track' && session.role === 'CUSTOMER' && (
          <Track
            token={session.token}
            initialAppId={targetAppId}
            onNavigateToRepay={handleNavigateToRepay}
          />
        )}
        {activeTab === 'repay' && session.role === 'CUSTOMER' && (
          <Repay token={session.token} initialAppId={targetAppId} />
        )}
        {activeTab === 'workbench' && (session.role === 'UNDERWRITER' || session.role === 'ADMIN') && (
          <Workbench token={session.token} />
        )}
        {activeTab === 'policy-editor' && session.role === 'ADMIN' && (
          <PolicyEditor token={session.token} />
        )}
        {activeTab === 'dashboard' && session.role === 'ADMIN' && (
          <Dashboard token={session.token} />
        )}
      </main>
    </div>
  );
};

export default App;
