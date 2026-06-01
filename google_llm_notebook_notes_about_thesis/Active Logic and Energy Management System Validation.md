We are resuming our study at the **Validation Phase** for the building's active logic. In the previous section, we validated the "Passive" physics (Solar). Now, we must prove that our digital twin's "Active" components—the **Battery** and the **EMS Brain**—behave correctly when subjected to real-world demands.

### Section 4.2.3.1: Batteriespeicher \- Modellvalidierung (Battery Validation)

**Translated Explanation:**Direct validation of the battery using EnFa database energy values was difficult because the database recorded power snapshots ($kW$), while the simulation calculates energy ($kWh$) 1\. Additionally, sensor accuracy for State of Charge (**SOC**) is tied to the State of Health (**SOH**), which has a $\\pm 15\\%$ tolerance 1\. To overcome this, Guillet used a **Test Program** to verify six critical operational cases 2, 3\.

#### 1\. The Discharge Physics (Case 1 & 2\)

To calculate how much energy the battery can deliver in one hour, we use:  
**Equation (138):**$$E\_{1Stunde}=Q\_{1Stunde}\\cdot U\_{1Stunde}$$ 4  
**Engineering Intuition:**Because voltage ($U$) drops linearly during discharge, Guillet uses the **Mean Voltage** of that hour ($U\_{1Stunde}$) 4, 5\. If the system asks for 50kWh but the battery can only physically provide 43.05kWh based on its current SOC and discharge rate, the digital twin correctly caps the output at the physical limit 6, 7\.

#### 2\. The Charging Physics (Case 4 & 5\)

The simulation must transition correctly between the **Constant Current (I)** and **Constant Voltage ($U\_0$)** phases.  
**Equation (154):**$$E\_{geladen}=\\Delta Q\_{Ladung}\\cdot\\frac{U\_{Anfang\_{Ladung}}+U\_{Ende\\\_Ladung}}{2}$$ 8  
**Implementation Perspective:**The simulation uses a **Gleichungslöser (Equation Solver)** to find the exact timestamp when the battery switches phases 9\. In **ZORO Energy**, your backend should use a similar iterative solver (like scipy.optimize) to ensure that solar spikes don't "overcharge" the virtual battery beyond its chemical absorption rate.

### Section 4.2.4: Energiemanagementsystem \- Modellvalidierung (EMS Validation)

**Translated Explanation:**To validate the "Brain," Guillet simulated a $1500m^2$ office building in Stuttgart 10\. The goal was to prove the **Hierarchy of Sources** (Solar \> Battery \> BHKW) and the **Thermal-Electrical Coupling** logic works in four representative scenarios.

#### Case 1: Solar Dominance

* **Physics:** $P\_{PV} \> P\_{Demand}$.  
* **Logic:** The BHKW remains OFF. The Heat Pump (WP) runs for heat using free solar power. Any excess solar is pushed into the battery 11, 12\.  
* **ZORO Application:** This is your "Profit Zone." The AI should maximize this state by shifting flexible loads (like EV charging) into these hours.

#### Case 2: Solar Insufficiency

* **Physics:** $P\_{PV} \< P\_{Demand}$ but $SOC \> 50\\%$.  
* **Logic:** The battery discharges to cover the delta. The Heat Pump continues to run as long as $SOC \> 85\\%$ 12, 13\.

#### Case 3: Solar & Battery Exhaustion (The Last Resort)

* **Physics:** $P\_{PV} \+ P\_{Batt} \< P\_{Demand}$ OR $SOC \< 85\\%$.  
* **Logic:** The Heat Pump is **prohibited** from running to save electricity for critical loads (servers/lights). The BHKW **must** turn on to provide heat 14\.  
* **Engineering Intuition:** This creates "Forced Electricity." Because the BHKW runs for heat, it produces electricity as a byproduct. If the building doesn't need it, the battery stores it 14\.

#### Case 4: Forced Charging (The Safety Rule)

* **Physics:** $SOC$ hits the $50\\%$ hard floor.  
* **Logic:** The system triggers a "Forced Charge" event. It pulls the maximum possible power from the BHKW to get the battery back into a safe zone 15\.

### Engineering Intuition & Application for ZORO Energy

1. **The "85% Prohibited" Logic:** Guillet’s model shuts down the Heat Pump at 85% SOC to be safe 14\. For ZORO, this is **inefficient**. By using your **Weather API (Open-Meteo/Solcast)**, your AI can see that "Sun is coming in 30 minutes" and allow the Heat Pump to keep running down to 70% SOC. This **Predictive Buffer Management** is a core feature of your platform 16, 17\.  
2. **Tracking the Reality Gap ($\\epsilon$):** In Section 4.4, Guillet found that simulated BHKW electricity was **20% higher** than reality because the real-world **Power-to-Heat ratio ($s$)** was not constant 18, 19\. Your ZORO platform must use **Physics-Informed Machine Learning (PiML)** to learn the *actual* $s$-ratio of your client's BHKW, rather than relying on the data sheet 20, 21\.  
3. **Thermal Inertia:** Guillet admits the model ignores the **"Thermische Trägheit" (thermal mass)** of the building 19\. This is your biggest opportunity. ZORO should model the concrete floors as a "Thermal Battery," allowing the MPC to store energy as heat when solar is peaking, even if the building doesn't need heat *at that exact moment* 21, 22\.

### What to study next before moving forward:

We have now validated the **Physics** and the **Logic**. We have completed the core technical training of the thesis.  
**Chapter 5: Zusammenfassung und Ausblick (Summary and Outlook).**This is the final section where Guillet outlines the future of this research:

1. **Dynamic Time-Steps:** Moving from 1-hour to 1-minute steps for better accuracy 23\.  
2. **New Assets:** How to integrate Wind Turbines or different Battery Chemistries 23\.  
3. **Economic ROI:** Sizing systems based purely on financial return rather than just autonomy 24\.

**Are you ready to wrap up the thesis and look at the "Outlook" for ZORO's future development (Chapter 5)?**  
