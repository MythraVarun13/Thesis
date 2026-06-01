Moving from the storage of energy to its consumption, we now focus on the primary thermal engine of the building: the **Heat Pump (Section 2.4)**. For **ZORO Energy**, modeling this is crucial because the Heat Pump is often the largest and most complex electrical load in a commercial building. Its efficiency is not a fixed number; it is a **dynamic variable** that changes every hour based on the weather.

### Section 2.4: Wärmepumpe (Heat Pump Modeling)

**Translated Explanation:**The EnFa system uses three identical **Stulz AquaBox FDSW-V** air-to-water heat pumps 1\. These units are "reversible," meaning they provide heating in the winter and cooling in the summer 1\. To model them accurately, we must account for the fact that their efficiency depends on two factors: the **Outdoor Temperature** and the **Flow Temperature** (the temperature of the water sent into the floor heating system) 2\.

### 1\. The Performance Equations (COP & EER)

Efficiency in heat pumps is measured by the ratio of "thermal energy moved" to "electricity consumed."  
**Equation (63) — Coefficient of Performance (Heating):**$$COP=\\frac{P\_{th}}{P\_{el}}$$  
**Equation (64) — Energy Efficiency Ratio (Cooling):**$$ERR=\\frac{P\_{kälte}}{P\_{el}}$$  
**Equation (65) — Electrical Demand Calculation:**$$P\_{el,wp}=\\frac{P\_{th,wp}}{COP}$$  
**Variable Definitions:**

* $P\_{th} W\_{th}$: Thermal power generated for heating 3\.  
* $P\_{kälte} W\_{th}$: Thermal power generated for cooling 3\.  
* $P\_{el} W\_{el}$: Electrical power consumed by the compressor and fans 3\.  
* **Engineering Intuition:** A COP of 3.6 means that for every **1 kW** of electricity you pay for, you get **3.6 kW** of heat for "free" from the outside air 2, 3\. However, as it gets colder outside, the COP drops because the heat pump has to work harder to extract heat from freezing air.

### 2\. The Heating Curve (Heizkurve)

The **Flow Temperature ($TVL$)** is the temperature of the water circulating in the building's pipes. To save energy, we don't always run the water at the maximum temperature. Instead, we use a **Heating Curve** 4\.

* **Logic:** When it is $-10^\\circ C$ outside, you might need $45^\\circ C$ water. When it is $+10^\\circ C$ outside, you might only need $25^\\circ C$ water 4\.  
* **The Slope (Steigung):** Guillet uses a slope of **0.5** 5, 6\. A lower slope indicates a better-insulated building (like the EnFa) because the building requires less "heat punch" as the temperature drops 5\.

### 3\. Implementation Perspective: Non-Linear Mapping

In your ZORO platform, you cannot treat COP as a constant. Guillet handles this via **Linear Interpolation** 6\.

* **The Problem:** Data sheets only provide COP values for specific points (e.g., at $-7^\\circ C$ and $+2^\\circ C$) 7\.  
* **The Solution:** The WP (Heat Pump) class in the code includes a wpDaten dictionary 8, 9\. Your algorithm must look up the current outdoor temperature from your **Weather API**, calculate the required flow temperature from the heating curve, and then **interpolate** the COP between the nearest data points in the data sheet 10\.

### Application to ZORO Energy

1. **Load Forecasting:** By integrating your **Weather API** (e.g., Open-Meteo) with Equation 65, ZORO can predict exactly how many **kWh of electricity** the building will need tomorrow morning at 8:00 AM 11, 12\. If the forecast shows a cold snap, your AI knows the COP will drop, and electrical demand will spike.  
2. **The ZORO "Site-Adaptive" IP:** As noted in the Layered Weather Architecture source, your AI can learn the **real-world COP** of the building 13, 14\. If the data sheet says the COP should be 3.5, but telemetry shows it is 2.8, your **Predictive Maintenance** engine can flag a "Refrigerant Leak" or "Dirty Heat Exchanger" before the system fails.  
3. **Advanced Control (Section 2.5 Preview):** In Guillet's model, the Heat Pump is **prohibited** from running if the battery SOC is below **85%** 15\. For ZORO, your **Model Predictive Control (MPC)** can be smarter: if the Weather API predicts high solar gain in 2 hours, the MPC might allow the battery to dip to 70% to start pre-heating the building now, knowing the solar "recharge" is coming.

### What to study next before moving forward:

We have modeled the **Physics** (Solar, BHKW, Battery, Heat Pump). Now we must study the **Logic** that ties them all together.  
**Section 2.5: Energiemanagementsystem (EMS Strategy).**This section describes the "Rules of Engagement" for the building:

* **Prioritization:** Which source runs first? (Solar \> Battery \> BHKW) 16\.  
* **Thermal vs. Electrical Coupling:** How the BHKW acts as a backup for both heat and power 15\.  
* **Droop-Mode:** How the system handles sudden frequency and voltage changes in off-grid mode 17, 18\.

**Are you ready to dive into the EMS Control Logic (Section 2.5)?**  
