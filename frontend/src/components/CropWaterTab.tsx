import React, { useState, useEffect } from 'react';
import { predictCropWater, fetchCropWaterModelStatus, fetchCropWaterFeatureImportance } from '../api';
import {
  Droplets, Leaf, Thermometer, Wind, CloudRain, Activity, AlertTriangle,
  CheckCircle2, BarChart3, Brain, Sprout, FlaskConical, ShieldAlert,
  Sparkles, Stethoscope, Pill, RefreshCw, ChevronRight, Info
} from 'lucide-react';

const CROPS = ['Rice', 'Cotton', 'Maize', 'Wheat', 'Sugarcane', 'Pulses', 'Tomato'];
const STAGES = ['Sowing', 'Vegetative', 'Flowering', 'Harvesting'];
const SOILS = ['Clay', 'Loam', 'Sandy', 'Black Cotton Soil'];

interface PredictionResult {
  water_requirement_mm: number;
  water_status: string;
  crop_stress_level: string;
  crop_disease_stress: string;
  recommended_treatment: string;
  treatment_details: {
    treatment_name: string;
    category: string;
    active_ingredient: string;
    application_info: string;
    target_condition: string;
  };
  expected_recovery: string;
  confidence: number;
  reason: string;
  advisory: { severity: string; messages: string[]; water_surplus_deficit_mm: number };
  input_features: Record<string, any>;
  model_info: {
    regressor: string;
    classifier: string;
    disease_classifier: string;
    treatment_classifier: string;
    recovery_classifier: string;
  };
}

const statusColorMap: Record<string, { bg: string; border: string; text: string; glow: string }> = {
  'EXCESS WATER / WATERLOGGING RISK': { bg: 'rgba(239, 68, 68, 0.15)', border: 'rgba(239, 68, 68, 0.5)', text: '#f87171', glow: '0 0 24px rgba(239,68,68,0.35)' },
  'HIGH WATER': { bg: 'rgba(249, 115, 22, 0.15)', border: 'rgba(249, 115, 22, 0.5)', text: '#fb923c', glow: '0 0 20px rgba(249,115,22,0.3)' },
  'LOW WATER / WATER STRESS': { bg: 'rgba(245, 158, 11, 0.15)', border: 'rgba(245, 158, 11, 0.5)', text: '#fbbf24', glow: '0 0 20px rgba(245,158,11,0.3)' },
  'OPTIMAL WATER': { bg: 'rgba(16, 185, 129, 0.15)', border: 'rgba(16, 185, 129, 0.5)', text: '#34d399', glow: '0 0 20px rgba(16,185,129,0.3)' },
};

function getStatusColors(status: string) {
  return statusColorMap[status] || { bg: 'rgba(148, 163, 184, 0.15)', border: 'rgba(148, 163, 184, 0.3)', text: '#94a3b8', glow: 'none' };
}

function RecoveryBadge({ recovery }: { recovery: string }) {
  let colorClass = 'badge-green';
  if (recovery.includes('Substantial')) colorClass = 'badge-blue';
  if (recovery.includes('Partial')) colorClass = 'badge-yellow';
  if (recovery.includes('Low')) colorClass = 'badge-red';
  return <span className={`badge ${colorClass}`} style={{ fontSize: '0.85rem', padding: '6px 12px' }}>{recovery}</span>;
}

function StressBadge({ level }: { level: string }) {
  const colors: Record<string, string> = {
    LOW: 'badge-green', MODERATE: 'badge-yellow', HIGH: 'badge-orange', SEVERE: 'badge-red'
  };
  return <span className={`badge ${colors[level] || 'badge-neutral'}`} style={{ fontWeight: 700 }}>{level}</span>;
}

// Simple feature importance bar
function FeatureBar({ label, value, max }: { label: string; value: number; max: number }) {
  const pct = Math.min((value / max) * 100, 100);
  return (
    <div style={{ marginBottom: 10 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.78rem', marginBottom: 4 }}>
        <span style={{ color: 'var(--text-muted)', textTransform: 'capitalize' }}>{label.replace(/_/g, ' ')}</span>
        <span style={{ color: 'var(--text-main)', fontWeight: 600 }}>{(value * 100).toFixed(1)}%</span>
      </div>
      <div style={{ height: 6, borderRadius: 3, background: 'rgba(255,255,255,0.06)' }}>
        <div style={{
          width: `${pct}%`, height: '100%', borderRadius: 3,
          background: 'linear-gradient(90deg, #38bdf8, #818cf8)',
          transition: 'width 0.8s cubic-bezier(0.4, 0, 0.2, 1)',
        }} />
      </div>
    </div>
  );
}

// Confidence gauge
function ConfidenceGauge({ value }: { value: number }) {
  const circumference = 2 * Math.PI * 36;
  const progress = (value / 100) * circumference;
  const color = value >= 90 ? '#10b981' : value >= 70 ? '#f59e0b' : '#ef4444';
  return (
    <div style={{ position: 'relative', width: 90, height: 90, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
      <svg width={90} height={90} style={{ transform: 'rotate(-90deg)' }}>
        <circle cx={45} cy={45} r={36} fill="none" stroke="rgba(255,255,255,0.06)" strokeWidth={6} />
        <circle cx={45} cy={45} r={36} fill="none" stroke={color} strokeWidth={6}
          strokeDasharray={circumference} strokeDashoffset={circumference - progress}
          strokeLinecap="round" style={{ transition: 'stroke-dashoffset 1s ease' }} />
      </svg>
      <div style={{ position: 'absolute', textAlign: 'center' }}>
        <div style={{ fontSize: '1.2rem', fontWeight: 800, color }}>{value.toFixed(0)}%</div>
        <div style={{ fontSize: '0.55rem', color: 'var(--text-dim)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Confidence</div>
      </div>
    </div>
  );
}

export function CropWaterTab() {
  const [modelStatus, setModelStatus] = useState<any>(null);
  const [featureImportance, setFeatureImportance] = useState<Record<string, number>>({});
  const [prediction, setPrediction] = useState<PredictionResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeSubTab, setActiveSubTab] = useState<'advisor' | 'benchmarks'>('advisor');
  const [history, setHistory] = useState<PredictionResult[]>([]);

  // Inputs state
  const [crop, setCrop] = useState('Rice');
  const [stage, setStage] = useState('Flowering');
  const [soil, setSoil] = useState('Clay');
  const [soilMoisture, setSoilMoisture] = useState(85);
  const [recentRainfall, setRecentRainfall] = useState(150);
  const [forecastRainfall, setForecastRainfall] = useState(80);
  const [temperature, setTemperature] = useState(28);
  const [humidity, setHumidity] = useState(92);
  const [windSpeed, setWindSpeed] = useState(12);

  useEffect(() => {
    fetchCropWaterModelStatus().then(setModelStatus).catch(() => {});
    fetchCropWaterFeatureImportance().then(d => setFeatureImportance(d.feature_importance || {})).catch(() => {});
  }, []);

  const handlePredict = async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await predictCropWater({
        crop, growth_stage: stage, soil_type: soil,
        soil_moisture: soilMoisture, recent_rainfall: recentRainfall,
        forecast_rainfall: forecastRainfall, temperature, humidity, wind_speed: windSpeed,
      });
      setPrediction(result);
      setHistory(prev => [result, ...prev].slice(0, 10));
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  const inputStyle: React.CSSProperties = {
    width: '100%', padding: '10px 14px', borderRadius: 8,
    background: 'rgba(15, 23, 42, 0.8)', border: '1px solid var(--border-subtle)',
    color: 'var(--text-main)', fontSize: '0.875rem', fontFamily: 'var(--font-main)',
    outline: 'none', transition: 'border-color 0.2s',
  };

  const labelStyle: React.CSSProperties = {
    fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-muted)',
    textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: 6, display: 'flex', alignItems: 'center', gap: 6,
  };

  const sectionTitle: React.CSSProperties = {
    fontSize: '1rem', fontWeight: 700, marginBottom: 16,
    display: 'flex', alignItems: 'center', gap: 8,
    background: 'linear-gradient(135deg, #38bdf8, #818cf8)',
    WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent',
  };

  return (
    <div>
      {/* Module Banner */}
      <div style={{
        display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 20,
        padding: '20px 24px', borderRadius: 16,
        background: 'linear-gradient(135deg, rgba(16, 185, 129, 0.1), rgba(56, 189, 248, 0.1), rgba(129, 140, 248, 0.1))',
        border: '1px solid rgba(16, 185, 129, 0.25)',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
          <div style={{
            width: 52, height: 52, borderRadius: 14,
            background: 'linear-gradient(135deg, #10b981, #059669)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            boxShadow: '0 8px 24px rgba(16, 185, 129, 0.3)',
          }}>
            <Stethoscope size={26} color="#fff" />
          </div>
          <div>
            <h2 style={{ fontSize: '1.35rem', fontWeight: 800, margin: 0, letterSpacing: '-0.01em' }}>
              Crop Health & Recovery Advisor
            </h2>
            <p style={{ fontSize: '0.82rem', color: 'var(--text-muted)', margin: '2px 0 0' }}>
              ML Pipeline: Water Need → Status → Stress/Disease → Treatment/Pesticide → Recovery Outlook
            </p>
          </div>
        </div>

        {/* Sub-tab Switcher */}
        <div style={{ display: 'flex', gap: 8, background: 'rgba(15, 23, 42, 0.6)', padding: 4, borderRadius: 10, border: '1px solid var(--border-subtle)' }}>
          <button
            onClick={() => setActiveSubTab('advisor')}
            className={`btn ${activeSubTab === 'advisor' ? 'btn-emerald' : ''}`}
            style={{ padding: '8px 16px', fontSize: '0.82rem', borderRadius: 8 }}
          >
            <Brain size={14} /> Health Advisor
          </button>
          <button
            onClick={() => setActiveSubTab('benchmarks')}
            className={`btn ${activeSubTab === 'benchmarks' ? 'btn-emerald' : ''}`}
            style={{ padding: '8px 16px', fontSize: '0.82rem', borderRadius: 8 }}
          >
            <BarChart3 size={14} /> ML Model Benchmarks
          </button>
        </div>
      </div>

      {activeSubTab === 'advisor' ? (
        <div style={{ display: 'grid', gridTemplateColumns: '380px 1fr', gap: 20 }}>
          {/* ──── LEFT: Inputs Form Panel ──── */}
          <div>
            <div className="glass-card" style={{ position: 'sticky', top: 20 }}>
              <h3 style={sectionTitle}><FlaskConical size={18} /> Crop & Environmental Inputs</h3>

              {/* Crop & Stage */}
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12, marginBottom: 14 }}>
                <div>
                  <label style={labelStyle}><Sprout size={13} /> Crop</label>
                  <select value={crop} onChange={e => setCrop(e.target.value)} style={inputStyle}>
                    {CROPS.map(c => <option key={c} value={c}>{c}</option>)}
                  </select>
                </div>
                <div>
                  <label style={labelStyle}><Leaf size={13} /> Growth Stage</label>
                  <select value={stage} onChange={e => setStage(e.target.value)} style={inputStyle}>
                    {STAGES.map(s => <option key={s} value={s}>{s}</option>)}
                  </select>
                </div>
              </div>

              {/* Soil Type */}
              <div style={{ marginBottom: 14 }}>
                <label style={labelStyle}>Soil Type</label>
                <select value={soil} onChange={e => setSoil(e.target.value)} style={inputStyle}>
                  {SOILS.map(s => <option key={s} value={s}>{s}</option>)}
                </select>
              </div>

              {/* Sliders */}
              {[
                { label: 'Soil Moisture (%)', icon: <Droplets size={13} />, value: soilMoisture, set: setSoilMoisture, min: 10, max: 100, step: 1 },
                { label: 'Recent Rainfall (mm)', icon: <CloudRain size={13} />, value: recentRainfall, set: setRecentRainfall, min: 0, max: 300, step: 1 },
                { label: 'Forecast Rainfall (mm)', icon: <CloudRain size={13} />, value: forecastRainfall, set: setForecastRainfall, min: 0, max: 300, step: 1 },
                { label: 'Temperature (°C)', icon: <Thermometer size={13} />, value: temperature, set: setTemperature, min: 10, max: 50, step: 0.5 },
                { label: 'Humidity (%)', icon: <Droplets size={13} />, value: humidity, set: setHumidity, min: 20, max: 100, step: 1 },
                { label: 'Wind Speed (km/h)', icon: <Wind size={13} />, value: windSpeed, set: setWindSpeed, min: 0, max: 60, step: 0.5 },
              ].map(({ label, icon, value, set, min, max, step }) => (
                <div key={label} style={{ marginBottom: 12 }}>
                  <label style={labelStyle}>{icon} {label}</label>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                    <input type="range" min={min} max={max} step={step} value={value}
                      onChange={e => set(Number(e.target.value))}
                      style={{ flex: 1, accentColor: '#38bdf8' }} />
                    <input type="number" min={min} max={max} step={step} value={value}
                      onChange={e => set(Number(e.target.value))}
                      style={{ ...inputStyle, width: 70, textAlign: 'center', padding: '6px 8px' }} />
                  </div>
                </div>
              ))}

              {/* Predict Button */}
              <button className="btn btn-emerald" onClick={handlePredict} disabled={loading}
                style={{ width: '100%', padding: '12px', marginTop: 10, fontSize: '0.95rem' }}>
                {loading ? (
                  <span style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                    <span style={{ width: 16, height: 16, border: '2px solid #fff', borderTop: '2px solid transparent', borderRadius: '50%', animation: 'spin 0.8s linear infinite' }} />
                    Predicting Pipeline...
                  </span>
                ) : (
                  <><Brain size={18} /> Execute ML Health Pipeline</>
                )}
              </button>
              <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>

              {error && (
                <div style={{ marginTop: 12, padding: 12, borderRadius: 8, background: 'rgba(239,68,68,0.15)', border: '1px solid rgba(239,68,68,0.3)', color: '#f87171', fontSize: '0.82rem' }}>
                  ⚠️ {error}
                </div>
              )}
            </div>
          </div>

          {/* ──── RIGHT: Advisor Output Panel ──── */}
          <div>
            {!prediction && !loading && (
              <div className="glass-card" style={{ textAlign: 'center', padding: '60px 40px' }}>
                <Stethoscope size={48} color="var(--text-dim)" style={{ marginBottom: 16, opacity: 0.4 }} />
                <h3 style={{ color: 'var(--text-muted)', fontWeight: 600, marginBottom: 8 }}>
                  Ready to Run Crop Health & Recovery Advisor
                </h3>
                <p style={{ color: 'var(--text-dim)', fontSize: '0.85rem', maxWidth: 450, margin: '0 auto 20px' }}>
                  Click <strong>Execute ML Health Pipeline</strong> to run real-time inference connecting water needs, excess-water disease detection, agrochemical treatment prediction, and post-treatment recovery.
                </p>
                <button className="btn btn-emerald" onClick={handlePredict}>
                  <Brain size={16} /> Run Initial Rice Sample
                </button>
              </div>
            )}

            {prediction && (
              <>
                {/* ── 1. Top Summary Banner ── */}
                <div className="glass-card" style={{
                  marginBottom: 20, padding: 0, overflow: 'hidden',
                  border: `1px solid ${getStatusColors(prediction.water_status).border}`,
                  boxShadow: getStatusColors(prediction.water_status).glow,
                }}>
                  <div style={{
                    padding: '20px 24px',
                    background: getStatusColors(prediction.water_status).bg,
                    display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                  }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
                      <Droplets size={28} color={getStatusColors(prediction.water_status).text} />
                      <div>
                        <div style={{ fontSize: '0.72rem', color: 'var(--text-dim)', textTransform: 'uppercase', letterSpacing: '0.08em' }}>
                          Water Availability Status
                        </div>
                        <div style={{
                          fontSize: '1.25rem', fontWeight: 800,
                          color: getStatusColors(prediction.water_status).text,
                        }}>
                          {prediction.water_status}
                        </div>
                        <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: 2 }}>
                          {prediction.input_features.crop} ({prediction.input_features.growth_stage}) • {prediction.input_features.soil_type} Soil
                        </div>
                      </div>
                    </div>
                    <ConfidenceGauge value={prediction.confidence} />
                  </div>

                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', borderTop: '1px solid var(--border-subtle)' }}>
                    <div style={{ padding: '16px', textAlign: 'center', borderRight: '1px solid var(--border-subtle)' }}>
                      <div style={{ fontSize: '0.7rem', color: 'var(--text-dim)', textTransform: 'uppercase' }}>Water Requirement</div>
                      <div style={{ fontSize: '1.2rem', fontWeight: 800, color: '#38bdf8', marginTop: 4 }}>
                        {prediction.water_requirement_mm} mm
                      </div>
                    </div>
                    <div style={{ padding: '16px', textAlign: 'center', borderRight: '1px solid var(--border-subtle)' }}>
                      <div style={{ fontSize: '0.7rem', color: 'var(--text-dim)', textTransform: 'uppercase' }}>Crop Stress Level</div>
                      <div style={{ marginTop: 4 }}><StressBadge level={prediction.crop_stress_level} /></div>
                    </div>
                    <div style={{ padding: '16px', textAlign: 'center', borderRight: '1px solid var(--border-subtle)' }}>
                      <div style={{ fontSize: '0.7rem', color: 'var(--text-dim)', textTransform: 'uppercase' }}>Expected Recovery</div>
                      <div style={{ marginTop: 4 }}><RecoveryBadge recovery={prediction.expected_recovery} /></div>
                    </div>
                    <div style={{ padding: '16px', textAlign: 'center' }}>
                      <div style={{ fontSize: '0.7rem', color: 'var(--text-dim)', textTransform: 'uppercase' }}>Surplus / Deficit</div>
                      <div style={{ fontSize: '1.1rem', fontWeight: 700, color: 'var(--text-main)', marginTop: 4 }}>
                        {prediction.advisory.water_surplus_deficit_mm > 0 ? '+' : ''}{prediction.advisory.water_surplus_deficit_mm} mm
                      </div>
                    </div>
                  </div>
                </div>

                {/* ── 2. Excess-Water Effect & Disease Identification ── */}
                <div className="glass-card" style={{ marginBottom: 20 }}>
                  <h3 style={sectionTitle}><Stethoscope size={18} /> Excess-Water Stress & Disease Identification</h3>
                  <div style={{
                    padding: '16px 20px', borderRadius: 12,
                    background: 'rgba(15, 23, 42, 0.6)', border: '1px solid var(--border-subtle)',
                    display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 14,
                  }}>
                    <div>
                      <div style={{ fontSize: '0.72rem', color: 'var(--text-dim)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                        ML Predicted Crop Condition / Disease
                      </div>
                      <div style={{ fontSize: '1.15rem', fontWeight: 800, color: '#f87171', marginTop: 2 }}>
                        {prediction.crop_disease_stress}
                      </div>
                    </div>
                    <span className="badge badge-red" style={{ fontSize: '0.8rem' }}>
                      {prediction.crop_stress_level} STRESS
                    </span>
                  </div>

                  <div style={{ fontSize: '0.83rem', color: 'var(--text-muted)', lineHeight: 1.6 }}>
                    <strong style={{ color: 'var(--text-main)' }}>ML Model Rationale: </strong>
                    {prediction.reason}
                  </div>
                </div>

                {/* ── 3. Recommended Treatment & Pesticide Prediction ── */}
                <div className="glass-card" style={{ marginBottom: 20, border: '1px solid rgba(16, 185, 129, 0.3)' }}>
                  <h3 style={sectionTitle}><Pill size={18} /> ML Predicted Treatment & Pesticide Recommendation</h3>
                  
                  <div style={{
                    padding: '18px 20px', borderRadius: 12, marginBottom: 16,
                    background: 'linear-gradient(135deg, rgba(16, 185, 129, 0.12), rgba(56, 189, 248, 0.12))',
                    border: '1px solid rgba(16, 185, 129, 0.3)',
                  }}>
                    <div style={{ fontSize: '0.72rem', color: '#34d399', textTransform: 'uppercase', letterSpacing: '0.06em', fontWeight: 700 }}>
                      Recommended Agrochemical / Agronomic Treatment
                    </div>
                    <div style={{ fontSize: '1.2rem', fontWeight: 800, color: 'var(--text-main)', marginTop: 4 }}>
                      {prediction.recommended_treatment}
                    </div>
                  </div>

                  {/* Treatment details grid */}
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 14 }}>
                    <div style={{ padding: '12px 16px', borderRadius: 8, background: 'rgba(15, 23, 42, 0.6)', border: '1px solid var(--border-subtle)' }}>
                      <div style={{ fontSize: '0.7rem', color: 'var(--text-dim)', textTransform: 'uppercase' }}>Treatment Category</div>
                      <div style={{ fontSize: '0.9rem', fontWeight: 600, color: '#38bdf8', marginTop: 2 }}>
                        {prediction.treatment_details.category}
                      </div>
                    </div>

                    <div style={{ padding: '12px 16px', borderRadius: 8, background: 'rgba(15, 23, 42, 0.6)', border: '1px solid var(--border-subtle)' }}>
                      <div style={{ fontSize: '0.7rem', color: 'var(--text-dim)', textTransform: 'uppercase' }}>Active Ingredient</div>
                      <div style={{ fontSize: '0.9rem', fontWeight: 600, color: '#a78bfa', marginTop: 2 }}>
                        {prediction.treatment_details.active_ingredient}
                      </div>
                    </div>

                    <div style={{ gridColumn: 'span 2', padding: '12px 16px', borderRadius: 8, background: 'rgba(15, 23, 42, 0.6)', border: '1px solid var(--border-subtle)' }}>
                      <div style={{ fontSize: '0.7rem', color: 'var(--text-dim)', textTransform: 'uppercase' }}>Recommended Application Protocol</div>
                      <div style={{ fontSize: '0.85rem', color: 'var(--text-main)', marginTop: 4, lineHeight: 1.5 }}>
                        {prediction.treatment_details.application_info}
                      </div>
                    </div>
                  </div>
                </div>

                {/* ── 4. Expected Recovery Condition ── */}
                <div className="glass-card" style={{ marginBottom: 20 }}>
                  <h3 style={sectionTitle}><CheckCircle2 size={18} /> Expected Post-Treatment Recovery Outcome</h3>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '16px 20px', borderRadius: 12, background: 'rgba(15, 23, 42, 0.6)', border: '1px solid var(--border-subtle)' }}>
                    <div>
                      <div style={{ fontSize: '0.72rem', color: 'var(--text-dim)', textTransform: 'uppercase' }}>Predicted Condition Outlook</div>
                      <div style={{ marginTop: 4 }}><RecoveryBadge recovery={prediction.expected_recovery} /></div>
                    </div>
                    <div style={{ textAlign: 'right' }}>
                      <div style={{ fontSize: '0.72rem', color: 'var(--text-dim)', textTransform: 'uppercase' }}>Recovery Model</div>
                      <div style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-muted)' }}>
                        {prediction.model_info.recovery_classifier}
                      </div>
                    </div>
                  </div>
                </div>

                {/* ── 5. Agricultural Advisory Messages ── */}
                <div className="glass-card" style={{ marginBottom: 20 }}>
                  <h3 style={sectionTitle}><ShieldAlert size={18} /> Contextual Agricultural Advisories</h3>
                  <ul style={{ listStyle: 'none', padding: 0, margin: 0 }}>
                    {prediction.advisory.messages.map((msg, i) => (
                      <li key={i} style={{
                        padding: '10px 14px', borderRadius: 8, marginBottom: 8,
                        background: 'rgba(15, 23, 42, 0.6)', border: '1px solid var(--border-subtle)',
                        fontSize: '0.85rem', color: 'var(--text-main)', display: 'flex', alignItems: 'center', gap: 10
                      }}>
                        <ChevronRight size={14} color="#38bdf8" />
                        {msg}
                      </li>
                    ))}
                  </ul>
                </div>

                {/* Scientific Disclaimer */}
                <div style={{ padding: '14px 18px', borderRadius: 12, background: 'rgba(245, 158, 11, 0.08)', border: '1px solid rgba(245, 158, 11, 0.25)', fontSize: '0.78rem', color: '#fbbf24', display: 'flex', gap: 10, alignItems: 'center' }}>
                  <Info size={18} style={{ flexShrink: 0 }} />
                  <div>
                    <strong>Scientific & Regulatory Safety Notice:</strong> This ML prediction is an academic decision-support advisor trained on FAO-56 & ICAR empirical datasets. Agrochemical treatments should be applied strictly following local product label instructions and certified agricultural extension officer guidelines.
                  </div>
                </div>
              </>
            )}
          </div>
        </div>
      ) : (
        /* ──── BENCHMARKS SUB-TAB ──── */
        <div>
          {modelStatus?.ready ? (
            <div>
              {/* Overview Metrics Cards */}
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 16, marginBottom: 24 }}>
                <div className="glass-card" style={{ textAlign: 'center' }}>
                  <div style={{ fontSize: '0.72rem', color: 'var(--text-dim)', textTransform: 'uppercase' }}>Water Req Regressor</div>
                  <div style={{ fontSize: '1.4rem', fontWeight: 800, color: '#38bdf8', marginTop: 4 }}>
                    R² = {modelStatus.regression?.metrics?.r2_score}
                  </div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                    MAE: {modelStatus.regression?.metrics?.mae} mm
                  </div>
                </div>

                <div className="glass-card" style={{ textAlign: 'center' }}>
                  <div style={{ fontSize: '0.72rem', color: 'var(--text-dim)', textTransform: 'uppercase' }}>Water Status Classifier</div>
                  <div style={{ fontSize: '1.4rem', fontWeight: 800, color: '#34d399', marginTop: 4 }}>
                    F1 = {modelStatus.classification?.metrics?.f1_score}
                  </div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                    Accuracy: {(modelStatus.classification?.metrics?.accuracy * 100).toFixed(1)}%
                  </div>
                </div>

                <div className="glass-card" style={{ textAlign: 'center' }}>
                  <div style={{ fontSize: '0.72rem', color: 'var(--text-dim)', textTransform: 'uppercase' }}>Treatment Classifier</div>
                  <div style={{ fontSize: '1.4rem', fontWeight: 800, color: '#a78bfa', marginTop: 4 }}>
                    F1 = {modelStatus.treatment_classification?.metrics?.f1_score}
                  </div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                    Accuracy: {(modelStatus.treatment_classification?.metrics?.accuracy * 100).toFixed(1)}%
                  </div>
                </div>

                <div className="glass-card" style={{ textAlign: 'center' }}>
                  <div style={{ fontSize: '0.72rem', color: 'var(--text-dim)', textTransform: 'uppercase' }}>Recovery Classifier</div>
                  <div style={{ fontSize: '1.4rem', fontWeight: 800, color: '#f472b6', marginTop: 4 }}>
                    F1 = {modelStatus.recovery_classification?.metrics?.f1_score}
                  </div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                    Accuracy: {(modelStatus.recovery_classification?.metrics?.accuracy * 100).toFixed(1)}%
                  </div>
                </div>
              </div>

              {/* Task Benchmarks Tables */}
              {[
                { title: 'Task 1: Water Requirement Regression Benchmark (mm)', data: modelStatus.regression?.all_candidates, metricKey: 'r2_score', metricName: 'R² Score' },
                { title: 'Task 2: Water Status Classification Benchmark', data: modelStatus.classification?.all_candidates, metricKey: 'f1_score', metricName: 'F1 Score' },
                { title: 'Task 3: Excess-Water Disease / Stress Classification Benchmark', data: modelStatus.disease_classification?.all_candidates, metricKey: 'f1_score', metricName: 'F1 Score' },
                { title: 'Task 4: Recommended Treatment / Pesticide Classification Benchmark', data: modelStatus.treatment_classification?.all_candidates, metricKey: 'f1_score', metricName: 'F1 Score' },
                { title: 'Task 5: Post-Treatment Expected Recovery Classification Benchmark', data: modelStatus.recovery_classification?.all_candidates, metricKey: 'f1_score', metricName: 'F1 Score' },
              ].map((bench, idx) => (
                <div key={idx} className="glass-card" style={{ marginBottom: 20 }}>
                  <h4 style={sectionTitle}><BarChart3 size={16} /> {bench.title}</h4>
                  {bench.data ? (
                    <table className="custom-table">
                      <thead>
                        <tr>
                          <th>Algorithm</th>
                          <th>Accuracy / R²</th>
                          <th>Precision / MAE</th>
                          <th>Recall / RMSE</th>
                          <th>F1-Score / R²</th>
                        </tr>
                      </thead>
                      <tbody>
                        {Object.entries(bench.data).map(([name, m]: [string, any]) => (
                          <tr key={name}>
                            <td style={{ fontWeight: 600, color: 'var(--text-main)' }}>{name}</td>
                            <td>{m.accuracy !== undefined ? `${(m.accuracy * 100).toFixed(2)}%` : m.mae}</td>
                            <td>{m.precision !== undefined ? `${(m.precision * 100).toFixed(2)}%` : m.rmse}</td>
                            <td>{m.recall !== undefined ? `${(m.recall * 100).toFixed(2)}%` : m.r2_score}</td>
                            <td style={{ fontFamily: 'var(--font-mono)', fontWeight: 700, color: '#38bdf8' }}>
                              {m.f1_score !== undefined ? m.f1_score : m.r2_score}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  ) : (
                    <p style={{ color: 'var(--text-dim)' }}>Candidate benchmark data unavailable.</p>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <div className="glass-card" style={{ textAlign: 'center', padding: 40 }}>
              <p style={{ color: 'var(--text-dim)' }}>Loading model status and benchmark metrics...</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default CropWaterTab;
