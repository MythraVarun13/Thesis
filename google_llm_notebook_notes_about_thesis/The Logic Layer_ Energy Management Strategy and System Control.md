We are now moving into the "Brain" of the building. Having modeled the individual physical components, we must now define the logic that orchestrates them. This is the **Energiemanagementsystem (EMS)**. For **ZORO Energy**, this section is the most important as it represents the "Logic Layer" your AI will eventually supersede with **Model Predictive Control (MPC)**.

### Section 2.5: Energiemanagementsystem (EMS Strategy)

**Translated Explanation:**The EMS is designed to optimally cover both the electrical and thermal demands of the building. Guillet defines a clear **hierarchy of sources** based on operating costs (fuel is expensive, sun is free). In the Energy Factory (EnFa), the system must constantly balance supply and demand without a grid connection, managing technical limits like battery state-of-charge (SOC) and device modulation ranges 1, 2\.

### 1\. The Hierarchy of Energy Generation

The EMS operates on a strict priority list to minimize the use of the BHKW (which requires purchased biogas) 2:  
**Electrical Priority:**

1. **Photovoltaic System:** Use free solar first.  
2. **Battery Storage:** Use stored energy when solar is insufficient.  
3. **BHKW (CHP):** Turn on the engine only as a last resort.

**Thermal Priority:**

1. **Heat Pump:** Primary heat source (uses electricity, ideally solar/battery).  
2. **BHKW (CHP):** Secondary heat source (used when it is too cold for the heat pump or when electricity is also needed).

**The "Coupling" Constraint:**Because the BHKW is a CHP unit, it produces electricity and heat simultaneously. If the BHKW runs to meet heat demand, it *must* produce electricity. If the battery is full and there is no load, this electricity is "excess." Conversely, if it runs for electricity, the excess heat is stored in a **thermal buffer** 2, 3\.

### 2\. Technical Thresholds (The Control Rules)

Guillet implements several "Hard Rules" in the simulation logic that are critical for your digital twin 3, 4:

* **Heat Pump Prohibited Zone:** The heat pump will **not run** if the Battery SOC is **below 85%**. This preserves the battery for critical building loads (lights, servers) rather than thermal comfort 3, 5\.  
* **Operating Range:** The BHKW and Heat Pump have minimum and maximum modulation limits. If the demand is below the minimum, the device runs at "Min" and stores the excess; if above "Max," the next device in the hierarchy kicks in 4, 6\.  
* **Temperature Cut-off:** The heat pump is deactivated below **$-5^\\circ C$** outside because its COP (efficiency) becomes too low to justify the electrical drain 7\.

### 3\. Handling Excess Energy: The "Droop-Mode"

When the battery is full and solar generation exceeds demand, the system must prevent overvoltage. The EnFa uses the **SMA "Droop-Mode"** (SelfSync®) 8\.  
**Control Logic:**

* **Frequency Droop:** As power supply exceeds demand, the inverters slightly increase the grid frequency (e.g., from 50Hz to 51Hz) 9, 10\.  
* **Response:** The PV inverters detect this frequency rise and automatically **curtail (Abregelung)** their output power to maintain stability 9\.

### Engineering Intuition: "The Conflict of Coupling"

The hardest part of building EMS logic is the **Thermal-Electrical Coupling**.

* **Scenario:** It’s a freezing winter night. The building needs 30kW of heat. The battery is at 90% SOC.  
* **Logic Conflict:** The Heat Pump could provide heat, but it would drain the battery rapidly. The BHKW could provide heat, but it would produce "forced" electricity that the battery might not have room to store.  
* **Guillet's Solution:** The simulation resolves this stündlich (hourly) by checking thermal demand first, then adjusting electrical generation/storage to fit 7, 11\.

### Implementation Perspective: The Decision Tree

In the Python code, this is implemented as a series of nested if/else statements within the Energiemanagementsystem function 12\.

* **Thermal Module:** Calculates waermeWP and bhkwWaerme based on outdoor temperature and the **Heizkurve** (Heating Curve) 7, 13\.  
* **Electrical Module:** Calculates solarStrom and battStrom. If solar \+ bhkw\_forced\_power \< demand, it discharges the battery 14, 15\.  
* **Buffer Logic:** If waermeErz \> waermeBedarf, the excess is "stored" for the next hour's calculation 16, 17\.

### Application to ZORO Energy

1. **From Heuristics to Optimization:** Guillet uses "Rule-Based Control" (e.g., "If SOC \< 85%, Stop HP"). Your ZORO platform will use **Model Predictive Control (MPC)**. Instead of a hard 85% limit, your AI will look at the **Weather API forecast** 18, 19\. If it knows the sun will shine in 2 hours, it might allow the battery to drop to 60% to run the heat pump now.  
2. **Supervisory Layer (The ZORO Edge):** Your hardware connects to the **Vitogate 300** and **SMA Modbus** interfaces 20, 21\. You don't replace the SMA Droop-Mode (which handles millisecond-level stability); you replace the **hourly strategy** to maximize ROI and minimize gas consumption 22, 23\.  
3. **Site-Adaptive IP:** By tracking the Wärmeüberschuss (thermal excess), ZORO learns the **Thermal Inertia** of the building 19\. This allows you to "pre-heat" or "pre-cool" the building mass, essentially using the concrete floors as a secondary battery.

### What to study next before moving forward:

We have completed **Chapter 2 (Physics & Logic)**. We are now ready to look at the **Business Case** that makes ZORO Energy viable.  
**Section 2.6: Kosten der Anlage (System Costs & LCOE).**This is where Guillet calculates the **Price per kWh** for an autonomous building. We will look at:

* **Investitionskosten (CAPEX):** PV, BHKW, and Battery costs 24, 25\.  
* **Abschreibung (Depreciation):** How to model equipment replacement over 20 years 26, 27\.  
* **Competitive Analysis:** Why the EnFa electricity (18.8 Cent/kWh) was cheaper than the German grid (29.1 Cent/kWh) in 2015 28, 29\.

**Are you ready to dive into the Economics and kWh pricing (Section 2.6)?**  
