import React, { useState, useEffect } from 'react';
import { 
  fetchSystemStatus, fetchDistricts, fetchStates, fetchFarmers, 
  fetchAlerts, fetchSmsLogs, fetchSmsConfig, fetchMlMetrics,
  refreshWeather, runPredictions, runMonitoringCycle 
} from './api';
import { Header } from './components/Header';
import { DashboardTab } from './components/DashboardTab';
import { FarmerRegistryTab } from './components/FarmerRegistryTab';
import { AlertsTab } from './components/AlertsTab';
import { SmsHubTab } from './components/SmsHubTab';
import { MLStudioTab } from './components/MLStudioTab';
import { CropWaterTab } from './components/CropWaterTab';
import { MarketplaceTab } from './components/MarketplaceTab';
import { OutputDashboard } from './components/OutputDashboard';
import { LayoutDashboard, Users, Bell, MessageSquare, Cpu, Droplets, ShoppingCart, Eye } from 'lucide-react';

export function App() {
  const [activeTab, setActiveTab] = useState<'dashboard' | 'farmers' | 'alerts' | 'sms' | 'ml' | 'output' | 'cropwater' | 'marketplace'>('dashboard');

  // App Data States
  const [systemStatus, setSystemStatus] = useState<any>(null);
  const [districts, setDistricts] = useState<any[]>([]);
  const [states, setStates] = useState<any[]>([]);
  const [farmers, setFarmers] = useState<any[]>([]);
  const [alerts, setAlerts] = useState<any[]>([]);
  const [smsLogs, setSmsLogs] = useState<any[]>([]);
  const [smsConfig, setSmsConfig] = useState<any>(null);
  const [mlMetrics, setMlMetrics] = useState<any>(null);

  // Interaction States
  const [loadingAction, setLoadingAction] = useState<string | null>(null);
  const [preselectedDistrict, setPreselectedDistrict] = useState<any | null>(null);

  // Load all initial data
  const loadData = async () => {
    try {
      const [statusData, distData, stateData, farmerData, alertData, smsData, cfgData, mlData] = await Promise.all([
        fetchSystemStatus().catch(() => null),
        fetchDistricts().catch(() => []),
        fetchStates().catch(() => []),
        fetchFarmers().catch(() => []),
        fetchAlerts().catch(() => []),
        fetchSmsLogs().catch(() => []),
        fetchSmsConfig().catch(() => null),
        fetchMlMetrics().catch(() => null),
      ]);

      if (statusData) setSystemStatus(statusData);
      setDistricts(distData || []);
      setStates(stateData || []);
      setFarmers(farmerData || []);
      setAlerts(alertData || []);
      setSmsLogs(smsData || []);
      if (cfgData) setSmsConfig(cfgData);
      if (mlData) setMlMetrics(mlData);
    } catch (err) {
      console.error('Error loading initial data', err);
    }
  };

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 20000); // 20s auto-sync
    return () => clearInterval(interval);
  }, []);

  // Action handlers
  const handleRefreshWeather = async () => {
    try {
      setLoadingAction('weather');
      await refreshWeather();
      await loadData();
    } catch (e: any) {
      alert('Weather sync failed: ' + e.message);
    } finally {
      setLoadingAction(null);
    }
  };

  const handleRunPredictions = async () => {
    try {
      setLoadingAction('predictions');
      await runPredictions();
      await loadData();
    } catch (e: any) {
      alert('Prediction run failed: ' + e.message);
    } finally {
      setLoadingAction(null);
    }
  };

  const handleRunCycle = async () => {
    try {
      setLoadingAction('cycle');
      const res = await runMonitoringCycle();
      await loadData();
      alert(`Monitoring Cycle Completed! ${res.alerts_generated} alerts dispatched.`);
    } catch (e: any) {
      alert('Cycle run failed: ' + e.message);
    } finally {
      setLoadingAction(null);
    }
  };

  const handleOpenAlertForDistrict = (district: any) => {
    setPreselectedDistrict(district);
    setActiveTab('alerts');
  };

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      <Header
        systemStatus={systemStatus}
        onRefreshWeather={handleRefreshWeather}
        onRunPredictions={handleRunPredictions}
        onRunCycle={handleRunCycle}
        loadingAction={loadingAction}
      />

      {/* Navigation Tabs */}
      <nav style={{
        background: 'rgba(15, 23, 42, 0.7)',
        borderBottom: '1px solid var(--border-subtle)',
        padding: '0 24px',
        display: 'flex',
        gap: '4px',
        overflowX: 'auto',
      }}>
        <button
          className={`btn ${activeTab === 'dashboard' ? 'btn-primary' : 'btn-secondary'}`}
          style={{ borderRadius: '8px 8px 0 0', borderBottom: 'none', padding: '10px 18px', background: activeTab === 'dashboard' ? undefined : 'transparent' }}
          onClick={() => setActiveTab('dashboard')}
        >
          <LayoutDashboard size={16} /> District Risk Matrix
        </button>

        <button
          className={`btn ${activeTab === 'farmers' ? 'btn-primary' : 'btn-secondary'}`}
          style={{ borderRadius: '8px 8px 0 0', borderBottom: 'none', padding: '10px 18px', background: activeTab === 'farmers' ? undefined : 'transparent' }}
          onClick={() => setActiveTab('farmers')}
        >
          <Users size={16} /> Farmer Registry ({farmers.length})
        </button>

        <button
          className={`btn ${activeTab === 'alerts' ? 'btn-primary' : 'btn-secondary'}`}
          style={{ borderRadius: '8px 8px 0 0', borderBottom: 'none', padding: '10px 18px', background: activeTab === 'alerts' ? undefined : 'transparent' }}
          onClick={() => setActiveTab('alerts')}
        >
          <Bell size={16} /> Early Warning Alerts ({alerts.length})
        </button>

        <button
          className={`btn ${activeTab === 'sms' ? 'btn-primary' : 'btn-secondary'}`}
          style={{ borderRadius: '8px 8px 0 0', borderBottom: 'none', padding: '10px 18px', background: activeTab === 'sms' ? undefined : 'transparent' }}
          onClick={() => setActiveTab('sms')}
        >
          <MessageSquare size={16} /> SMS Delivery Hub ({smsLogs.length})
        </button>

        <button
          className={`btn ${activeTab === 'ml' ? 'btn-primary' : 'btn-secondary'}`}
          style={{ borderRadius: '8px 8px 0 0', borderBottom: 'none', padding: '10px 18px', background: activeTab === 'ml' ? undefined : 'transparent' }}
          onClick={() => setActiveTab('ml')}
        >
          <Cpu size={16} /> AI / ML Studio
        </button>

        <button
          className={`btn ${activeTab === 'output' ? 'btn-primary' : 'btn-secondary'}`}
          style={{ borderRadius: '8px 8px 0 0', borderBottom: 'none', padding: '10px 18px', background: activeTab === 'output' ? undefined : 'transparent' }}
          onClick={() => setActiveTab('output')}
        >
          <Eye size={16} /> Output Dashboard
        </button>

        <button
          className={`btn ${activeTab === 'cropwater' ? 'btn-primary' : 'btn-secondary'}`}
          style={{ borderRadius: '8px 8px 0 0', borderBottom: 'none', padding: '10px 18px', background: activeTab === 'cropwater' ? undefined : 'transparent' }}
          onClick={() => setActiveTab('cropwater')}
        >
          <Droplets size={16} /> Crop Water Intelligence
        </button>

        <button
          className={`btn ${activeTab === 'marketplace' ? 'btn-primary' : 'btn-secondary'}`}
          style={{ borderRadius: '8px 8px 0 0', borderBottom: 'none', padding: '10px 18px', background: activeTab === 'marketplace' ? undefined : 'transparent' }}
          onClick={() => setActiveTab('marketplace')}
        >
          <ShoppingCart size={16} /> Marketplace
        </button>
      </nav>

      {/* Main Content Area */}
      <main style={{ flex: 1, padding: '24px', maxWidth: '1440px', width: '100%', margin: '0 auto' }}>
        {activeTab === 'dashboard' && (
          <DashboardTab
            systemStatus={systemStatus}
            districts={districts}
            states={states}
            onOpenAlertModal={handleOpenAlertForDistrict}
          />
        )}

        {activeTab === 'farmers' && (
          <FarmerRegistryTab
            farmers={farmers}
            states={states}
            districts={districts}
            onFarmerRegistered={loadData}
          />
        )}

        {activeTab === 'alerts' && (
          <AlertsTab
            alerts={alerts}
            states={states}
            districts={districts}
            onAlertTriggered={loadData}
            preselectedDistrict={preselectedDistrict}
          />
        )}

        {activeTab === 'sms' && (
          <SmsHubTab
            smsLogs={smsLogs}
            smsConfig={smsConfig}
            onSmsSent={loadData}
          />
        )}

        {activeTab === 'ml' && (
          <MLStudioTab
            mlMetrics={mlMetrics}
          />
        )}

        {activeTab === 'output' && (
          <OutputDashboard />
        )}

        {activeTab === 'cropwater' && (
          <CropWaterTab />
        )}

        {activeTab === 'marketplace' && (
          <MarketplaceTab />
        )}
      </main>

      {/* Footer */}
      <footer style={{
        borderTop: '1px solid var(--border-subtle)',
        padding: '16px 24px',
        textAlign: 'center',
        fontSize: '0.8rem',
        color: 'var(--text-dim)',
        background: 'rgba(15, 23, 42, 0.8)',
      }}>
        KRISHIRAKSHA AI &bull; B.Tech Final Year CSE Project &bull; Heavy Rainfall & Flood Risk Early Warning System for Indian Farmers
      </footer>
    </div>
  );
}

export default App;
