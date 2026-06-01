We are now moving from the "stochastic" energy source (Solar), which we cannot control, to the "dispatchable" energy source: the **Blockheizkraftwerk (BHKW)** or Combined Heat and Power (CHP) unit. For **ZORO Energy**, this is the "lever" your controller pulls when the sun isn't shining.

### Section 2.2: Blockheizkraftwerk (BHKW / CHP)

**Translated Explanation:**A BHKW is a combustion engine (often powered by natural gas or biogas) that generates electricity via an alternator while capturing the "waste" heat from the engine's cooling jacket and exhaust gases. Guillet models the Energy Factory (EnFa) system, which uses two identical **Viessmann Vitobloc 200** units 1\.  
A CHP is defined by its ability to provide both types of energy simultaneously. In an autonomous building like the EnFa, it acts as the primary backup for the PV system 2, 3\.

### 1\. The Efficiency Equations

To model how much fuel (gas) you need to buy to produce a certain amount of power, you use the following efficiency relationships:  
**Equation (32): Total Efficiency**$$\\eta\_{bhkw} \= \\eta\_{el,bhkw} \+ \\eta\_{th,bhkw}$$  
**Equations (33) & (34): Electrical and Thermal Efficiency**$$\\eta\_{el,bhkw} \= \\frac{P\_{el}}{W\_{br}}$$$$\\eta\_{th,bhkw} \= \\frac{Q\_{Nutz}}{W\_{br}}$$  
**Variable Definitions:**

* $\\eta\_{bhkw}$ %: Total system efficiency.  
* $\\eta\_{el,bhkw}$ %: Electrical efficiency (how much fuel becomes power). 4  
* $\\eta\_{th,bhkw}$ %: Thermal efficiency (how much fuel becomes heat). 4  
* $P\_{el}$ $W\_{el}$: Delivered electrical power. 5  
* $Q\_{Nutz}$ $W\_{th}$: Delivered useful thermal power. 5  
* $W\_{br}$ W: Fuel power (energy input from gas). 5

### 2\. The Fuel Consumption Equation

**Equation (35): Fuel Power Calculation**$$W\_{br} \= \\frac{(m\_{Br,Beginn} \- m\_{Br,Ende})}{t} \\cdot H\_{u}$$

* **$H\_{u}$** $\\frac{kWh}{m^3}$: Lower heating value (Net Calorific Value) of the fuel. 6  
* **Engineering Intuition:** This is critical for your **Cost Optimization Engine**. Since ZORO Energy must optimize for ROI, you need $H\_{u}$ to translate the cubic meters of gas recorded by the meter into the actual energy the building consumed. Biogas has a lower $H\_{u}$ than natural gas, meaning you need more volume for the same power 7\.

### 3\. The Power-to-Heat Ratio (Stromkennzahl)

**Equation (36):**$$s \= \\frac{P\_{el}}{Q\_{Nutz}}$$

* **Physics Explanation:** For every 1 unit of heat produced, a certain amount of electricity is generated. In Guillet’s simplified model, this is treated as a constant **0.512** 8\.  
* **Engineering Intuition:** This "locks" your outputs together. If you need 10kW of heat to warm the building, you *must* produce roughly 5kW of electricity. If the battery is full and the building doesn't need electricity, that 5kW is wasted (curtailment). This is the "balancing act" your **Model Predictive Control (MPC)** must solve.

### 4\. Operating Modes (Section 2.2.1.1.2)

Guillet describes two primary control strategies:

1. **Electricity-led (Stromgeführt):** The BHKW follows the building's electrical demand. Excess heat is dumped or buffered 9\.  
2. **Heat-led (Wärmegeführt):** The BHKW follows the thermal demand. The electricity is treated as a byproduct 3\.

### Engineering Intuition: The "Efficiency Curve"

In reality, a BHKW is **not** equally efficient at all levels. Guillet notes that electrical efficiency drops from **32.2% at full load** to **24.6% at half load** 1\.  
**ZORO Energy Strategy:**Your AI should avoid running the BHKW at "low throttle." It is far more cost-effective to run the engine at **100% load** for one hour to charge the battery and the thermal buffer, and then turn it off for three hours, rather than idling it at 25% load for four hours.

### Implementation Perspective (Python OOP)

In the source code, this was implemented in the BHKWGruppe class 10:

* **Logic:** If one unit cannot meet the demand, the second unit kicks in. If both run, the load is distributed equally 11\.  
* **Equation (37): Total Gas Consumption**$$Gas\_{Menge} \= \\frac{1}{\\eta\_{el\_{BHKW}}} \\cdot kWh\_{el\_{Gesamt}}$$  
* **ZORO Application:** Your cloud platform's **Digital Twin** uses this equation to calculate the "Carbon Footprint" and "Operating Costs" in real-time by pulling gas price data from local utilities.

### Application to ZORO Energy

1. **Supervisory Control Layer:** Your platform sits *above* the Vitogate/BMS 12\. Instead of letting the BMS decide when to turn on the BHKW based on a simple thermostat, ZORO uses the **Solar Forecast** (from your Weather API) to say: *"Don't turn on the BHKW for heat now; the sun will provide enough solar gain in 2 hours. Use the thermal inertia of the floor instead."*  
2. **Predictive Maintenance:** By tracking the Abtauzeit (defrost cycles) and run hours, you can predict when the engine needs an oil change or spark plug replacement before a fault occurs 13\.

### What to study next before moving forward:

Now that we have modeled the **Generation** (Solar \+ BHKW), we must model the **Storage**.  
**Section 2.3: Batteriespeicher (Battery Storage Modeling).**This is the most complex physical model in the thesis because batteries are non-linear. We will look at:

* **SOC (State of Charge)** math 14\.  
* **IUOU Charging Curves** (Constant Current vs. Constant Voltage) 15\.  
* **Efficiency Losses** during conversion 16\.

**Are you ready to model the 400kWh Lead-Gel Battery system (Section 2.3)?**  
