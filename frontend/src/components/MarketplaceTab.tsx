import React, { useState, useEffect, useCallback } from 'react';
import {
  fetchMarketListings, createMarketListing, registerBuyer, listBuyers,
  createPurchaseRequest, fetchPurchaseRequests, updatePurchaseRequestStatus,
  fetchMarketPriceForecast, fetchMarketOverview, fetchMarketModelStatus,
  fetchMarketSupportedOptions
} from '../api';

const REC_COLORS: Record<string, string> = {
  WAIT: '#10b981', SELL_NOW: '#f59e0b', MONITOR: '#3b82f6', CAUTION: '#ef4444',
};
const STATUS_COLORS: Record<string, string> = {
  ACTIVE: '#10b981', SOLD: '#6366f1', EXPIRED: '#94a3b8', CANCELLED: '#ef4444',
  REQUESTED: '#f59e0b', ACCEPTED: '#10b981', REJECTED: '#ef4444',
  NEGOTIATING: '#3b82f6', CONFIRMED: '#6366f1', COMPLETED: '#22c55e',
};

function StatusBadge({ status }: { status: string }) {
  return (
    <span style={{
      display: 'inline-block', padding: '2px 10px', borderRadius: 20,
      fontSize: '0.72rem', fontWeight: 700,
      background: (STATUS_COLORS[status] || '#94a3b8') + '22',
      color: STATUS_COLORS[status] || '#94a3b8',
      border: `1px solid ${STATUS_COLORS[status] || '#94a3b8'}55`,
    }}>{status}</span>
  );
}

function SparkLine({ data }: { data: number[] }) {
  if (!data || data.length < 2) return null;
  const min = Math.min(...data), max = Math.max(...data);
  const range = max - min || 1;
  const W = 120, H = 36;
  const pts = data.map((v, i) => `${(i / (data.length - 1)) * W},${H - ((v - min) / range) * H}`).join(' ');
  const color = data[data.length - 1] - data[0] >= 0 ? '#10b981' : '#ef4444';
  return (
    <svg width={W} height={H} style={{ display: 'block' }}>
      <polyline points={pts} fill="none" stroke={color} strokeWidth={2} strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

export function MarketplaceTab() {
  const [tab, setTab] = useState<'overview' | 'listings' | 'buyers' | 'forecast' | 'model'>('overview');
  const [overviewData, setOverviewData] = useState<any>(null);
  const [overviewLoading, setOverviewLoading] = useState(false);
  const [listings, setListings] = useState<any[]>([]);
  const [listingsLoading, setListingsLoading] = useState(false);
  const [showNewListing, setShowNewListing] = useState(false);
  const [buyers, setBuyers] = useState<any[]>([]);
  const [purchaseRequests, setPurchaseRequests] = useState<any[]>([]);
  const [showBuyerForm, setShowBuyerForm] = useState(false);
  const [showPRForm, setShowPRForm] = useState<number | null>(null);
  const [forecast, setForecast] = useState<any>(null);
  const [forecastLoading, setForecastLoading] = useState(false);
  const [forecastCrop, setForecastCrop] = useState('Paddy');
  const [forecastMarket, setForecastMarket] = useState('Guntur');
  const [forecastState, setForecastState] = useState('Andhra Pradesh');
  const [supportedOptions, setSupportedOptions] = useState<{ crops: string[], markets: string[] }>({ crops: [], markets: [] });
  const [modelStatus, setModelStatus] = useState<any>(null);
  const [nlForm, setNlForm] = useState({
    farmer_id: '', crop: 'Paddy', variety: '', quantity: '', quantity_unit: 'quintal',
    quality: 'Grade A', state: '', district: '', village: '',
    expected_price: '', available_from: '', harvest_date: '', description: '',
  });
  const [buyerForm, setBuyerForm] = useState({ name: '', mobile_or_email: '', organization: '', state: '', district: '' });
  const [prForm, setPrForm] = useState({ buyer_id: '', requested_quantity: '', offered_price: '', message: '' });
  const [feedback, setFeedback] = useState<{ type: 'success' | 'error'; msg: string } | null>(null);

  const showMsg = (type: 'success' | 'error', msg: string) => {
    setFeedback({ type, msg });
    setTimeout(() => setFeedback(null), 4000);
  };

  const loadOverview = useCallback(async () => {
    setOverviewLoading(true);
    try {
      const [ov, opts, ms] = await Promise.all([
        fetchMarketOverview().catch(() => null),
        fetchMarketSupportedOptions().catch(() => ({ crops: [], markets: [] })),
        fetchMarketModelStatus().catch(() => null),
      ]);
      if (ov) setOverviewData(ov);
      if (opts) setSupportedOptions(opts);
      if (ms) setModelStatus(ms);
    } finally { setOverviewLoading(false); }
  }, []);

  const loadListings = useCallback(async () => {
    setListingsLoading(true);
    try { setListings((await fetchMarketListings()) || []); }
    finally { setListingsLoading(false); }
  }, []);

  const loadBuyers = useCallback(async () => {
    const [b, pr] = await Promise.all([listBuyers().catch(() => []), fetchPurchaseRequests().catch(() => [])]);
    setBuyers(b || []); setPurchaseRequests(pr || []);
  }, []);

  useEffect(() => { loadOverview(); }, []);
  useEffect(() => {
    if (tab === 'listings') loadListings();
    else if (tab === 'buyers') loadBuyers();
    else if (tab === 'model') fetchMarketModelStatus().catch(() => null).then(ms => { if (ms) setModelStatus(ms); });
  }, [tab]);

  const handleRunForecast = async () => {
    setForecastLoading(true);
    try {
      setForecast(await fetchMarketPriceForecast(forecastCrop, forecastMarket, forecastState));
    } catch (e: any) { showMsg('error', e.message || 'Forecast failed'); }
    finally { setForecastLoading(false); }
  };

  const handleCreateListing = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await createMarketListing({ ...nlForm, farmer_id: Number(nlForm.farmer_id), quantity: Number(nlForm.quantity), expected_price: Number(nlForm.expected_price) });
      showMsg('success', 'Crop listing created!'); setShowNewListing(false); loadListings();
    } catch (e: any) { showMsg('error', e.message); }
  };

  const handleRegisterBuyer = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await registerBuyer(buyerForm); showMsg('success', 'Buyer registered!'); setShowBuyerForm(false); loadBuyers();
    } catch (e: any) { showMsg('error', e.message); }
  };

  const handleCreatePR = async (listing_id: number, e: React.FormEvent) => {
    e.preventDefault();
    try {
      await createPurchaseRequest({ listing_id, ...prForm, buyer_id: Number(prForm.buyer_id), requested_quantity: Number(prForm.requested_quantity), offered_price: Number(prForm.offered_price) });
      showMsg('success', 'Purchase request submitted!'); setShowPRForm(null); loadListings();
    } catch (e: any) { showMsg('error', e.message); }
  };

  const handleUpdatePRStatus = async (req_id: number, status: string) => {
    try { await updatePurchaseRequestStatus(req_id, status); showMsg('success', `Request ${status}`); loadBuyers(); }
    catch (e: any) { showMsg('error', e.message); }
  };

  const cardStyle: React.CSSProperties = {
    background: 'rgba(30, 41, 59, 0.8)', border: '1px solid rgba(99,102,241,0.2)',
    borderRadius: 14, padding: 20, marginBottom: 16, boxShadow: '0 4px 24px rgba(0,0,0,0.2)',
  };
  const inputStyle: React.CSSProperties = {
    width: '100%', background: 'rgba(15,23,42,0.8)', border: '1px solid rgba(99,102,241,0.3)',
    borderRadius: 8, color: '#e2e8f0', padding: '10px 14px', fontSize: '0.88rem',
    outline: 'none', boxSizing: 'border-box',
  };
  const labelStyle: React.CSSProperties = { fontSize: '0.78rem', color: '#94a3b8', fontWeight: 600, marginBottom: 4, display: 'block' };
  const tabBtnStyle = (active: boolean): React.CSSProperties => ({
    padding: '9px 18px', borderRadius: '8px 8px 0 0', border: 'none', cursor: 'pointer',
    fontWeight: 600, fontSize: '0.83rem', transition: 'all 0.2s', whiteSpace: 'nowrap',
    background: active ? 'linear-gradient(135deg, #6366f1, #8b5cf6)' : 'rgba(30,41,59,0.6)',
    color: active ? '#fff' : '#94a3b8',
  });
  const btnPrimary: React.CSSProperties = {
    background: 'linear-gradient(135deg, #6366f1, #8b5cf6)', color: '#fff',
    border: 'none', borderRadius: 8, padding: '9px 20px', cursor: 'pointer', fontWeight: 600, fontSize: '0.85rem',
  };
  const btnSecondary: React.CSSProperties = {
    background: 'rgba(99,102,241,0.15)', color: '#a5b4fc', border: '1px solid rgba(99,102,241,0.3)',
    borderRadius: 8, padding: '8px 16px', cursor: 'pointer', fontWeight: 600, fontSize: '0.82rem',
  };
  const gridStyle: React.CSSProperties = { display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: 16 };

  return (
    <div>
      {/* Header */}
      <div style={{ marginBottom: 24, padding: '20px 24px', borderRadius: 14, background: 'linear-gradient(135deg, rgba(99,102,241,0.15), rgba(139,92,246,0.1))', border: '1px solid rgba(99,102,241,0.25)' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 12 }}>
          <div>
            <h2 style={{ margin: 0, fontSize: '1.5rem', fontWeight: 800, background: 'linear-gradient(135deg, #818cf8, #a78bfa)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
              🏪 Farmer-to-Buyer Marketplace
            </h2>
            <p style={{ margin: '4px 0 0', fontSize: '0.85rem', color: '#94a3b8' }}>Direct crop sales • ML price intelligence • Zero middlemen</p>
          </div>
          {modelStatus?.ready && (
            <span style={{ padding: '6px 14px', borderRadius: 20, fontSize: '0.78rem', fontWeight: 700, background: '#10b98122', color: '#10b981', border: '1px solid #10b98155' }}>
              ✓ ML Model Ready · R² = {modelStatus?.champion_metrics?.r2_score ?? '—'}
            </span>
          )}
        </div>
      </div>

      {feedback && (
        <div style={{ padding: '12px 18px', borderRadius: 10, marginBottom: 16, fontSize: '0.87rem', fontWeight: 600,
          background: feedback.type === 'success' ? '#10b98122' : '#ef444422',
          border: `1px solid ${feedback.type === 'success' ? '#10b98155' : '#ef444455'}`,
          color: feedback.type === 'success' ? '#10b981' : '#ef4444' }}>
          {feedback.type === 'success' ? '✅ ' : '❌ '}{feedback.msg}
        </div>
      )}

      {/* Sub-tabs */}
      <div style={{ display: 'flex', gap: 4, borderBottom: '1px solid rgba(99,102,241,0.2)', marginBottom: 24, overflowX: 'auto' }}>
        {(['overview', 'listings', 'buyers', 'forecast', 'model'] as const).map(t => (
          <button key={t} style={tabBtnStyle(tab === t)} onClick={() => setTab(t)}>
            {{ overview: '📊 Overview', listings: '📋 Listings', buyers: '🤝 Buyers', forecast: '🔮 Price Forecast', model: '🤖 ML Model' }[t]}
          </button>
        ))}
      </div>

      {/* OVERVIEW */}
      {tab === 'overview' && (
        <div>
          {overviewLoading && <p style={{ color: '#94a3b8' }}>Loading market overview…</p>}
          {overviewData && (
            <>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16, flexWrap: 'wrap', gap: 8 }}>
                <h3 style={{ margin: 0, color: '#e2e8f0' }}>Live Crop Price Intelligence</h3>
                <span style={{ fontSize: '0.72rem', color: '#64748b' }}>Source: {overviewData.data_source}</span>
              </div>
              <div style={gridStyle}>
                {(overviewData.market_overview || []).map((item: any, i: number) => (
                  <div key={i} style={{ ...cardStyle, padding: 18 }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                      <div>
                        <div style={{ fontWeight: 700, color: '#c7d2fe', fontSize: '1rem' }}>{item.crop}</div>
                        <div style={{ fontSize: '0.78rem', color: '#64748b' }}>{item.market}</div>
                      </div>
                      <span style={{
                        padding: '3px 10px', borderRadius: 20, fontSize: '0.7rem', fontWeight: 700,
                        background: item.trend_direction === 'UP' ? '#10b98122' : item.trend_direction === 'DOWN' ? '#ef444422' : '#6366f122',
                        color: item.trend_direction === 'UP' ? '#10b981' : item.trend_direction === 'DOWN' ? '#ef4444' : '#818cf8',
                      }}>
                        {item.trend_direction === 'UP' ? '↑' : item.trend_direction === 'DOWN' ? '↓' : '→'} {Math.abs(item.trend_7d_pct).toFixed(1)}%
                      </span>
                    </div>
                    <div style={{ marginTop: 10, fontSize: '1.5rem', fontWeight: 800, color: '#e2e8f0' }}>₹{item.latest_price.toLocaleString()}</div>
                    <div style={{ fontSize: '0.72rem', color: '#64748b', marginTop: 2 }}>{item.price_unit}</div>
                  </div>
                ))}
              </div>
              <div style={{ marginTop: 16, padding: '10px 16px', borderRadius: 8, background: 'rgba(99,102,241,0.08)', border: '1px solid rgba(99,102,241,0.15)', fontSize: '0.77rem', color: '#64748b' }}>
                ⚠️ Historical AGMARKNET/eNAM data. Go to <strong style={{ color: '#a5b4fc' }}>Price Forecast</strong> for ML predictions.
              </div>
            </>
          )}
        </div>
      )}

      {/* LISTINGS */}
      {tab === 'listings' && (
        <div>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
            <h3 style={{ margin: 0, color: '#e2e8f0' }}>Active Crop Listings ({listings.length})</h3>
            <button style={btnPrimary} onClick={() => setShowNewListing(!showNewListing)}>{showNewListing ? '✕ Cancel' : '+ New Listing'}</button>
          </div>
          {showNewListing && (
            <div style={{ ...cardStyle, marginBottom: 24, border: '1px solid rgba(99,102,241,0.5)' }}>
              <h4 style={{ margin: '0 0 16px', color: '#a5b4fc' }}>📝 Create New Crop Listing</h4>
              <form onSubmit={handleCreateListing}>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: 14 }}>
                  {[{ key: 'farmer_id', label: 'Farmer ID', type: 'number' }, { key: 'crop', label: 'Crop', type: 'text' }, { key: 'variety', label: 'Variety (optional)', type: 'text' }, { key: 'quantity', label: 'Quantity', type: 'number' }, { key: 'expected_price', label: 'Asking Price (₹/quintal)', type: 'number' }, { key: 'state', label: 'State', type: 'text' }, { key: 'district', label: 'District', type: 'text' }, { key: 'village', label: 'Village', type: 'text' }, { key: 'available_from', label: 'Available From', type: 'date' }, { key: 'harvest_date', label: 'Harvest Date', type: 'date' }].map(({ key, label, type }) => (
                    <div key={key}>
                      <label style={labelStyle}>{label}</label>
                      <input type={type} value={(nlForm as any)[key]} style={inputStyle} onChange={e => setNlForm(p => ({ ...p, [key]: e.target.value }))} />
                    </div>
                  ))}
                  <div>
                    <label style={labelStyle}>Quality Grade</label>
                    <select value={nlForm.quality} style={inputStyle} onChange={e => setNlForm(p => ({ ...p, quality: e.target.value }))}>
                      {['Grade A', 'Grade B', 'Organic', 'FAQ'].map(g => <option key={g}>{g}</option>)}
                    </select>
                  </div>
                  <div style={{ gridColumn: '1 / -1' }}>
                    <label style={labelStyle}>Description</label>
                    <textarea value={nlForm.description} style={{ ...inputStyle, height: 64, resize: 'vertical' }} onChange={e => setNlForm(p => ({ ...p, description: e.target.value }))} />
                  </div>
                </div>
                <div style={{ marginTop: 16, display: 'flex', gap: 10 }}>
                  <button type="submit" style={btnPrimary}>Submit Listing</button>
                  <button type="button" style={btnSecondary} onClick={() => setShowNewListing(false)}>Cancel</button>
                </div>
              </form>
            </div>
          )}
          {listingsLoading && <p style={{ color: '#94a3b8' }}>Loading listings…</p>}
          {!listingsLoading && listings.length === 0 && <div style={{ textAlign: 'center', color: '#64748b', padding: 40 }}>No active listings. Farmers can add listings above.</div>}
          <div style={gridStyle}>
            {listings.map(l => (
              <div key={l.id} style={cardStyle}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 10 }}>
                  <div style={{ fontWeight: 700, color: '#c7d2fe', fontSize: '1.05rem' }}>{l.crop}{l.variety ? ` (${l.variety})` : ''}</div>
                  <StatusBadge status={l.status} />
                </div>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 6, fontSize: '0.82rem', color: '#94a3b8', marginBottom: 12 }}>
                  <span>👨‍🌾 {l.farmer_name}</span><span>📍 {l.district}, {l.state}</span>
                  <span>⚖️ {l.quantity} {l.quantity_unit}</span><span>🏷️ {l.quality}</span>
                  <span style={{ color: '#10b981', fontWeight: 700, fontSize: '1rem' }}>₹{l.expected_price}/qntl</span>
                  <span>🤝 {l.purchase_requests_count} requests</span>
                </div>
                {showPRForm === l.id ? (
                  <form onSubmit={e => handleCreatePR(l.id, e)}>
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8, marginBottom: 8 }}>
                      {[{ k: 'buyer_id', l: 'Buyer ID', t: 'number' }, { k: 'requested_quantity', l: 'Qty (quintal)', t: 'number' }, { k: 'offered_price', l: 'Offer (₹/qntl)', t: 'number' }, { k: 'message', l: 'Message', t: 'text' }].map(({ k, l: lbl, t }) => (
                        <div key={k}><label style={labelStyle}>{lbl}</label><input type={t} value={(prForm as any)[k]} style={inputStyle} onChange={e => setPrForm(p => ({ ...p, [k]: e.target.value }))} /></div>
                      ))}
                    </div>
                    <div style={{ display: 'flex', gap: 8 }}>
                      <button type="submit" style={{ ...btnPrimary, padding: '7px 14px', fontSize: '0.8rem' }}>Submit</button>
                      <button type="button" style={{ ...btnSecondary, padding: '7px 14px', fontSize: '0.8rem' }} onClick={() => setShowPRForm(null)}>Cancel</button>
                    </div>
                  </form>
                ) : (
                  <button style={{ ...btnSecondary, width: '100%', marginTop: 8 }} onClick={() => setShowPRForm(l.id)}>🛒 Send Purchase Request</button>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* BUYERS */}
      {tab === 'buyers' && (
        <div>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 20, flexWrap: 'wrap', gap: 10 }}>
            <h3 style={{ margin: 0, color: '#e2e8f0' }}>Buyers & Purchase Requests</h3>
            <button style={btnPrimary} onClick={() => setShowBuyerForm(!showBuyerForm)}>{showBuyerForm ? '✕ Cancel' : '+ Register Buyer'}</button>
          </div>
          {showBuyerForm && (
            <div style={{ ...cardStyle, marginBottom: 24, border: '1px solid rgba(99,102,241,0.5)' }}>
              <h4 style={{ margin: '0 0 16px', color: '#a5b4fc' }}>🤝 Register New Buyer</h4>
              <form onSubmit={handleRegisterBuyer}>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(180px, 1fr))', gap: 12 }}>
                  {[['name', 'Full Name'], ['mobile_or_email', 'Mobile / Email'], ['organization', 'Organization'], ['state', 'State'], ['district', 'District']].map(([k, lbl]) => (
                    <div key={k}><label style={labelStyle}>{lbl}</label><input type="text" value={(buyerForm as any)[k]} style={inputStyle} onChange={e => setBuyerForm(p => ({ ...p, [k]: e.target.value }))} /></div>
                  ))}
                </div>
                <div style={{ marginTop: 14, display: 'flex', gap: 10 }}>
                  <button type="submit" style={btnPrimary}>Register</button>
                  <button type="button" style={btnSecondary} onClick={() => setShowBuyerForm(false)}>Cancel</button>
                </div>
              </form>
            </div>
          )}
          <h4 style={{ color: '#94a3b8', margin: '0 0 12px' }}>Registered Buyers ({buyers.length})</h4>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 10, marginBottom: 24 }}>
            {buyers.map(b => (
              <div key={b.id} style={{ background: 'rgba(30,41,59,0.7)', border: '1px solid rgba(99,102,241,0.2)', borderRadius: 10, padding: '10px 16px', minWidth: 150 }}>
                <div style={{ fontWeight: 700, color: '#c7d2fe' }}>{b.name}</div>
                {b.organization && <div style={{ fontSize: '0.75rem', color: '#64748b' }}>{b.organization}</div>}
                <div style={{ fontSize: '0.72rem', color: '#6366f1', marginTop: 4 }}>ID: {b.id}</div>
              </div>
            ))}
          </div>
          <h4 style={{ color: '#94a3b8', margin: '0 0 12px' }}>Purchase Requests ({purchaseRequests.length})</h4>
          {purchaseRequests.length === 0 && <p style={{ color: '#64748b' }}>No purchase requests yet.</p>}
          {purchaseRequests.map(r => (
            <div key={r.id} style={{ ...cardStyle, padding: 16, display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 10 }}>
              <div>
                <div style={{ fontWeight: 700, color: '#c7d2fe' }}>{r.crop} — {r.requested_quantity} qntl</div>
                <div style={{ fontSize: '0.8rem', color: '#94a3b8' }}>Farmer: {r.farmer_name} | Buyer: {r.buyer_name}</div>
                <div style={{ fontSize: '0.82rem', color: '#10b981', fontWeight: 700 }}>Offer: ₹{r.offered_price}/qntl</div>
                {r.message && <div style={{ fontSize: '0.75rem', color: '#64748b' }}>{r.message}</div>}
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
                <StatusBadge status={r.status} />
                {r.status === 'REQUESTED' && (
                  <>
                    <button style={{ ...btnPrimary, padding: '6px 12px', fontSize: '0.78rem', background: '#10b981' }} onClick={() => handleUpdatePRStatus(r.id, 'ACCEPTED')}>Accept</button>
                    <button style={{ ...btnPrimary, padding: '6px 12px', fontSize: '0.78rem', background: '#ef4444' }} onClick={() => handleUpdatePRStatus(r.id, 'REJECTED')}>Reject</button>
                  </>
                )}
                {r.status === 'ACCEPTED' && (
                  <button style={{ ...btnPrimary, padding: '6px 12px', fontSize: '0.78rem', background: '#6366f1' }} onClick={() => handleUpdatePRStatus(r.id, 'COMPLETED')}>Mark Completed</button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* PRICE FORECAST */}
      {tab === 'forecast' && (
        <div>
          <div style={{ ...cardStyle, marginBottom: 24 }}>
            <h3 style={{ margin: '0 0 12px', color: '#a5b4fc' }}>🔮 ML Crop Price Forecast</h3>
            <div style={{ fontSize: '0.78rem', color: '#94a3b8', marginBottom: 14, padding: '10px 14px', borderRadius: 8, background: 'rgba(239,68,68,0.07)', border: '1px solid rgba(239,68,68,0.2)' }}>
              ⚠️ <strong style={{ color: '#fca5a5' }}>Scientific Disclaimer:</strong> ML estimates based on historical patterns. NOT guaranteed market outcomes. Use for decision support only.
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: 14, marginBottom: 16 }}>
              <div>
                <label style={labelStyle}>Crop</label>
                <select value={forecastCrop} style={inputStyle} onChange={e => setForecastCrop(e.target.value)}>
                  {(supportedOptions.crops.length ? supportedOptions.crops : ['Paddy', 'Wheat', 'Maize', 'Cotton', 'Sugarcane', 'Onion', 'Tomato']).map(c => <option key={c}>{c}</option>)}
                </select>
              </div>
              <div>
                <label style={labelStyle}>Market</label>
                <select value={forecastMarket} style={inputStyle} onChange={e => setForecastMarket(e.target.value)}>
                  {(supportedOptions.markets.length ? supportedOptions.markets : ['Guntur', 'Warangal', 'Nashik', 'Indore', 'Agra', 'Ludhiana', 'Coimbatore']).map(m => <option key={m}>{m}</option>)}
                </select>
              </div>
              <div>
                <label style={labelStyle}>State</label>
                <input type="text" value={forecastState} style={inputStyle} onChange={e => setForecastState(e.target.value)} />
              </div>
            </div>
            <button style={{ ...btnPrimary, minWidth: 180 }} onClick={handleRunForecast} disabled={forecastLoading}>
              {forecastLoading ? '⏳ Forecasting…' : '🔮 Get ML Price Forecast'}
            </button>
          </div>
          {forecast && (
            <div>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: 14, marginBottom: 20 }}>
                <div style={{ ...cardStyle, textAlign: 'center' }}>
                  <div style={{ fontSize: '0.72rem', color: '#64748b', marginBottom: 4 }}>Current Price</div>
                  <div style={{ fontSize: '1.8rem', fontWeight: 800, color: '#e2e8f0' }}>₹{forecast.current_price.toLocaleString()}</div>
                  <div style={{ fontSize: '0.72rem', color: '#64748b' }}>{forecast.price_unit}</div>
                  <div style={{ fontSize: '0.75rem', color: '#94a3b8', marginTop: 6 }}>7d avg: ₹{forecast.current_price_context.avg_7d}</div>
                </div>
                <div style={{ ...cardStyle, background: `${REC_COLORS[forecast.recommendation] || '#6366f1'}11`, border: `1px solid ${REC_COLORS[forecast.recommendation] || '#6366f1'}33`, textAlign: 'center' }}>
                  <div style={{ fontSize: '0.72rem', color: '#64748b', marginBottom: 4 }}>ML Recommendation</div>
                  <div style={{ fontSize: '1rem', fontWeight: 800, color: REC_COLORS[forecast.recommendation] || '#818cf8' }}>{forecast.recommendation_label}</div>
                  <div style={{ fontSize: '0.72rem', color: '#94a3b8', marginTop: 6 }}>{forecast.model_algorithm}</div>
                </div>
                {forecast.best_selling_window && (
                  <div style={{ ...cardStyle, textAlign: 'center' }}>
                    <div style={{ fontSize: '0.72rem', color: '#64748b', marginBottom: 4 }}>Best Predicted Price</div>
                    <div style={{ fontSize: '1.5rem', fontWeight: 800, color: '#10b981' }}>₹{forecast.best_selling_window.predicted_price.toLocaleString()}</div>
                    <div style={{ fontSize: '0.75rem', color: '#94a3b8' }}>in {forecast.best_selling_window.days_ahead} days ({forecast.best_selling_window.forecast_date})</div>
                    <div style={{ fontSize: '0.78rem', marginTop: 4, color: forecast.best_selling_window.price_change_pct >= 0 ? '#10b981' : '#ef4444' }}>
                      {forecast.best_selling_window.price_change_pct >= 0 ? '+' : ''}{forecast.best_selling_window.price_change_pct}% vs current
                    </div>
                  </div>
                )}
              </div>
              <div style={cardStyle}>
                <h4 style={{ margin: '0 0 14px', color: '#c7d2fe' }}>📅 {forecast.crop} @ {forecast.market} — Forecast Timeline</h4>
                <div style={{ display: 'flex', gap: 14, flexWrap: 'wrap', marginBottom: 16 }}>
                  {forecast.forecasts.map((f: any) => (
                    <div key={f.days_ahead} style={{ flex: 1, minWidth: 140, padding: '12px 14px', borderRadius: 10, background: 'rgba(15,23,42,0.6)', border: '1px solid rgba(99,102,241,0.2)', textAlign: 'center' }}>
                      <div style={{ fontSize: '0.72rem', color: '#64748b' }}>+{f.days_ahead} Days</div>
                      <div style={{ fontSize: '0.75rem', color: '#94a3b8', marginBottom: 4 }}>{f.forecast_date}</div>
                      <div style={{ fontSize: '1.4rem', fontWeight: 800, color: '#e2e8f0' }}>₹{f.predicted_price.toLocaleString()}</div>
                      <div style={{ fontSize: '0.75rem', marginTop: 4, color: f.price_change_pct >= 0 ? '#10b981' : '#ef4444' }}>
                        {f.price_change_pct >= 0 ? '▲' : '▼'} {Math.abs(f.price_change_pct)}%
                      </div>
                      <div style={{ fontSize: '0.65rem', color: '#6366f1', marginTop: 4 }}>🤖 ML Prediction</div>
                    </div>
                  ))}
                </div>
                {forecast.historical_price_series.length > 0 && (
                  <div>
                    <div style={{ fontSize: '0.78rem', color: '#64748b', marginBottom: 6 }}>30-Day Observed Price History</div>
                    <SparkLine data={forecast.historical_price_series.map((p: any) => p.price)} />
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.7rem', color: '#64748b', marginTop: 2 }}>
                      <span>{forecast.historical_price_series[0]?.date}</span>
                      <span>{forecast.historical_price_series[forecast.historical_price_series.length - 1]?.date}</span>
                    </div>
                  </div>
                )}
              </div>
              <div style={{ padding: '10px 14px', borderRadius: 8, background: 'rgba(239,68,68,0.06)', border: '1px solid rgba(239,68,68,0.15)', fontSize: '0.75rem', color: '#94a3b8', marginTop: 12 }}>
                🔬 {forecast.scientific_disclaimer}
              </div>
            </div>
          )}
        </div>
      )}

      {/* ML MODEL */}
      {tab === 'model' && (
        <div>
          {!modelStatus?.ready ? (
            <div style={{ ...cardStyle, textAlign: 'center', padding: 40 }}>
              <div style={{ fontSize: '2.5rem', marginBottom: 12 }}>🤖</div>
              <p style={{ color: '#94a3b8' }}>Price forecast model not trained. Click Train in Dashboard or wait for background training.</p>
            </div>
          ) : (
            <>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(180px, 1fr))', gap: 14, marginBottom: 20 }}>
                {[
                  { label: 'Champion Algorithm', value: modelStatus.champion_algorithm, color: '#818cf8' },
                  { label: 'R² Score', value: modelStatus.champion_metrics?.r2_score, color: '#10b981' },
                  { label: 'RMSE (₹/quintal)', value: modelStatus.champion_metrics?.rmse, color: '#f59e0b' },
                  { label: 'MAPE', value: `${modelStatus.champion_metrics?.mape_pct}%`, color: '#3b82f6' },
                  { label: 'MAE (₹)', value: modelStatus.champion_metrics?.mae, color: '#6366f1' },
                  { label: 'Train Samples', value: modelStatus.training_dataset_size?.toLocaleString(), color: '#94a3b8' },
                ].map(({ label, value, color }) => (
                  <div key={label} style={{ ...cardStyle, textAlign: 'center', padding: 16 }}>
                    <div style={{ fontSize: '0.72rem', color: '#64748b', marginBottom: 4 }}>{label}</div>
                    <div style={{ fontSize: '1.2rem', fontWeight: 800, color }}>{value}</div>
                  </div>
                ))}
              </div>
              <div style={cardStyle}>
                <h4 style={{ margin: '0 0 12px', color: '#c7d2fe' }}>All Candidate Models</h4>
                <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.82rem' }}>
                  <thead>
                    <tr style={{ borderBottom: '1px solid rgba(99,102,241,0.2)' }}>
                      {['Algorithm', 'RMSE', 'MAE', 'R²', 'MAPE'].map(h => <th key={h} style={{ padding: '8px 12px', textAlign: 'left', color: '#64748b', fontWeight: 600 }}>{h}</th>)}
                    </tr>
                  </thead>
                  <tbody>
                    {Object.entries(modelStatus.all_candidate_metrics || {}).map(([algo, m]: [string, any]) => (
                      <tr key={algo} style={{ borderBottom: '1px solid rgba(99,102,241,0.08)', background: algo === modelStatus.champion_algorithm ? 'rgba(99,102,241,0.08)' : 'transparent' }}>
                        <td style={{ padding: '10px 12px', color: algo === modelStatus.champion_algorithm ? '#818cf8' : '#94a3b8', fontWeight: algo === modelStatus.champion_algorithm ? 700 : 400 }}>
                          {algo === modelStatus.champion_algorithm ? '👑 ' : ''}{algo}
                        </td>
                        <td style={{ padding: '10px 12px', color: '#e2e8f0' }}>{m.rmse}</td>
                        <td style={{ padding: '10px 12px', color: '#e2e8f0' }}>{m.mae}</td>
                        <td style={{ padding: '10px 12px', color: '#10b981' }}>{m.r2_score}</td>
                        <td style={{ padding: '10px 12px', color: '#e2e8f0' }}>{m.mape_pct}%</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <div style={cardStyle}>
                <h4 style={{ margin: '0 0 12px', color: '#c7d2fe' }}>Dataset & Coverage</h4>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10, fontSize: '0.82rem', marginBottom: 14 }}>
                  <div><span style={{ color: '#64748b' }}>Data Source: </span><span style={{ color: '#c7d2fe' }}>{modelStatus.data_source}</span></div>
                  <div><span style={{ color: '#64748b' }}>Trained At: </span><span style={{ color: '#c7d2fe' }}>{modelStatus.trained_at?.substring(0, 16)}</span></div>
                  <div><span style={{ color: '#64748b' }}>Crops: </span><span style={{ color: '#c7d2fe' }}>{modelStatus.supported_crops?.join(', ')}</span></div>
                  <div><span style={{ color: '#64748b' }}>Test Samples: </span><span style={{ color: '#c7d2fe' }}>{modelStatus.test_dataset_size?.toLocaleString()}</span></div>
                </div>
                <div style={{ padding: '10px 14px', borderRadius: 8, background: 'rgba(99,102,241,0.08)', fontSize: '0.75rem', color: '#94a3b8' }}>
                  🔬 {modelStatus.scientific_note}
                </div>
              </div>
            </>
          )}
        </div>
      )}
    </div>
  );
}

export default MarketplaceTab;
