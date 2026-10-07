import React, { useState } from 'react';
import { 
  AlertTriangle, CheckCircle, Droplets, MapPin, 
  Wind, Thermometer, ShieldAlert, ArrowUpRight, Search, Filter, Info
} from 'lucide-react';
import { fetchDistrictDetail } from '../api';

interface DashboardTabProps {
  systemStatus: any;
  districts: any[];
  states: any[];
  onOpenAlertModal: (district: any) => void;
}

export const DashboardTab: React.FC<DashboardTabProps> = ({
  systemStatus,
  districts,
  states,
  onOpenAlertModal,
}) => {
  const [search, setSearch] = useState('');
  const [selectedState, setSelectedState] = useState<string>('ALL');
  const [selectedRisk, setSelectedRisk] = useState<string>('ALL');
  const [detailModal, setDetailModal] = useState<any | null>(null);
  const [loadingDetail, setLoadingDetail] = useState(false);

  const handleOpenDetail = async (districtId: number) => {
    try {
      setLoadingDetail(true);
      const detail = await fetchDistrictDetail(districtId);
      setDetailModal(detail);
    } catch (e) {
      alert('Error fetching district details');
    } finally {
      setLoadingDetail(false);
    }
  };

  const getRiskBadge = (level: string) => {
    switch (level) {
      case 'VERY_HIGH': return <span className="badge badge-red pulse-badge">CRITICAL (RED)</span>;
      case 'HIGH': return <span className="badge badge-orange">HIGH (ORANGE)</span>;
      case 'MODERATE': return <span className="badge badge-yellow">MODERATE (YELLOW)</span>;
      default: return <span className="badge badge-green">LOW (GREEN)</span>;
    }
  };

  const filteredDistricts = districts.filter((d) => {
    const matchesSearch = d.name.toLowerCase().includes(search.toLowerCase()) || 
                          d.state_name.toLowerCase().includes(search.toLowerCase());
    const matchesState = selectedState === 'ALL' || d.state_name === selectedState;
    const matchesRisk = selectedRisk === 'ALL' || d.current_risk === selectedRisk;
    return matchesSearch && matchesState && matchesRisk;
  });

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      {/* KPI Overview Tiles */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
        gap: '16px'
      }}>
        <div className="glass-card" style={{ borderLeft: '4px solid #0284c7' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
            <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 600 }}>
              Monitored Districts
            </span>
            <MapPin size={18} color="#0284c7" />
          </div>
          <div style={{ fontSize: '1.8rem', fontWeight: 800 }}>
            {systemStatus?.total_districts_monitored || districts.length}
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)', marginTop: '4px' }}>
            Across {systemStatus?.total_states_monitored || states.length} key agricultural states
          </div>
        </div>

        <div className="glass-card" style={{ borderLeft: '4px solid #ef4444' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
            <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 600 }}>
              Critical Risk Zones
            </span>
            <ShieldAlert size={18} color="#ef4444" />
          </div>
          <div style={{ fontSize: '1.8rem', fontWeight: 800, color: '#f87171' }}>
            {(systemStatus?.very_high_risk_count || 0) + (systemStatus?.high_risk_count || 0)}
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)', marginTop: '4px' }}>
            {systemStatus?.very_high_risk_count || 0} Very High &bull; {systemStatus?.high_risk_count || 0} High
          </div>
        </div>

        <div className="glass-card" style={{ borderLeft: '4px solid #10b981' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
            <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 600 }}>
              Active Farmers
            </span>
            <CheckCircle size={18} color="#10b981" />
          </div>
          <div style={{ fontSize: '1.8rem', fontWeight: 800 }}>
            {systemStatus?.active_farmers_count || 0}
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)', marginTop: '4px' }}>
            Multi-lingual SMS subscribers
          </div>
        </div>

        <div className="glass-card" style={{ borderLeft: '4px solid #f59e0b' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
            <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 600 }}>
              Alerts Dispatched Today
            </span>
            <AlertTriangle size={18} color="#f59e0b" />
          </div>
          <div style={{ fontSize: '1.8rem', fontWeight: 800, color: '#fbbf24' }}>
            {systemStatus?.alerts_today || 0}
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)', marginTop: '4px' }}>
            With DLT-compliant templates
          </div>
        </div>
      </div>

      {/* District Matrix Filter & Search Bar */}
      <div className="glass-card" style={{ display: 'flex', gap: '12px', flexWrap: 'wrap', alignItems: 'center' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flex: '1', minWidth: '240px' }}>
          <Search size={16} color="var(--text-muted)" />
          <input
            type="text"
            className="form-input"
            placeholder="Search district or state..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Filter size={16} color="var(--text-muted)" />
          <select
            className="form-select"
            value={selectedState}
            onChange={(e) => setSelectedState(e.target.value)}
            style={{ width: 'auto' }}
          >
            <option value="ALL">All States</option>
            {states.map((s) => (
              <option key={s.id} value={s.name}>{s.name}</option>
            ))}
          </select>

          <select
            className="form-select"
            value={selectedRisk}
            onChange={(e) => setSelectedRisk(e.target.value)}
            style={{ width: 'auto' }}
          >
            <option value="ALL">All Risk Levels</option>
            <option value="VERY_HIGH">Very High Risk</option>
            <option value="HIGH">High Risk</option>
            <option value="MODERATE">Moderate Risk</option>
            <option value="LOW">Low Risk</option>
          </select>
        </div>
      </div>

      {/* District Risk Table */}
      <div className="glass-card" style={{ padding: 0, overflow: 'hidden' }}>
        <div style={{ padding: '16px 20px', borderBottom: '1px solid var(--border-subtle)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <h2 style={{ fontSize: '1rem', fontWeight: 700 }}>
            Real-Time Heavy Rain & Flood Risk Matrix ({filteredDistricts.length} Districts)
          </h2>
          <span style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>
            Composite Risk = ML Probability + IMD Warnings + 7D Soil Saturation
          </span>
        </div>

        <div style={{ overflowX: 'auto' }}>
          <table className="custom-table">
            <thead>
              <tr>
                <th>District / State</th>
                <th>24h Rainfall</th>
                <th>Risk Score</th>
                <th>AI Risk Status</th>
                <th>IMD Warning</th>
                <th style={{ textAlign: 'right' }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {filteredDistricts.length === 0 ? (
                <tr>
                  <td colSpan={6} style={{ textAlign: 'center', padding: '32px', color: 'var(--text-muted)' }}>
                    No districts found matching your criteria.
                  </td>
                </tr>
              ) : (
                filteredDistricts.map((d) => (
                  <tr key={d.id}>
                    <td>
                      <div style={{ fontWeight: 700, color: '#f8fafc' }}>{d.name}</div>
                      <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{d.state_name} ({d.code})</div>
                    </td>
                    <td>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                        <Droplets size={14} color="#38bdf8" />
                        <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 600 }}>
                          {d.current_rainfall.toFixed(1)} mm
                        </span>
                      </div>
                    </td>
                    <td>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <div style={{
                          flex: 1,
                          height: '6px',
                          background: 'rgba(255,255,255,0.1)',
                          borderRadius: '3px',
                          overflow: 'hidden',
                          width: '60px'
                        }}>
                          <div style={{
                            width: `${Math.min(d.risk_score, 100)}%`,
                            height: '100%',
                            background: d.risk_score > 75 ? '#ef4444' : d.risk_score > 55 ? '#f97316' : d.risk_score > 35 ? '#f59e0b' : '#10b981'
                          }} />
                        </div>
                        <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.8rem' }}>
                          {Math.round(d.risk_score)}/100
                        </span>
                      </div>
                    </td>
                    <td>{getRiskBadge(d.current_risk)}</td>
                    <td>
                      <span className={`badge ${
                        d.official_warning === 'RED' ? 'badge-red' :
                        d.official_warning === 'ORANGE' ? 'badge-orange' :
                        d.official_warning === 'YELLOW' ? 'badge-yellow' : 'badge-green'
                      }`}>
                        {d.official_warning}
                      </span>
                    </td>
                    <td style={{ textAlign: 'right' }}>
                      <div style={{ display: 'flex', gap: '6px', justifyContent: 'flex-end' }}>
                        <button
                          className="btn btn-secondary"
                          style={{ padding: '4px 10px', fontSize: '0.75rem' }}
                          onClick={() => handleOpenDetail(d.id)}
                        >
                          <Info size={14} /> Detail
                        </button>
                        <button
                          className="btn btn-primary"
                          style={{ padding: '4px 10px', fontSize: '0.75rem' }}
                          onClick={() => onOpenAlertModal(d)}
                        >
                          <ArrowUpRight size={14} /> Alert
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* District Detail Drawer / Modal */}
      {detailModal && (
        <div className="modal-overlay" onClick={() => setDetailModal(null)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div style={{ padding: '20px', borderBottom: '1px solid var(--border-subtle)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div>
                <h3 style={{ fontSize: '1.2rem', fontWeight: 800 }}>{detailModal.name} District Analysis</h3>
                <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>{detailModal.state_name} &bull; Lat: {detailModal.latitude}, Lon: {detailModal.longitude}</p>
              </div>
              <button className="btn btn-secondary" onClick={() => setDetailModal(null)}>✕</button>
            </div>

            <div style={{ padding: '20px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
              {/* Telemetry Grid */}
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '12px' }}>
                <div className="glass-card" style={{ padding: '12px' }}>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: '4px' }}>
                    <Droplets size={12} color="#38bdf8" /> 24h Rainfall
                  </div>
                  <div style={{ fontSize: '1.2rem', fontWeight: 800, marginTop: '4px' }}>
                    {detailModal.current_rainfall.toFixed(1)} mm
                  </div>
                </div>

                <div className="glass-card" style={{ padding: '12px' }}>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: '4px' }}>
                    <Droplets size={12} color="#a855f7" /> 7D Accumulation
                  </div>
                  <div style={{ fontSize: '1.2rem', fontWeight: 800, marginTop: '4px' }}>
                    {detailModal.recent_accumulated_7d.toFixed(1)} mm
                  </div>
                </div>

                <div className="glass-card" style={{ padding: '12px' }}>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: '4px' }}>
                    <Droplets size={12} color="#f59e0b" /> 24h Forecast
                  </div>
                  <div style={{ fontSize: '1.2rem', fontWeight: 800, marginTop: '4px' }}>
                    {detailModal.forecast_rainfall_24h.toFixed(1)} mm
                  </div>
                </div>
              </div>

              {/* Weather Sensor Conditions */}
              <div className="glass-card" style={{ padding: '14px', display: 'flex', justifyContent: 'space-around' }}>
                <div style={{ textAlign: 'center' }}>
                  <Thermometer size={16} color="#fb7171" style={{ margin: '0 auto 4px' }} />
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Temperature</div>
                  <div style={{ fontWeight: 700 }}>{detailModal.temperature ?? '--'}°C</div>
                </div>
                <div style={{ textAlign: 'center' }}>
                  <Droplets size={16} color="#38bdf8" style={{ margin: '0 auto 4px' }} />
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Humidity</div>
                  <div style={{ fontWeight: 700 }}>{detailModal.humidity ?? '--'}%</div>
                </div>
                <div style={{ textAlign: 'center' }}>
                  <Wind size={16} color="#a3e635" style={{ margin: '0 auto 4px' }} />
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Wind Speed</div>
                  <div style={{ fontWeight: 700 }}>{detailModal.wind_speed ?? '--'} km/h</div>
                </div>
              </div>

              {/* AI Inference & Contributing Factors */}
              <div className="glass-card" style={{ padding: '16px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
                  <span style={{ fontWeight: 700, fontSize: '0.9rem' }}>AI Model Reasoning & Risk Factors</span>
                  <span className="badge badge-green">Confidence: {(detailModal.prediction_confidence * 100).toFixed(0)}%</span>
                </div>
                <ul style={{ paddingLeft: '20px', fontSize: '0.85rem', color: 'var(--text-muted)', lineHeight: '1.6' }}>
                  {detailModal.risk_reasons.map((reason: string, i: number) => (
                    <li key={i}>{reason}</li>
                  ))}
                </ul>
              </div>

              {/* Registered Farmers Alert Potential */}
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: 'rgba(2, 132, 199, 0.1)', border: '1px solid rgba(2, 132, 199, 0.3)', borderRadius: '8px', padding: '12px 16px' }}>
                <div>
                  <div style={{ fontWeight: 700, fontSize: '0.9rem' }}>Registered Subscribers</div>
                  <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>{detailModal.active_farmers_count} active farmers in this district</div>
                </div>
                <button
                  className="btn btn-primary"
                  onClick={() => {
                    setDetailModal(null);
                    onOpenAlertModal(detailModal);
                  }}
                >
                  Send Early Warning
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
