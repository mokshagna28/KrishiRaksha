// API Client for KRISHIRAKSHA AI

export const API_BASE = '';

export async function fetchSystemStatus() {
  const res = await fetch(`${API_BASE}/api/system/status`);
  if (!res.ok) throw new Error('Failed to fetch system status');
  return res.json();
}

export async function fetchDistricts() {
  const res = await fetch(`${API_BASE}/api/districts`);
  if (!res.ok) throw new Error('Failed to fetch districts');
  return res.json();
}

export async function fetchDistrictDetail(id: number) {
  const res = await fetch(`${API_BASE}/api/districts/${id}`);
  if (!res.ok) throw new Error('Failed to fetch district details');
  return res.json();
}

export async function fetchStates() {
  const res = await fetch(`${API_BASE}/api/states`);
  if (!res.ok) throw new Error('Failed to fetch states');
  return res.json();
}

export async function fetchFarmers(stateId?: number, districtId?: number) {
  let url = `${API_BASE}/api/farmers`;
  const params = new URLSearchParams();
  if (stateId) params.append('state_id', stateId.toString());
  if (districtId) params.append('district_id', districtId.toString());
  if (params.toString()) url += `?${params.toString()}`;
  const res = await fetch(url);
  if (!res.ok) throw new Error('Failed to fetch farmers');
  return res.json();
}

export async function registerFarmer(farmerData: any) {
  const res = await fetch(`${API_BASE}/api/farmers`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(farmerData),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Failed to register farmer' }));
    throw new Error(err.detail || 'Failed to register farmer');
  }
  return res.json();
}

export async function fetchAlerts() {
  const res = await fetch(`${API_BASE}/api/alerts`);
  if (!res.ok) throw new Error('Failed to fetch alerts');
  return res.json();
}

export async function simulateAlertPreview(districtId: number, stateId: number, riskLevel: string) {
  const res = await fetch(`${API_BASE}/api/alerts/simulate-preview`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ district_id: districtId, state_id: stateId, risk_level: riskLevel, send_sms: false }),
  });
  if (!res.ok) throw new Error('Failed to preview alert');
  return res.json();
}

export async function generateAlert(districtId: number, stateId: number, riskLevel: string, sendSms: boolean) {
  const res = await fetch(`${API_BASE}/api/alerts/generate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ district_id: districtId, state_id: stateId, risk_level: riskLevel, send_sms: sendSms }),
  });
  if (!res.ok) throw new Error('Failed to generate alert');
  return res.json();
}

export async function fetchSmsLogs() {
  const res = await fetch(`${API_BASE}/api/sms/logs`);
  if (!res.ok) throw new Error('Failed to fetch SMS logs');
  return res.json();
}

export async function fetchSmsConfig() {
  const res = await fetch(`${API_BASE}/api/sms/config`);
  if (!res.ok) throw new Error('Failed to fetch SMS config');
  return res.json();
}

export async function sendTestSms(payload: any) {
  const res = await fetch(`${API_BASE}/api/sms/test`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Failed to send test SMS' }));
    throw new Error(err.detail || 'Failed to send test SMS');
  }
  return res.json();
}

export async function fetchMlMetrics() {
  const res = await fetch(`${API_BASE}/api/ml/metrics`);
  if (!res.ok) throw new Error('Failed to fetch ML metrics');
  return res.json();
}

export async function runMonitoringCycle() {
  const res = await fetch(`${API_BASE}/api/monitor/cycle`, { method: 'POST' });
  if (!res.ok) throw new Error('Failed to run monitoring cycle');
  return res.json();
}

export async function refreshWeather() {
  const res = await fetch(`${API_BASE}/api/weather/refresh`, { method: 'POST' });
  if (!res.ok) throw new Error('Failed to refresh weather');
  return res.json();
}

export async function runPredictions() {
  const res = await fetch(`${API_BASE}/api/predictions/run`, { method: 'POST' });
  if (!res.ok) throw new Error('Failed to run predictions');
  return res.json();
}

// ═══════════════════════════════════════════════════════════════════════
// CROP WATER INTELLIGENCE
// ═══════════════════════════════════════════════════════════════════════
export async function predictCropWater(payload: {
  crop: string;
  growth_stage: string;
  soil_type: string;
  soil_moisture: number;
  recent_rainfall: number;
  forecast_rainfall: number;
  temperature: number;
  humidity: number;
  wind_speed: number;
}) {
  const res = await fetch(`${API_BASE}/api/crop-water/predict`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Prediction failed' }));
    throw new Error(err.detail || 'Crop water prediction failed');
  }
  return res.json();
}

export async function fetchCropWaterModelStatus() {
  const res = await fetch(`${API_BASE}/api/crop-water/model-status`);
  if (!res.ok) throw new Error('Failed to fetch crop water model status');
  return res.json();
}

export async function fetchCropWaterFeatureImportance() {
  const res = await fetch(`${API_BASE}/api/crop-water/feature-importance`);
  if (!res.ok) throw new Error('Failed to fetch feature importance');
  return res.json();
}

// ═══════════════════════════════════════════════════════════════════════
// MARKETPLACE — CROP LISTINGS, BUYERS, PURCHASE REQUESTS & PRICE INTELLIGENCE
// ═══════════════════════════════════════════════════════════════════════

export async function fetchMarketListings(crop?: string, state?: string, status = 'ACTIVE') {
  let url = `${API_BASE}/api/market/listings?status=${status}`;
  if (crop) url += `&crop=${encodeURIComponent(crop)}`;
  if (state) url += `&state=${encodeURIComponent(state)}`;
  const res = await fetch(url);
  if (!res.ok) throw new Error('Failed to fetch listings');
  return res.json();
}

export async function createMarketListing(payload: any) {
  const res = await fetch(`${API_BASE}/api/market/listings`, {
    method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload),
  });
  if (!res.ok) { const err = await res.json().catch(() => ({ detail: 'Failed to create listing' })); throw new Error(err.detail || 'Create listing failed'); }
  return res.json();
}

export async function registerBuyer(payload: any) {
  const res = await fetch(`${API_BASE}/api/market/buyers`, {
    method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload),
  });
  if (!res.ok) { const err = await res.json().catch(() => ({ detail: 'Failed to register buyer' })); throw new Error(err.detail || 'Buyer registration failed'); }
  return res.json();
}

export async function listBuyers() {
  const res = await fetch(`${API_BASE}/api/market/buyers`);
  if (!res.ok) throw new Error('Failed to fetch buyers');
  return res.json();
}

export async function createPurchaseRequest(payload: any) {
  const res = await fetch(`${API_BASE}/api/market/purchase-requests`, {
    method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload),
  });
  if (!res.ok) { const err = await res.json().catch(() => ({ detail: 'Failed to submit request' })); throw new Error(err.detail || 'Purchase request failed'); }
  return res.json();
}

export async function fetchPurchaseRequests(listingId?: number, buyerId?: number) {
  let url = `${API_BASE}/api/market/purchase-requests`;
  const params = new URLSearchParams();
  if (listingId) params.append('listing_id', listingId.toString());
  if (buyerId) params.append('buyer_id', buyerId.toString());
  if (params.toString()) url += `?${params.toString()}`;
  const res = await fetch(url);
  if (!res.ok) throw new Error('Failed to fetch purchase requests');
  return res.json();
}

export async function updatePurchaseRequestStatus(requestId: number, status: string) {
  const res = await fetch(`${API_BASE}/api/market/purchase-requests/${requestId}/status`, {
    method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ status }),
  });
  if (!res.ok) throw new Error('Failed to update request status');
  return res.json();
}

export async function fetchMarketPriceForecast(crop: string, market: string, state: string, forecastDays = 30) {
  const url = `${API_BASE}/api/market/price-forecast?crop=${encodeURIComponent(crop)}&market=${encodeURIComponent(market)}&state=${encodeURIComponent(state)}&forecast_days=${forecastDays}`;
  const res = await fetch(url);
  if (!res.ok) { const err = await res.json().catch(() => ({ detail: 'Forecast failed' })); throw new Error(err.detail || 'Price forecast failed'); }
  return res.json();
}

export async function fetchMarketOverview() {
  const res = await fetch(`${API_BASE}/api/market/overview`);
  if (!res.ok) throw new Error('Failed to fetch market overview');
  return res.json();
}

export async function fetchMarketModelStatus() {
  const res = await fetch(`${API_BASE}/api/market/model-status`);
  if (!res.ok) throw new Error('Failed to fetch market model status');
  return res.json();
}

export async function fetchMarketSupportedOptions() {
  const res = await fetch(`${API_BASE}/api/market/supported-options`);
  if (!res.ok) throw new Error('Failed to fetch supported options');
  return res.json();
}

export async function triggerMarketTraining() {
  const res = await fetch(`${API_BASE}/api/market/train`, { method: 'POST' });
  if (!res.ok) throw new Error('Failed to trigger market model training');
  return res.json();
}

// ═══════════════════════════════════════════════════════════════════════
// STATE-WISE SMS BROADCAST
// ═══════════════════════════════════════════════════════════════════════

export async function fetchStatesWithFarmers() {
  const res = await fetch(`${API_BASE}/api/alerts/states-with-farmers`);
  if (!res.ok) throw new Error('Failed to fetch states with farmers');
  return res.json();
}

export async function previewStateBroadcast(stateId: number, riskLevel: string) {
  const res = await fetch(`${API_BASE}/api/alerts/state-broadcast-preview`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ state_id: stateId, risk_level: riskLevel }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Preview failed' }));
    throw new Error(err.detail || 'State broadcast preview failed');
  }
  return res.json();
}

export async function executeStateBroadcast(payload: {
  state_id: number;
  risk_level: string;
  official_warning: string;
  forecast_period: string;
}) {
  const res = await fetch(`${API_BASE}/api/alerts/state-broadcast`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Broadcast failed' }));
    throw new Error(err.detail || 'State broadcast failed');
  }
  return res.json();
}
