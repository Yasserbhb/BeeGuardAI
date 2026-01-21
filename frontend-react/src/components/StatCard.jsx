import styles from './StatCard.module.css';

export default function StatCard({
  title,
  value,
  unit = '',
  icon: Icon,
  color = 'honey',
  trend,
  subtitle
}) {
  const colorClass = styles[`color${color.charAt(0).toUpperCase() + color.slice(1)}`];

  return (
    <div className={`${styles.statCard} ${colorClass} animate-scale-in`}>
      <div className={styles.iconWrapper}>
        {Icon && <Icon size={24} />}
      </div>
      <div className={styles.content}>
        <span className={styles.title}>{title}</span>
        <div className={styles.valueRow}>
          <span className={styles.value}>{value}</span>
          {unit && <span className={styles.unit}>{unit}</span>}
        </div>
        {subtitle && <span className={styles.subtitle}>{subtitle}</span>}
        {trend !== undefined && (
          <span className={`${styles.trend} ${trend >= 0 ? styles.trendUp : styles.trendDown}`}>
            {trend >= 0 ? '↑' : '↓'} {Math.abs(trend)}%
          </span>
        )}
      </div>
    </div>
  );
}
