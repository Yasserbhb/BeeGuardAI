import { useState, useEffect } from 'react';
import { useTheme } from '../context/ThemeContext';
import { useAuth } from '../context/AuthContext';
import { ruches as ruchesApi, settings as settingsApi } from '../services/api';
import Card, { CardHeader, CardContent } from '../components/Card';
import Button from '../components/Button';
import Input from '../components/Input';
import {
  Sun,
  Moon,
  Bell,
  Mail,
  FileText,
  Save,
  AlertTriangle,
  Check
} from 'lucide-react';
import styles from './Settings.module.css';

export default function Settings() {
  const { theme, toggleTheme } = useTheme();
  const { user } = useAuth();
  const [ruches, setRuches] = useState([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  // Alert settings
  const [alertSettings, setAlertSettings] = useState({
    enabled: false,
    email: '',
    hornetThreshold: 5, // Percentage of hornets vs bees in 1 hour
    checkInterval: 60, // minutes
  });

  // Report settings
  const [reportSettings, setReportSettings] = useState({
    enabled: false,
    email: '',
    frequency: 'weekly', // 'daily' or 'weekly'
    dayOfWeek: 1, // Monday (for weekly)
    hourOfDay: 8, // 8 AM
  });

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [ruchesRes, settingsRes] = await Promise.all([
        ruchesApi.list(),
        settingsApi.get().catch(() => null)
      ]);
      setRuches(ruchesRes);

      if (settingsRes) {
        if (settingsRes.alerts) {
          setAlertSettings(prev => ({ ...prev, ...settingsRes.alerts }));
        }
        if (settingsRes.reports) {
          setReportSettings(prev => ({ ...prev, ...settingsRes.reports }));
        }
      }
    } catch (err) {
      console.error('Failed to load settings:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    setSaving(true);
    setSaved(false);
    try {
      await settingsApi.update({
        alerts: alertSettings,
        reports: reportSettings
      });
      setSaved(true);
      setTimeout(() => setSaved(false), 3000);
    } catch (err) {
      alert('Erreur lors de la sauvegarde: ' + err.message);
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className={styles.loading}>
        <div className={styles.spinner} />
        <p>Chargement des paramètres...</p>
      </div>
    );
  }

  return (
    <div className={styles.settings}>
      <div className={styles.header}>
        <h1>Paramètres</h1>
        <p className={styles.subtitle}>Configurez vos préférences et notifications</p>
      </div>

      <div className={styles.grid}>
        {/* Theme Settings */}
        <Card>
          <CardHeader title="Apparence" subtitle="Personnalisez l'interface" />
          <CardContent>
            <div className={styles.themeSection}>
              <div className={styles.themeOption}>
                <div className={styles.themeInfo}>
                  {theme === 'light' ? <Sun size={24} /> : <Moon size={24} />}
                  <div>
                    <h4>Thème {theme === 'light' ? 'clair' : 'sombre'}</h4>
                    <p>Changez l'apparence de l'application</p>
                  </div>
                </div>
                <button
                  className={styles.themeToggle}
                  onClick={toggleTheme}
                  data-active={theme === 'dark'}
                >
                  <span className={styles.themeToggleThumb} />
                </button>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Alert Settings */}
        <Card>
          <CardHeader title="Alertes frelons" subtitle="Notifications par email en cas de danger" />
          <CardContent>
            <div className={styles.settingGroup}>
              <div className={styles.settingRow}>
                <div className={styles.settingInfo}>
                  <Bell size={20} />
                  <div>
                    <h4>Activer les alertes</h4>
                    <p>Recevez un email quand le ratio frelons/abeilles dépasse le seuil</p>
                  </div>
                </div>
                <button
                  className={styles.toggle}
                  onClick={() => setAlertSettings(prev => ({ ...prev, enabled: !prev.enabled }))}
                  data-active={alertSettings.enabled}
                >
                  <span className={styles.toggleThumb} />
                </button>
              </div>

              {alertSettings.enabled && (
                <div className={styles.settingDetails}>
                  <div className={styles.inputGroup}>
                    <label><Mail size={16} /> Email pour les alertes</label>
                    <Input
                      type="email"
                      value={alertSettings.email}
                      onChange={(e) => setAlertSettings(prev => ({ ...prev, email: e.target.value }))}
                      placeholder={user?.email || 'votre@email.com'}
                    />
                  </div>

                  <div className={styles.inputGroup}>
                    <label><AlertTriangle size={16} /> Seuil d'alerte (%)</label>
                    <div className={styles.thresholdInput}>
                      <Input
                        type="number"
                        min="1"
                        max="50"
                        value={alertSettings.hornetThreshold}
                        onChange={(e) => setAlertSettings(prev => ({ ...prev, hornetThreshold: parseInt(e.target.value) || 5 }))}
                      />
                      <span className={styles.thresholdHelp}>
                        Alerte si frelons &ge; {alertSettings.hornetThreshold}% des abeilles sur 1h
                      </span>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Report Settings */}
        <Card>
          <CardHeader title="Rapports automatiques" subtitle="Recevez des synthèses par email" />
          <CardContent>
            <div className={styles.settingGroup}>
              <div className={styles.settingRow}>
                <div className={styles.settingInfo}>
                  <FileText size={20} />
                  <div>
                    <h4>Activer les rapports</h4>
                    <p>Rapport PDF avec statistiques, pics et moyennes</p>
                  </div>
                </div>
                <button
                  className={styles.toggle}
                  onClick={() => setReportSettings(prev => ({ ...prev, enabled: !prev.enabled }))}
                  data-active={reportSettings.enabled}
                >
                  <span className={styles.toggleThumb} />
                </button>
              </div>

              {reportSettings.enabled && (
                <div className={styles.settingDetails}>
                  <div className={styles.inputGroup}>
                    <label><Mail size={16} /> Email pour les rapports</label>
                    <Input
                      type="email"
                      value={reportSettings.email}
                      onChange={(e) => setReportSettings(prev => ({ ...prev, email: e.target.value }))}
                      placeholder={user?.email || 'votre@email.com'}
                    />
                  </div>

                  <div className={styles.inputGroup}>
                    <label>Fréquence</label>
                    <div className={styles.frequencyOptions}>
                      <button
                        className={`${styles.frequencyBtn} ${reportSettings.frequency === 'daily' ? styles.active : ''}`}
                        onClick={() => setReportSettings(prev => ({ ...prev, frequency: 'daily' }))}
                      >
                        Quotidien
                      </button>
                      <button
                        className={`${styles.frequencyBtn} ${reportSettings.frequency === 'weekly' ? styles.active : ''}`}
                        onClick={() => setReportSettings(prev => ({ ...prev, frequency: 'weekly' }))}
                      >
                        Hebdomadaire
                      </button>
                    </div>
                  </div>

                  {reportSettings.frequency === 'weekly' && (
                    <div className={styles.inputGroup}>
                      <label>Jour d'envoi</label>
                      <select
                        className={styles.select}
                        value={reportSettings.dayOfWeek}
                        onChange={(e) => setReportSettings(prev => ({ ...prev, dayOfWeek: parseInt(e.target.value) }))}
                      >
                        <option value={1}>Lundi</option>
                        <option value={2}>Mardi</option>
                        <option value={3}>Mercredi</option>
                        <option value={4}>Jeudi</option>
                        <option value={5}>Vendredi</option>
                        <option value={6}>Samedi</option>
                        <option value={0}>Dimanche</option>
                      </select>
                    </div>
                  )}

                  <div className={styles.inputGroup}>
                    <label>Heure d'envoi</label>
                    <select
                      className={styles.select}
                      value={reportSettings.hourOfDay}
                      onChange={(e) => setReportSettings(prev => ({ ...prev, hourOfDay: parseInt(e.target.value) }))}
                    >
                      {Array.from({ length: 24 }, (_, i) => (
                        <option key={i} value={i}>{i.toString().padStart(2, '0')}:00</option>
                      ))}
                    </select>
                  </div>

                  <div className={styles.reportPreview}>
                    <h5>Contenu du rapport</h5>
                    <ul>
                      <li>Température moyenne, min et max</li>
                      <li>Humidité moyenne</li>
                      <li>Activité des abeilles (moyenne et pics)</li>
                      <li>Détections de frelons</li>
                      <li>Alertes de la période</li>
                    </ul>
                  </div>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Save Button */}
      <div className={styles.saveSection}>
        <Button onClick={handleSave} disabled={saving}>
          {saving ? (
            <>Sauvegarde...</>
          ) : saved ? (
            <><Check size={18} /> Sauvegardé</>
          ) : (
            <><Save size={18} /> Sauvegarder les paramètres</>
          )}
        </Button>
      </div>
    </div>
  );
}
