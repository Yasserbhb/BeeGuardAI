import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Mail, Lock, User, Building } from 'lucide-react';
import Button from '../components/Button';
import Input from '../components/Input';
import styles from './Login.module.css';

export default function Login() {
  const [isLogin, setIsLogin] = useState(true);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const { login, register } = useAuth();
  const navigate = useNavigate();

  const [formData, setFormData] = useState({
    email: '',
    mot_de_passe: '',
    nom: '',
    prenom: '',
    organisation_nom: '',
  });

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
    setError('');
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      if (isLogin) {
        await login(formData.email, formData.mot_de_passe);
        navigate('/');
      } else {
        await register(formData);
        setIsLogin(true);
        setError('');
        alert('Compte créé ! Vous pouvez maintenant vous connecter.');
      }
    } catch (err) {
      setError(err.message || 'Une erreur est survenue');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className={styles.container}>
      <div className={styles.leftPanel}>
        <div className={styles.branding}>
          <div className={styles.logo}>
            <svg viewBox="0 0 80 80" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M40 8L70 24V56L40 72L10 56V24L40 8Z" fill="currentColor" opacity="0.3"/>
              <path d="M40 16L60 28V52L40 64L20 52V28L40 16Z" fill="currentColor"/>
              <circle cx="40" cy="40" r="8" fill="#1a1a1a"/>
            </svg>
          </div>
          <h1>BeeGuardAI</h1>
          <p>Surveillance intelligente de vos ruches</p>
        </div>
        <div className={styles.features}>
          <div className={styles.feature}>
            <span className={styles.featureIcon}>🐝</span>
            <span>Détection automatique des frelons</span>
          </div>
          <div className={styles.feature}>
            <span className={styles.featureIcon}>📊</span>
            <span>Monitoring en temps réel</span>
          </div>
          <div className={styles.feature}>
            <span className={styles.featureIcon}>🔔</span>
            <span>Alertes instantanées</span>
          </div>
        </div>
      </div>

      <div className={styles.rightPanel}>
        <div className={styles.formContainer}>
          <div className={styles.formHeader}>
            <h2>{isLogin ? 'Connexion' : 'Créer un compte'}</h2>
            <p>
              {isLogin
                ? 'Connectez-vous pour accéder à votre tableau de bord'
                : 'Inscrivez-vous pour commencer à surveiller vos ruches'}
            </p>
          </div>

          {error && <div className={styles.error}>{error}</div>}

          <form onSubmit={handleSubmit} className={styles.form}>
            {!isLogin && (
              <>
                <div className={styles.row}>
                  <Input
                    label="Prénom"
                    name="prenom"
                    value={formData.prenom}
                    onChange={handleChange}
                    placeholder="Jean"
                    icon={User}
                    required
                  />
                  <Input
                    label="Nom"
                    name="nom"
                    value={formData.nom}
                    onChange={handleChange}
                    placeholder="Dupont"
                    icon={User}
                    required
                  />
                </div>
                <Input
                  label="Organisation"
                  name="organisation_nom"
                  value={formData.organisation_nom}
                  onChange={handleChange}
                  placeholder="Mon Rucher"
                  icon={Building}
                  required
                />
              </>
            )}

            <Input
              label="Email"
              type="email"
              name="email"
              value={formData.email}
              onChange={handleChange}
              placeholder="vous@exemple.fr"
              icon={Mail}
              required
            />

            <Input
              label="Mot de passe"
              type="password"
              name="mot_de_passe"
              value={formData.mot_de_passe}
              onChange={handleChange}
              placeholder="••••••••"
              icon={Lock}
              required
            />

            <Button
              type="submit"
              loading={loading}
              className={styles.submitBtn}
              size="large"
            >
              {isLogin ? 'Se connecter' : 'Créer mon compte'}
            </Button>
          </form>

          <div className={styles.switchMode}>
            <span>
              {isLogin ? "Pas encore de compte ?" : "Déjà un compte ?"}
            </span>
            <button
              type="button"
              onClick={() => {
                setIsLogin(!isLogin);
                setError('');
              }}
            >
              {isLogin ? "S'inscrire" : "Se connecter"}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
