We have now reached the financial engine of the thesis. While the previous sections established the **physics** of the building, **Section 2.6: Kosten der Anlage (System Costs & LCOE)** establishes the **business case**. For **ZORO Energy**, this section is your "Sales Deck Math"—it provides the framework to prove to a commercial client that your optimization platform isn't just "green," it's more profitable than the status quo 1, 2\.

### Section 2.6: Kosten der Anlage (System Costs & LCOE)

**Translated Explanation:**Guillet calculates the **Levelised Cost of Energy (LCOE)** for the EnFa. This includes **CAPEX** (Investment), **OPEX** (Maintenance and Fuel), and **Depreciation**. The goal is to determine the actual price per kilowatt-hour ($kWh$) for both electricity and heat. The analysis assumes a 20-year operation period 2, 3\.

### 1\. Corrected Investment Costs (CAPEX)

Guillet introduces a "Correction Factor" ($p\_{Invest}$) because mechanical systems often have residual value or parts (like inverters) that outlast the core components (like battery cells) 4\.  
**Equation (66):**$$Invest\_{Anlage-neu}=(1-\\frac{p\_{Invest}}{100})\\cdot Invest\_{Anlage}$$

* **Variable Definitions:**  
* $Invest\_{Anlage-neu}$ €: Adjusted investment cost for depreciation.  
* $p\_{Invest}$ %: The percentage of the system that *doesn't* need replacing at the end of its life (e.g., 30% for PV racking/cabling) 5, 6\.  
* **ZORO Application:** Your digital twin should use this to track **Asset Valuation**. By knowing the "run-hours" and "health" (SOH) of the battery, your platform can provide a real-time estimate of the building’s infrastructure value.

### 2\. The LCOE of Solar Power

To find the solar price, we spread the lifetime costs over the total energy generated.  
**Equation (67):**$$1kWh\_{Solar}=\\frac{\\frac{Invest\_{PV}}{t\_{PV}}+Wartung\_{PV}}{kWh\_{strom-1Jahr\_{PV}}}$$

* **Variables:** $t\_{PV}$ is the lifespan (25 years); $Wartung\_{PV}$ is annual maintenance (standard: 7€ per kWp) 7\.  
* **The "Abregelung" Penalty:** In Equation (68), Guillet calculates the EnFa's solar cost at **9.5 Cent/kWh** 8\.  
* **Engineering Intuition:** She notes this price is "mid-field" because the building often has to **curtail (abregeln)** solar power when the battery is full 8, 9\.  
* **ZORO Energy Strategy:** This is your value proposition. By using **Model Predictive Control (MPC)** to shift loads (like pre-cooling the building), you reduce curtailment, increasing $kWh\_{strom-1Jahr}$ and thus **lowering the LCOE** for your client.

### 3\. The LCOE of the BHKW (The Coupling Problem)

Calculating the price of electricity from a CHP unit is tricky because it produces heat simultaneously. Guillet treats the heat as a "credit" ($Q\_{1kWhstrom}$) 10, 11\.  
**Equation (71):**$$1kWh\_{Strom-BHKW}=Gas\_{1kWhstrom}+Abschr\_{Strom-BHKW}+Wartung\_{kWh}-Q\_{1kWhstrom}$$

* **Variable Definitions:**  
* $Gas\_{1kWhstrom}$: Cost of fuel needed for 1 kWh of electricity.  
* $Abschr$: Depreciation.  
* $Q\_{1kWhstrom}$: The value of the byproduct heat (benchmarked against local district heating prices) 10, 11\.  
* **Result:** The EnFa's BHKW electricity costs **18.8 Cent/kWh** 12\.

### 4\. The LCOE of the Battery (Storage Surcharge)

The battery doesn't "generate" energy; it adds a "storage fee" to every kWh that passes through it 12\.  
**Equation (91):**$$1kWh\_{el\_{Batt}}=1kWh\_{Speicherung\_{t\>tBatt}}+1kWh\_{in\~Batt}$$

* **Engineering Intuition:** Storing energy in a lead-gel battery adds roughly **1.8 Cent/kWh** in depreciation costs ($1kWh\_{Speicherung}$) 13, 14\.  
* **The ZORO Insight:** If your AI decides to store solar power (9.5 cents) instead of running the BHKW (18.8 cents), the total cost of that battery power is $9.5 \+ 1.8 \= 11.3$ cents. Compared to the grid price (approx. 29 cents in 2015), **storage is a massive profit center** 14, 15\.

### 5\. Total Building Energy Price

Finally, Guillet aggregates everything into a single building-wide metric 16\.  
**Equations (103) & (104):**$$1kWh\_{el}=\\frac{\\sum(Abschr+Wartung)+Gas\_{jahr\_{Strom}}}{kWh\_{strom-1Jahr\_{Gesamt}}}$$$$1kWh\_{th}=\\frac{\\sum(Abschr+Wartung)+Gas\_{jahr\_{Warme}}}{kWh\_{Warme-1Jahr\_{Gesamt}}}$$

* **The Verdict (2015):**  
* **EnFa Electricity:** 18.8 Cent/kWh (vs. 29.13 Cent Grid) 17\.  
* **EnFa Heat:** 2.4 Cent/kWh (vs. 8.57 Cent District Heat) 17\.  
* **Implementation Perspective:** Your ZORO platform should have a **"Financial Dashboard"** that continuously updates these equations. If gas prices spike or a cloudier-than-average month occurs, your AI should report the shifting LCOE to the facility manager.

### Engineering Intuition: Economic Optimization as a Control Goal

In **Steve Brunton’s Control Bootcamp**, we talk about a "Cost Function" ($J$). For ZORO Energy, $J$ isn't just "minimize temperature error"; it is **"Minimize Equation 103 and 104 in real-time."**  
Your MPC should look at the **Weather API** and **Dynamic Electricity Prices** (if grid-connected) to decide:*"Is it cheaper to discharge the battery now or run the BHKW?"*By mathematically modeling these costs, your control logic becomes an **Economic Optimizer**.

### What to study next:

We have finished **Chapter 2 (The Physics and Economics)**. We now move to **Chapter 3: Software Structure**. This is where Guillet explains how she translated these equations into **Python Code**.  
We will look at:

1. **Section 3.2.1: OOP and UML:** How to structure your "Digital Twin" using classes like KompPVModul and BHKWGruppe 18, 19\.  
2. **Section 3.2.4: Simulation Logic:** How the stündlich (hourly) calculation loops actually work 20, 21\.

**Are you ready to see how this is architected in Python (Chapter 3)?**  
