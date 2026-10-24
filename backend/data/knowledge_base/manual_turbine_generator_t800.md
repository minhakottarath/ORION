# MAN-T800: Industrial Gas Turbine Generator Maintenance Manual
**Equipment Model:** Orion Dynamics Titan-800 Heavy-Duty Industrial Gas Turbine (50 MW)
**Section 8:** Vibration Diagnostics, Bearing Temperatures, and Lube Oil System

---

## 8.1 Critical Operational Thresholds
| Parameter | Normal Range | Alert / Alarm Level | Trip / Emergency Shutdown |
| :--- | :--- | :--- | :--- |
| Bearing #1 Vibration (Radial X/Y) | 1.2 - 2.8 mm/s RMS | > 4.5 mm/s RMS | > 7.1 mm/s RMS |
| Bearing #2 Vibration (Thrust) | 0.8 - 2.0 mm/s RMS | > 3.8 mm/s RMS | > 6.5 mm/s RMS |
| Journal Bearing Temperature | 65°C - 82°C | > 95°C | > 110°C |
| Lube Oil Supply Pressure | 2.8 - 3.2 bar | < 2.0 bar | < 1.4 bar |
| Lube Oil Supply Temperature | 42°C - 48°C | > 55°C | > 62°C |
| Turbine Exhaust Gas Temp (EGT) | 540°C - 580°C | Spread > 35°C | Spread > 55°C |

---

## 8.2 Vibration Spectrum Diagnosis & Root Cause Guide

### Pattern A: 1X RPM Dominant Peak (Sub-Synchronous or 1st Harmonic)
- **Probable Root Cause:** Rotor mass unbalance caused by compressor blade fouling, turbine deposit spallation, or thermal bow.
- **Remedy:**
  1. Perform off-line compressor water wash (Standard Wash Procedure Section 4.3).
  2. Inspect inlet guide vanes (IGVs) for foreign object damage (FOD) or particulate erosion.
  3. If vibration persists after wash, execute single-plane or two-plane dynamic trim balancing using Bently Nevada 3500 rack data.

### Pattern B: 2X RPM Dominant Peak (Double Frequency)
- **Probable Root Cause:** Shaft misalignment between turbine output shaft and reduction gearbox, or loose coupling diaphragm bolts.
- **Remedy:**
  1. Check cold alignment offsets using dial gauges or laser alignment kit (Part #ALIGN-OPT-02).
  2. Verify thermal growth compensation values (Gearbox vertical rise: +0.45 mm, Turbine forward rise: +0.72 mm).
  3. Check torque on coupling spacer bolts (Target torque: 185 Nm with Loctite 271).

### Pattern C: Non-Synchronous Sub-Harmonic (0.43X to 0.48X RPM)
- **Probable Root Cause:** Oil Whirl / Oil Whip in hydrodynamic tilt-pad journal bearings.
- **Remedy:**
  1. Verify lube oil viscosity (ISO VG 32 synthetic turbine oil required; minimum viscosity index: 140).
  2. Check lube oil supply temperature. Cold oil (<35°C) increases viscosity and induces hydrodynamic oil whirl.
  3. Inspect bearing pad clearances using plastigauge (Permissible radial clearance: 0.12 mm - 0.18 mm). Replace worn pads if clearance exceeds 0.24 mm.

---

## 8.3 Emergency Response Protocol: High Vibration Alarm (>4.5 mm/s)
1. **Reduce Load:** Immediately derate generator output by 30% (from 50 MW to 35 MW) and observe vibration trend over 3 minutes.
2. **Monitor Bearing Metal Temperatures:** If Bearing #1 temperature rises by >2°C per minute, initiate controlled fired shutdown sequence.
3. **Do Not Restart Hot:** If unit trips on high vibration, engage turning gear mechanism (slow roll at 6 rpm for minimum 24 hours) to prevent rotor sag/permanent thermal deformation.
