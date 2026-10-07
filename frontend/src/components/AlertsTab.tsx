import React, { useState } from 'react';
import { ShieldAlert, Send, Eye, Clock, CheckCircle2, AlertOctagon, Smartphone } from 'lucide-react';
import { simulateAlertPreview, generateAlert } from '../api';

interface AlertsTabProps {
  alerts: any[];
  states: any[];
  districts: any[];
  onAlertTriggered: () => void;
  preselectedDistrict?: any;
}

export const AlertsTab: React.FC<AlertsTabProps> = ({
  alerts,
  states,
  districts,
  onAlertTriggered,
  preselectedDistrict,
}) => {
  const [showDispatchModal, setShowDispatchModal] = useState(!!preselectedDistrict);
  const [selectedDistrictId, setSelectedDistrictId] = useState<string>(
    preselectedDistrict?.id?.toString() || (districts[0]?.id?.toString() || '')
  );
  const [riskLevel, setRiskLevel] = useState<string>('VERY_HIGH');
  const [sendSms, setSendSms] = useState(true);

  const [previewData, setPreviewData] = useState<any | null>(null);
  const [loadingPreview, setLoadingPreview] = useState(false);
  const [dispatching, setDispatching] = useState(false);
  const [dispatchResult, setDispatchResult] = useState<any | null>(null);

  const currentDist = districts.find((d) => d.id === parseInt(selectedDistrictId));

  const handlePreview = async () => {
    if (!currentDist) return;
    try {
      setLoadingPreview(true);
      const data = await simulateAlertPreview(currentDist.id, currentDist.state_id, riskLevel);
      setPreviewData(data);
    } catch (e: any) {
      alert('Error fetching preview: ' + e.message);
    } finally {
      setLoadingPreview(false);
    }
  };

  const handleDispatch = async () => {
    if (!currentDist) return;
    try {
      setDispatching(true);
      const res = await generateAlert(currentDist.id, currentDist.state_id, riskLevel, sendSms);
      setDispatchResult(res);
      onAlertTriggered();
    } catch (e: any) {
      alert('Error dispatching alert: ' + e.message);
    } finally {
      setDispatching(false);
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      {/* Top Banner & Quick Trigger */}
      <div className="glass-card" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '16px' }}>
        <div>
          <h2 style={{ fontSize: '1.1rem', fontWeight: 800, display: 'flex', alignItems: 'center', gap: '8px' }}>
            <ShieldAlert size={20} color="#f97316" />
            Early Warning Broadcast Operations
          </h2>
          <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
            System automatically deduplicates alerts within 12 hours unless risk level escalates
          </p>
        </div>

        <button
          className="btn btn-primary"
          onClick={() => {
            setDispatchResult(null);
            setPreviewData(null);
            setShowDispatchModal(true);
          }}
        >
          <Send size={16} /> Broadcast New Alert
        </button>
      </div>

      {/* Dispatched Alerts Table */}
      <div className="glass-card" style={{ padding: 0, overflow: 'hidden' }}>
        <div style={{ padding: '16px 20px', borderBottom: '1px solid var(--border-subtle)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <h3 style={{ fontSize: '0.95rem', fontWeight: 700 }}>
            Recent Early Warning Broadcasts ({alerts.length})
          </h3>
          <span style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>
            Live records stored with SHA-256 deduplication fingerprints
          </span>
        </div>

        <div style={{ overflowX: 'auto' }}>
          <table className="custom-table">
            <thead>
              <tr>
                <th>Broadcast Time</th>
                <th>District / State</th>
                <th>Risk / Warning</th>
                <th>Alert Headline</th>
                <th>Recipients</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {alerts.length === 0 ? (
                <tr>
                  <td colSpan={6} style={{ textAlign: 'center', padding: '36px', color: 'var(--text-muted)' }}>
                    No alerts triggered yet. Click "Broadcast New Alert" to simulate or trigger an early warning.
                  </td>
                </tr>
              ) : (
                alerts.map((a) => (
                  <tr key={a.id}>
                    <td>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                        <Clock size={13} />
                        {new Date(a.created_at).toLocaleString()}
                      </div>
                    </td>
                    <td>
                      <div style={{ fontWeight: 700 }}>{a.district_name}</div>
                      <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{a.state_name}</div>
                    </td>
                    <td>
                      <div style={{ display: 'flex', gap: '6px' }}>
                        <span className={`badge ${a.risk_level === 'VERY_HIGH' ? 'badge-red' : 'badge-orange'}`}>
                          {a.risk_level}
                        </span>
                      </div>
                    </td>
                    <td>
                      <div style={{ fontSize: '0.85rem', fontWeight: 600, maxWidth: '320px' }}>
                        {a.headline}
                      </div>
                      <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)', fontFamily: 'var(--font-mono)' }}>
                        FP: {a.alert_fingerprint?.slice(0, 16)}...
                      </div>
                    </td>
                    <td>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                        <Smartphone size={14} color="#38bdf8" />
                        <span style={{ fontWeight: 700 }}>{a.recipients_count}</span>
                      </div>
                    </td>
                    <td>
                      <span className="badge badge-green">
                        <CheckCircle2 size={12} /> {a.status}
                      </span>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Broadcast Modal */}
      {showDispatchModal && (
        <div className="modal-overlay" onClick={() => setShowDispatchModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()} style={{ maxWidth: '680px' }}>
            <div style={{ padding: '20px', borderBottom: '1px solid var(--border-subtle)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <h3 style={{ fontSize: '1.2rem', fontWeight: 800 }}>Broadcast Early Warning Alert</h3>
              <button className="btn btn-secondary" onClick={() => setShowDispatchModal(false)}>✕</button>
            </div>

            <div style={{ padding: '20px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
              {dispatchResult && (
                <div style={{
                  padding: '14px',
                  borderRadius: '8px',
                  background: dispatchResult.status === 'CREATED' ? 'rgba(16, 185, 129, 0.15)' : 'rgba(245, 158, 11, 0.15)',
                  border: `1px solid ${dispatchResult.status === 'CREATED' ? 'rgba(16, 185, 129, 0.4)' : 'rgba(245, 158, 11, 0.4)'}`,
                  fontSize: '0.85rem'
                }}>
                  <div style={{ fontWeight: 700, marginBottom: '4px' }}>
                    Status: {dispatchResult.status}
                  </div>
                  <div>{dispatchResult.message || dispatchResult.reason}</div>
                  {dispatchResult.recipients_queued !== undefined && (
                    <div style={{ marginTop: '4px', color: 'var(--text-muted)' }}>
                      Recipients Queued: <strong>{dispatchResult.recipients_queued}</strong> &bull; Mode: <strong>{dispatchResult.sms_mode}</strong>
                    </div>
                  )}
                </div>
              )}

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                <div>
                  <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '6px' }}>
                    Target District *
                  </label>
                  <select
                    className="form-select"
                    value={selectedDistrictId}
                    onChange={(e) => {
                      setSelectedDistrictId(e.target.value);
                      setPreviewData(null);
                    }}
                  >
                    {districts.map((d) => (
                      <option key={d.id} value={d.id}>
                        {d.name} ({d.state_name})
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '6px' }}>
                    Risk Severity Level *
                  </label>
                  <select
                    className="form-select"
                    value={riskLevel}
                    onChange={(e) => {
                      setRiskLevel(e.target.value);
                      setPreviewData(null);
                    }}
                  >
                    <option value="VERY_HIGH">VERY HIGH (Red Warning)</option>
                    <option value="HIGH">HIGH (Orange Warning)</option>
                    <option value="MODERATE">MODERATE (Yellow Watch)</option>
                  </select>
                </div>
              </div>

              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <input
                  type="checkbox"
                  id="sendSmsCheck"
                  checked={sendSms}
                  onChange={(e) => setSendSms(e.target.checked)}
                />
                <label htmlFor="sendSmsCheck" style={{ fontSize: '0.85rem', cursor: 'pointer' }}>
                  Dispatch SMS to registered farmers in this district
                </label>
              </div>

              {/* Multilingual Template Preview */}
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <button
                  type="button"
                  className="btn btn-secondary"
                  onClick={handlePreview}
                  disabled={loadingPreview}
                >
                  <Eye size={16} /> {loadingPreview ? 'Generating Preview...' : 'Preview DLT Message Templates'}
                </button>
              </div>

              {previewData && (
                <div className="glass-card" style={{ padding: '16px', display: 'flex', flexDirection: 'column', gap: '12px' }}>
                  <div style={{ fontSize: '0.85rem', fontWeight: 700, color: '#38bdf8' }}>
                    Targeting {previewData.affected_farmers_count} registered farmer(s) across {Object.keys(previewData.language_breakdown).length} language(s)
                  </div>
                  
                  {Object.entries(previewData.templates_preview).map(([lang, text]: any) => (
                    <div key={lang} style={{ background: 'rgba(0,0,0,0.3)', padding: '10px 14px', borderRadius: '8px', border: '1px solid var(--border-subtle)' }}>
                      <div style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-muted)', marginBottom: '4px' }}>
                        {lang} ({previewData.language_breakdown[lang] || 0} farmers):
                      </div>
                      <div style={{ fontSize: '0.85rem', fontFamily: 'var(--font-mono)', lineHeight: '1.4' }}>
                        {text}
                      </div>
                    </div>
                  ))}
                </div>
              )}

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px', marginTop: '8px' }}>
                <button
                  type="button"
                  className="btn btn-secondary"
                  onClick={() => setShowDispatchModal(false)}
                >
                  Close
                </button>
                <button
                  type="button"
                  className="btn btn-primary"
                  onClick={handleDispatch}
                  disabled={dispatching}
                >
                  <Send size={16} /> {dispatching ? 'Broadcasting...' : 'Execute Alert Broadcast'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
