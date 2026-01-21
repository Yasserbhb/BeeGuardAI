import styles from './Button.module.css';

export default function Button({
  children,
  variant = 'primary',
  size = 'medium',
  disabled = false,
  loading = false,
  icon: Icon,
  onClick,
  type = 'button',
  className = '',
  ...props
}) {
  const variantClass = styles[variant];
  const sizeClass = styles[size];

  return (
    <button
      type={type}
      className={`${styles.button} ${variantClass} ${sizeClass} ${className}`}
      disabled={disabled || loading}
      onClick={onClick}
      {...props}
    >
      {loading ? (
        <span className={styles.spinner} />
      ) : (
        <>
          {Icon && <Icon size={size === 'small' ? 16 : 18} />}
          {children && <span>{children}</span>}
        </>
      )}
    </button>
  );
}
