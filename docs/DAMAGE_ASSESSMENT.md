# Risk2Relief: Dynamic Damage Assessment & Predefined Compensation Filter Engine

---

## 1. Overview & Purpose

In parametric climate insurance, automated payouts are triggered when external verifiable metrics (such as rainfall, wind speed, or temperature) cross predetermined risk thresholds. However, different victims—such as smallholder farmers, local shopkeepers, and daily wage workers—experience heterogeneous losses during the same macro climate event.

The **Damage Assessment & Dynamic Filter Engine** provides a structured, deterministic mechanism to:
1. Capture victim profile data (Climate Event Reason, Occupation).
2. Dynamically adapt input forms to occupation-specific damage characteristics.
3. Normalize non-standard regional units (such as Indian land cents to standard acres: $1\text{ acre} = 100\text{ cents}$).
4. Select auditable, predefined compensation rules and evaluate payouts via deterministic mathematical formulas.
5. Enforce strict backend maximum payout caps to safeguard liquidity.
6. Record every assessment step in the sequential decision audit trail.

> **CRITICAL INVARIANT: ZERO ML / LLM FINANCIAL AUTHORITY**
> Machine learning models and Large Language Models are **never** permitted to determine compensation values, approve claims, or execute payouts. All financial calculations are 100% deterministic and auditable.

---

## 2. High-Level User Flow

```
[ Beneficiary / Claimant ]
           │
           ▼
1. Select Reason for Applying (Flood, Cyclone, Extreme Rainfall, Extreme Heat, Drought)
           │
           ▼
2. Select Occupation (Farmer, Shopkeeper, Daily Wage Worker, etc.)
           │
           ▼
3. Dynamic Subform Renders (Crop & Land Area for Farmer; Store Type & Inventory Band for Shopkeeper)
           │
           ▼
4. Enter Damage Specifics & Land Units
           │
           ▼
5. Backend Pre-flight Calculation (/api/v1/damage-assessments/calculate)
   - Schema & Range Validation
   - Indian Land Unit Normalization (Cents -> Acres)
   - Predefined Rule Selection
   - Formula Evaluation & Max Payout Cap Enforcement
           │
           ▼
6. Interactive Breakdown Displayed (Rule Code, Rate, Formula, Cap Notice, Final Compensation)
           │
           ▼
7. Submit Official Assessment (/api/v1/damage-assessments)
   - Generates Unique Assessment ID (ASM-2026-XXXXXX)
   - Appends to Immutable Decision Audit Trail
```

---

## 3. Dynamic Filter Hierarchy

### Filter 1: Reason for Applying
Controlled enum:
- `FLOOD`: Riverine inundation, urban flash flooding.
- `CYCLONE`: Severe tropical storm, high wind damage.
- `EXTREME_RAINFALL`: Precipitation exceeding localized 24-hour thresholds.
- `EXTREME_HEAT`: Extended temperatures exceeding human/crop survivability limits.
- `DROUGHT`: Soil moisture depletion and precipitation deficits.
- `OTHER`: Unforeseen acute climatic disruptions.

### Filter 2: Occupation (Parent Dynamic Filter)
When the user switches occupation, non-applicable inputs are cleanly reset and hidden:

| Occupation | Dynamic Fields Rendered | Validation Rules |
| :--- | :--- | :--- |
| **`FARMER`** | Crop Type, Damaged Area, Land Unit (`ACRES`/`CENTS`), Damage Severity, Affected % | Area must be $> 0.0$ and $\le 10,000.0$. Crop type is mandatory. |
| **`SHOPKEEPER`** | Store Type, Damage Category, Inventory Damage Band, Damage Severity | Store type and damage category are mandatory. |
| **`DAILY_WAGE_WORKER`** | Trade / Work Description, Days / Units Lost, Damage Severity | Days disrupted must be $\ge 1$. |
| **`STREET_VENDOR`** | Cart / Kiosk Asset Type, Damage Severity | Asset disruption recorded. |
| **`FISHER`** | Boat / Net Equipment Type, Damage Severity | Gear disruption recorded. |
| **`SMALL_BUSINESS`** | Enterprise Type, Facility Ingress Tier | Commercial tier evaluated. |
| **`OTHER`** | Trade Description, Units Disrupted | Fallback general relief tier. |

---

## 4. Land Unit Normalization (Indian Measurement Standards)

In many agricultural regions across India, land is measured in **Cents** alongside **Acres**:
$$1\text{ Acre} = 100\text{ Cents} \implies \text{Acres} = \frac{\text{Cents}}{100}$$

The backend `DamageCompensationService.normalize_land_area()` function guarantees deterministic normalization:
- **Input:** $250.0\text{ Cents}$
- **Stored Values:**
  - `damaged_area` = $250.0$
  - `damaged_area_unit` = `CENTS`
  - `normalized_area_acres` = $2.50$
- **Calculation Formula:** `(250.0 Cents ÷ 100 = 2.5 Acres) × ₹10,000/acre = ₹25,000`

---

## 5. Predefined Compensation Rule Engine & Formulas

### Sample Rule Registry

| Rule Code | Occupation | Target Subtype | Severity | Calculation Type | Rate | Unit | Max Payout Cap |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `FARMER_PADDY_MAJOR_V1` | `FARMER` | `PADDY` | `MAJOR` | `PER_UNIT` | ₹10,000 | `ACRES` | ₹50,000 |
| `FARMER_PADDY_COMPLETE_V1` | `FARMER` | `PADDY` | `COMPLETE`| `PER_UNIT` | ₹15,000 | `ACRES` | ₹60,000 |
| `FARMER_WHEAT_MAJOR_V1` | `FARMER` | `WHEAT` | `MAJOR` | `PER_UNIT` | ₹9,000 | `ACRES` | ₹45,000 |
| `FARMER_SUGARCANE_MAJOR_V1`| `FARMER` | `SUGARCANE` | `MAJOR` | `PER_UNIT` | ₹12,000 | `ACRES` | ₹60,000 |
| `SHOP_GROCERY_INVENTORY_MAJOR_V1` | `SHOPKEEPER`| `GROCERY_STORE` | `MAJOR` | `FIXED_TIER` | ₹30,000 | `STORE_UNIT` | ₹45,000 |
| `SHOP_CLOTHING_INVENTORY_MAJOR_V1`| `SHOPKEEPER`| `CLOTHING_STORE`| `MAJOR` | `FIXED_TIER` | ₹35,000 | `STORE_UNIT` | ₹50,000 |
| `SHOP_ELECTRONICS_INVENTORY_MAJOR_V1`| `SHOPKEEPER`| `ELECTRONICS_STORE`| `MAJOR` | `FIXED_TIER` | ₹45,000 | `STORE_UNIT` | ₹60,000 |
| `DAILY_WAGE_HEAT_MAJOR_V1` | `DAILY_WAGE_WORKER`| `GENERAL` | `MAJOR` | `PER_UNIT` | ₹800 | `DAYS` | ₹15,000 |
| `STREET_VENDOR_FLOOD_MAJOR_V1`| `STREET_VENDOR`| `GENERAL` | `MAJOR` | `FIXED_TIER` | ₹15,000 | `CART_UNIT` | ₹20,000 |
| `FISHER_CYCLONE_MAJOR_V1` | `FISHER` | `GENERAL` | `MAJOR` | `FIXED_TIER` | ₹25,000 | `BOAT_NET` | ₹40,000 |

### Formula & Cap Enforcement
$$\text{RawAmount} = \text{Rate} \times \text{NormalizedQuantity} \times \frac{\text{AffectedPercentage}}{100}$$
$$\text{FinalCompensation} = \min(\text{RawAmount}, \text{MaxPayoutCap})$$

Example of Cap Protection:
- Farmer with $10\text{ Acres Paddy}$ at $₹10,000/\text{acre} \rightarrow \text{Raw} = ₹100,000$.
- Rule Max Cap = $₹50,000$.
- Backend enforces: `Final Compensation = ₹50,000.00 INR [Capped at Max Limit ₹50,000]`.

---

## 6. REST API Reference

- `POST /api/v1/damage-assessments/calculate`: Preview deterministic compensation breakdown without persisting records.
- `POST /api/v1/damage-assessments`: Validate, calculate, log to audit trail, and persist assessment record.
- `GET /api/v1/damage-assessments`: List all submitted assessments.
- `GET /api/v1/damage-assessments/{id}`: Retrieve single assessment by UUID.
- `GET /api/v1/damage-rules`: List all active compensation rules.
- `GET /api/v1/damage-rules/{rule_code}`: Retrieve rate configuration for a specific rule.

---

## 7. Audit Trail Integration

When a damage assessment is submitted, the system appends two immutable lifecycle stages to `ClimateAuditTrailService`:
1. `DAMAGE_DATA_VALIDATED`: Records input validation, applicant metadata, and parsed parameters.
2. `COMPENSATION_CALCULATED`: Records rule code, formula applied, raw calculation, and cap enforcement status.
