To accurately architect the **ZORO Energy** platform, it is essential to understand the specific hardware and data infrastructure used in the Energy Factory (EnFa) case study. The thesis utilizes a combination of **physical energy systems**, **local sensors**, and **external climatic databases** to build its digital twin.

### 1\. Primary Energy Systems (Hardware Sources)

These are the physical assets that generate, store, or consume energy within the building.

* **Photovoltaic (PV) System:** Consists of **IBC MonoSol** monocrystalline modules (195 DS for facades and 265 EX for the roof) 1, 2\. Power conversion is handled by **SMA Sunny Tripower** inverters (ranging from 6kW to 17kW) 3\.  
* **Combined Heat and Power (BHKW):** Two identical **Viessmann Vitobloc 200** (Type EM-20/39) units powered by biogas 4\. They provide a combined electrical output of 40kW and thermal output of 78kW 5\.  
* **Battery Storage System:** A **400kWh lead-gel battery** bank using **Moll OPzV Solar** cells 6\. The system is managed by **SMA Sunny Island 8.0H** bi-directional inverters 7\.  
* **Heat Pump System:** Three identical **Stulz AquaBox FDSW-V** air-to-water heat pumps 8\. These units provide both heating (32kWth) and cooling (28kWth) 9\.  
* **Thermal Storage:** Uses water-based thermal buffer tanks for both heating and cooling to decouple generation from demand 10\.  
* **E-Mobility:** Three electric vehicle charging stations integrated into the building's energy management 11\.

### 2\. Sensing and Telemetry Infrastructure

These systems provide the real-time data used to validate the thesis's mathematical models.

* **Solar Irradiance:** A **Sunny SensorBox** mounted horizontally on the roof measures global horizontal irradiance (GHI) with a measurement accuracy of ±8% 12, 13\.  
* **Ambient Weather:** A **Suntracer KNX-GPS** weather station measures outdoor temperature, wind speed, and brightness 13, 14\.  
* **Energy Metering:** **MID-compliant energy meters** and **Janitza 823** meters track the performance of individual strands (HVAC, PV, BHKW, Grid) 15, 16\.  
* **Indoor Climate:** **Z-Wave RS Room Sensors** and **Danfoss Living Connect** thermostats provide wireless telemetry for room temperatures and user setpoints 16, 17\.  
* **Communication Gateways:** A **Viessmann Vitogate 300** acts as the bridge for Modbus TCP/IP control of the BHKW and Heat Pumps 16, 17\.

### 3\. External and Software Data Sources

The thesis relies on these sources for simulation and comparison against real-world telemetry.

* **Meteonorm:** This professional climatic database provides the "typical year" hourly weather files (irradiance and temperature) used for the baseline simulation 18, 19\.  
* **EnFa Database:** A proprietary database that records telemetry from all sensors and inverters every **15 minutes** 14, 20\. Key variables include dblSOCCluster1 (Battery SOC), dblStromErzgPvGesamtkWh (PV Yield), and dblStromZWaermepumpeKwh (Heat Pump load) 21\.  
* **Open-Meteo & Solcast (Integration Perspective):** While not in the original 2016 thesis, your "Layered Weather Architecture" source identifies these as the modern API sources for real-time disturbances (GHI, DNI, DHI) required for **ZORO's Model Predictive Control** 22, 23\.

### Summary of Data Flows for ZORO Energy

Source Type,System/Data Source,Protocol/Method,Use Case  
Environmental,Meteonorm / Weather APIs,REST / EPW,"Forecasting & Baseline Simulation 18, 24"  
Generation,SMA Inverters,Modbus TCP,Real-time PV Yield & Curtailment Tracking 16  
Storage,Sunny Island Inverters,Modbus TCP,"SOC, SOH, and Charging Phase monitoring 16, 21"  
Thermal,Vitogate 300 (Viessmann),Modbus TCP,"Heat Pump COP & BHKW modulation control 16, 17"  
Feedback,Z-Wave Sensors,Wireless,Thermal load and occupancy feedback 17  
**Study Tip:** Before we proceed to the final chapters on **Conclusion and Outlook (Chapter 5\)**, you should review the **Modbus Register Mapping** in the Technikerarbeit source. It details exactly how the **Vitogate 300** translates physical boiler states into the digital variables your AI will need 25, 26\.  
