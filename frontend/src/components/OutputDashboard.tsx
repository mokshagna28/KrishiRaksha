import React, { useEffect, useState, useCallback } from 'react';
import {
  Activity, BarChart2, AlertTriangle, RefreshCw, CheckCircle,
  XCircle, Clock, Shield, Zap, TrendingUp, Database, Cloud,
  MessageSquare, Cpu, Eye, ChevronDown, ChevronUp
} from 'lucide-react';
import { fetchSystemStatus, fetchMlMetrics, fetchLatestPredictions } from '../api';

/* ── helper: status dot colour ── */
const statusColor = (s: string) => {
  if (!s) return '#64748b';
  const up = s.toUpperCase();
  if (['CONNECTED', 'READY', 'CONFIGURED', 'ACTIVE', 'LIVE'].includes(up)) return '#10b981';
  if (['AWAITING_FIRST_SYNC', 'NOT_TRAINED', 'PENDING'].includes(up)) return '#f59e0b';
  return '#ef4444';
};

const StatusDot: React.FC<{ status: string }> = ({ status }) => (
  <span style={{
    display: 'inline-block', width: 8, height: 8, borderRadius: '50%',
    background: statusColor(status),
    boxShadow: `0 0 6px ${statusColor(status)}80`,
    marginRight: 8, flexShrink: 0,
  }} />
);

/* ── risk badge ── */
const RiskBadge: React.FC<{ level: string }> = ({ level }) => {
  const map: Record<string, { cls: string; label: string }> = {
    VERY_HIGH: { cls: 'badge-red pulse-badge', label: 'CRITICAL' },
    HIGH: { cls: 'badge-orange', label: 'HIGH' },
    MODERATE: { cls: 'badge-yellow', label: 'MODERATE' },
    LOW: { cls: 'badge-green', label: 'LOW' },
  };
  const m = map[level] ?? map.LOW;
  return <span className={`badge ${m.cls}`}>{m.label}</span>;
};

/* ── gauge ring (SVG) ── */
const GaugeRing: React.FC<{ value: number; label: string; color: string; size?: number }> = ({
  value, label, color, size = 90,
}) => {
  const r = (size - 12) / 2;
  const circ = 2 * Math.PI * r;
  const offset = circ * (1 - Math.min(value, 1));
  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 6 }}>
      <svg width={size} height={size} style={{ transform: 'rotate(-90deg)' }}>
        <circle cx={size / 2} cy={size / 2} r={r} fill="none"
          stroke="rgba(255,255,255,0.06)" strokeWidth={8} />
        <circle cx={size / 2} cy={size / 2} r={r} fill="none"
          stroke={color} strokeWidth={8} strokeLinecap="round"
          strokeDasharray={circ} strokeDashoffset={offset}
          style={{ transition: 'stroke-dashoffset 1.2s cubic-bezier(.4,0,.2,1)' }} />
      </svg>
      <span style={{ position: 'relative', top: -(size / 2 + 10), fontSize: '1rem', fontWeight: 700, color }}>
        {(value * 100).toFixed(1)}%
      </span>
      <span style={{ marginTop: -(size / 2 - 2), fontSize: '0.72rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
        {label}
      </span>
    </div>
  );
};

/* ═══════════════════════════════════════════════════════════ */
/* ███  MAIN COMPONENT                                  ███ */
/* ═══════════════════════════════════════════════════════════ */
export const OutputDashboard: React.FC = () => {
  const [system, setSystem] = useState<any>(null);
  const [mlMetrics, setMlMetrics] = useState<any>(null);
  const [predictions, setPredictions] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [lastRefresh, setLastRefresh] = useState<Date | null>(null);
  const [showAllPreds, setShowAllPreds] = useState(false);
  const [refreshing, setRefreshing] = useState(false);

  const load = useCallback(async (isManual = false) => {
    if (isManual) setRefreshing(true);
    else setLoading(true);
    try {
      const [sys, ml, preds] = await Promise.all([
        fetchSystemStatus().catch(() => null),
        fetchMlMetrics().catch(() => null),
        fetchLatestPredictions().catch(() => []),
      ]);
      if (sys) setSystem(sys);
      if (ml) setMlMetrics(ml);
      setPredictions(preds ?? []);
      setLastRefresh(new Date());
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    load();
    const id = setInterval(() => load(), 30000);
    return () => clearInterval(id);
  }, [load]);

  /* ── loading state ── */
  if (loading) {
    return (
      <div className="glass-card" style={{ textAlign: 'center', padding: 64 }}>
        <RefreshCw size={36} color="var(--text-muted)" className="spin"
          style={{ animation: 'spin 1.2s linear infinite' }} />
        <p style={{ marginTop: 16, color: 'var(--text-muted)' }}>Initialising Output Dashboard…</p>
        <style>{`@keyframes spin{to{transform:rotate(360deg)}}`}</style>
      </div>
    );
  }

  /* ── derived stats ── */
  const riskCounts = { LOW: 0, MODERATE: 0, HIGH: 0, VERY_HIGH: 0 };
  predictions.forEach(p => { if (riskCounts[p.final_risk_level as keyof typeof riskCounts] !== undefined) riskCounts[p.final_risk_level as keyof typeof riskCounts]++; });
  const totalDistricts = predictions.length;
  const criticalCount = riskCounts.VERY_HIGH + riskCounts.HIGH;
  const avgConfidence = predictions.length ? predictions.reduce((s, p) => s + (p.confidence ?? 0), 0) / predictions.length : 0;

  const serviceRows = [
    { icon: <Cloud size={16} />, name: 'Weather API (IMD)', status: system?.weather_api },
    { icon: <Database size={16} />, name: 'Database', status: system?.database },
    { icon: <Cpu size={16} />, name: 'ML Model (Rainfall)', status: system?.ml_model },
    { icon: <Zap size={16} />, name: 'Crop Water ML', status: system?.crop_water_ml },
    { icon: <TrendingUp size={16} />, name: 'Marketplace ML', status: system?.marketplace_ml },
    { icon: <Activity size={16} />, name: 'MLflow Tracking', status: system?.mlflow },
    { icon: <MessageSquare size={16} />, name: 'SMS Gateway', status: system?.sms_gateway },
    { icon: <Shield size={16} />, name: 'DLT Registration', status: system?.dlt },
  ];

  const visiblePreds = showAllPreds ? predictions : predictions.slice(0, 8);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>

      {/* ═══ Header row ═══ */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 12 }}>
        <div>
          <h2 style={{ margin: 0, fontSize: '1.5rem', fontWeight: 700, display: 'flex', alignItems: 'center', gap: 10 }}>
            <Eye size={22} color="#38bdf8" /> Output Dashboard
          </h2>
          <p style={{ margin: '4px 0 0', fontSize: '0.8rem', color: 'var(--text-dim)' }}>
            Real-time system health, ML performance & district risk overview
          </p>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          {lastRefresh && (
            <span style={{ fontSize: '0.75rem', color: 'var(--text-dim)', display: 'flex', alignItems: 'center', gap: 4 }}>
              <Clock size={12} /> {lastRefresh.toLocaleTimeString()}
            </span>
          )}
          <button className="btn btn-secondary" onClick={() => load(true)} disabled={refreshing}
            style={{ padding: '6px 14px', fontSize: '0.8rem' }}>
            <RefreshCw size={14} style={refreshing ? { animation: 'spin 1s linear infinite' } : {}} /> Refresh
          </button>
        </div>
      </div>

      {/* ═══ KPI Strip ═══ */}
      <div style={{
        display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: 14,
      }}>
        {[
          { label: 'Districts Monitored', value: system?.total_districts_monitored ?? totalDistricts, icon: <Activity size={18} />, accent: '#38bdf8' },
          { label: 'Active Farmers', value: system?.active_farmers_count ?? '—', icon: <CheckCircle size={18} />, accent: '#10b981' },
          { label: 'Alerts Today', value: system?.alerts_today ?? 0, icon: <AlertTriangle size={18} />, accent: '#f59e0b' },
          { label: 'Critical Zones', value: criticalCount, icon: <XCircle size={18} />, accent: '#ef4444' },
        ].map((kpi, i) => (
          <div key={i} className="glass-card" style={{
            padding: '16px 18px', display: 'flex', alignItems: 'center', gap: 14,
            borderLeft: `3px solid ${kpi.accent}`,
            transition: 'transform 0.2s',
          }}
            onMouseEnter={e => (e.currentTarget.style.transform = 'translateY(-2px)')}
            onMouseLeave={e => (e.currentTarget.style.transform = 'translateY(0)')}>
            <div style={{
              width: 40, height: 40, borderRadius: 10,
              background: `${kpi.accent}18`, display: 'flex', alignItems: 'center', justifyContent: 'center',
            }}>
              {React.cloneElement(kpi.icon, { color: kpi.accent })}
            </div>
            <div>
              <div style={{ fontSize: '1.5rem', fontWeight: 700, lineHeight: 1 }}>{kpi.value}</div>
              <div style={{ fontSize: '0.7rem', color: 'var(--text-dim)', marginTop: 2, textTransform: 'uppercase', letterSpacing: '0.04em' }}>{kpi.label}</div>
            </div>
          </div>
        ))}
      </div>

      {/* ═══ Two-column: Services + ML Gauges ═══ */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20 }}>

        {/* Service Health */}
        <div className="glass-card" style={{ padding: 0, overflow: 'hidden' }}>
          <div style={{
            padding: '16px 20px', borderBottom: '1px solid var(--border-subtle)',
            display: 'flex', alignItems: 'center', gap: 8,
            background: 'linear-gradient(135deg, rgba(56,189,248,0.08), transparent)',
          }}>
            <Shield size={18} color="#38bdf8" />
            <h3 style={{ margin: 0, fontSize: '0.95rem', fontWeight: 700 }}>Service Health</h3>
            <span className="badge badge-green" style={{ marginLeft: 'auto', fontSize: '0.65rem' }}>
              {serviceRows.filter(r => ['CONNECTED', 'READY', 'CONFIGURED', 'ACTIVE', 'LIVE'].includes(r.status?.toUpperCase())).length}/{serviceRows.length} UP
            </span>
          </div>
          <div style={{ padding: '8px 0' }}>
            {serviceRows.map((r, i) => (
              <div key={i} style={{
                display: 'flex', alignItems: 'center', gap: 10,
                padding: '10px 20px',
                borderBottom: i < serviceRows.length - 1 ? '1px solid rgba(255,255,255,0.03)' : 'none',
                transition: 'background 0.15s',
              }}
                onMouseEnter={e => (e.currentTarget.style.background = 'rgba(255,255,255,0.03)')}
                onMouseLeave={e => (e.currentTarget.style.background = 'transparent')}>
                <span style={{ color: 'var(--text-dim)' }}>{r.icon}</span>
                <span style={{ flex: 1, fontSize: '0.85rem' }}>{r.name}</span>
                <StatusDot status={r.status ?? ''} />
                <span style={{
                  fontSize: '0.72rem', fontWeight: 600, letterSpacing: '0.04em',
                  color: statusColor(r.status ?? ''),
                  textTransform: 'uppercase',
                }}>
                  {r.status ?? 'UNKNOWN'}
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* ML Performance Gauges */}
        <div className="glass-card" style={{ padding: 0, overflow: 'hidden' }}>
          <div style={{
            padding: '16px 20px', borderBottom: '1px solid var(--border-subtle)',
            display: 'flex', alignItems: 'center', gap: 8,
            background: 'linear-gradient(135deg, rgba(16,185,129,0.08), transparent)',
          }}>
            <BarChart2 size={18} color="#10b981" />
            <h3 style={{ margin: 0, fontSize: '0.95rem', fontWeight: 700 }}>ML Model Performance</h3>
            {mlMetrics?.algorithm && (
              <span className="badge badge-neutral" style={{ marginLeft: 'auto', fontSize: '0.65rem' }}>
                {mlMetrics.algorithm}
              </span>
            )}
          </div>
          {mlMetrics && mlMetrics.status !== 'NOT_TRAINED' ? (
            <div style={{ padding: '24px 20px 20px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-around', flexWrap: 'wrap', gap: 12 }}>
                <GaugeRing value={mlMetrics.accuracy ?? 0} label="Accuracy" color="#38bdf8" />
                <GaugeRing value={mlMetrics.precision ?? 0} label="Precision" color="#a78bfa" />
                <GaugeRing value={mlMetrics.recall ?? 0} label="Recall" color="#10b981" />
                <GaugeRing value={mlMetrics.f1_score ?? 0} label="F1-Score" color="#f59e0b" />
                <GaugeRing value={mlMetrics.roc_auc ?? 0} label="ROC-AUC" color="#f472b6" />
              </div>
              <div style={{
                marginTop: 18, padding: '10px 14px', borderRadius: 8,
                background: 'rgba(255,255,255,0.03)', fontSize: '0.78rem', color: 'var(--text-dim)',
                display: 'flex', gap: 16, flexWrap: 'wrap',
              }}>
                <span><strong style={{ color: 'var(--text-muted)' }}>Training:</strong> {mlMetrics.training_dataset_size?.toLocaleString()} samples</span>
                <span><strong style={{ color: 'var(--text-muted)' }}>Test:</strong> {mlMetrics.test_dataset_size?.toLocaleString()} samples</span>
                {mlMetrics.trained_at && <span><strong style={{ color: 'var(--text-muted)' }}>Trained:</strong> {new Date(mlMetrics.trained_at).toLocaleDateString()}</span>}
              </div>
            </div>
          ) : (
            <div style={{ padding: 40, textAlign: 'center', color: 'var(--text-dim)' }}>
              <Cpu size={32} style={{ marginBottom: 8 }} />
              <p>No ML model has been trained yet.</p>
            </div>
          )}
        </div>
      </div>

      {/* ═══ Risk Distribution Bar ═══ */}
      {totalDistricts > 0 && (
        <div className="glass-card">
          <h3 style={{ margin: '0 0 14px', fontSize: '0.95rem', fontWeight: 700, display: 'flex', alignItems: 'center', gap: 8 }}>
            <AlertTriangle size={18} color="#f59e0b" /> Risk Distribution
          </h3>
          {/* stacked bar */}
          <div style={{ display: 'flex', height: 28, borderRadius: 8, overflow: 'hidden', marginBottom: 14 }}>
            {[
              { key: 'LOW', count: riskCounts.LOW, bg: '#10b981' },
              { key: 'MODERATE', count: riskCounts.MODERATE, bg: '#f59e0b' },
              { key: 'HIGH', count: riskCounts.HIGH, bg: '#f97316' },
              { key: 'VERY_HIGH', count: riskCounts.VERY_HIGH, bg: '#ef4444' },
            ].filter(b => b.count > 0).map(b => (
              <div key={b.key} title={`${b.key}: ${b.count}`} style={{
                flex: b.count, background: b.bg, display: 'flex', alignItems: 'center', justifyContent: 'center',
                fontSize: '0.7rem', fontWeight: 700, color: '#fff', minWidth: b.count > 0 ? 30 : 0,
                transition: 'flex 0.6s ease',
              }}>
                {b.count}
              </div>
            ))}
          </div>
          <div style={{ display: 'flex', gap: 20, fontSize: '0.78rem', color: 'var(--text-muted)', flexWrap: 'wrap' }}>
            {[
              { label: 'Low', count: riskCounts.LOW, color: '#10b981' },
              { label: 'Moderate', count: riskCounts.MODERATE, color: '#f59e0b' },
              { label: 'High', count: riskCounts.HIGH, color: '#f97316' },
              { label: 'Critical', count: riskCounts.VERY_HIGH, color: '#ef4444' },
            ].map(l => (
              <span key={l.label} style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                <span style={{ width: 10, height: 10, borderRadius: 3, background: l.color, display: 'inline-block' }} />
                {l.label} — <strong style={{ color: 'var(--text-main)' }}>{l.count}</strong> ({totalDistricts ? ((l.count / totalDistricts) * 100).toFixed(0) : 0}%)
              </span>
            ))}
          </div>
        </div>
      )}

      {/* ═══ Latest District Predictions Table ═══ */}
      <div className="glass-card" style={{ padding: 0, overflow: 'hidden' }}>
        <div style={{
          padding: '16px 20px', borderBottom: '1px solid var(--border-subtle)',
          display: 'flex', alignItems: 'center', gap: 8,
          background: 'linear-gradient(135deg, rgba(245,158,11,0.08), transparent)',
        }}>
          <TrendingUp size={18} color="#f59e0b" />
          <h3 style={{ margin: 0, fontSize: '0.95rem', fontWeight: 700 }}>Latest District Risk Assessments</h3>
          <span className="badge badge-neutral" style={{ marginLeft: 'auto', fontSize: '0.65rem' }}>
            {totalDistricts} districts • avg conf {(avgConfidence * 100).toFixed(0)}%
          </span>
        </div>

        {predictions.length > 0 ? (
          <>
            <div style={{ overflowX: 'auto' }}>
              <table className="custom-table">
                <thead>
                  <tr>
                    <th>District</th>
                    <th>State</th>
                    <th>AI Risk</th>
                    <th>Official Warning</th>
                    <th>Final Risk</th>
                    <th>Score</th>
                    <th>Confidence</th>
                    <th>Freshness</th>
                  </tr>
                </thead>
                <tbody>
                  {visiblePreds.map((p: any) => (
                    <tr key={p.district_id}>
                      <td style={{ fontWeight: 600 }}>{p.district_name}</td>
                      <td style={{ color: 'var(--text-muted)' }}>{p.state_name}</td>
                      <td><RiskBadge level={p.ai_risk_level} /></td>
                      <td>
                        <span className={`badge ${p.official_warning_level === 'RED' ? 'badge-red' : p.official_warning_level === 'ORANGE' ? 'badge-orange' : p.official_warning_level === 'YELLOW' ? 'badge-yellow' : 'badge-green'}`}>
                          {p.official_warning_level ?? '—'}
                        </span>
                      </td>
                      <td><RiskBadge level={p.final_risk_level} /></td>
                      <td>
                        <span style={{
                          fontFamily: 'var(--font-mono)', fontSize: '0.82rem', fontWeight: 600,
                          color: (p.risk_score ?? 0) > 0.7 ? '#f87171' : (p.risk_score ?? 0) > 0.4 ? '#fbbf24' : '#34d399',
                        }}>
                          {((p.risk_score ?? 0) * 100).toFixed(1)}
                        </span>
                      </td>
                      <td>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                          <div style={{
                            width: 50, height: 6, borderRadius: 3, background: 'rgba(255,255,255,0.08)', overflow: 'hidden',
                          }}>
                            <div style={{
                              height: '100%', borderRadius: 3, width: `${(p.confidence ?? 0) * 100}%`,
                              background: (p.confidence ?? 0) > 0.8 ? '#10b981' : (p.confidence ?? 0) > 0.5 ? '#f59e0b' : '#ef4444',
                              transition: 'width 0.6s ease',
                            }} />
                          </div>
                          <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.78rem', color: 'var(--text-muted)' }}>
                            {((p.confidence ?? 0) * 100).toFixed(0)}%
                          </span>
                        </div>
                      </td>
                      <td>
                        <span className={`badge ${p.data_freshness_status === 'FRESH' ? 'badge-green' : p.data_freshness_status === 'STALE' ? 'badge-yellow' : 'badge-neutral'}`}>
                          {p.data_freshness_status ?? '—'}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            {predictions.length > 8 && (
              <div style={{ textAlign: 'center', padding: '12px 0', borderTop: '1px solid var(--border-subtle)' }}>
                <button className="btn btn-secondary" onClick={() => setShowAllPreds(!showAllPreds)}
                  style={{ fontSize: '0.8rem', padding: '6px 18px' }}>
                  {showAllPreds ? <><ChevronUp size={14} /> Show Less</> : <><ChevronDown size={14} /> Show All {predictions.length} Districts</>}
                </button>
              </div>
            )}
          </>
        ) : (
          <div style={{ padding: 40, textAlign: 'center', color: 'var(--text-dim)' }}>
            <AlertTriangle size={32} style={{ marginBottom: 8 }} />
            <p>No predictions available yet. Run the monitoring cycle to generate risk assessments.</p>
          </div>
        )}
      </div>

      {/* ═══ Footer Meta ═══ */}
      <div style={{
        display: 'flex', justifyContent: 'space-between', flexWrap: 'wrap', gap: 8,
        fontSize: '0.72rem', color: 'var(--text-dim)', padding: '0 4px',
      }}>
        <span>States: {system?.total_states_monitored ?? '—'} • SMS Mode: {system?.sms_mode ?? '—'}</span>
        <span>
          Last weather sync: {system?.last_weather_update ? new Date(system.last_weather_update).toLocaleString() : 'Never'}
          {' '} • Last prediction: {system?.last_prediction_update ? new Date(system.last_prediction_update).toLocaleString() : 'Never'}
        </span>
      </div>
    </div>
  );
};
