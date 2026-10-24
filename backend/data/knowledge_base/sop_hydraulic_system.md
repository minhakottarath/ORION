# SOP-702: Hydraulic Power Unit (HPU) Pressure Fluctuation Troubleshooting
**Standard Operating Procedure | Revision: 4.2 | Safety Class: Level 2 Industrial Hazard**
**Target Equipment:** HPU Series-900, Proportional Relief Valve PRV-12, Bladder Accumulators ACC-1/ACC-2

---

## 1. Safety and Pre-Inspection Requirements
> **CRITICAL SAFETY WARNING:**
> Before servicing any hydraulic components, technicians must:
> 1. Perform Lockout/Tagout (LOTO) on Primary Motor Breaker 480V (Panel MCC-3, Breaker 14B).
> 2. Manually relieve residual circuit pressure by opening Manual Bleed Valve BV-1 until system gauge PG-1 reads **0.0 bar (0.0 PSI)**.
> 3. Verify accumulator nitrogen pre-charge isolation. Pressurized hydraulic fluid injection hazard (skin puncture risk).
> 4. Wear safety glasses, face shield, and chemical-resistant nitrile gloves.

---

## 2. Symptom Identification: Pressure Oscillations
If system pressure gauge PG-1 fluctuates between 140 bar and 210 bar (normal operating pressure: 180 ± 5 bar):
- **Symptom A: Rapid needle jitter (>10 Hz)**: Indicates cavitation, aeration in pump inlet, or defective proportional relief valve pilot stage.
- **Symptom B: Slow cyclical pressure surge (0.2 Hz to 1 Hz)**: Indicates accumulator bladder rupture or loss of nitrogen pre-charge.
- **Symptom C: Gradual pressure decay under load**: Indicates directional valve spool bypass or internal pump displacement piston slippage.

---

## 3. Diagnostic & Corrective Action Sequence

### Step 1: Accumulator Pre-Charge Verification
1. Connect Nitrogen Charging Kit (Part #NCK-44) to Schrader valve on Accumulator ACC-1.
2. Read pre-charge pressure:
   - **Nominal Pre-Charge:** 110 bar at 20°C ambient.
   - If pre-charge is <70 bar: Recharge with dry Nitrogen (N2) only. Never use oxygen or compressed air (explosion hazard).
   - If hydraulic oil emerges from Schrader valve: Accumulator bladder is ruptured. Replace bladder kit (Part #BLD-900-K).

### Step 2: Proportional Relief Valve (PRV-12) Inspection
1. Inspect solenoid coil resistance across pins A and B:
   - **Normal Resistance:** 18.5 Ω to 22.0 Ω at 25°C.
   - If open circuit or <5 Ω, replace solenoid coil (Part #COIL-PRV-24V).
2. Check 4-20mA control signal from PLC Output Module Q4:
   - At 0 bar demand: 4.0 mA.
   - At 180 bar setpoint: 16.8 mA.
3. Remove and inspect PRV-12 pilot orifice for particulate contamination. Flush with solvent and ultrasonic bath if varnish buildup is detected.

### Step 3: Hydraulic Fluid Condition & Suction Strainer
1. Inspect oil sight glass on reservoir RES-1. If oil is milky/cloudy, water ingress has exceeded 500 ppm limit. Initiate offline centrifugal dehydration.
2. Check suction filter differential pressure indicator DP-1. If indicator is in RED zone, replace 10-micron suction element (Part #FLT-10M-HPU).

---

## 4. Verification and Return-to-Service Checklist
- [ ] Bleed valve BV-1 fully closed and torqued to 35 Nm.
- [ ] LOTO removed according to plant safety protocol.
- [ ] Motor jog test performed (verify clockwise rotation on pump shaft).
- [ ] Run HPU at idle (30 bar) for 5 minutes; inspect for external leaks at SAE flanges.
- [ ] Ramp to 180 bar setpoint. Confirm pressure stability within ±2.5 bar for 15 minutes continuous operation.
