import React, { useState } from 'react';
import { UserPlus, Users, Search, Phone, MapPin, Globe, Check, AlertCircle } from 'lucide-react';
import { registerFarmer } from '../api';

interface FarmerRegistryTabProps {
  farmers: any[];
  states: any[];
  districts: any[];
  onFarmerRegistered: () => void;
}

export const FarmerRegistryTab: React.FC<FarmerRegistryTabProps> = ({
  farmers,
  states,
  districts,
  onFarmerRegistered,
}) => {
  const [search, setSearch] = useState('');
  const [selectedState, setSelectedState] = useState<string>('ALL');
  const [showModal, setShowModal] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [formError, setFormError] = useState('');

  // Form State
  const [formData, setFormData] = useState({
    full_name: '',
    mobile_number: '',
    state_id: '',
    district_id: '',
    mandal_block: '',
    preferred_language: 'Telugu',
    crop: 'Paddy',
    crop_stage: 'Vegetative',
  });

  const filteredDistricts = districts.filter(
    (d) => !formData.state_id || d.state_id === parseInt(formData.state_id)
  );

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setFormError('');

    if (!formData.full_name || !formData.mobile_number || !formData.state_id || !formData.district_id) {
      setFormError('Please fill in all required fields');
      return;
    }

    if (!/^\d{10}$/.test(formData.mobile_number.trim())) {
      setFormError('Mobile number must be exactly 10 digits without leading 0 or +91');
      return;
    }

    try {
      setSubmitting(true);
      await registerFarmer({
        full_name: formData.full_name.trim(),
        mobile_number: formData.mobile_number.trim(),
        state_id: parseInt(formData.state_id),
        district_id: parseInt(formData.district_id),
        mandal_block: formData.mandal_block.trim() || undefined,
        preferred_language: formData.preferred_language,
        crop: formData.crop,
        crop_stage: formData.crop_stage,
      });
      setShowModal(false);
      setFormData({
        full_name: '',
        mobile_number: '',
        state_id: '',
        district_id: '',
        mandal_block: '',
        preferred_language: 'Telugu',
        crop: 'Paddy',
        crop_stage: 'Vegetative',
      });
      onFarmerRegistered();
    } catch (err: any) {
      setFormError(err.message || 'Registration failed');
    } finally {
      setSubmitting(false);
    }
  };

  const filteredFarmers = farmers.filter((f) => {
    const matchesSearch = f.full_name.toLowerCase().includes(search.toLowerCase()) ||
                          f.district_name.toLowerCase().includes(search.toLowerCase()) ||
                          f.crop?.toLowerCase().includes(search.toLowerCase());
    const matchesState = selectedState === 'ALL' || f.state_name === selectedState;
    return matchesSearch && matchesState;
  });

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      {/* Top action & filter bar */}
      <div className="glass-card" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '16px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', flex: 1, minWidth: '280px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flex: 1 }}>
            <Search size={16} color="var(--text-muted)" />
            <input
              type="text"
              className="form-input"
              placeholder="Search farmer by name, district, crop..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>

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
        </div>

        <button
          className="btn btn-emerald"
          onClick={() => setShowModal(true)}
        >
          <UserPlus size={16} /> Register New Farmer
        </button>
      </div>

      {/* Farmers List Table */}
      <div className="glass-card" style={{ padding: 0, overflow: 'hidden' }}>
        <div style={{ padding: '16px 20px', borderBottom: '1px solid var(--border-subtle)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <h2 style={{ fontSize: '1rem', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Users size={18} color="#10b981" />
            Registered Farmer Beneficiaries ({filteredFarmers.length})
          </h2>
          <span style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>
            Phone numbers masked for DPDP Act privacy compliance
          </span>
        </div>

        <div style={{ overflowX: 'auto' }}>
          <table className="custom-table">
            <thead>
              <tr>
                <th>Farmer Name</th>
                <th>Contact</th>
                <th>State / District</th>
                <th>Crop & Stage</th>
                <th>Preferred Language</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {filteredFarmers.length === 0 ? (
                <tr>
                  <td colSpan={6} style={{ textAlign: 'center', padding: '36px', color: 'var(--text-muted)' }}>
                    No farmers registered yet. Click "Register New Farmer" to add one!
                  </td>
                </tr>
              ) : (
                filteredFarmers.map((f) => (
                  <tr key={f.id}>
                    <td>
                      <div style={{ fontWeight: 700, color: '#f8fafc' }}>{f.full_name}</div>
                      {f.mandal_block && (
                        <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Block: {f.mandal_block}</div>
                      )}
                    </td>
                    <td>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontFamily: 'var(--font-mono)' }}>
                        <Phone size={13} color="var(--text-dim)" />
                        {f.mobile_number_masked}
                      </div>
                    </td>
                    <td>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                        <MapPin size={13} color="#38bdf8" />
                        <span>{f.district_name}, {f.state_name}</span>
                      </div>
                    </td>
                    <td>
                      <div style={{ fontWeight: 600 }}>{f.crop || 'Mixed'}</div>
                      <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>Stage: {f.crop_stage || 'Active'}</div>
                    </td>
                    <td>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                        <Globe size={13} color="#a855f7" />
                        <span style={{ fontWeight: 600 }}>{f.preferred_language}</span>
                      </div>
                    </td>
                    <td>
                      {f.is_active ? (
                        <span className="badge badge-green">ACTIVE</span>
                      ) : (
                        <span className="badge badge-neutral">INACTIVE</span>
                      )}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Registration Modal */}
      {showModal && (
        <div className="modal-overlay" onClick={() => setShowModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div style={{ padding: '20px', borderBottom: '1px solid var(--border-subtle)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <h3 style={{ fontSize: '1.2rem', fontWeight: 800 }}>Register Farmer for Early Warnings</h3>
              <button className="btn btn-secondary" onClick={() => setShowModal(false)}>✕</button>
            </div>

            <form onSubmit={handleSubmit} style={{ padding: '20px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
              {formError && (
                <div style={{ padding: '10px 14px', background: 'rgba(239, 68, 68, 0.2)', border: '1px solid rgba(239, 68, 68, 0.4)', borderRadius: '8px', color: '#fca5a5', fontSize: '0.85rem', display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <AlertCircle size={16} /> {formError}
                </div>
              )}

              <div>
                <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '6px' }}>
                  Farmer Full Name *
                </label>
                <input
                  type="text"
                  required
                  className="form-input"
                  placeholder="e.g. Ramesh Kumar Patel"
                  value={formData.full_name}
                  onChange={(e) => setFormData({ ...formData, full_name: e.target.value })}
                />
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '6px' }}>
                  Mobile Number (10 Digits) *
                </label>
                <input
                  type="tel"
                  required
                  className="form-input"
                  placeholder="e.g. 9876543210"
                  value={formData.mobile_number}
                  onChange={(e) => setFormData({ ...formData, mobile_number: e.target.value.replace(/\D/g, '').slice(0, 10) })}
                />
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                <div>
                  <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '6px' }}>
                    State *
                  </label>
                  <select
                    required
                    className="form-select"
                    value={formData.state_id}
                    onChange={(e) => setFormData({ ...formData, state_id: e.target.value, district_id: '' })}
                  >
                    <option value="">Select State</option>
                    {states.map((s) => (
                      <option key={s.id} value={s.id}>{s.name}</option>
                    ))}
                  </select>
                </div>

                <div>
                  <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '6px' }}>
                    District *
                  </label>
                  <select
                    required
                    disabled={!formData.state_id}
                    className="form-select"
                    value={formData.district_id}
                    onChange={(e) => setFormData({ ...formData, district_id: e.target.value })}
                  >
                    <option value="">Select District</option>
                    {filteredDistricts.map((d) => (
                      <option key={d.id} value={d.id}>{d.name}</option>
                    ))}
                  </select>
                </div>
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '6px' }}>
                  Mandal / Block / Village (Optional)
                </label>
                <input
                  type="text"
                  className="form-input"
                  placeholder="e.g. Tenali Mandal"
                  value={formData.mandal_block}
                  onChange={(e) => setFormData({ ...formData, mandal_block: e.target.value })}
                />
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                <div>
                  <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '6px' }}>
                    Primary Crop
                  </label>
                  <select
                    className="form-select"
                    value={formData.crop}
                    onChange={(e) => setFormData({ ...formData, crop: e.target.value })}
                  >
                    <option value="Paddy">Paddy (Rice)</option>
                    <option value="Cotton">Cotton</option>
                    <option value="Wheat">Wheat</option>
                    <option value="Maize">Maize</option>
                    <option value="Sugarcane">Sugarcane</option>
                    <option value="Soybean">Soybean</option>
                    <option value="Pulses">Pulses</option>
                    <option value="Vegetables">Vegetables</option>
                  </select>
                </div>

                <div>
                  <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '6px' }}>
                    Preferred Language *
                  </label>
                  <select
                    className="form-select"
                    value={formData.preferred_language}
                    onChange={(e) => setFormData({ ...formData, preferred_language: e.target.value })}
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
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px', marginTop: '10px' }}>
                <button type="button" className="btn btn-secondary" onClick={() => setShowModal(false)}>
                  Cancel
                </button>
                <button type="submit" className="btn btn-emerald" disabled={submitting}>
                  {submitting ? 'Registering...' : 'Save & Register Farmer'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
