We are now entering the most critical part of your digital twin’s energy balancing act: **The Battery Storage System (Section 2.3)**. In a building like the EnFa (and potentially your ZORO-optimized buildings), the battery is the "buffer" that compensates for the volatility of solar power. 1, 2

### Section 2.3: Batteriespeicher (Battery Storage Modeling)

**Translated Explanation:**The EnFa utilizes a **400kWh lead-gel battery** system consisting of Moll OPzV Solar cells. 1 The system is organized into four parallel strings, each containing 24 cells in series (nominal voltage 2V per cell, 48V per string). 3, 4 These are managed by **SMA Sunny Island** inverters. 3, 5 For your digital twin, modeling the battery requires tracking three states: capacity, voltage behavior, and charging/discharging efficiency. 6

### 1\. State of Charge (SOC) and Capacity Math

To know how much "fuel" is in your electric tank, you must calculate the **SOC**.  
**Equation (38) — State of Charge:**$$SOC=\\frac{Q\_{e}}{Q\_{max}}\\cdot100\\%$$  
**Equation (39) — Current Charge (Coulomb Counting):**$$Q\_{e}=\\int\_{t=0}^{te}I(t)dt$$  
**Equation (40) — Depth of Discharge (DOD):**$$DOD=1-SOC$$

* **Variable Definitions:**  
* $Q\_{e}$ Ah: Current charge quantity. 7  
* $Q\_{max}$ Ah: Maximum extractable capacity (depends on battery health). 7  
* $I(t)$ A: Current flowing into or out of the battery over time. 8  
* **Engineering Intuition:** Equation 39 is "Coulomb Counting." In the real world, batteries don't have a "fuel gauge"; we simply track every electron that goes in or out. However, lead-gel batteries have a **50% maximum depth of discharge (DOD)** to preserve life. 9 This means your "400kWh" battery only provides **200kWh of usable energy** for ZORO’s optimization engine. 10, 11

### 2\. Round-trip Efficiency

Energy is lost as heat during both charging and discharging.  
**Equations (42) & (43):**$$\\eta\_{gesamt,Batt}=\\eta\_{Entl}\\cdot\\eta\_{Lad}$$$$\\eta\_{Entl}=\\eta\_{Lad}$$

* **Engineering Intuition:** Guillet assumes a total efficiency ($\\eta\_{gesamt,Batt}$) of **0.85 (85%)**. 9 This means if you put 100kWh of solar power into the battery, you only get 85kWh back out. 12 Your **Model Predictive Control (MPC)** must account for this 15% loss when deciding whether to store energy or use the BHKW. 13

### 3\. The $IU\_0U$ Charging Procedure

Batteries cannot be charged at a constant rate until full. Lead-gel batteries follow a three-phase curve. 14

1. **Phase 1: Constant Current (I-Phase):** The inverter pushes the maximum allowable current ($I\_{max}$) until the battery reaches the charging voltage. 15  
2. **Phase 2: Constant Voltage ($U\_0$-Phase):** The voltage is held constant while the current drops exponentially as the battery nears 100%. 16  
3. **Phase 3: Float/Maintenance (U-Phase):** A low voltage is held to keep the battery full without overcharging. 17

### 4\. Implementation Perspective: Linearization for Digital Twins

Guillet makes a brilliant simplification for the simulation software (and your ZORO platform): **Linearization**. 14  
**Equation (50) — Time to reach 90% SOC:**$$t\_{1}=\\frac{0.4\\cdot Q\_{nom}}{I\_{max}}$$

* **Logic:** For the EnFa battery, $t\_1$ is calculated as 4 hours. 18  
* **Engineering Intuition:** Real battery physics involves complex non-linear curves. However, for a building simulation with 1-hour time steps, **linearizing the voltage and current curves** (as shown in Guillet's Figures 2-9 to 2-12) provides enough accuracy while saving massive amounts of computational power for your AI. 14, 19, 20

### Application to ZORO Energy

1. **The State-Space State ($x$):** In control theory (Steve Brunton’s Bootcamp), the battery SOC is one of your primary **states**. Your AI must predict how this state changes based on your control inputs (BHKW power) and disturbances (Solar volatility). 13, 21  
2. **Inverter Efficiency Mapping (Equation 58):**$$\\eta\_{Entlad,BattSp}=\\eta\_{Entlad}\\cdot\\eta\_{WR}(P\_{a})$$The efficiency of the **SMA Sunny Island** inverter isn't constant—it peaks at 96% but drops significantly at low power loads. 5, 22 Your ZORO platform should pull the **Inverter Efficiency Vector** (Figure 2-16) to ensure the MPC doesn't discharge the battery at inefficiently low power levels. 23, 24  
3. **Site-Adaptive State of Health (SOH):** Guillet notes that lead batteries are considered "defective" once their capacity drops to **80% SOH**. 25 Your **Predictive Maintenance** engine can use Equation 41 ($SOH=\\frac{Q\_{max}}{Q\_{nom}}\\cdot100\\%$) to track degradation over time and alert the facility manager when the battery needs replacement before it fails. 25

### What to study next before moving forward:

We have now modeled **Solar**, **BHKW**, and **Battery**. We need to look at how we *spend* that energy for climate control.

1. **Section 2.4: Wärmepumpe (Heat Pump Modeling):** We will model the **COP (Coefficient of Performance)** and how temperature dictates electrical demand. 26  
2. **Section 2.5: Energiemanagementsystem (EMS Strategy):** This is the "brain" that connects all our physics models together. 27

**Are you ready to model the Heat Pump and its non-linear COP values (Section 2.4)?**  
