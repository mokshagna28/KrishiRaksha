import React from 'react';
import { CloudRain, Cpu, Database, MessageSquare, RefreshCw, Zap, ShieldAlert, Droplets } from 'lucide-react';

interface HeaderProps {
  systemStatus: any;
  onRefreshWeather: () => void;
  onRunPredictions: () => void;
  onRunCycle: () => void;
  loadingAction: string | null;
}

export const Header: React.FC<HeaderProps> = ({
  systemStatus,
  onRefreshWeather,
  onRunPredictions,
  onRunCycle,
  loadingAction,
}) => {
  const getBadgeClass = (status: string) => {
    if (status === 'CONNECTED' || status === 'READY') return 'badge-green';
    if (status === 'AWAITING_FIRST_SYNC' || status === 'TRAINED') return 'badge-yellow';
    return 'badge-orange';
  };

  const isSmsLive = systemStatus?.sms_mode === 'live';

  return (
    <header style={{
      background: 'rgba(15, 23, 42, 0.95)',
      borderBottom: '1px solid var(--border-subtle)',
      padding: '16px 24px',
      position: 'sticky',
      top: 0,
      zIndex: 100,
      backdropFilter: 'blur(16px)',
    }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '16px' }}>
        {/* Brand & Project Info */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
          <div style={{
            background: 'linear-gradient(135deg, #0284c7, #10b981)',
            padding: '10px',
            borderRadius: '12px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            boxShadow: '0 0 20px rgba(2, 132, 199, 0.4)'
          }}>
            <ShieldAlert size={28} color="#ffffff" />
          </div>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <h1 style={{ fontSize: '1.4rem', fontWeight: 800, letterSpacing: '-0.02em', color: '#fff' }}>
                KRISHIRAKSHA AI
              </h1>
              <span className="badge badge-green" style={{ fontSize: '0.7rem' }}>
                FINAL YEAR PROJECT
              </span>
            </div>
            <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
              AI-Based Heavy Rainfall & Flood Risk Early Warning System for Indian Farmers
            </p>
          </div>
        </div>

        {/* Live System Health Indicators */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
          <div className="glass-card" style={{ padding: '6px 12px', display: 'flex', alignItems: 'center', gap: '6px' }}>
            <CloudRain size={14} color="#38bdf8" />
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Weather API:</span>
            <span className={`badge ${getBadgeClass(systemStatus?.weather_api || 'DISCONNECTED')}`}>
              {systemStatus?.weather_api || 'IDLE'}
            </span>
          </div>

          <div className="glass-card" style={{ padding: '6px 12px', display: 'flex', alignItems: 'center', gap: '6px' }}>
            <Cpu size={14} color="#a855f7" />
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>ML Engine:</span>
            <span className={`badge ${getBadgeClass(systemStatus?.ml_model || 'READY')}`}>
              {systemStatus?.ml_model || 'READY'}
            </span>
          </div>

          <div className="glass-card" style={{ padding: '6px 12px', display: 'flex', alignItems: 'center', gap: '6px' }}>
            <Database size={14} color="#10b981" />
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>DB:</span>
            <span className={`badge ${getBadgeClass(systemStatus?.database || 'CONNECTED')}`}>
              {systemStatus?.database || 'OK'}
            </span>
          </div>

          <div className="glass-card" style={{ padding: '6px 12px', display: 'flex', alignItems: 'center', gap: '6px' }}
               title={isSmsLive ? "MSG91 Live Gateway Active" : "MSG91 Test/Demo Mode Active (Configurable in .env)"}>
            <MessageSquare size={14} color="#f59e0b" />
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>SMS Gateway:</span>
            <span className={`badge ${isSmsLive ? 'badge-green' : 'badge-yellow'}`}>
              {isSmsLive ? 'MSG91 LIVE' : 'DEMO MODE'}
            </span>
          </div>

          <div className="glass-card" style={{ padding: '6px 12px', display: 'flex', alignItems: 'center', gap: '6px' }}
               title="Crop Water Intelligence ML Module">
            <Droplets size={14} color="#06b6d4" />
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Crop Water:</span>
            <span className={`badge ${getBadgeClass(systemStatus?.crop_water_ml || 'NOT_TRAINED')}`}>
              {systemStatus?.crop_water_ml || 'IDLE'}
              {systemStatus?.crop_water_version && systemStatus.crop_water_version !== 'N/A' ? ` v${systemStatus.crop_water_version}` : ''}
            </span>
          </div>
        </div>

        {/* Direct Operation Trigger Buttons */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <button
            className="btn btn-secondary"
            onClick={onRefreshWeather}
            disabled={loadingAction !== null}
            title="Fetch live radar/weather from IMD/Open-Meteo"
          >
            <CloudRain size={16} />
            {loadingAction === 'weather' ? 'Fetching...' : 'Sync Weather'}
          </button>

          <button
            className="btn btn-secondary"
            onClick={onRunPredictions}
            disabled={loadingAction !== null}
            title="Run ML heavy rain inference for all districts"
          >
            <Zap size={16} color="#38bdf8" />
            {loadingAction === 'predictions' ? 'Predicting...' : 'Run ML'}
          </button>

          <button
            className="btn btn-primary"
            onClick={onRunCycle}
            disabled={loadingAction !== null}
            title="Perform Full Automated Loop: Weather -> Predict -> Assess -> Alert"
          >
            <RefreshCw size={16} className={loadingAction === 'cycle' ? 'pulse-badge' : ''} />
            {loadingAction === 'cycle' ? 'Running Cycle...' : 'Run Full Cycle'}
          </button>
        </div>
      </div>
    </header>
  );
};
