import { useState, useEffect } from 'react';
import { ruches as ruchesApi, ruchers as ruchersApi } from '../services/api';
import {
  Plus,
  Trash2,
  MapPin,
  Box,
  AlertCircle,
  Wifi,
  Check,
  X,
  FolderOpen,
  ChevronDown,
  ChevronRight,
  Pencil
} from 'lucide-react';
import Card, { CardHeader, CardContent } from '../components/Card';
import Button from '../components/Button';
import Input from '../components/Input';
import styles from './Ruches.module.css';

export default function Ruches() {
  const [ruches, setRuches] = useState([]);
  const [ruchers, setRuchers] = useState([]);
  const [loading, setLoading] = useState(true);

  // Forms
  const [showRucherForm, setShowRucherForm] = useState(false);
  const [showRucheForm, setShowRucheForm] = useState(false);
  const [rucherFormData, setRucherFormData] = useState({ nom: '', localisation: '' });
  const [rucheFormData, setRucheFormData] = useState({ nom: '', rucher_id: '' });
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');

  // Editing
  const [editingDeviceId, setEditingDeviceId] = useState(null);
  const [editDeviceIdValue, setEditDeviceIdValue] = useState('');

  // Editing Rucher
  const [editingRucherId, setEditingRucherId] = useState(null);
  const [editRucherData, setEditRucherData] = useState({ nom: '', localisation: '' });

  // Collapsed state for ruchers
  const [collapsedRuchers, setCollapsedRuchers] = useState({});

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [ruchesData, ruchersData] = await Promise.all([
        ruchesApi.list(),
        ruchersApi.list()
      ]);
      setRuches(ruchesData);
      setRuchers(ruchersData);
    } catch (err) {
      console.error('Failed to load data:', err);
    } finally {
      setLoading(false);
    }
  };

  // Group ruches by rucher
  const groupedRuches = ruchers.map(rucher => ({
    ...rucher,
    ruches: ruches.filter(r => r.rucher_id === rucher.id)
  }));

  const unassignedRuches = ruches.filter(r => !r.rucher_id);

  const toggleRucherCollapse = (rucherId) => {
    setCollapsedRuchers(prev => ({
      ...prev,
      [rucherId]: !prev[rucherId]
    }));
  };

  // Rucher handlers
  const handleCreateRucher = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    setError('');

    try {
      await ruchersApi.create(rucherFormData.nom, rucherFormData.localisation);
      setRucherFormData({ nom: '', localisation: '' });
      setShowRucherForm(false);
      loadData();
    } catch (err) {
      setError(err.message || 'Erreur lors de la création');
    } finally {
      setSubmitting(false);
    }
  };

  const handleDeleteRucher = async (id, nom) => {
    if (!confirm(`Supprimer le rucher "${nom}" ? Les ruches seront conservées mais non assignées.`)) return;

    try {
      await ruchersApi.delete(id);
      loadData();
    } catch (err) {
      alert('Erreur lors de la suppression');
    }
  };

  const startEditRucher = (rucher) => {
    setEditingRucherId(rucher.id);
    setEditRucherData({ nom: rucher.nom, localisation: rucher.localisation || '' });
  };

  const cancelEditRucher = () => {
    setEditingRucherId(null);
    setEditRucherData({ nom: '', localisation: '' });
  };

  const saveRucher = async () => {
    try {
      await ruchersApi.update(editingRucherId, editRucherData);
      setEditingRucherId(null);
      setEditRucherData({ nom: '', localisation: '' });
      loadData();
    } catch (err) {
      alert('Erreur: ' + err.message);
    }
  };

  // Ruche handlers
  const handleCreateRuche = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    setError('');

    try {
      await ruchesApi.create(rucheFormData.nom, rucheFormData.rucher_id || null);
      setRucheFormData({ nom: '', rucher_id: '' });
      setShowRucheForm(false);
      loadData();
    } catch (err) {
      setError(err.message || 'Erreur lors de la création');
    } finally {
      setSubmitting(false);
    }
  };

  const handleDeleteRuche = async (id, nom) => {
    if (!confirm(`Supprimer la ruche "${nom}" ?`)) return;

    try {
      await ruchesApi.delete(id);
      loadData();
    } catch (err) {
      alert('Erreur lors de la suppression');
    }
  };

  // Device ID editing
  const startEditDeviceId = (ruche) => {
    setEditingDeviceId(ruche.id);
    setEditDeviceIdValue(ruche.ttn_device_id || '');
  };

  const cancelEditDeviceId = () => {
    setEditingDeviceId(null);
    setEditDeviceIdValue('');
  };

  const saveDeviceId = async (rucheId) => {
    try {
      await ruchesApi.update(rucheId, { ttn_device_id: editDeviceIdValue || null });
      setEditingDeviceId(null);
      setEditDeviceIdValue('');
      loadData();
    } catch (err) {
      alert('Erreur: ' + err.message);
    }
  };

  // Ruche card component
  const RucheCard = ({ ruche }) => (
    <div className={styles.rucheCard}>
      <div className={styles.rucheHeader}>
        <div className={styles.rucheIcon}>
          <Box size={20} />
        </div>
        <h4 className={styles.rucheName}>{ruche.nom}</h4>
        <Button
          variant="ghost"
          size="small"
          icon={Trash2}
          onClick={() => handleDeleteRuche(ruche.id, ruche.nom)}
          className={styles.deleteBtn}
        />
      </div>

      <div className={styles.deviceIdSection}>
        <label className={styles.deviceIdLabel}>
          <Wifi size={12} />
          TTN Device ID
        </label>
        {editingDeviceId === ruche.id ? (
          <div className={styles.deviceIdEdit}>
            <input
              type="text"
              value={editDeviceIdValue}
              onChange={(e) => setEditDeviceIdValue(e.target.value)}
              placeholder="beehive-00000"
              className={styles.deviceIdInput}
              autoFocus
            />
            <button className={styles.deviceIdBtn} onClick={() => saveDeviceId(ruche.id)}>
              <Check size={14} />
            </button>
            <button className={styles.deviceIdBtn} onClick={cancelEditDeviceId}>
              <X size={14} />
            </button>
          </div>
        ) : (
          <div className={styles.deviceIdDisplay} onClick={() => startEditDeviceId(ruche)} style={{cursor: 'pointer'}}>
            <code className={styles.hasDeviceId} title="Cliquez pour modifier">
              {ruche.ttn_device_id}
            </code>
          </div>
        )}
      </div>
    </div>
  );

  if (loading) {
    return (
      <div className={styles.loading}>
        <div className={styles.spinner} />
        <p>Chargement...</p>
      </div>
    );
  }

  return (
    <div className={styles.page}>
      {/* Header */}
      <div className={styles.header}>
        <div>
          <h1 className={styles.title}>Gestion des ruches</h1>
          <p className={styles.subtitle}>
            {ruchers.length} rucher{ruchers.length !== 1 ? 's' : ''} · {ruches.length} ruche{ruches.length !== 1 ? 's' : ''}
          </p>
        </div>
        <div className={styles.headerActions}>
          <Button variant="secondary" icon={FolderOpen} onClick={() => setShowRucherForm(true)}>
            Nouveau rucher
          </Button>
          <Button icon={Plus} onClick={() => setShowRucheForm(true)}>
            Nouvelle ruche
          </Button>
        </div>
      </div>

      {/* Info Box */}
      <Card className={styles.infoCard}>
        <CardContent>
          <div className={styles.infoBox}>
            <Wifi size={20} />
            <div>
              <strong>Organisation par ruchers</strong>
              <p>
                Les ruchers regroupent vos ruches par emplacement géographique.
                Chaque ruche doit avoir un TTN Device ID correspondant à l'appareil enregistré dans The Things Network.
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Create Rucher Form */}
      {showRucherForm && (
        <Card className={`${styles.formCard} animate-scale-in`}>
          <CardHeader title="Créer un rucher" />
          <CardContent>
            {error && (
              <div className={styles.error}>
                <AlertCircle size={18} />
                {error}
              </div>
            )}
            <form onSubmit={handleCreateRucher} className={styles.form}>
              <Input
                label="Nom du rucher"
                placeholder="Ex: Jardin Nord"
                value={rucherFormData.nom}
                onChange={(e) => setRucherFormData({ ...rucherFormData, nom: e.target.value })}
                icon={FolderOpen}
                required
              />
              <Input
                label="Localisation"
                placeholder="Ex: Campus Jussieu - Zone Nord"
                value={rucherFormData.localisation}
                onChange={(e) => setRucherFormData({ ...rucherFormData, localisation: e.target.value })}
                icon={MapPin}
              />
              <div className={styles.formActions}>
                <Button type="button" variant="ghost" onClick={() => {
                  setShowRucherForm(false);
                  setRucherFormData({ nom: '', localisation: '' });
                  setError('');
                }}>
                  Annuler
                </Button>
                <Button type="submit" loading={submitting}>
                  Créer
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      )}

      {/* Create Ruche Form */}
      {showRucheForm && (
        <Card className={`${styles.formCard} animate-scale-in`}>
          <CardHeader title="Ajouter une ruche" />
          <CardContent>
            {error && (
              <div className={styles.error}>
                <AlertCircle size={18} />
                {error}
              </div>
            )}
            <form onSubmit={handleCreateRuche} className={styles.form}>
              <Input
                label="Nom de la ruche"
                placeholder="Ex: Ruche Alpha"
                value={rucheFormData.nom}
                onChange={(e) => setRucheFormData({ ...rucheFormData, nom: e.target.value })}
                icon={Box}
                required
              />
              <div className={styles.selectGroup}>
                <label>Rucher (optionnel)</label>
                <select
                  value={rucheFormData.rucher_id}
                  onChange={(e) => setRucheFormData({ ...rucheFormData, rucher_id: e.target.value })}
                  className={styles.select}
                >
                  <option value="">Aucun rucher</option>
                  {ruchers.map((rucher) => (
                    <option key={rucher.id} value={rucher.id}>
                      {rucher.nom}
                    </option>
                  ))}
                </select>
              </div>
              <div className={styles.formActions}>
                <Button type="button" variant="ghost" onClick={() => {
                  setShowRucheForm(false);
                  setRucheFormData({ nom: '', rucher_id: '' });
                  setError('');
                }}>
                  Annuler
                </Button>
                <Button type="submit" loading={submitting}>
                  Créer
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      )}

      {/* Empty State */}
      {ruches.length === 0 && ruchers.length === 0 ? (
        <Card>
          <CardContent>
            <div className={styles.empty}>
              <Box size={48} className={styles.emptyIcon} />
              <h3>Aucune ruche</h3>
              <p>Commencez par créer un rucher, puis ajoutez vos ruches</p>
              <div className={styles.emptyActions}>
                <Button variant="secondary" icon={FolderOpen} onClick={() => setShowRucherForm(true)}>
                  Créer un rucher
                </Button>
                <Button icon={Plus} onClick={() => setShowRucheForm(true)}>
                  Ajouter une ruche
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      ) : (
        <div className={styles.ruchersContainer}>
          {/* Ruchers with their ruches */}
          {groupedRuches.map((rucher) => (
            <Card key={rucher.id} className={styles.rucherCard}>
              <div
                className={styles.rucherHeader}
                onClick={() => editingRucherId !== rucher.id && toggleRucherCollapse(rucher.id)}
              >
                <div className={styles.rucherToggle}>
                  {collapsedRuchers[rucher.id] ? <ChevronRight size={20} /> : <ChevronDown size={20} />}
                </div>
                <div className={styles.rucherIcon}>
                  <FolderOpen size={24} />
                </div>
                {editingRucherId === rucher.id ? (
                  <div className={styles.rucherEditForm} onClick={(e) => e.stopPropagation()}>
                    <input
                      type="text"
                      value={editRucherData.nom}
                      onChange={(e) => setEditRucherData({ ...editRucherData, nom: e.target.value })}
                      placeholder="Nom du rucher"
                      className={styles.rucherEditInput}
                      autoFocus
                    />
                    <input
                      type="text"
                      value={editRucherData.localisation}
                      onChange={(e) => setEditRucherData({ ...editRucherData, localisation: e.target.value })}
                      placeholder="Localisation"
                      className={styles.rucherEditInput}
                    />
                    <button className={styles.rucherEditBtn} onClick={saveRucher}>
                      <Check size={16} />
                    </button>
                    <button className={styles.rucherEditBtn} onClick={cancelEditRucher}>
                      <X size={16} />
                    </button>
                  </div>
                ) : (
                  <>
                    <div className={styles.rucherInfo}>
                      <h3 className={styles.rucherName}>{rucher.nom}</h3>
                      {rucher.localisation && (
                        <p className={styles.rucherLocation}>
                          <MapPin size={14} />
                          {rucher.localisation}
                        </p>
                      )}
                    </div>
                    <span className={styles.rucherCount}>
                      {rucher.ruches.length} ruche{rucher.ruches.length !== 1 ? 's' : ''}
                    </span>
                    <button
                      className={styles.rucherActionBtn}
                      onClick={(e) => {
                        e.stopPropagation();
                        startEditRucher(rucher);
                      }}
                      title="Modifier"
                    >
                      <Pencil size={16} />
                    </button>
                    <button
                      className={`${styles.rucherActionBtn} ${styles.rucherDeleteBtn}`}
                      onClick={(e) => {
                        e.stopPropagation();
                        handleDeleteRucher(rucher.id, rucher.nom);
                      }}
                      title="Supprimer"
                    >
                      <Trash2 size={16} />
                    </button>
                  </>
                )}
              </div>

              {!collapsedRuchers[rucher.id] && (
                <div className={styles.ruchesGrid}>
                  {rucher.ruches.length === 0 ? (
                    <p className={styles.noRuches}>Aucune ruche dans ce rucher</p>
                  ) : (
                    rucher.ruches.map((ruche) => (
                      <RucheCard key={ruche.id} ruche={ruche} />
                    ))
                  )}
                </div>
              )}
            </Card>
          ))}

          {/* Unassigned ruches */}
          {unassignedRuches.length > 0 && (
            <Card className={styles.rucherCard}>
              <div className={styles.rucherHeader}>
                <div className={styles.rucherToggle}>
                  <ChevronDown size={20} />
                </div>
                <div className={`${styles.rucherIcon} ${styles.unassigned}`}>
                  <Box size={24} />
                </div>
                <div className={styles.rucherInfo}>
                  <h3 className={styles.rucherName}>Non assignées</h3>
                  <p className={styles.rucherLocation}>Ruches sans rucher</p>
                </div>
                <span className={styles.rucherCount}>
                  {unassignedRuches.length} ruche{unassignedRuches.length !== 1 ? 's' : ''}
                </span>
              </div>

              <div className={styles.ruchesGrid}>
                {unassignedRuches.map((ruche) => (
                  <RucheCard key={ruche.id} ruche={ruche} />
                ))}
              </div>
            </Card>
          )}
        </div>
      )}
    </div>
  );
}
