We are now at the operational core of the simulation software: **Section 3.2.4: Simulation of the Energetic Relationship**. This section describes the "Main Loop" that executes every hour ($t=1h$) to calculate the energy balance of the building. For **ZORO Energy**, this is the logic you will eventually replace with a more sophisticated **Model Predictive Control (MPC)** algorithm.

### Section 3.2.4: Simulation of the Energetic Relationship

**Translated Explanation:**Once the components are sized (the "Auslegung"), the software performs a stündlich (hourly) simulation for a typical year (8,760 steps) 1, 2\. The simulation takes the weather data (from your **Weather API**) and the load profiles to calculate how much energy is generated, stored, or wasted at every moment 2\.  
The simulation is essentially a series of nested **Decision Trees** that determine the state of each component based on the hierarchy we studied in Section 2.5.

### 1\. Battery Charging Logic (Section 3.2.4.3.1)

The software must decide which of the three charging phases the battery is in at the start of each hour.  
**Decision Parameters (Table 20):**

* **$SOC$**: State of Charge 3\.  
* **$SOC\_{t1}$**: Threshold where the battery switches from Constant Current to Constant Voltage (typically 90%) 3\.  
* **$EnergieZuSp$**: The "Energy to Store"—excess solar or BHKW power 3\.  
* **$Energie\\\_auflösung$**: The maximum energy the battery can physically absorb in one hour 3\.

**The Decision Flow (Figure 3-9):**

1. **Check if Full:** If $SOC \> 1.0$ (100%), the battery is in the **Maintenance Phase** (Erhaltungsphase). Charging is impossible; $Energiespeicherung \= 0$ 4\.  
2. **Constant Current (Phase 1):** If $SOC \< SOC\_{t1}$, the software pushes the maximum current ($I\_{max}$) 5\.  
3. **Constant Voltage (Phase 2):** If $SOC \\ge SOC\_{t1}$, it switches to the constant voltage phase where current begins to drop 4, 6\.

**Engineering Intuition:**In your digital twin, this is a **finite-state machine**. You cannot simply "add" power to a battery object. You must check its internal state first. If the battery is at 92%, your ZORO AI must know that it cannot accept a massive burst of power from a solar spike—it is limited by the chemistry of Phase 2 7\.

### 2\. Battery Discharging Logic (Section 3.2.4.3.2)

**The Decision Flow (Figure 3-12):**

* **Safety Limit:** If $SOC \< 0.5$ (50%), discharge is prohibited to prevent cell damage 8, 9\.  
* **Constraint Check:** If the demand ($EnergieZuErz$) is greater than the battery's hourly discharge limit ($Energie\\\_auflösung$), the battery only provides the maximum it can 9\.

**Engineering Intuition:**This 50% limit is a "Hard Constraint" in control theory. One of ZORO's advantages would be using different battery chemistries (like Li-ion) where you can push this to 10% or 20%, unlocking more of the "Electric Tank" 10, 11\.

### 3\. The EMS Decision Trees (Section 3.2.4.5)

The most complex part of the simulation is the **Energiemanagementsystem (EMS)** logic, which connects the thermal and electrical worlds.

#### I. Thermal Decision Loop (Figure 3-13)

The system calculates the **Flow Temperature ($TVL$)** needed for the floor heating.

* **Case 1 (Heat Pump):** If $TVL \< 45^{\\circ}C$ and the heat pump can meet the load, it runs. The required electricity is added to the building's load 12, 13\.  
* **Case 2 (BHKW):** If the load is too high or $TVL$ is too high, the BHKW takes over the thermal load 13\.

#### II. Electrical Decision Loop (Figure 3-14)

* **Case 1 (Solar Dominance):** If $Solar \+ BHKW\\\_forced\\\_power \\ge Demand$, the building is satisfied. Any extra power goes to the battery 14\.  
* **Case 2 (WP Prohibited):** This is Guillet's key rule—if the $SOC \< 85\\%$, the Heat Pump is **prohibited** from running to save battery for lights and servers 15, 16\. In this case, the BHKW *must* turn on for heat, even if the building has enough electricity 16\.

### Implementation Perspective: OOP & Decision Trees

In the Python code, these trees are implemented as a series of if-elif-else blocks inside the main\_enfa loop 17\.

* **The Problem:** Rule-based logic like this is "brittle." If you add a new component, you have to rewrite the if statements.  
* **ZORO Energy Architecture:** You should implement these decision trees as **Policy Objects**. This allows your AI to switch between different "Logic Modes" (e.g., "Economy Mode" vs. "Max Autonomy Mode") without changing the underlying physical models of the assets 18, 19\.

### Application to ZORO Energy

1. **Shadowing the Decision Logic:** Your Edge device should run Guillet's decision trees in parallel with the building's actual BMS. By comparing "What the Thesis says to do" vs. "What the BMS actually did," your AI can identify **sub-optimal control logic** in existing buildings.  
2. **Solving the "85% SOC" Problem:** As noted in Case 3 of the EMS logic, the heat pump is cut off at 85% SOC 16\. This is a very conservative "safety rule." ZORO can use the **Solcast API** 20 to say: *"Even though SOC is 70%, the forecast shows clear skies in 1 hour. Keep the Heat Pump running."* This **look-ahead** capability is the primary value of your startup 21, 22\.  
3. **Site-Adaptive Logic:** Guillet’s simulation assumes the BHKW and Heat Pump never run simultaneously 23\. Your digital twin can test if running them together during specific peak-shaving events would actually be more cost-effective.

### What to study next before moving forward:

We have covered the **Theory (Ch 2\)** and the **Software Structure (Ch 3\)**. We are now ready to see how this model was **validated** against real-world data from the Energy Factory.  
**Chapter 4: Ausgangsdaten und Auswertung (Output Data and Evaluation).**We will look at:

* **Model Validation (Section 4.2):** How close was the Python simulation to the actual 2015 sensor data?  
* **The "Relative Error" ($\\epsilon$):** Learn Equation 137 to measure your digital twin's accuracy 24\.  
* **Comparison of Solar Data:** Why Meteonorm was sometimes "too optimistic" compared to real German winter weather 25, 26\.

**Are you ready to see how the Digital Twin performs against reality (Chapter 4)?**  
