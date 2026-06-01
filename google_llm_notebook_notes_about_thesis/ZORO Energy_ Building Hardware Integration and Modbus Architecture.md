We are now transitioning from the **Theoretical Physics** (how energy moves) to the **Implementation Layer** (how data moves). This is where your startup, **ZORO Energy**, becomes a tangible product. To control a building, your AI must speak the language of the hardware, which is primarily **Modbus**.

### 1\. Modbus Protocol Fundamentals: The Building's Language

Based on the **Technikerarbeit** source, Modbus is an industrial standard (IEC 61158\) that uses a Master-Slave architecture to exchange data 1\. For your Edge device to "read" the building, it acts as the **Master**, requesting data from **Slaves** (Inverters, Gateways, Meters).  
**The Data Structure 1, 2:**A Modbus message consists of:

* **Address Field (8 bits):** Identifies which specific device (e.g., Inverter \#2) is being spoken to.  
* **Function Field (8 bits):** Tells the device what to do (Read or Write).  
* **Data Field ($n \\times 8$ bits):** Contains the actual payload (e.g., the temperature value).  
* **Checksum (16 bits CRC):** Ensures the data wasn't corrupted during transmission.

### 2\. The ZORO Edge Architecture: Modbus TCP vs. RTU

To design your Edge device, you must support two distinct physical "wiring" methods described in the source.

#### I. Modbus TCP/IP (The High-Speed Network)

As shown in **Figure 5**, this uses standard **RJ45 Ethernet** cables 3, 4\.

* **Target Devices:** The **Vitogate 300** (Viessmann Gateway), **SMA Inverters**, and **Janitza 823** Energy Meters 4\.  
* **ZORO Implementation:** Your Edge device connects to the building’s local LAN. This allows your AI to pull high-frequency data and send control setpoints to the HVAC system via the Vitogate 3\.

#### II. Modbus RTU (The Serial Network)

As shown in **Figure 6**, this uses **RS485 serial** connections (twisted pair wires) 3, 4\.

* **Target Devices:** Specialized sub-meters (Janitza) and older PV inverters 1, 3\.  
* **ZORO Implementation:** Your Edge hardware (e.g., a Raspberry Pi or industrial PLC) needs an **RS485-to-USB adapter** or a dedicated serial port to poll these "legacy" sensors.

### 3\. The ZORO Data Map: Register-Level Integration

This is the most critical part of your software development. Data in Modbus is stored in **Registers**. You must map these registers to your **Database Schema** (the telemetry\_logs table we designed earlier).  
**The Four Address Ranges 5:**| Range | Name | Access | Role in ZORO || :--- | :--- | :--- | :--- || **0x (00001+)** | Binary Outputs | Read/Write | **Actuators:** Turning a pump ON/OFF. || **1x (10001+)** | Binary Inputs | Read Only | **Status:** Is the BHKW currently running? || **3x (30001+)** | **Input Registers**| Read Only | **Sensors:** Pulling Aussentemperatur or SOC. || **4x (40001+)** | **Holding Registers**| Read/Write | **Setpoints:** Changing the heating curve slope. |

#### Example: Pulling Outdoor Temperature (Register 30001\)

* **The Math:** Modbus registers are 16-bit. If the sensor reads **21.5°C**, it might send the integer 215 2\.  
* **ZORO Logic:** Your Python backend must read **Register 30001** via FC 04 (Read Input Register), then multiply by a scaling factor (e.g., $0.1$) to get the real-world value 5\.

### 4\. Engineering Intuition: From Bits to AI Control

The **Technikerarbeit** highlights a key challenge: **Automated Defrost (Abtauprozess)**. The Viessmann heat pumps automatically enter a defrost cycle if the temperature difference between the air and the refrigerant exceeds **8K** 6\.  
**The ZORO IP Opportunity:**The source notes that every defrost cycle in the last 48 hours is stored in a multi-dimensional array (WP\_Zykl\_Daten) along with temperature and humidity 6, 7\.

* **The Thesis Logic:** Simply records when it happens 6\.  
* **The ZORO Logic:** Your AI should poll these registers to **predict** the next defrost cycle. By knowing a defrost is coming, your **MPC** can ramp up the BHKW 15 minutes early so the building's indoor temperature (the **Behaglichkeitsfeld** 8\) never dips.

### 5\. Hardware Implementation Perspective: The Communication Mesh

Your Edge device should be designed as a **Supervisory Multi-Protocol Gateway**:

1. **Modbus TCP Port:** To talk to the heavy machinery (SMA/Viessmann) 4\.  
2. **Modbus RTU (RS485):** To talk to the precision sub-meters 1\.  
3. **Z-Wave/Wireless:** As specified in the source, use this for **Room Sensors** (Danfoss Living Connect) to avoid the high cost of wiring every office 3, 9\.

### What to study next to build the first Prototype:

1. **The Heating Curve Formula (Section 9):** We will study the linear equation **$y \= mx \+ b$** used in the Technikerarbeit 10\. This is the exact formula you will need to program into your AI to override the BMS and calculate the required **Flow Temperature (VLT)** based on the outdoor temperature 11, 12\.  
2. **Logic for Excess Power (Leistungsüberschuss):** We will look at the **Struktogramm** (Figure 29\) for handling solar surpluses and EV charging 13\.

**Are you ready to study the "Heizkennlinie" (Heating Curve) math and how to calculate the Slope ($N$) for your AI control loops? 10**  
