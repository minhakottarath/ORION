# INC-2024-88: Plant Incident Investigation Report
**Incident ID:** INC-2024-88 | **Severity:** High (Unplanned Unit Derate)
**Facility:** Block 2 Boiler Feedwater Pumphouse | **Asset:** Boiler Feed Pump BFP-02B (Sulzer Multi-Stage)
**Date:** 2024-08-14 | **Lead Investigator:** Senior Reliability Engineer M. Vance

---

## 1. Incident Description and Timeline
At 04:12 AM, BFP-02B experienced acoustic crackling sounds described by operators as "gravel or marbles rattling inside the pump casing".
- **04:15 AM:** Drive-end (DE) bearing vibration escalated from 1.4 mm/s to 5.8 mm/s.
- **04:18 AM:** Deaerator storage tank level dropped from 65% to 42%, causing suction pressure to plunge from 4.2 bar to 1.8 bar.
- **04:22 AM:** Net Positive Suction Head Available (NPSHa) fell below Net Positive Suction Head Required (NPSHr: 2.6 bar), initiating severe cavitation.
- **04:30 AM:** Mechanical seal barrier fluid pressure dropped to zero, resulting in tandem mechanical seal failure and hot feedwater leakage (145°C).

---

## 2. Root Cause Analysis (RCA) - 5-Whys Methodology
1. **Why did mechanical seal leak?** -> Silicon carbide face cracked due to thermal shock and dry running.
2. **Why did seal faces dry run?** -> Vapor pocket formed in pump suction eye from cavitation bubbles collapsing against the impeller vanes.
3. **Why did cavitation occur?** -> Suction pressure dropped below vapor pressure of 145°C water (approx 4.15 bar absolute).
4. **Why did suction pressure drop?** -> Suction basket strainer STR-02B was 85% blinded with magnetite scale dislodged from upstream economizer piping.
5. **Why was strainer blinded?** -> Scheduled quarterly strainer differential pressure (DP) inspection was deferred during the previous PM cycle.

---

## 3. Corrective and Preventive Actions (CAPA)
1. **Immediate Maintenance Action:**
   - Dismantled suction strainer STR-02B; removed 4.2 kg of oxidized iron debris.
   - Installed replacement John Crane Type 5620P dual cartridge seal with Plan 53A barrier fluid reservoir.
   - Performed ultrasonic thickness testing on suction elbow; verified wall thickness remains within safety limits (>9.5 mm).
2. **Mandatory Operating Rule (Added to SOP-BFP-01):**
   - High DP Alarm on Suction Strainer DP > 0.35 bar must trigger automated pump transfer to standby unit BFP-02A.
   - Technicians must never bypass strainer DP interlocks during load ramps.
   - Minimum NPSH margin of at least 1.5 meters must be maintained at all times.
