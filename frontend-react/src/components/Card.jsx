import styles from './Card.module.css';

export default function Card({ children, className = '', animate = true }) {
  return (
    <div className={`${styles.card} ${animate ? 'animate-fade-in' : ''} ${className}`}>
      {children}
    </div>
  );
}

export function CardHeader({ title, subtitle, action }) {
  return (
    <div className={styles.cardHeader}>
      <div>
        <h3 className={styles.cardTitle}>{title}</h3>
        {subtitle && <p className={styles.cardSubtitle}>{subtitle}</p>}
      </div>
      {action && <div className={styles.cardAction}>{action}</div>}
    </div>
  );
}

export function CardContent({ children, className = '' }) {
  return (
    <div className={`${styles.cardContent} ${className}`}>
      {children}
    </div>
  );
}
