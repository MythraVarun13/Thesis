We are now moving from the theoretical physics of the building into the **Software Architecture (Chapter 3\)**. This is where Guillet translates the equations we’ve studied into a functional "Digital Twin." For **ZORO Energy**, this chapter serves as the structural blueprint for your cloud platform and edge logic.

### Section 3.1 & 3.2.1: Object-Oriented Architecture (OOP)

**Translated Explanation:**The software is developed in **Python** because of its extensive libraries and industrial applicability 1\. Guillet uses **Object-Oriented Programming (OOP)** to represent the physical building components as digital objects 2\. This allows the system to be extensible—new components (like a wind turbine) can be added without rewriting the core engine 2\.  
**The Class Hierarchy 3, 4:**

* **Mother Class:** Komponente (Attributes: nominal power, efficiency, state).  
* **Daughter Classes:** KompBHKW, KompPVModul, WP (Heat Pump), and KompZelleBatt.  
* **Aggregation Classes:** BHKWGruppe and PV\_Anlage (These manage multiple units as a single logical entity) 5\.

**Engineering Intuition:**In control theory, this is known as **Modular Modeling**. By treating the BHKW as an object with its own berechnStromErz() (calculate power) method, you decouple the *device physics* from the *control logic*. This is exactly how you should build the ZORO platform: a library of "Asset Models" that can be dropped into a virtual building.

### Section 3.2.2.1: Modeling the Unmeasured (Load Forecasting)

To simulate a building, you need to know how much energy it *will* use. If real-time meter data isn't available, Guillet uses a **Physics-Based Load Model**.

#### I. The Thermal Load Equations

**Equation (134): Maximum Temperature Difference**$$\\Delta T\_{max}=T\_{Innen\_{AuBen-min}}-T\_{AuBen\_{min}}$$  
**Equation (136): Instantaneous Heat Demand**$$E\_{th}=\\frac{\\Delta T\\cdot E\_{th\_{max}}}{\\Delta T\_{max}}$$  
**Variable Definitions 6-8:**

* $E\_{th} kWh\_{th}$: Current thermal load.  
* $E\_{th\_{max}}$: The maximum heat load at the coldest possible temperature.  
* $T\_{Innen}$: Desired indoor temperature (e.g., 20°C in winter).  
* $T\_{AuBen}$: Current outdoor temperature (from your Weather API).

**Engineering Intuition:**This is a **Linear Degree-Day Model**. It assumes that heat loss is perfectly proportional to the temperature delta between inside and outside. While simplified (it ignores thermal mass/inertia), it provides a "first-order" approximation for your Digital Twin's baseline.

### Section 3.2.3: The Design (Auslegung) Functions

**Translated Explanation:**These functions determine the **optimal size** of the equipment for a new building based on its specific location and load profile 9\.

1. **BHKW Sizing (Section 3.2.3.2):** The BHKW is sized for the "Worst Case"—consecutive cloudy winter days where the battery is empty and heat demand is at its peak 10\.  
2. **Battery Sizing (Section 3.2.3.3):** The battery is sized based on the **"Summer Night"** duration—it must be large enough to power the building from sunset to sunrise without needing the BHKW 11\.  
3. **Heat Pump Sizing (Section 3.2.3.4):** Sized to cover the full heat load down to **$-5^\\circ C$** 12\.

### Implementation Perspective: Application to ZORO Energy

#### 1\. The "ZORO Asset Library"

Guillet’s UML diagram (Figure 3-3) is your **Database Schema** 13, 14\. When you onboard a new building, your Edge device should scan for these assets (BHKW, PV, Battery) via **BACnet/Modbus** and instantiate them as Python objects in your cloud.

#### 2\. Predictive Load Modeling

Guillet’s Equation 136 uses **Static Temperatures** 7\. Your ZORO platform should upgrade this to a **State-Space RC Model** (Resistance-Capacitance). This allows your AI to account for **Thermal Inertia** (how long the concrete floor stays warm), which Guillet identifies as a missing feature for future development 15, 16\.

#### 3\. Site-Adaptive Scaling

Guillet’s "EnFa-Proportional" sizing 17 is a great sales tool. You can tell a customer: *"Based on your Meteonorm weather files and current utility bills, you need exactly 95kWp of PV to achieve the same 18.8 Cent/kWh price as the EnFa case study"* 18, 19\.

### What to study next before moving forward:

We have seen the **Structure**; now we must look at the **Execution**.  
**Section 3.2.4: Simulation of the Energetic Relationship.**This is the "Main Loop" of the digital twin. We will study the **Decision Trees** (Figures 3-13 to 3-16) that the software uses every hour to decide:

* Should I charge the battery?  
* Should I ramp up the BHKW?  
* Should I curtail the PV?

**Are you ready for the "Logic Loops" and Decision Trees of the simulation (Section 3.2.4)?**  
