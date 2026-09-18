import React, { useState } from 'react';
import {
  FileText,
  Calculator,
  CheckCircle2,
  AlertTriangle,
  Layers,
  Sparkles,
  ShieldCheck,
  Send,
  User,
  MapPin,
  RefreshCw,
  Scale,
  Info,
} from 'lucide-react';
import {
  ReasonForApplying,
  Occupation,
  FarmerCropType,
  LandAreaUnit,
  DamageSeverity,
  ShopStoreType,
  ShopDamageCategory,
  InventoryDamageBand,
  DamageAssessmentFormData,
  CalculationBreakdown,
  DamageAssessment,
} from '../types';
import {
  useCalculateDamageMutation,
  useSubmitDamageAssessmentMutation,
  useDamageAssessmentsQuery,
} from '../api/damage';

export const DamageAssessmentView: React.FC = () => {
  // Form State
  const [reason, setReason] = useState<ReasonForApplying>('EXTREME_RAINFALL');
  const [occupation, setOccupation] = useState<Occupation>('FARMER');
  const [applicantName, setApplicantName] = useState<string>('Ramesh Patel');
  const [locationName, setLocationName] = useState<string>('Wayanad District, Kerala');
  const [damageSeverity, setDamageSeverity] = useState<DamageSeverity>('MAJOR');

  // Farmer specific
  const [cropType, setCropType] = useState<FarmerCropType>('PADDY');
  const [damagedArea, setDamagedArea] = useState<number>(2.5);
  const [damagedAreaUnit, setDamagedAreaUnit] = useState<LandAreaUnit>('ACRES');
  const [affectedPercentage, setAffectedPercentage] = useState<number>(100);

  // Shopkeeper specific
  const [storeType, setStoreType] = useState<ShopStoreType>('GROCERY_STORE');
  const [damageCategory, setDamageCategory] = useState<ShopDamageCategory>('INVENTORY_DAMAGE');
  const [inventoryBand, setInventoryBand] = useState<InventoryDamageBand>('BAND_25K_50K');

  // Generic specific
  const [workType, setWorkType] = useState<string>('Agricultural Labor');
  const [lossQuantity, setLossQuantity] = useState<number>(10);

  // Result & Submission state
  const [calculationResult, setCalculationResult] = useState<CalculationBreakdown | null>(null);
  const [lastSubmitted, setLastSubmitted] = useState<DamageAssessment | null>(null);
  const [validationError, setValidationError] = useState<string | null>(null);

  const calculateMutation = useCalculateDamageMutation();
  const submitMutation = useSubmitDamageAssessmentMutation();
  const { data: recentAssessments, refetch: refetchAssessments, isFetching } = useDamageAssessmentsQuery();

  // Handlers
  const handleOccupationChange = (newOcc: Occupation) => {
    setOccupation(newOcc);
    setCalculationResult(null);
    setValidationError(null);

    // Reset occupation-specific defaults cleanly
    if (newOcc === 'FARMER') {
      setCropType('PADDY');
      setDamagedArea(2.5);
      setDamagedAreaUnit('ACRES');
    } else if (newOcc === 'SHOPKEEPER') {
      setStoreType('GROCERY_STORE');
      setDamageCategory('INVENTORY_DAMAGE');
      setInventoryBand('BAND_25K_50K');
    } else if (newOcc === 'DAILY_WAGE_WORKER') {
      setWorkType('Construction Labor');
      setLossQuantity(10);
    }
  };

  const getFormData = (): DamageAssessmentFormData => {
    const base: DamageAssessmentFormData = {
      reason_for_applying: reason,
      occupation,
      applicant_name: applicantName || 'Anonymous Applicant',
      location_name: locationName || 'Monitored District',
      damage_severity: damageSeverity,
    };

    if (occupation === 'FARMER') {
      base.crop_type = cropType;
      base.damaged_area = Number(damagedArea);
      base.damaged_area_unit = damagedAreaUnit;
      base.affected_percentage = Number(affectedPercentage);
    } else if (occupation === 'SHOPKEEPER') {
      base.store_type = storeType;
      base.damage_category = damageCategory;
      base.inventory_damage_band = inventoryBand;
    } else {
      base.work_type = workType;
      base.loss_quantity = Number(lossQuantity);
    }

    return base;
  };

  const handleCalculate = async () => {
    setValidationError(null);
    if (occupation === 'FARMER' && (!damagedArea || damagedArea <= 0)) {
      setValidationError('Damaged land area must be strictly greater than zero.');
      return;
    }

    try {
      const formData = getFormData();
      const res = await calculateMutation.mutateAsync(formData);
      setCalculationResult(res.breakdown);
    } catch (err: any) {
      setValidationError(err.message || 'Calculation failed.');
    }
  };

  const handleSubmit = async () => {
    setValidationError(null);
    try {
      const formData = getFormData();
      const res = await submitMutation.mutateAsync(formData);
      setLastSubmitted(res);
      setCalculationResult(null);
    } catch (err: any) {
      setValidationError(err.message || 'Submission failed.');
    }
  };

  // Demo Presets
  const applyPreset = (presetName: 'FARMER_ACRES' | 'FARMER_CENTS' | 'SHOP_GROCERY' | 'DAILY_WAGE' | 'CAP_TEST') => {
    setCalculationResult(null);
    setLastSubmitted(null);
    setValidationError(null);

    switch (presetName) {
      case 'FARMER_ACRES':
        setReason('EXTREME_RAINFALL');
        setOccupation('FARMER');
        setApplicantName('Ramesh Patel');
        setLocationName('Wayanad District, Kerala');
        setCropType('PADDY');
        setDamagedArea(2.5);
        setDamagedAreaUnit('ACRES');
        setDamageSeverity('MAJOR');
        setAffectedPercentage(100);
        break;
      case 'FARMER_CENTS':
        setReason('FLOOD');
        setOccupation('FARMER');
        setApplicantName('Kavita Devi');
        setLocationName('Cuttack, Odisha');
        setCropType('PADDY');
        setDamagedArea(250);
        setDamagedAreaUnit('CENTS');
        setDamageSeverity('MAJOR');
        setAffectedPercentage(100);
        break;
      case 'SHOP_GROCERY':
        setReason('FLOOD');
        setOccupation('SHOPKEEPER');
        setApplicantName('Suresh Kumar');
        setLocationName('Chennai North, Tamil Nadu');
        setStoreType('GROCERY_STORE');
        setDamageCategory('INVENTORY_DAMAGE');
        setInventoryBand('BAND_25K_50K');
        setDamageSeverity('MAJOR');
        break;
      case 'DAILY_WAGE':
        setReason('EXTREME_HEAT');
        setOccupation('DAILY_WAGE_WORKER');
        setApplicantName('Manoj Yadav');
        setLocationName('Nagpur, Maharashtra');
        setWorkType('Daily Construction Labor');
        setLossQuantity(10);
        setDamageSeverity('MAJOR');
        break;
      case 'CAP_TEST':
        setReason('FLOOD');
        setOccupation('FARMER');
        setApplicantName('Balwinder Singh');
        setLocationName('Ludhiana, Punjab');
        setCropType('PADDY');
        setDamagedArea(10.0);
        setDamagedAreaUnit('ACRES');
        setDamageSeverity('MAJOR');
        setAffectedPercentage(100);
        break;
    }
  };

  const reasonList: Array<{ id: ReasonForApplying; label: string; icon: string }> = [
    { id: 'FLOOD', label: 'Flood Inundation', icon: '🌊' },
    { id: 'CYCLONE', label: 'Cyclone Storm', icon: '🌀' },
    { id: 'EXTREME_RAINFALL', label: 'Extreme Rainfall', icon: '🌧️' },
    { id: 'EXTREME_HEAT', label: 'Extreme Heatwave', icon: '☀️' },
    { id: 'DROUGHT', label: 'Severe Drought', icon: '🏜️' },
    { id: 'OTHER', label: 'Other Climate Event', icon: '⚡' },
  ];

  const occupationList: Array<{ id: Occupation; label: string; icon: string }> = [
    { id: 'FARMER', label: 'Smallholder Farmer', icon: '🌾' },
    { id: 'SHOPKEEPER', label: 'Local Shopkeeper', icon: '🏪' },
    { id: 'DAILY_WAGE_WORKER', label: 'Daily Wage Worker', icon: '👷' },
    { id: 'STREET_VENDOR', label: 'Street Vendor', icon: '🛒' },
    { id: 'FISHER', label: 'Artisanal Fisher', icon: '🎣' },
    { id: 'SMALL_BUSINESS', label: 'Small Enterprise', icon: '🏢' },
    { id: 'TRANSPORT_WORKER', label: 'Transport / Courier', icon: '🚚' },
    { id: 'OTHER', label: 'Informal Worker', icon: '👤' },
  ];

  return (
    <div className="section-container">
      {/* Header */}
      <div className="section-header-row">
        <div>
          <h2 className="section-title">Climate Relief Application & Damage Assessment</h2>
          <p className="section-subtitle">
            Dynamic victim profile filter with deterministic backend calculation rules, land unit normalization, and maximum payout cap protection.
          </p>
        </div>
      </div>

      {/* Demo Quick Presets */}
      <div className="glass-panel" style={{ padding: '1rem', border: '1px solid rgba(56, 189, 248, 0.3)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.6rem' }}>
          <Sparkles size={16} color="#38bdf8" />
          <span style={{ fontSize: '0.8rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.04em', color: 'var(--accent-cyan)' }}>
            Quick Demo Presets (Instant Form Population)
          </span>
        </div>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
          <button className="btn btn-secondary" onClick={() => applyPreset('FARMER_ACRES')} style={{ fontSize: '0.75rem' }}>
            🌾 Scenario A: Farmer (2.5 Acres Paddy)
          </button>
          <button className="btn btn-secondary" onClick={() => applyPreset('FARMER_CENTS')} style={{ fontSize: '0.75rem' }}>
            📐 Scenario B: Farmer Cent Conversion (250 Cents)
          </button>
          <button className="btn btn-secondary" onClick={() => applyPreset('SHOP_GROCERY')} style={{ fontSize: '0.75rem' }}>
            🏪 Scenario C: Shopkeeper (Grocery Flood Loss)
          </button>
          <button className="btn btn-secondary" onClick={() => applyPreset('DAILY_WAGE')} style={{ fontSize: '0.75rem' }}>
            👷 Scenario D: Daily Wage (10 Days Heat Loss)
          </button>
          <button className="btn btn-secondary" onClick={() => applyPreset('CAP_TEST')} style={{ fontSize: '0.75rem', borderColor: '#f59e0b', color: '#f59e0b' }}>
            🛡️ Scenario E: Payout Cap Test (10 Acres)
          </button>
        </div>
      </div>

      {/* Main Dynamic Assessment Form Layout */}
      <div className="assessment-form-grid" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(420px, 1fr))', gap: '1.5rem' }}>
        {/* Left Column: Form Inputs */}
        <div className="glass-panel" style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
          <div style={{ borderBottom: '1px solid var(--border-subtle)', paddingBottom: '0.75rem' }}>
            <h3 style={{ fontSize: '1rem', fontWeight: 700, color: 'var(--text-primary)', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <FileText size={18} color="#38bdf8" />
              Beneficiary Profile & Assessment Details
            </h3>
          </div>

          {/* Applicant & Location Inputs */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem' }}>
            <div>
              <label className="form-label">
                <User size={12} /> Applicant Name
              </label>
              <input
                type="text"
                className="form-input"
                value={applicantName}
                onChange={(e) => setApplicantName(e.target.value)}
                placeholder="e.g. Ramesh Patel"
              />
            </div>
            <div>
              <label className="form-label">
                <MapPin size={12} /> Location / District
              </label>
              <input
                type="text"
                className="form-input"
                value={locationName}
                onChange={(e) => setLocationName(e.target.value)}
                placeholder="e.g. Wayanad District"
              />
            </div>
          </div>

          {/* Filter 1: Reason for Applying */}
          <div>
            <label className="form-label">
              <AlertTriangle size={12} color="#f59e0b" /> Step 1: Reason for Applying (Climate Event)
            </label>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '0.5rem' }}>
              {reasonList.map((r) => (
                <div
                  key={r.id}
                  className={`card-select-btn ${reason === r.id ? 'selected' : ''}`}
                  onClick={() => setReason(r.id)}
                >
                  <span style={{ fontSize: '1.1rem' }}>{r.icon}</span>
                  <span style={{ fontSize: '0.75rem', fontWeight: 600 }}>{r.label}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Filter 2: Occupation (Parent Dynamic Filter) */}
          <div>
            <label className="form-label">
              <Layers size={12} color="#38bdf8" /> Step 2: Occupation (Parent Dynamic Filter)
            </label>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '0.5rem' }}>
              {occupationList.map((occ) => (
                <div
                  key={occ.id}
                  className={`card-select-btn ${occupation === occ.id ? 'selected' : ''}`}
                  onClick={() => handleOccupationChange(occ.id)}
                >
                  <span style={{ fontSize: '1.1rem' }}>{occ.icon}</span>
                  <span style={{ fontSize: '0.75rem', fontWeight: 600 }}>{occ.label}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Step 3: Dynamic Occupation Fields */}
          <div className="dynamic-subform-box" style={{ background: 'rgba(11, 17, 32, 0.8)', border: '1px dashed rgba(56, 189, 248, 0.4)', borderRadius: '10px', padding: '1rem', display: 'flex', flexDirection: 'column', gap: '0.85rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <span style={{ fontSize: '0.8rem', fontWeight: 700, color: 'var(--accent-teal)' }}>
                Step 3: {occupation} Specific Damage Parameters
              </span>
              <span className="badge badge-primary" style={{ fontSize: '0.65rem' }}>
                DYNAMIC SUBFORM
              </span>
            </div>

            {/* FARMER FORM */}
            {occupation === 'FARMER' && (
              <>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem' }}>
                  <div>
                    <label className="form-label">Crop Type</label>
                    <select
                      className="form-input"
                      value={cropType}
                      onChange={(e) => setCropType(e.target.value as FarmerCropType)}
                    >
                      <option value="PADDY">Paddy (Rice)</option>
                      <option value="WHEAT">Wheat</option>
                      <option value="SUGARCANE">Sugarcane</option>
                      <option value="MAIZE">Maize</option>
                      <option value="COTTON">Cotton</option>
                      <option value="PULSES">Pulses</option>
                      <option value="VEGETABLES">Horticulture / Vegetables</option>
                      <option value="OTHER">Other Crop</option>
                    </select>
                  </div>
                  <div>
                    <label className="form-label">Damage Severity</label>
                    <select
                      className="form-input"
                      value={damageSeverity}
                      onChange={(e) => setDamageSeverity(e.target.value as DamageSeverity)}
                    >
                      <option value="PARTIAL">Partial Damage (Minor loss)</option>
                      <option value="MAJOR">Major Damage (Severe loss)</option>
                      <option value="COMPLETE">Complete Destruction (100% loss)</option>
                    </select>
                  </div>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '0.75rem' }}>
                  <div>
                    <label className="form-label">Damaged Land Area</label>
                    <input
                      type="number"
                      step="0.1"
                      min="0.01"
                      className="form-input"
                      value={damagedArea}
                      onChange={(e) => setDamagedArea(parseFloat(e.target.value) || 0)}
                    />
                  </div>
                  <div>
                    <label className="form-label">Unit</label>
                    <select
                      className="form-input"
                      value={damagedAreaUnit}
                      onChange={(e) => setDamagedAreaUnit(e.target.value as LandAreaUnit)}
                    >
                      <option value="ACRES">Acres</option>
                      <option value="CENTS">Cents</option>
                    </select>
                  </div>
                </div>

                {/* Indian Land Unit Normalization Notice */}
                <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', display: 'flex', alignItems: 'center', gap: '0.4rem', background: 'rgba(56, 189, 248, 0.08)', padding: '0.5rem', borderRadius: '6px' }}>
                  <Info size={14} color="#38bdf8" />
                  <span>
                    <strong>Land Area Normalization:</strong> 1 Acre = 100 Cents &bull;{' '}
                    {damagedAreaUnit === 'CENTS'
                      ? `${damagedArea} Cents = ${(damagedArea / 100).toFixed(2)} Normalized Acres`
                      : `${damagedArea} Acres = ${damagedArea * 100} Cents`}
                  </span>
                </div>

                <div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', marginBottom: '0.2rem' }}>
                    <span>Estimated Crop Area Affected (%):</span>
                    <strong style={{ color: 'var(--accent-teal)' }}>{affectedPercentage}%</strong>
                  </div>
                  <input
                    type="range"
                    min="10"
                    max="100"
                    step="5"
                    value={affectedPercentage}
                    onChange={(e) => setAffectedPercentage(parseInt(e.target.value))}
                    style={{ width: '100%', accentColor: 'var(--accent-teal)' }}
                  />
                </div>
              </>
            )}

            {/* SHOPKEEPER FORM */}
            {occupation === 'SHOPKEEPER' && (
              <>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem' }}>
                  <div>
                    <label className="form-label">Store / Enterprise Type</label>
                    <select
                      className="form-input"
                      value={storeType}
                      onChange={(e) => setStoreType(e.target.value as ShopStoreType)}
                    >
                      <option value="GROCERY_STORE">Grocery / Provisions Store</option>
                      <option value="CLOTHING_STORE">Clothing / Apparel Shop</option>
                      <option value="ELECTRONICS_STORE">Electronics / Appliances</option>
                      <option value="HARDWARE_STORE">Hardware & Building Supplies</option>
                      <option value="PHARMACY">Pharmacy / Medical Store</option>
                      <option value="RESTAURANT_FOOD">Restaurant / Food Eatery</option>
                      <option value="STATIONERY_STORE">Stationery / Book Store</option>
                      <option value="MOBILE_ACCESSORIES">Mobile & Tech Accessories</option>
                      <option value="AGRI_INPUT_STORE">Agricultural Input Store</option>
                      <option value="OTHER">Other Retail Store</option>
                    </select>
                  </div>
                  <div>
                    <label className="form-label">Damage Category</label>
                    <select
                      className="form-input"
                      value={damageCategory}
                      onChange={(e) => setDamageCategory(e.target.value as ShopDamageCategory)}
                    >
                      <option value="INVENTORY_DAMAGE">Inventory Inundation / Spoilage</option>
                      <option value="PREMISES_DAMAGE">Premises / Structural Ingress</option>
                      <option value="EQUIPMENT_DAMAGE">Refrigeration / Equipment Damage</option>
                      <option value="COMPLETE_STORE_LOSS">Complete Store Destruction</option>
                    </select>
                  </div>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem' }}>
                  <div>
                    <label className="form-label">Estimated Damage Band</label>
                    <select
                      className="form-input"
                      value={inventoryBand}
                      onChange={(e) => setInventoryBand(e.target.value as InventoryDamageBand)}
                    >
                      <option value="BELOW_25K">Below ₹25,000 (Minor)</option>
                      <option value="BAND_25K_50K">₹25,000 – ₹50,000 (Moderate)</option>
                      <option value="BAND_50K_100K">₹50,000 – ₹1,00,000 (Substantial)</option>
                      <option value="ABOVE_100K">₹1,00,000+ (Extensive)</option>
                    </select>
                  </div>
                  <div>
                    <label className="form-label">Damage Severity</label>
                    <select
                      className="form-input"
                      value={damageSeverity}
                      onChange={(e) => setDamageSeverity(e.target.value as DamageSeverity)}
                    >
                      <option value="PARTIAL">Partial Loss</option>
                      <option value="MAJOR">Major Loss</option>
                      <option value="COMPLETE">Complete Loss</option>
                    </select>
                  </div>
                </div>
              </>
            )}

            {/* GENERIC / OTHER OCCUPATIONS FORM */}
            {occupation !== 'FARMER' && occupation !== 'SHOPKEEPER' && (
              <>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem' }}>
                  <div>
                    <label className="form-label">Trade / Work Description</label>
                    <input
                      type="text"
                      className="form-input"
                      value={workType}
                      onChange={(e) => setWorkType(e.target.value)}
                      placeholder="e.g. Construction Daily Labor"
                    />
                  </div>
                  <div>
                    <label className="form-label">Days / Units Disrupted</label>
                    <input
                      type="number"
                      min="1"
                      className="form-input"
                      value={lossQuantity}
                      onChange={(e) => setLossQuantity(parseFloat(e.target.value) || 0)}
                    />
                  </div>
                </div>
                <div>
                  <label className="form-label">Damage Severity Tier</label>
                  <select
                    className="form-input"
                    value={damageSeverity}
                    onChange={(e) => setDamageSeverity(e.target.value as DamageSeverity)}
                  >
                    <option value="PARTIAL">Partial Loss</option>
                    <option value="MAJOR">Major Loss</option>
                    <option value="COMPLETE">Complete Loss</option>
                  </select>
                </div>
              </>
            )}
          </div>

          {/* Validation Error Message */}
          {validationError && (
            <div style={{ background: 'rgba(239, 68, 68, 0.1)', border: '1px solid rgba(239, 68, 68, 0.4)', borderRadius: '8px', padding: '0.75rem', color: '#f87171', fontSize: '0.8rem', display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
              <AlertTriangle size={16} />
              <span>{validationError}</span>
            </div>
          )}

          {/* Calculate Button */}
          <button
            className="btn btn-primary"
            onClick={handleCalculate}
            disabled={calculateMutation.isPending}
            style={{ padding: '0.75rem', fontSize: '0.9rem', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.5rem' }}
          >
            <Calculator size={18} />
            {calculateMutation.isPending ? 'Calculating via Predefined Rules...' : 'Calculate Relief Compensation (Backend Rule Engine)'}
          </button>
        </div>

        {/* Right Column: Calculation Breakdown & Submission */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
          {/* Calculation Breakdown Panel */}
          {calculationResult ? (
            <div className="glass-panel" style={{ border: '1px solid rgba(16, 185, 129, 0.4)', background: 'linear-gradient(135deg, rgba(15, 23, 42, 0.85), rgba(6, 78, 59, 0.15))' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem', borderBottom: '1px solid var(--border-subtle)', paddingBottom: '0.75rem' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <CheckCircle2 size={20} color="#10b981" />
                  <h3 style={{ fontSize: '1.05rem', fontWeight: 700, color: 'var(--text-primary)', margin: 0 }}>
                    Deterministic Calculation Breakdown
                  </h3>
                </div>
                <span className="badge badge-success">
                  {calculationResult.rule_code}
                </span>
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.5rem', fontSize: '0.8rem' }}>
                  <div>
                    <span style={{ color: 'var(--text-secondary)' }}>Applicant:</span>{' '}
                    <strong>{applicantName}</strong>
                  </div>
                  <div>
                    <span style={{ color: 'var(--text-secondary)' }}>Occupation:</span>{' '}
                    <strong>{calculationResult.occupation}</strong>
                  </div>
                  <div>
                    <span style={{ color: 'var(--text-secondary)' }}>Reason:</span>{' '}
                    <strong>{calculationResult.reason}</strong>
                  </div>
                  <div>
                    <span style={{ color: 'var(--text-secondary)' }}>Severity:</span>{' '}
                    <span className="badge badge-primary" style={{ fontSize: '0.65rem' }}>{calculationResult.damage_severity}</span>
                  </div>
                </div>

                {/* Formula Breakdown Card */}
                <div style={{ background: 'rgba(11, 17, 32, 0.9)', border: '1px solid var(--border-subtle)', borderRadius: '8px', padding: '0.85rem' }}>
                  <div style={{ fontSize: '0.7rem', color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.04em', marginBottom: '0.25rem' }}>
                    Mathematical Formula Applied:
                  </div>
                  <div style={{ fontFamily: 'var(--font-mono)', fontSize: '0.95rem', fontWeight: 700, color: 'var(--accent-cyan)' }}>
                    {calculationResult.formula_string}
                  </div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginTop: '0.35rem' }}>
                    Base Rule Rate: <strong>₹{calculationResult.rate_per_unit.toLocaleString()} / {calculationResult.normalized_unit}</strong> &bull; Raw Amount: <strong>₹{calculationResult.raw_calculated_amount.toLocaleString()}</strong>
                  </div>
                </div>

                {/* Cap Applied Notification */}
                {calculationResult.cap_applied && (
                  <div style={{ background: 'rgba(245, 158, 11, 0.1)', border: '1px solid rgba(245, 158, 11, 0.4)', borderRadius: '8px', padding: '0.6rem', color: '#f59e0b', fontSize: '0.75rem', display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                    <ShieldCheck size={16} />
                    <span>
                      <strong>Maximum Payout Cap Applied:</strong> Raw calculation (₹{calculationResult.raw_calculated_amount.toLocaleString()}) exceeded the rule cap of ₹{calculationResult.max_payout_cap.toLocaleString()}.
                    </span>
                  </div>
                )}

                {/* Final Compensation Output */}
                <div style={{ background: 'rgba(16, 185, 129, 0.08)', border: '1px solid rgba(16, 185, 129, 0.3)', borderRadius: '10px', padding: '1rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div>
                    <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
                      Total Assessed Compensation
                    </div>
                    <div style={{ fontFamily: 'var(--font-mono)', fontSize: '1.75rem', fontWeight: 800, color: '#10b981' }}>
                      ₹{calculationResult.final_compensation_amount.toLocaleString()} <span style={{ fontSize: '0.85rem' }}>{calculationResult.currency}</span>
                    </div>
                  </div>
                  <div style={{ textAlign: 'right', fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
                    <div>Rule v{calculationResult.rule_version}</div>
                    <div className="badge badge-teal" style={{ marginTop: '0.25rem' }}>AUDITABLE</div>
                  </div>
                </div>

                <p style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', margin: 0, fontStyle: 'italic' }}>
                  &ldquo;{calculationResult.explanation}&rdquo;
                </p>

                {/* Submit Assessment Button */}
                <button
                  className="btn btn-primary"
                  onClick={handleSubmit}
                  disabled={submitMutation.isPending}
                  style={{ marginTop: '0.5rem', background: 'linear-gradient(135deg, #10b981, #059669)', color: '#ffffff', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.5rem', padding: '0.75rem' }}
                >
                  <Send size={16} />
                  {submitMutation.isPending ? 'Recording in Audit Trail...' : 'Submit Official Assessment & Log to Audit Ledger'}
                </button>
              </div>
            </div>
          ) : lastSubmitted ? (
            <div className="glass-panel" style={{ border: '1px solid rgba(16, 185, 129, 0.4)', textAlign: 'center', padding: '2rem' }}>
              <CheckCircle2 size={44} color="#10b981" style={{ margin: '0 auto 0.75rem' }} />
              <h3 style={{ fontSize: '1.15rem', color: 'var(--text-primary)', marginBottom: '0.25rem' }}>
                Assessment Submitted Successfully!
              </h3>
              <div className="mono-code" style={{ fontSize: '0.9rem', color: 'var(--accent-cyan)', marginBottom: '0.75rem' }}>
                {lastSubmitted.assessment_number}
              </div>
              <div style={{ fontSize: '1.35rem', fontWeight: 800, color: '#10b981', fontFamily: 'var(--font-mono)', marginBottom: '0.75rem' }}>
                ₹{lastSubmitted.calculated_amount.toLocaleString()} INR
              </div>
              <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', maxWidth: '400px', margin: '0 auto 1.25rem' }}>
                Assessment logged into the cryptographic audit trail (<span className="mono-code">DAMAGE_DATA_VALIDATED</span> & <span className="mono-code">COMPENSATION_CALCULATED</span>).
              </p>
              <button
                className="btn btn-secondary"
                onClick={() => {
                  setLastSubmitted(null);
                  handleCalculate();
                }}
              >
                Create Another Assessment
              </button>
            </div>
          ) : (
            <div className="glass-panel" style={{ textAlign: 'center', padding: '3rem 1.5rem', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center' }}>
              <Scale size={44} color="#38bdf8" style={{ opacity: 0.6, marginBottom: '0.75rem' }} />
              <h4 style={{ fontSize: '1.05rem', color: 'var(--text-primary)', marginBottom: '0.35rem' }}>
                Predefined Compensation Preview
              </h4>
              <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', maxWidth: '360px', margin: 0 }}>
                Select your climate reason and occupation, fill in the dynamic parameters, and click <strong>Calculate Relief Compensation</strong> to preview the deterministic breakdown.
              </p>
            </div>
          )}
        </div>
      </div>

      {/* Recent Submitted Assessments Ledger */}
      <div className="section-container" style={{ marginTop: '1.5rem' }}>
        <div className="section-header-row">
          <div>
            <h3 className="section-title">Submitted Damage Assessments Ledger</h3>
            <p className="section-subtitle">
              Audit-verified disaster relief assessments recorded in this demonstration session.
            </p>
          </div>
          <button
            className="btn btn-secondary"
            onClick={() => refetchAssessments()}
            disabled={isFetching}
            style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}
          >
            <RefreshCw size={14} className={isFetching ? 'spin' : ''} />
            Refresh Ledger
          </button>
        </div>

        <div className="table-wrapper">
          <table className="custom-table">
            <thead>
              <tr>
                <th>Assessment Number</th>
                <th>Applicant & Location</th>
                <th>Reason & Occupation</th>
                <th>Specifics & Damage</th>
                <th>Rule Applied</th>
                <th>Formula & Breakdown</th>
                <th>Assessed Amount</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {recentAssessments && recentAssessments.length > 0 ? (
                recentAssessments.map((asm: DamageAssessment) => (
                  <tr key={asm.id}>
                    <td>
                      <span className="mono-code" style={{ fontWeight: 700, color: 'var(--accent-cyan)' }}>
                        {asm.assessment_number}
                      </span>
                    </td>
                    <td>
                      <div style={{ fontWeight: 600, color: 'var(--text-primary)' }}>{asm.applicant_name}</div>
                      <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>{asm.location_name}</div>
                    </td>
                    <td>
                      <span className="badge badge-primary">{asm.occupation}</span>
                      <div style={{ fontSize: '0.7rem', color: 'var(--text-secondary)', marginTop: '2px' }}>
                        {asm.reason_for_applying}
                      </div>
                    </td>
                    <td>
                      {asm.occupation === 'FARMER' && (
                        <div style={{ fontSize: '0.8rem' }}>
                          <strong>{asm.crop_type}</strong> &bull; {asm.damaged_area} {asm.damaged_area_unit} ({asm.normalized_area_acres} Acres)
                        </div>
                      )}
                      {asm.occupation === 'SHOPKEEPER' && (
                        <div style={{ fontSize: '0.8rem' }}>
                          <strong>{asm.store_type}</strong> &bull; {asm.damage_category}
                        </div>
                      )}
                      {asm.occupation !== 'FARMER' && asm.occupation !== 'SHOPKEEPER' && (
                        <div style={{ fontSize: '0.8rem' }}>
                          <strong>{asm.work_type}</strong> &bull; {asm.damage_severity}
                        </div>
                      )}
                    </td>
                    <td>
                      <span className="mono-code" style={{ fontSize: '0.75rem' }}>{asm.rule_code}</span>
                    </td>
                    <td>
                      <div className="mono-code" style={{ fontSize: '0.75rem', color: 'var(--accent-teal)' }}>
                        {asm.calculation_formula}
                      </div>
                    </td>
                    <td>
                      <div style={{ fontWeight: 700, color: '#10b981', fontSize: '0.95rem' }}>
                        ₹{asm.calculated_amount.toLocaleString()} <span style={{ fontSize: '0.7rem' }}>{asm.currency}</span>
                      </div>
                    </td>
                    <td>
                      <span className="badge badge-success">
                        <CheckCircle2 size={10} style={{ marginRight: '4px' }} /> {asm.status}
                      </span>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={8} style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-secondary)' }}>
                    No damage assessments submitted yet. Fill the dynamic form above or click a <strong>Quick Demo Preset</strong> to submit.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
