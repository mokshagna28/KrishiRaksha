import React, { useState } from 'react';
import { MessageSquare, Send, CheckCircle2, XCircle, AlertTriangle, ShieldCheck, Terminal, Smartphone } from 'lucide-react';
import { sendTestSms } from '../api';

interface SmsHubTabProps {
  smsLogs: any[];
  smsConfig: any;
  onSmsSent: () => void;
}

export const SmsHubTab: React.FC<SmsHubTabProps> = ({
  smsLogs,
  smsConfig,
  onSmsSent,
}) => {
  const [mobileNumber, setMobileNumber] = useState('');
  const [language, setLanguage] = useState('Telugu');
  const [districtName, setDistrictName] = useState('Guntur');
  const [stateName, setStateName] = useState('Andhra Pradesh');
  const [sending, setSending] = useState(false);
  const [testResult, setTestResult] = useState<any | null>(null);

  const handleSendTest = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!/^\d{10}$/.test(mobileNumber.trim())) {
      alert('Please enter a valid 10-digit Indian mobile number');
      return;
    }

    try {
      setSending(true);
      const res = await sendTestSms({
        mobile_number: mobileNumber.trim(),
        language,
        district_name: districtName,
        state_name: stateName,
        period: 'Next 24-48 Hours',
      });
      setTestResult(res);
      onSmsSent();
    } catch (e: any) {
      alert('Test SMS Error: ' + e.message);
    } finally {
      setSending(false);
    }
  };

  const isLive = smsConfig?.sms_mode === 'live';

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      {/* Gateway & DLT Status Card */}
      <div className="glass-card" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: '16px' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
            <MessageSquare size={18} color="#0284c7" />
            <span style={{ fontWeight: 700, fontSize: '0.9rem' }}>SMS Gateway Integration</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span className={`badge ${isLive ? 'badge-green' : 'badge-yellow'}`}>
              {isLive ? 'LIVE MSG91 GATEWAY' : 'DEMO / TEST SIMULATOR'}
            </span>
            <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
              Provider: {smsConfig?.provider || 'MSG91'}
            </span>
          </div>
          <p style={{ fontSize: '0.75rem', color: 'var(--text-dim)', marginTop: '6px' }}>
            {smsConfig?.status_message || 'Simulating DLT delivery pipeline with full schema validation.'}
          </p>
        </div>

        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
            <ShieldCheck size={18} color="#10b981" />
            <span style={{ fontWeight: 700, fontSize: '0.9rem' }}>TRAI / DLT Compliance</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span className={`badge ${smsConfig?.dlt_registered ? 'badge-green' : 'badge-neutral'}`}>
              {smsConfig?.dlt_registered ? 'DLT REGISTERED' : 'DLT TEMPLATES PREPARED'}
            </span>
            <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
              Sender: {smsConfig?.sender_id || 'KRISHI'}
            </span>
          </div>
          <p style={{ fontSize: '0.75rem', color: 'var(--text-dim)', marginTop: '6px' }}>
            Templates registered across 11 Indian languages with static & variable headers.
          </p>
        </div>
      </div>

      {/* Interactive SMS Testing Tool */}
      <div className="glass-card">
        <h3 style={{ fontSize: '1rem', fontWeight: 700, marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Smartphone size={18} color="#38bdf8" />
          Live SMS Delivery Verification & Test Terminal
        </h3>

        <form onSubmit={handleSendTest} style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '12px' }}>
            <div>
              <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '4px' }}>
                Test Mobile Number (10 Digits) *
              </label>
              <input
                type="tel"
                required
                className="form-input"
                placeholder="e.g. 9876543210"
                value={mobileNumber}
                onChange={(e) => setMobileNumber(e.target.value.replace(/\D/g, '').slice(0, 10))}
              />
            </div>

            <div>
              <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '4px' }}>
                Preferred Language *
              </label>
              <select
                className="form-select"
                value={language}
                onChange={(e) => setLanguage(e.target.value)}
              >
                <option value="Telugu">Telugu (తెలుగు)</option>
                <option value="Hindi">Hindi (हिन्दी)</option>
                <option value="Tamil">Tamil (தமிழ்)</option>
                <option value="Kannada">Kannada (ಕನ್ನಡ)</option>
                <option value="Malayalam">Malayalam (മലയാളം)</option>
                <option value="Marathi">Marathi (मराठी)</option>
                <option value="Bengali">Bengali (বাংলা)</option>
                <option value="Odia">Odia (ଓଡ଼ିଆ)</option>
                <option value="Gujarati">Gujarati (ગુજરાતી)</option>
                <option value="Punjabi">Punjabi (ਪੰਜਾਬੀ)</option>
                <option value="English">English</option>
              </select>
            </div>

            <div>
              <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '4px' }}>
                District Name
              </label>
              <input
                type="text"
                className="form-input"
                value={districtName}
                onChange={(e) => setDistrictName(e.target.value)}
              />
            </div>

            <div>
              <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '4px' }}>
                State Name
              </label>
              <input
                type="text"
                className="form-input"
                value={stateName}
                onChange={(e) => setStateName(e.target.value)}
              />
            </div>
          </div>

          <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '6px' }}>
            <button type="submit" className="btn btn-primary" disabled={sending}>
              <Send size={16} /> {sending ? 'Transmitting...' : 'Dispatch Test SMS'}
            </button>
          </div>
        </form>

        {testResult && (
          <div style={{ marginTop: '16px', padding: '16px', background: 'rgba(0,0,0,0.4)', borderRadius: '8px', border: '1px solid var(--border-subtle)' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
              <Terminal size={16} color="#38bdf8" />
              <span style={{ fontWeight: 700, fontSize: '0.85rem' }}>Transmission Response:</span>
              <span className={`badge ${testResult.status === 'DELIVERED' || testResult.status === 'SUBMITTED' ? 'badge-green' : 'badge-yellow'}`}>
                {testResult.status} ({testResult.sms_mode.toUpperCase()})
              </span>
            </div>

            <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginBottom: '8px' }}>
              {testResult.message}
            </div>

            {testResult.rendered_text && (
              <div style={{ background: 'rgba(255,255,255,0.03)', padding: '10px 14px', borderRadius: '6px', fontFamily: 'var(--font-mono)', fontSize: '0.85rem', color: '#f8fafc', lineHeight: '1.4' }}>
                {testResult.rendered_text}
              </div>
            )}
          </div>
        )}
      </div>

      {/* Real-time SMS Dispatch Audit Trail */}
      <div className="glass-card" style={{ padding: 0, overflow: 'hidden' }}>
        <div style={{ padding: '16px 20px', borderBottom: '1px solid var(--border-subtle)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <h3 style={{ fontSize: '0.95rem', fontWeight: 700 }}>
            SMS Dispatch Audit Trail ({smsLogs.length} Messages)
          </h3>
          <span style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>
            Full traceability with masked phone numbers
          </span>
        </div>

        <div style={{ overflowX: 'auto' }}>
          <table className="custom-table">
            <thead>
              <tr>
                <th>Submitted Time</th>
                <th>Recipient</th>
                <th>Language</th>
                <th>DLT Template</th>
                <th>Provider MSG ID</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {smsLogs.length === 0 ? (
                <tr>
                  <td colSpan={6} style={{ textAlign: 'center', padding: '36px', color: 'var(--text-muted)' }}>
                    No SMS messages dispatched yet. Trigger an alert or send a test SMS to view logs.
                  </td>
                </tr>
              ) : (
                smsLogs.map((m) => (
                  <tr key={m.id}>
                    <td>
                      <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                        {new Date(m.submitted_at).toLocaleString()}
                      </div>
                    </td>
                    <td>
                      <div style={{ fontWeight: 600 }}>{m.farmer_name}</div>
                      <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)', fontFamily: 'var(--font-mono)' }}>
                        {m.mobile_masked}
                      </div>
                    </td>
                    <td>
                      <span className="badge badge-neutral">{m.language}</span>
                    </td>
                    <td>
                      <span style={{ fontSize: '0.8rem', fontFamily: 'var(--font-mono)', color: 'var(--text-muted)' }}>
                        {m.template_id || 'DLT_DEFAULT'}
                      </span>
                    </td>
                    <td>
                      <span style={{ fontSize: '0.75rem', fontFamily: 'var(--font-mono)', color: 'var(--text-dim)' }}>
                        {m.provider_message_id || 'PENDING'}
                      </span>
                    </td>
                    <td>
                      <span className={`badge ${
                        m.status === 'DELIVERED' ? 'badge-green' :
                        m.status === 'SUBMITTED' ? 'badge-yellow' : 'badge-red'
                      }`}>
                        {m.status}
                      </span>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
