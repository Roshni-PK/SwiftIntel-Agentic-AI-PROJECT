import React from 'react';
import {
  ShieldCheck, LayoutDashboard, Search, Database, BarChart3, Settings,
  Plus, Menu, X, CircleHelp, LogOut
} from 'lucide-react';

interface NavbarProps {
  activeTab: string;
  setActiveTab: (tab: string) => void;
  onNewInvestigation: () => void;
  isDemoMode: boolean;
  userName: string;
  onLogout: () => void;
}

export const Navbar: React.FC<NavbarProps> = ({
  activeTab, setActiveTab, onNewInvestigation, isDemoMode, userName, onLogout
}) => {
  const [mobileOpen, setMobileOpen] = React.useState(false);
  const navItems = [
    { id: 'dashboard', label: 'Overview', icon: LayoutDashboard },
    { id: 'investigations', label: 'Investigations', icon: Search },
    { id: 'evidence', label: 'Evidence library', icon: Database },
    { id: 'evaluation', label: 'Evaluation', icon: BarChart3 },
    { id: 'settings', label: 'Settings', icon: Settings }
  ];

  const go = (id: string) => {
    setActiveTab(id);
    setMobileOpen(false);
  };

  return (
    <>
      <aside className="app-sidebar hidden lg:flex">
        <button className="brand-lockup" onClick={() => go('dashboard')} aria-label="SwiftIntel overview">
          <span className="brand-mark"><ShieldCheck size={21} /></span>
          <span><strong>SwiftIntel</strong><small>Investigation workspace</small></span>
        </button>
        <div className="sidebar-label">WORKSPACE</div>
        <nav className="sidebar-nav" aria-label="Main navigation">
          {navItems.map(({ id, label, icon: Icon }) => (
            <button key={id} onClick={() => go(id)} className={`sidebar-link ${activeTab === id || (activeTab === 'workspace' && id === 'investigations') ? 'active' : ''}`}>
              <Icon size={18} strokeWidth={1.8} /><span>{label}</span>
            </button>
          ))}
        </nav>
        <button className="button-primary sidebar-new" onClick={onNewInvestigation}><Plus size={16} />Start an investigation</button>
        <div className="sidebar-bottom">
          <div className="nav-user"><span className="nav-user-avatar">{userName.slice(0, 1).toUpperCase()}</span><span className="nav-user-name">{userName}</span><button className="icon-button nav-logout" title="Logout" aria-label="Logout" onClick={onLogout}><LogOut size={16} /></button></div>
          <div className="system-status">
            <span className={`status-dot ${isDemoMode ? 'demo' : ''}`} />
            <span><strong>{isDemoMode ? 'Demo mode' : 'AI service connected'}</strong><small>{isDemoMode ? 'Fictional records only' : 'Ready to assist'}</small></span>
          </div>
          <div className="sidebar-note"><CircleHelp size={16} /><span>AI findings need human review. Synthetic records are fictional.</span></div>
        </div>
      </aside>
      <header className="mobile-header lg:hidden">
        <button className="brand-lockup" onClick={() => go('dashboard')}>
          <span className="brand-mark"><ShieldCheck size={20} /></span><strong>SwiftIntel</strong>
        </button>
        <button className="icon-button" aria-label={mobileOpen ? 'Close navigation' : 'Open navigation'} onClick={() => setMobileOpen(!mobileOpen)}>
          {mobileOpen ? <X size={20} /> : <Menu size={20} />}
        </button>
      </header>
      {mobileOpen && <div className="mobile-nav-backdrop" onClick={() => setMobileOpen(false)}>
        <nav className="mobile-nav" onClick={(event) => event.stopPropagation()} aria-label="Main navigation">
          {navItems.map(({ id, label, icon: Icon }) => <button key={id} onClick={() => go(id)} className={`sidebar-link ${activeTab === id ? 'active' : ''}`}><Icon size={18} />{label}</button>)}
          <button className="sidebar-link mobile-logout" onClick={onLogout}><LogOut size={18} />Logout</button>
          <button className="button-primary mobile-new" onClick={() => { onNewInvestigation(); setMobileOpen(false); }}><Plus size={17} />Start an investigation</button>
        </nav>
      </div>}
    </>
  );
};
