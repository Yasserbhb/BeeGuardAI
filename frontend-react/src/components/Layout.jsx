import { NavLink, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useTheme } from '../context/ThemeContext';
import {
  LayoutDashboard,
  Box,
  LogOut,
  User,
  Menu,
  X,
  Sun,
  Moon
} from 'lucide-react';
import { useState } from 'react';
import styles from './Layout.module.css';

export default function Layout({ children }) {
  const { user, logout } = useAuth();
  const { theme, toggleTheme } = useTheme();
  const navigate = useNavigate();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  const navItems = [
    { to: '/', icon: LayoutDashboard, label: 'Dashboard' },
    { to: '/ruches', icon: Box, label: 'Ruches' },
  ];

  return (
    <div className={styles.layout}>
      {/* Header */}
      <header className={styles.header}>
        <div className={styles.headerContent}>
          <div className={styles.logo}>
            <div className={styles.logoIcon}>
              <svg viewBox="0 0 40 40" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M20 4L35 12V28L20 36L5 28V12L20 4Z" fill="currentColor" opacity="0.2"/>
                <path d="M20 8L30 14V26L20 32L10 26V14L20 8Z" fill="currentColor"/>
                <circle cx="20" cy="20" r="4" fill="white"/>
              </svg>
            </div>
            <div>
              <h1 className={styles.logoText}>BeeGuardAI</h1>
              <span className={styles.logoSubtext}>Surveillance intelligente</span>
            </div>
          </div>

          {/* Desktop Navigation */}
          <nav className={styles.nav}>
            {navItems.map(({ to, icon: Icon, label }) => (
              <NavLink
                key={to}
                to={to}
                className={({ isActive }) =>
                  `${styles.navLink} ${isActive ? styles.navLinkActive : ''}`
                }
              >
                <Icon size={18} />
                <span>{label}</span>
              </NavLink>
            ))}
          </nav>

          {/* User Menu */}
          <div className={styles.userMenu}>
            <button onClick={toggleTheme} className={styles.themeBtn} title={theme === 'light' ? 'Mode sombre' : 'Mode clair'}>
              {theme === 'light' ? <Moon size={18} /> : <Sun size={18} />}
            </button>
            <div className={styles.userInfo}>
              <User size={18} />
              <span>{user?.prenom} {user?.nom}</span>
            </div>
            <button onClick={handleLogout} className={styles.logoutBtn}>
              <LogOut size={18} />
              <span>Déconnexion</span>
            </button>
          </div>

          {/* Mobile Menu Button */}
          <button
            className={styles.mobileMenuBtn}
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
          >
            {mobileMenuOpen ? <X size={24} /> : <Menu size={24} />}
          </button>
        </div>

        {/* Mobile Navigation */}
        {mobileMenuOpen && (
          <div className={styles.mobileNav}>
            {navItems.map(({ to, icon: Icon, label }) => (
              <NavLink
                key={to}
                to={to}
                className={({ isActive }) =>
                  `${styles.mobileNavLink} ${isActive ? styles.mobileNavLinkActive : ''}`
                }
                onClick={() => setMobileMenuOpen(false)}
              >
                <Icon size={20} />
                <span>{label}</span>
              </NavLink>
            ))}
            <button onClick={handleLogout} className={styles.mobileLogoutBtn}>
              <LogOut size={20} />
              <span>Déconnexion</span>
            </button>
          </div>
        )}
      </header>

      {/* Main Content */}
      <main className={styles.main}>
        <div className={styles.container}>
          {children}
        </div>
      </main>
    </div>
  );
}
