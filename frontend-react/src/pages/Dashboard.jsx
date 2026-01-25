import { useState, useEffect } from 'react';
import { data, ruches as ruchesApi } from '../services/api';
import {
  Thermometer,
  Droplets,
  Bug,
  Activity,
  RefreshCw,
  ChevronRight,
  Clock,
  Calendar
} from 'lucide-react';
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
  ReferenceArea
} from 'recharts';
import Card, { CardHeader, CardContent } from '../components/Card';
import StatCard from '../components/StatCard';
import Button from '../components/Button';
import styles from './Dashboard.module.css';

const TIME_FILTERS = [
  { label: '1 heure', value: 1 },
  { label: '6 heures', value: 6 },
  { label: '24 heures', value: 24 },
  { label: '7 jours', value: 168 },
  { label: '30 jours', value: 720 },
  { label: 'Personnalisé', value: 'custom' },
];

export default function Dashboard() {
  const [latestData, setLatestData] = useState([]);
  const [historicalData, setHistoricalData] = useState([]);
  const [ruches, setRuches] = useState([]);
  const [selectedRuche, setSelectedRuche] = useState(null);
  const [timeFilter, setTimeFilter] = useState(24);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [customRange, setCustomRange] = useState({ start: '', end: '' });
  const [showCustomPicker, setShowCustomPicker] = useState(false);

  useEffect(() => {
    loadData();
    const interval = setInterval(() => {
      loadData();
      // Also refresh charts if viewing a specific ruche
      if (selectedRuche && timeFilter !== 'custom') {
        loadHistoricalData(selectedRuche, timeFilter);
      }
    }, 5000);
    return () => clearInterval(interval);
  }, [selectedRuche, timeFilter]);

  useEffect(() => {
    if (selectedRuche && timeFilter !== 'custom') {
      loadHistoricalData(selectedRuche, timeFilter);
    }
  }, [selectedRuche, timeFilter]);

  const loadData = async () => {
    try {
      const [latestRes, ruchesRes] = await Promise.all([
        data.latest(),
        ruchesApi.list()
      ]);
      setLatestData(latestRes);
      setRuches(ruchesRes);
    } catch (err) {
      console.error('Failed to load data:', err);
    } finally {
      setLoading(false);
    }
  };

  const loadHistoricalData = async (rucheId, hours, start = null, end = null) => {
    try {
      const history = await ruchesApi.getData(rucheId, hours, start, end);
      const formatted = [];

      history.forEach((d, i) => {
        const isNight = d.luminosite === 0;
        const timestamp = new Date(d.timestamp);

        const beeCount = d.nombre_abeilles || 0;
        const point = {
          ...d,
          time: timestamp.toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' }),
          date: timestamp.toLocaleDateString('fr-FR', { day: '2-digit', month: '2-digit' }),
          fullTime: hours > 24 || start
            ? timestamp.toLocaleDateString('fr-FR', { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' })
            : timestamp.toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' }),
          isNight,
          abeilles_min: Math.max(0, Math.round(beeCount * 0.85)),
          abeilles_max: Math.round(beeCount * 1.15)
        };

        formatted.push(point);

        // After a night point, insert a gap (null values) to break the line
        if (isNight && i < history.length - 1 && history[i + 1].luminosite === 1) {
          formatted.push({
            fullTime: point.fullTime + ' ',  // Unique key with space
            temperature: null,
            humidite: null,
            nombre_frelons: null,
            nombre_abeilles: null,
            abeilles_min: null,
            abeilles_max: null,
            isGap: true
          });
        }
      });

      setHistoricalData(formatted);
    } catch (err) {
      console.error('Failed to load historical data:', err);
    }
  };

  const handleRefresh = async () => {
    setRefreshing(true);
    await loadData();
    if (selectedRuche) {
      await loadHistoricalData(selectedRuche, timeFilter);
    }
    setRefreshing(false);
  };

  const handleSelectRuche = (rucheId) => setSelectedRuche(rucheId);

  const handleBackToOverview = () => {
    setSelectedRuche(null);
    setHistoricalData([]);
  };

  const handleTimeFilterChange = (value) => {
    if (value === 'custom') {
      setShowCustomPicker(true);
      // Set default: last 24 hours
      const now = new Date();
      const yesterday = new Date(now.getTime() - 24 * 60 * 60 * 1000);
      // Format for datetime-local: YYYY-MM-DDTHH:MM
      const formatForInput = (d) => {
        const pad = (n) => n.toString().padStart(2, '0');
        return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`;
      };
      setCustomRange({ start: formatForInput(yesterday), end: formatForInput(now) });
    } else {
      setShowCustomPicker(false);
    }
    setTimeFilter(value);
  };

  const handleCustomRangeSubmit = () => {
    if (customRange.start && customRange.end && selectedRuche) {
      // Convert datetime-local to ISO format for InfluxDB
      const startISO = new Date(customRange.start).toISOString();
      const endISO = new Date(customRange.end).toISOString();
      loadHistoricalData(selectedRuche, 0, startISO, endISO);
    }
  };

  // Group ruches by rucher
  const ruchesByRucher = ruches.reduce((acc, ruche) => {
    const rucherName = ruche.rucher_nom || 'Sans rucher';
    if (!acc[rucherName]) {
      acc[rucherName] = { name: rucherName, location: ruche.rucher_localisation || '', ruches: [] };
    }
    acc[rucherName].ruches.push(ruche);
    return acc;
  }, {});

  // Calculate night periods for charts
  // Night = luminosite=0 sent once, then device sleeps until morning
  const getNightPeriods = () => {
    if (!historicalData.length) return [];
    const periods = [];
    let nightStart = null;
    historicalData.forEach((d) => {
      // Skip gap points
      if (d.isGap) return;

      if (d.isNight && !nightStart) {
        nightStart = d.fullTime;
      } else if (!d.isNight && nightStart) {
        // Night ends at current point (first daytime point after night)
        periods.push({ start: nightStart, end: d.fullTime });
        nightStart = null;
      }
    });
    if (nightStart) {
      const lastRealPoint = historicalData.filter(d => !d.isGap).pop();
      periods.push({ start: nightStart, end: lastRealPoint?.fullTime });
    }
    return periods;
  };

  const nightPeriods = getNightPeriods();

  const totals = latestData.reduce(
    (acc, d) => ({
      frelons: acc.frelons + (d.nombre_frelons || 0),
      abeilles: acc.abeilles + (d.nombre_abeilles || 0),
      avgTemp: acc.avgTemp + (d.temperature || 0),
      avgHum: acc.avgHum + (d.humidite || 0),
      count: acc.count + 1
    }),
    { frelons: 0, abeilles: 0, avgTemp: 0, avgHum: 0, count: 0 }
  );

  const avgTemp = totals.count > 0 ? (totals.avgTemp / totals.count).toFixed(1) : 0;
  const avgHum = totals.count > 0 ? (totals.avgHum / totals.count).toFixed(0) : 0;
  const selectedRucheData = latestData.find(d => d.ruche_id === selectedRuche);
  const selectedRucheInfo = ruches.find(r => r.id === selectedRuche);
  const currentTimeFilter = TIME_FILTERS.find(f => f.value === timeFilter);

  if (loading) {
    return (
      <div className={styles.loading}>
        <div className={styles.spinner} />
        <p>Chargement des données...</p>
      </div>
    );
  }

  return (
    <div className={styles.dashboard}>
      <div className={styles.header}>
        <div>
          <h1 className={styles.title}>
            {selectedRuche ? (
              <span className={styles.breadcrumb}>
                <span className={styles.breadcrumbLink} onClick={handleBackToOverview}>Tableau de bord</span>
                <ChevronRight size={20} />
                <span>{selectedRucheInfo?.nom || `Ruche ${selectedRuche}`}</span>
              </span>
            ) : 'Tableau de bord'}
          </h1>
          <p className={styles.subtitle}>
            {selectedRuche
              ? selectedRucheInfo?.rucher_nom || 'Détails de la ruche'
              : `Surveillance de vos ${ruches.length} ruche${ruches.length > 1 ? 's' : ''}`}
          </p>
        </div>
        <div className={styles.headerActions}>
          {selectedRuche && <Button onClick={handleBackToOverview} variant="secondary">Vue d'ensemble</Button>}
          <Button onClick={handleRefresh} loading={refreshing} icon={RefreshCw} variant="secondary">Actualiser</Button>
        </div>
      </div>

      {!selectedRuche && (
        <>
          <div className={styles.statsGrid}>
            <StatCard title="Frelons détectés" value={totals.frelons} icon={Bug} color={totals.frelons > 5 ? 'red' : totals.frelons > 0 ? 'honey' : 'green'} subtitle="Total - Dernière heure" />
            <StatCard title="Température moyenne" value={avgTemp} unit="°C" icon={Thermometer} color="honey" />
            <StatCard title="Humidité moyenne" value={avgHum} unit="%" icon={Droplets} color="blue" />
            <StatCard title="Abeilles à l'entrée" value={totals.abeilles} icon={Activity} color="green" subtitle="Total détecté" />
          </div>

          {Object.values(ruchesByRucher).map((rucher) => (
            <Card key={rucher.name}>
              <CardHeader title={rucher.name} subtitle={rucher.location ? `${rucher.location}` : `${rucher.ruches.length} ruche(s)`} />
              <CardContent>
                <div className={styles.ruchesOverviewGrid}>
                  {rucher.ruches.map((ruche) => {
                    const rucheData = latestData.find(d => d.ruche_id === ruche.id);
                    const hasAlert = rucheData?.nombre_frelons > 0;
                    return (
                      <div key={ruche.id} className={`${styles.rucheOverviewCard} ${hasAlert ? styles.rucheAlert : ''}`} onClick={() => handleSelectRuche(ruche.id)}>
                        <div className={styles.rucheOverviewHeader}>
                          <span className={styles.rucheOverviewName}>{ruche.nom}</span>
                          <span className={`${styles.rucheOverviewStatus} ${hasAlert ? styles.statusWarning : styles.statusOk}`}>{hasAlert ? 'Alerte' : 'Normal'}</span>
                        </div>
                        <div className={styles.rucheOverviewStats}>
                          <div className={styles.rucheOverviewStat}><Thermometer size={18} className={styles.iconTemp} /><span className={styles.statValue}>{rucheData?.temperature?.toFixed(1) || '--'}°C</span></div>
                          <div className={styles.rucheOverviewStat}><Droplets size={18} className={styles.iconHum} /><span className={styles.statValue}>{rucheData?.humidite?.toFixed(0) || '--'}%</span></div>
                          <div className={styles.rucheOverviewStat}><Bug size={18} className={hasAlert ? styles.iconAlert : styles.iconOk} /><span className={styles.statValue}>{rucheData?.nombre_frelons || 0}</span></div>
                          <div className={styles.rucheOverviewStat}><Activity size={18} className={styles.iconActivity} /><span className={styles.statValue}>{rucheData?.nombre_abeilles || 0}</span></div>
                        </div>
                        <div className={styles.rucheOverviewFooter}><span>Voir détails</span><ChevronRight size={16} /></div>
                      </div>
                    );
                  })}
                </div>
              </CardContent>
            </Card>
          ))}
        </>
      )}

      {selectedRuche && (
        <>
          <div className={styles.statsGrid}>
            <StatCard title="Frelons détectés" value={selectedRucheData?.nombre_frelons || 0} icon={Bug} color={selectedRucheData?.nombre_frelons > 0 ? 'red' : 'green'} />
            <StatCard title="Température" value={selectedRucheData?.temperature?.toFixed(1) || 0} unit="°C" icon={Thermometer} color="honey" />
            <StatCard title="Humidité" value={selectedRucheData?.humidite?.toFixed(0) || 0} unit="%" icon={Droplets} color="blue" />
            <StatCard title="Abeilles à l'entrée" value={selectedRucheData?.nombre_abeilles || 0} icon={Activity} color="green" subtitle="Total détecté" />
          </div>

          <div className={styles.timeFilterBar}>
            <div className={styles.timeFilterLabel}><Clock size={16} /><span>Période :</span></div>
            <div className={styles.timeFilterButtons}>
              {TIME_FILTERS.map((filter) => (
                <button key={filter.value} className={`${styles.timeFilterBtn} ${timeFilter === filter.value ? styles.timeFilterActive : ''}`} onClick={() => handleTimeFilterChange(filter.value)}>{filter.label}</button>
              ))}
            </div>
          </div>

          {showCustomPicker && (
            <div className={styles.customDatePicker}>
              <div className={styles.dateInputGroup}>
                <label><Calendar size={14} /> Début</label>
                <input type="datetime-local" value={customRange.start} onChange={(e) => setCustomRange({ ...customRange, start: e.target.value })} />
              </div>
              <div className={styles.dateInputGroup}>
                <label><Calendar size={14} /> Fin</label>
                <input type="datetime-local" value={customRange.end} onChange={(e) => setCustomRange({ ...customRange, end: e.target.value })} />
              </div>
              <Button onClick={handleCustomRangeSubmit} size="small">Appliquer</Button>
            </div>
          )}

          <div className={styles.chartsGrid}>
            <Card className={styles.chartCard}>
              <CardHeader title="Température & Humidité" subtitle={currentTimeFilter?.label || 'Personnalisé'} />
              <CardContent>
                <div className={styles.chartContainer}>
                  <ResponsiveContainer width="100%" height={300}>
                    <AreaChart data={historicalData}>
                      <defs>
                        <linearGradient id="tempGradient" x1="0" y1="0" x2="0" y2="1"><stop offset="5%" stopColor="#f59e0b" stopOpacity={0.3} /><stop offset="95%" stopColor="#f59e0b" stopOpacity={0} /></linearGradient>
                        <linearGradient id="humGradient" x1="0" y1="0" x2="0" y2="1"><stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3} /><stop offset="95%" stopColor="#3b82f6" stopOpacity={0} /></linearGradient>
                        <linearGradient id="nightGradient" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor="#1e3a8a" stopOpacity={0.15} /><stop offset="100%" stopColor="#3b82f6" stopOpacity={0.08} /></linearGradient>
                      </defs>
                      <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                      {nightPeriods.map((p, i) => <ReferenceArea key={i} x1={p.start} x2={p.end} fill="url(#nightGradient)" />)}
                      <XAxis dataKey="fullTime" stroke="#9ca3af" fontSize={11} tickLine={false} interval="preserveStartEnd" />
                      <YAxis stroke="#9ca3af" fontSize={12} tickLine={false} />
                      <Tooltip contentStyle={{ background: 'white', border: 'none', borderRadius: '12px', boxShadow: '0 10px 40px rgba(0,0,0,0.15)' }} />
                      <Legend />
                      <Area type="monotone" dataKey="temperature" stroke="#f59e0b" strokeWidth={2} fill="url(#tempGradient)" name="Température (°C)" connectNulls={false} dot={false} />
                      <Area type="monotone" dataKey="humidite" stroke="#3b82f6" strokeWidth={2} fill="url(#humGradient)" name="Humidité (%)" connectNulls={false} dot={false} />
                    </AreaChart>
                  </ResponsiveContainer>
                </div>
              </CardContent>
            </Card>

            <Card className={styles.chartCard}>
              <CardHeader title="Détection de frelons" subtitle={currentTimeFilter?.label || 'Personnalisé'} />
              <CardContent>
                <div className={styles.chartContainer}>
                  <ResponsiveContainer width="100%" height={300}>
                    <AreaChart data={historicalData}>
                      <defs>
                        <linearGradient id="hornetsGradient" x1="0" y1="0" x2="0" y2="1"><stop offset="5%" stopColor="#ef4444" stopOpacity={0.4} /><stop offset="95%" stopColor="#ef4444" stopOpacity={0} /></linearGradient>
                        <linearGradient id="nightGradient2" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor="#1e3a8a" stopOpacity={0.15} /><stop offset="100%" stopColor="#3b82f6" stopOpacity={0.08} /></linearGradient>
                      </defs>
                      <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                      {nightPeriods.map((p, i) => <ReferenceArea key={i} x1={p.start} x2={p.end} fill="url(#nightGradient2)" />)}
                      <XAxis dataKey="fullTime" stroke="#9ca3af" fontSize={11} tickLine={false} interval="preserveStartEnd" />
                      <YAxis stroke="#9ca3af" fontSize={12} tickLine={false} />
                      <Tooltip contentStyle={{ background: 'white', border: 'none', borderRadius: '12px', boxShadow: '0 10px 40px rgba(0,0,0,0.15)' }} />
                      <Area type="monotone" dataKey="nombre_frelons" stroke="#ef4444" strokeWidth={2} fill="url(#hornetsGradient)" name="Frelons détectés" connectNulls={false} dot={false} />
                    </AreaChart>
                  </ResponsiveContainer>
                </div>
              </CardContent>
            </Card>

            <Card className={`${styles.chartCard} ${styles.fullWidth}`}>
              <CardHeader title="Abeilles à l'entrée" subtitle={`Comptage estimé (±15%) - ${currentTimeFilter?.label || 'Personnalisé'}`} />
              <CardContent>
                <div className={styles.chartContainer}>
                  <ResponsiveContainer width="100%" height={300}>
                    <AreaChart data={historicalData}>
                      <defs>
                        <linearGradient id="nightGradient3" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor="#1e3a8a" stopOpacity={0.15} /><stop offset="100%" stopColor="#3b82f6" stopOpacity={0.08} /></linearGradient>
                        <linearGradient id="beesGradient" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor="#22c55e" stopOpacity={0.5} /><stop offset="100%" stopColor="#22c55e" stopOpacity={0.05} /></linearGradient>
                        <linearGradient id="uncertaintyGradient" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor="#22c55e" stopOpacity={0.25} /><stop offset="100%" stopColor="#22c55e" stopOpacity={0.05} /></linearGradient>
                      </defs>
                      <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                      {nightPeriods.map((p, i) => <ReferenceArea key={i} x1={p.start} x2={p.end} fill="url(#nightGradient3)" />)}
                      <XAxis dataKey="fullTime" stroke="#9ca3af" fontSize={11} tickLine={false} interval="preserveStartEnd" />
                      <YAxis stroke="#9ca3af" fontSize={12} tickLine={false} />
                      <Tooltip contentStyle={{ background: 'white', border: 'none', borderRadius: '12px', boxShadow: '0 10px 40px rgba(0,0,0,0.15)' }} formatter={(value, name) => {
                        if (name === 'Plage estimée (max)') return [null, null];
                        if (name === 'Plage estimée (min)') return [null, null];
                        return [value, name];
                      }} />
                      <Legend formatter={(value) => value === 'Plage estimée (max)' || value === 'Plage estimée (min)' ? null : value} />
                      <Area type="monotone" dataKey="abeilles_max" stroke="none" fill="url(#uncertaintyGradient)" connectNulls={false} name="Plage estimée (max)" legendType="none" />
                      <Area type="monotone" dataKey="abeilles_min" stroke="none" fill="white" connectNulls={false} name="Plage estimée (min)" legendType="none" />
                      <Area type="monotone" dataKey="nombre_abeilles" stroke="#22c55e" strokeWidth={2} fill="none" connectNulls={false} name="Abeilles détectées" dot={false} />
                    </AreaChart>
                  </ResponsiveContainer>
                </div>
              </CardContent>
            </Card>
          </div>
        </>
      )}
    </div>
  );
}
