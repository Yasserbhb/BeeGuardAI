import { useState, useEffect } from 'react';
import { data, ruches as ruchesApi } from '../services/api';
import {
  Thermometer,
  Droplets,
  Bug,
  Activity,
  RefreshCw,
  MapPin,
  ChevronRight,
  Clock
} from 'lucide-react';
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend
} from 'recharts';
import Card, { CardHeader, CardContent } from '../components/Card';
import StatCard from '../components/StatCard';
import Button from '../components/Button';
import styles from './Dashboard.module.css';

// Time filter options
const TIME_FILTERS = [
  { label: '1 heure', value: 1 },
  { label: '6 heures', value: 6 },
  { label: '24 heures', value: 24 },
  { label: '7 jours', value: 168 },
  { label: '30 jours', value: 720 },
];

export default function Dashboard() {
  const [latestData, setLatestData] = useState([]);
  const [historicalData, setHistoricalData] = useState([]);
  const [ruches, setRuches] = useState([]);
  const [selectedRuche, setSelectedRuche] = useState(null);
  const [timeFilter, setTimeFilter] = useState(24); // Default 24 hours
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 30000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    if (selectedRuche) {
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

  const loadHistoricalData = async (rucheId, hours) => {
    try {
      const history = await ruchesApi.getData(rucheId, hours);
      const formatted = history.map((d) => ({
        ...d,
        time: new Date(d.timestamp).toLocaleTimeString('fr-FR', {
          hour: '2-digit',
          minute: '2-digit'
        }),
        date: new Date(d.timestamp).toLocaleDateString('fr-FR', {
          day: '2-digit',
          month: '2-digit'
        }),
        fullTime: hours > 24
          ? new Date(d.timestamp).toLocaleDateString('fr-FR', { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' })
          : new Date(d.timestamp).toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' })
      }));
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

  const handleSelectRuche = (rucheId) => {
    setSelectedRuche(rucheId);
  };

  const handleBackToOverview = () => {
    setSelectedRuche(null);
    setHistoricalData([]);
  };

  // Calculate totals from latest data
  const totals = latestData.reduce(
    (acc, d) => ({
      frelons: acc.frelons + (d.nombre_frelons || 0),
      entrees: acc.entrees + (d.nombre_abeilles_entrees || 0),
      sorties: acc.sorties + (d.nombre_abeilles_sorties || 0),
      avgTemp: acc.avgTemp + (d.temperature || 0),
      avgHum: acc.avgHum + (d.humidite || 0),
      count: acc.count + 1
    }),
    { frelons: 0, entrees: 0, sorties: 0, avgTemp: 0, avgHum: 0, count: 0 }
  );

  const avgTemp = totals.count > 0 ? (totals.avgTemp / totals.count).toFixed(1) : 0;
  const avgHum = totals.count > 0 ? (totals.avgHum / totals.count).toFixed(0) : 0;

  // Get selected ruche data
  const selectedRucheData = latestData.find(d => d.ruche_id === selectedRuche);
  const selectedRucheInfo = ruches.find(r => r.id === selectedRuche);

  // Get time filter label
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
      {/* Header */}
      <div className={styles.header}>
        <div>
          <h1 className={styles.title}>
            {selectedRuche ? (
              <span className={styles.breadcrumb}>
                <span className={styles.breadcrumbLink} onClick={handleBackToOverview}>
                  Tableau de bord
                </span>
                <ChevronRight size={20} />
                <span>{selectedRucheInfo?.nom || `Ruche ${selectedRuche}`}</span>
              </span>
            ) : (
              'Tableau de bord'
            )}
          </h1>
          <p className={styles.subtitle}>
            {selectedRuche
              ? selectedRucheInfo?.localisation || 'Détails de la ruche'
              : `Surveillance en temps réel de vos ${ruches.length} ruche${ruches.length > 1 ? 's' : ''}`
            }
          </p>
        </div>
        <div className={styles.headerActions}>
          {selectedRuche && (
            <Button
              onClick={handleBackToOverview}
              variant="secondary"
            >
              Vue d'ensemble
            </Button>
          )}
          <Button
            onClick={handleRefresh}
            loading={refreshing}
            icon={RefreshCw}
            variant="secondary"
          >
            Actualiser
          </Button>
        </div>
      </div>

      {/* Overview Mode - No ruche selected */}
      {!selectedRuche && (
        <>
          {/* Global Stats */}
          <div className={styles.statsGrid}>
            <StatCard
              title="Frelons détectés"
              value={totals.frelons}
              icon={Bug}
              color={totals.frelons > 5 ? 'red' : totals.frelons > 0 ? 'honey' : 'green'}
              subtitle="Total - Dernière heure"
            />
            <StatCard
              title="Température moyenne"
              value={avgTemp}
              unit="°C"
              icon={Thermometer}
              color="honey"
            />
            <StatCard
              title="Humidité moyenne"
              value={avgHum}
              unit="%"
              icon={Droplets}
              color="blue"
            />
            <StatCard
              title="Activité des abeilles"
              value={totals.entrees + totals.sorties}
              icon={Activity}
              color="green"
              subtitle={`${totals.entrees} entrées / ${totals.sorties} sorties`}
            />
          </div>

          {/* Ruches Grid - Click to select */}
          <Card>
            <CardHeader
              title="Vos ruches"
              subtitle="Cliquez sur une ruche pour voir les détails"
            />
            <CardContent>
              <div className={styles.ruchesOverviewGrid}>
                {ruches.map((ruche) => {
                  const rucheData = latestData.find(d => d.ruche_id === ruche.id);
                  const hasAlert = rucheData?.nombre_frelons > 0;

                  return (
                    <div
                      key={ruche.id}
                      className={`${styles.rucheOverviewCard} ${hasAlert ? styles.rucheAlert : ''}`}
                      onClick={() => handleSelectRuche(ruche.id)}
                    >
                      <div className={styles.rucheOverviewHeader}>
                        <span className={styles.rucheOverviewName}>{ruche.nom}</span>
                        <span className={`${styles.rucheOverviewStatus} ${hasAlert ? styles.statusWarning : styles.statusOk}`}>
                          {hasAlert ? 'Alerte' : 'Normal'}
                        </span>
                      </div>

                      {ruche.localisation && (
                        <div className={styles.rucheLocation}>
                          <MapPin size={14} />
                          <span>{ruche.localisation}</span>
                        </div>
                      )}

                      <div className={styles.rucheOverviewStats}>
                        <div className={styles.rucheOverviewStat}>
                          <Thermometer size={18} className={styles.iconTemp} />
                          <span className={styles.statValue}>{rucheData?.temperature?.toFixed(1) || '--'}°C</span>
                        </div>
                        <div className={styles.rucheOverviewStat}>
                          <Droplets size={18} className={styles.iconHum} />
                          <span className={styles.statValue}>{rucheData?.humidite?.toFixed(0) || '--'}%</span>
                        </div>
                        <div className={styles.rucheOverviewStat}>
                          <Bug size={18} className={hasAlert ? styles.iconAlert : styles.iconOk} />
                          <span className={styles.statValue}>{rucheData?.nombre_frelons || 0}</span>
                        </div>
                        <div className={styles.rucheOverviewStat}>
                          <Activity size={18} className={styles.iconActivity} />
                          <span className={styles.statValue}>
                            {(rucheData?.nombre_abeilles_entrees || 0) + (rucheData?.nombre_abeilles_sorties || 0)}
                          </span>
                        </div>
                      </div>

                      <div className={styles.rucheOverviewFooter}>
                        <span>Voir détails</span>
                        <ChevronRight size={16} />
                      </div>
                    </div>
                  );
                })}
              </div>
            </CardContent>
          </Card>
        </>
      )}

      {/* Detail Mode - Ruche selected */}
      {selectedRuche && (
        <>
          {/* Selected Ruche Stats */}
          <div className={styles.statsGrid}>
            <StatCard
              title="Frelons détectés"
              value={selectedRucheData?.nombre_frelons || 0}
              icon={Bug}
              color={selectedRucheData?.nombre_frelons > 0 ? 'red' : 'green'}
            />
            <StatCard
              title="Température"
              value={selectedRucheData?.temperature?.toFixed(1) || 0}
              unit="°C"
              icon={Thermometer}
              color="honey"
            />
            <StatCard
              title="Humidité"
              value={selectedRucheData?.humidite?.toFixed(0) || 0}
              unit="%"
              icon={Droplets}
              color="blue"
            />
            <StatCard
              title="Activité"
              value={(selectedRucheData?.nombre_abeilles_entrees || 0) + (selectedRucheData?.nombre_abeilles_sorties || 0)}
              icon={Activity}
              color="green"
              subtitle={`${selectedRucheData?.nombre_abeilles_entrees || 0} entrées / ${selectedRucheData?.nombre_abeilles_sorties || 0} sorties`}
            />
          </div>

          {/* Time Filter */}
          <div className={styles.timeFilterBar}>
            <div className={styles.timeFilterLabel}>
              <Clock size={16} />
              <span>Période :</span>
            </div>
            <div className={styles.timeFilterButtons}>
              {TIME_FILTERS.map((filter) => (
                <button
                  key={filter.value}
                  className={`${styles.timeFilterBtn} ${timeFilter === filter.value ? styles.timeFilterActive : ''}`}
                  onClick={() => setTimeFilter(filter.value)}
                >
                  {filter.label}
                </button>
              ))}
            </div>
          </div>

          {/* Charts */}
          <div className={styles.chartsGrid}>
            {/* Temperature & Humidity Chart */}
            <Card className={styles.chartCard}>
              <CardHeader
                title="Température & Humidité"
                subtitle={`Dernières ${currentTimeFilter?.label || '24 heures'}`}
              />
              <CardContent>
                <div className={styles.chartContainer}>
                  <ResponsiveContainer width="100%" height={300}>
                    <AreaChart data={historicalData}>
                      <defs>
                        <linearGradient id="tempGradient" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor="#f59e0b" stopOpacity={0.3} />
                          <stop offset="95%" stopColor="#f59e0b" stopOpacity={0} />
                        </linearGradient>
                        <linearGradient id="humGradient" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3} />
                          <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                        </linearGradient>
                      </defs>
                      <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                      <XAxis
                        dataKey="fullTime"
                        stroke="#9ca3af"
                        fontSize={11}
                        tickLine={false}
                        interval="preserveStartEnd"
                      />
                      <YAxis stroke="#9ca3af" fontSize={12} tickLine={false} />
                      <Tooltip
                        contentStyle={{
                          background: 'white',
                          border: 'none',
                          borderRadius: '12px',
                          boxShadow: '0 10px 40px rgba(0,0,0,0.15)'
                        }}
                      />
                      <Legend />
                      <Area
                        type="monotone"
                        dataKey="temperature"
                        stroke="#f59e0b"
                        strokeWidth={2}
                        fill="url(#tempGradient)"
                        name="Température (°C)"
                      />
                      <Area
                        type="monotone"
                        dataKey="humidite"
                        stroke="#3b82f6"
                        strokeWidth={2}
                        fill="url(#humGradient)"
                        name="Humidité (%)"
                      />
                    </AreaChart>
                  </ResponsiveContainer>
                </div>
              </CardContent>
            </Card>

            {/* Hornets Chart */}
            <Card className={styles.chartCard}>
              <CardHeader
                title="Détection de frelons"
                subtitle={`Dernières ${currentTimeFilter?.label || '24 heures'}`}
              />
              <CardContent>
                <div className={styles.chartContainer}>
                  <ResponsiveContainer width="100%" height={300}>
                    <AreaChart data={historicalData}>
                      <defs>
                        <linearGradient id="hornetsGradient" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor="#ef4444" stopOpacity={0.4} />
                          <stop offset="95%" stopColor="#ef4444" stopOpacity={0} />
                        </linearGradient>
                      </defs>
                      <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                      <XAxis
                        dataKey="fullTime"
                        stroke="#9ca3af"
                        fontSize={11}
                        tickLine={false}
                        interval="preserveStartEnd"
                      />
                      <YAxis stroke="#9ca3af" fontSize={12} tickLine={false} />
                      <Tooltip
                        contentStyle={{
                          background: 'white',
                          border: 'none',
                          borderRadius: '12px',
                          boxShadow: '0 10px 40px rgba(0,0,0,0.15)'
                        }}
                      />
                      <Area
                        type="monotone"
                        dataKey="nombre_frelons"
                        stroke="#ef4444"
                        strokeWidth={2}
                        fill="url(#hornetsGradient)"
                        name="Frelons détectés"
                      />
                    </AreaChart>
                  </ResponsiveContainer>
                </div>
              </CardContent>
            </Card>

            {/* Bee Activity Chart */}
            <Card className={`${styles.chartCard} ${styles.fullWidth}`}>
              <CardHeader
                title="Activité des abeilles"
                subtitle={`Entrées et sorties - Dernières ${currentTimeFilter?.label || '24 heures'}`}
              />
              <CardContent>
                <div className={styles.chartContainer}>
                  <ResponsiveContainer width="100%" height={300}>
                    <LineChart data={historicalData}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                      <XAxis
                        dataKey="fullTime"
                        stroke="#9ca3af"
                        fontSize={11}
                        tickLine={false}
                        interval="preserveStartEnd"
                      />
                      <YAxis stroke="#9ca3af" fontSize={12} tickLine={false} />
                      <Tooltip
                        contentStyle={{
                          background: 'white',
                          border: 'none',
                          borderRadius: '12px',
                          boxShadow: '0 10px 40px rgba(0,0,0,0.15)'
                        }}
                      />
                      <Legend />
                      <Line
                        type="monotone"
                        dataKey="nombre_abeilles_entrees"
                        stroke="#22c55e"
                        strokeWidth={2}
                        dot={false}
                        name="Entrées"
                      />
                      <Line
                        type="monotone"
                        dataKey="nombre_abeilles_sorties"
                        stroke="#f59e0b"
                        strokeWidth={2}
                        dot={false}
                        name="Sorties"
                      />
                    </LineChart>
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
