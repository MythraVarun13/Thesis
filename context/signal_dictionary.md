# Signal Dictionary

_Generated: 2026-05-31T08:39:58.005639_

**233 signals | 223 pipeline-mappable | 3 excluded | 5 unknown**

## ZORO Use-Case Signal Counts

| Use Case | Signals |
|---|---|
| hvac | 129 |
| fdd | 120 |
| mpc | 109 |
| energy | 106 |
| heatpump | 60 |
| battery | 23 |
| pv | 16 |
| weather | 6 |

## Full Signal Table

| Signal | Category | English | Unit | Conf | ZORO Metric | ZORO Unit |
|---|---|---|---|---|---|---|
| `A` | EXCLUDE EXCLUDE | Ramp test |  | high | `` |  |
| `_value` | EXCLUDE EXCLUDE | Counter ramp test |  | high | `` |  |
| `pilot` | EXCLUDE EXCLUDE | CPU monitoring |  | high | `` |  |
| `grealCluster_1_Ladung` | battery_charge | Battery cluster charge | Ah | medium | `battery_cluster_charge` | Ah |
| `grealCluster_2_Ladung` | battery_charge | Battery cluster charge | Ah | medium | `battery_cluster_charge` | Ah |
| `grealCluster_3_Ladung` | battery_charge | Battery cluster charge | Ah | medium | `battery_cluster_charge` | Ah |
| `grealCluster_4_Ladung` | battery_charge | Battery cluster charge | Ah | medium | `battery_cluster_charge` | Ah |
| `green_bat` | battery_current | Battery cluster current raw | A | medium | `battery_cluster_current` | A |
| `greal_E_BatterieAbgabe` | battery_energy | Battery energy discharged | kWh | high | `battery_energy_discharged` | kWh |
| `greal_E_BatterieLaden` | battery_energy | Battery energy charged | kWh | high | `battery_energy_charged` | kWh |
| `real_BatterieVerlustEnergie` | battery_energy | Battery loss energy | kWh | high | `battery_loss_energy` | kWh |
| `real_BatterieAbgabeLeistung` | battery_power | Battery discharge power | kW | high | `battery_discharge_power` | kW |
| `real_BatterieLadeLeistung` | battery_power | Battery charge power | kW | high | `battery_charge_power` | kW |
| `real_BatterieLeistung` | battery_power | Battery net power | kW | high | `battery_power_net` | kW |
| `real_BatterieVerlustLeistung` | battery_power | Battery loss power | kW | high | `battery_loss_power` | kW |
| `Vreal_WP_Ein_Batterie` | battery_setpoint | Battery SOC threshold for HP enable | % | high | `hp_enable_battery_soc_threshold` | % |
| `Vreal_WP_Ein_BatterieKritsch` | battery_setpoint | Battery SOC threshold for HP enable | % | high | `hp_enable_battery_soc_threshold` | % |
| `Vreal_WP_Ein_BatterieKritschHys` | battery_setpoint | Battery SOC threshold for HP enable | % | high | `hp_enable_battery_soc_threshold` | % |
| `greal_BatterieLadeZustand` | battery_soc | Battery state of charge | % | high | `battery_soc` | % |
| `green_t1` | battery_temp | Battery cluster temperature | C | medium | `battery_cluster_temp` | C |
| `green_t2` | battery_temp | Battery cluster temperature | C | medium | `battery_cluster_temp` | C |
| `green_t3` | battery_temp | Battery cluster temperature | C | medium | `battery_cluster_temp` | C |
| `grealCluster_1_Spannung` | battery_voltage | Battery cluster voltage | V | high | `battery_cluster_voltage` | V |
| `grealCluster_2_Spannung` | battery_voltage | Battery cluster voltage | V | high | `battery_cluster_voltage` | V |
| `grealCluster_3_Spannung` | battery_voltage | Battery cluster voltage | V | high | `battery_cluster_voltage` | V |
| `grealCluster_4_Spannung` | battery_voltage | Battery cluster voltage | V | high | `battery_cluster_voltage` | V |
| `realIstTempPuffAltbau` | buffer_temp | Buffer tank temperature | C | high | `temperature` | C |
| `realIstTempRuecklPuffAltbau` | buffer_temp | Buffer tank return temperature | C | high | `return_temperature` | C |
| `greal_E_Gebaeude` | building_energy | Building electrical energy | kWh | high | `electrical_energy_total` | kWh |
| `greal_E_GebaeudeNord` | building_energy | Building electrical energy | kWh | high | `electrical_energy_total` | kWh |
| `greal_E_GebaeudeSued` | building_energy | Building electrical energy | kWh | high | `electrical_energy_total` | kWh |
| `greal_E_GebaeudeSystem` | building_energy | Building electrical energy | kWh | high | `electrical_energy_total` | kWh |
| `greal_E_Gesamtverbrauch` | building_energy | Total energy consumption | kWh | high | `total_energy_consumption` | kWh |
| `greal_LeistungGebaeude` | building_power | Building electrical power demand | kW | high | `electrical_power_demand` | kW |
| `realLeistungGebNord` | building_power | Building zone electrical power | kW | medium | `zone_electrical_power` | kW |
| `realLeistungGebSued` | building_power | Building zone electrical power | kW | medium | `zone_electrical_power` | kW |
| `realLeistungGebSystem` | building_power | Building zone electrical power | kW | medium | `zone_electrical_power` | kW |
| `real_WirkleistungEnFa` | building_power | Building active power net | kW | medium | `active_power_net` | kW |
| `greal_E_bhkw1` | chp_energy | BHKW unit 1 electrical energy | kWh | high | `electrical_energy` | kWh |
| `greal_E_bhkw2` | chp_energy | BHKW unit 2 electrical energy | kWh | high | `electrical_energy` | kWh |
| `dintVolGasVerbrauchBhkwImp1` | chp_gas | BHKW gas volume counter | m3 | medium | `gas_volume_counter` | m3 |
| `dintVolGasVerbrauchBhkwImp2` | chp_gas | BHKW gas volume counter | m3 | medium | `gas_volume_counter` | m3 |
| `greal_Gas_bhkw1` | chp_gas | BHKW unit 1 gas consumption | m3 | high | `gas_volume` | m3 |
| `greal_Gas_bhkw2` | chp_gas | BHKW unit 2 gas consumption | m3 | high | `gas_volume` | m3 |
| `greal_Gas_bhkwges` | chp_gas | BHKW total gas consumption | m3 | high | `gas_volume_total` | m3 |
| `real_aktVerbrauchGasBhkwImp` | chp_gas | BHKW gas consumption rate | m3/h | medium | `gas_consumption_rate` | m3/h |
| `real_aktVerbrauchGasBhkwImp1` | chp_gas | BHKW gas consumption rate | m3/h | medium | `gas_consumption_rate` | m3/h |
| `real_aktVerbrauchGasBhkwImp2` | chp_gas | BHKW gas consumption rate | m3/h | medium | `gas_consumption_rate` | m3/h |
| `real_E_Verlustbhkw1` | chp_loss | BHKW loss energy | kWh | high | `loss_energy` | kWh |
| `real_E_Verlustbhkw2` | chp_loss | BHKW loss energy | kWh | high | `loss_energy` | kWh |
| `real_aktVerlustLeistungBHKW` | chp_loss | BHKW loss power | kW | high | `loss_power` | kW |
| `real_aktVerlustLeistungBHKW1` | chp_loss | BHKW loss power | kW | high | `loss_power` | kW |
| `real_aktVerlustLeistungBHKW2` | chp_loss | BHKW loss power | kW | high | `loss_power` | kW |
| `greal_LeistungBHKW1` | chp_power | BHKW unit 1 power | kW | high | `electrical_power` | kW |
| `greal_LeistungBHKW2` | chp_power | BHKW unit 2 power | kW | high | `electrical_power` | kW |
| `real_P_BHKW` | chp_power | BHKW electrical power output | kW | high | `electrical_power` | kW |
| `real_aktGesamtLeistungBHKW` | chp_power | BHKW total active power | kW | high | `total_active_power` | kW |
| `greal_Administrator_HT` | control_param | Administrator high-tariff state |  | medium | `high_tariff_state` | bool |
| `greal_JalousienMaxWind` | control_param | Blind shading max wind threshold | m/s | medium | `max_wind_threshold` | m/s |
| `realIPhARmsST24` | current_rms | Phase A current RMS | A | high | `phase_a_current_rms` | A |
| `realIPhARmsST25` | current_rms | Phase A current RMS | A | high | `phase_a_current_rms` | A |
| `realIPhBRmsST24` | current_rms | Phase B current RMS | A | high | `phase_b_current_rms` | A |
| `realIPhBRmsST25` | current_rms | Phase B current RMS | A | high | `phase_b_current_rms` | A |
| `realIPhCRmsST24` | current_rms | Phase C current RMS | A | high | `phase_c_current_rms` | A |
| `realIPhCRmsST25` | current_rms | Phase C current RMS | A | high | `phase_c_current_rms` | A |
| `greal_StellungFortluftKlappe` | damper_position | Exhaust air damper position | % | high | `exhaust_damper_position` | % |
| `greal_StellungUmluftKlappe` | damper_position | Recirculation damper position | % | high | `recirculation_damper_position` | % |
| `greal_Speicher_WW_Prozent` | dhw_level | DHW storage fill level | % | high | `fill_level_percent` | % |
| `VrealSpeicherWW_BHKW_Aus` | dhw_setpoint | DHW storage setpoint | C | high | `dhw_setpoint` | C |
| `VrealSpeicherWW_BHKW_Ein` | dhw_setpoint | DHW storage setpoint | C | high | `dhw_setpoint` | C |
| `realIstTempKaltWasOben` | dhw_temp | Cold water temperature | C | high | `cold_water_temperature` | C |
| `realIstTempKaltWasObenMitte` | dhw_temp | Cold water temperature | C | high | `cold_water_temperature` | C |
| `realIstTempKaltWasUnt` | dhw_temp | Cold water temperature | C | high | `cold_water_temperature` | C |
| `realIstTempKaltWasUntMitte` | dhw_temp | Cold water temperature | C | high | `cold_water_temperature` | C |
| `realIstTempWarmWasOben` | dhw_temp | DHW warm water temperature | C | high | `dhw_temperature` | C |
| `realIstTempWarmWasObenMitte` | dhw_temp | DHW warm water temperature | C | high | `dhw_temperature` | C |
| `realIstTempWarmWasUnt` | dhw_temp | DHW warm water temperature | C | high | `dhw_temperature` | C |
| `realIstTempWarmWasUntMitte` | dhw_temp | DHW warm water temperature | C | high | `dhw_temperature` | C |
| `greal_E_Tankstelle1` | ev_energy | EV charger 1 energy | kWh | high | `energy` | kWh |
| `greal_E_Tankstelle2` | ev_energy | EV charger 2 energy | kWh | high | `energy` | kWh |
| `greal_E_Tankstelle3` | ev_energy | EV charger 3 energy | kWh | high | `energy` | kWh |
| `greal_LeistungTankStelle1` | ev_power | EV charger 1 power | kW | high | `power` | kW |
| `greal_LeistungTankStelle2` | ev_power | EV charger 2 power | kW | high | `power` | kW |
| `greal_LeistungTankStelle3` | ev_power | EV charger 3 power | kW | high | `power` | kW |
| `V_real_maxVorlaufTemp` | heating_curve | Heating curve max supply temp setpoint | C | high | `max_supply_temp_setpoint` | C |
| `V_real_maxVorlaufTempK` | heating_curve | Heating curve max supply temp setpoint | C | high | `max_supply_temp_setpoint` | C |
| `V_real_maxVorlaufTempY4` | heating_curve | Heating curve max supply temp setpoint | C | high | `max_supply_temp_setpoint` | C |
| `V_real_minVorlaufTemp` | heating_curve | Heating curve min supply temp setpoint | C | high | `min_supply_temp_setpoint` | C |
| `V_real_minVorlaufTempK` | heating_curve | Heating curve min supply temp setpoint | C | high | `min_supply_temp_setpoint` | C |
| `V_real_minVorlaufTempY4` | heating_curve | Heating curve min supply temp setpoint | C | high | `min_supply_temp_setpoint` | C |
| `greal_VorlaufTempKennlinie` | heating_curve | Heating curve supply temp calculated | C | high | `heating_curve_supply_temp` | C |
| `greal_VorlaufTempKennlinie_K` | heating_curve | Heating curve supply temp calculated | C | high | `heating_curve_supply_temp` | C |
| `greal_K_WMZ_TR_Altbau` | heating_return_temp | Heating return temp cooling circuit | C | high | `return_temperature` | C |
| `greal_K_WMZ_TR_Bespr` | heating_return_temp | Heating return temp cooling circuit | C | high | `return_temperature` | C |
| `greal_K_WMZ_TR_GF` | heating_return_temp | Heating return temp cooling circuit | C | high | `return_temperature` | C |
| `greal_K_WMZ_TR_Halle` | heating_return_temp | Heating return temp cooling circuit | C | high | `return_temperature` | C |
| `greal_K_WMZ_TR_Nord` | heating_return_temp | Heating return temp cooling circuit | C | high | `return_temperature` | C |
| `greal_K_WMZ_TR_Server` | heating_return_temp | Heating return temp cooling circuit | C | high | `return_temperature` | C |
| `greal_K_WMZ_TR_Sued` | heating_return_temp | Heating return temp cooling circuit | C | high | `return_temperature` | C |
| `greal_K_WMZ_TR_WP` | heating_return_temp | Heating return temp cooling circuit | C | high | `return_temperature` | C |
| `greal_K_WMZ_TR_bhkw1` | heating_return_temp | Heating return temp cooling circuit | C | high | `return_temperature` | C |
| `greal_K_WMZ_TR_bhkw2` | heating_return_temp | Heating return temp cooling circuit | C | high | `return_temperature` | C |
| `greal_W_WMZ_TR_Altbau` | heating_return_temp | Heating return temp heating circuit | C | high | `return_temperature` | C |
| `greal_W_WMZ_TR_Halle` | heating_return_temp | Heating return temp heating circuit | C | high | `return_temperature` | C |
| `greal_W_WMZ_TR_Nord` | heating_return_temp | Heating return temp heating circuit | C | high | `return_temperature` | C |
| `greal_W_WMZ_TR_Sued` | heating_return_temp | Heating return temp heating circuit | C | high | `return_temperature` | C |
| `greal_W_WMZ_TR_WP` | heating_return_temp | Heating return temp heating circuit | C | high | `return_temperature` | C |
| `greal_W_WMZ_TR_bhkw1` | heating_return_temp | Heating return temp heating circuit | C | high | `return_temperature` | C |
| `greal_W_WMZ_TR_bhkw2` | heating_return_temp | Heating return temp heating circuit | C | high | `return_temperature` | C |
| `greal_K_WMZ_TV_Altbau` | heating_supply_temp | Heating supply temp cooling circuit | C | high | `supply_temperature` | C |
| `greal_K_WMZ_TV_Bespr` | heating_supply_temp | Heating supply temp cooling circuit | C | high | `supply_temperature` | C |
| `greal_K_WMZ_TV_GF` | heating_supply_temp | Heating supply temp cooling circuit | C | high | `supply_temperature` | C |
| `greal_K_WMZ_TV_Halle` | heating_supply_temp | Heating supply temp cooling circuit | C | high | `supply_temperature` | C |
| `greal_K_WMZ_TV_Nord` | heating_supply_temp | Heating supply temp cooling circuit | C | high | `supply_temperature` | C |
| `greal_K_WMZ_TV_Server` | heating_supply_temp | Heating supply temp cooling circuit | C | high | `supply_temperature` | C |
| `greal_K_WMZ_TV_Sued` | heating_supply_temp | Heating supply temp cooling circuit | C | high | `supply_temperature` | C |
| `greal_K_WMZ_TV_WP` | heating_supply_temp | Heating supply temp cooling circuit | C | high | `supply_temperature` | C |
| `greal_K_WMZ_TV_bhkw1` | heating_supply_temp | Heating supply temp cooling circuit | C | high | `supply_temperature` | C |
| `greal_K_WMZ_TV_bhkw2` | heating_supply_temp | Heating supply temp cooling circuit | C | high | `supply_temperature` | C |
| `greal_W_WMZ_TV_Altbau` | heating_supply_temp | Heating supply temp heating circuit | C | high | `supply_temperature` | C |
| `greal_W_WMZ_TV_Halle` | heating_supply_temp | Heating supply temp heating circuit | C | high | `supply_temperature` | C |
| `greal_W_WMZ_TV_Nord` | heating_supply_temp | Heating supply temp heating circuit | C | high | `supply_temperature` | C |
| `greal_W_WMZ_TV_Sued` | heating_supply_temp | Heating supply temp heating circuit | C | high | `supply_temperature` | C |
| `greal_W_WMZ_TV_WP` | heating_supply_temp | Heating supply temp heating circuit | C | high | `supply_temperature` | C |
| `greal_W_WMZ_TV_bhkw1` | heating_supply_temp | Heating supply temp heating circuit | C | high | `supply_temperature` | C |
| `greal_W_WMZ_TV_bhkw2` | heating_supply_temp | Heating supply temp heating circuit | C | high | `supply_temperature` | C |
| `V_real_AbtauTemperaturBetrieb` | hp_defrost | Heat pump defrost trigger temp | C | high | `defrost_trigger_temp` | C |
| `greal_WP1AbtauSek` | hp_defrost | Heat pump defrost duration | s | high | `defrost_duration` | s |
| `greal_WP2AbtauSek` | hp_defrost | Heat pump defrost duration | s | high | `defrost_duration` | s |
| `greal_WP3AbtauSek` | hp_defrost | Heat pump defrost duration | s | high | `defrost_duration` | s |
| `greal_AZ_WP_Energie` | hp_energy | Heat pump compressor energy | kWh | high | `compressor_energy` | kWh |
| `greal_E_WP` | hp_energy | Heat pump total electrical energy | kWh | high | `electrical_energy` | kWh |
| `V_realAZmax` | hp_setpoint | HP runtime setpoint | h | medium | `runtime_setpoint` | h |
| `V_realAZmin` | hp_setpoint | HP runtime setpoint | h | medium | `runtime_setpoint` | h |
| `V_realHysWP` | hp_setpoint | Heat pump hysteresis setpoint | K | high | `hysteresis_setpoint` | K |
| `V_realMaxVL_WP` | hp_setpoint | Max supply temp setpoint HP | C | high | `max_supply_temp_setpoint` | C |
| `V_realMinVL_WPcool` | hp_setpoint | Min supply temp cool setpoint HP | C | high | `min_supply_temp_cool_setpoint` | C |
| `V_realSollTempAZmax` | hp_setpoint | HP max setpoint temp for runtime | C | medium | `max_setpoint_temp_runtime` | C |
| `realSollwertReglerWP1` | hp_setpoint | Heat pump 1 controller setpoint | C | high | `controller_setpoint` | C |
| `grealIstWaermepumpVorlauf` | hp_supply_temp | Heat pump supply temperature | C | high | `supply_temperature` | C |
| `V_real_maxAT` | hvac_setpoint | Max outdoor temp threshold HP | C | high | `max_outdoor_temp_threshold` | C |
| `V_real_maxATY4` | hvac_setpoint | Max outdoor temp threshold HP | C | high | `max_outdoor_temp_threshold` | C |
| `V_real_maxAT_K` | hvac_setpoint | Max outdoor temp threshold HP | C | high | `max_outdoor_temp_threshold` | C |
| `V_real_minAT` | hvac_setpoint | Min outdoor temp threshold HP | C | high | `min_outdoor_temp_threshold` | C |
| `V_real_minATY4` | hvac_setpoint | Min outdoor temp threshold HP | C | high | `min_outdoor_temp_threshold` | C |
| `V_real_minAT_K` | hvac_setpoint | Min outdoor temp threshold HP | C | high | `min_outdoor_temp_threshold` | C |
| `greal_SollTempAZplus` | hvac_setpoint | Heating setpoint AZ+ | C | medium | `heating_setpoint_az_plus` | C |
| `greal_Wochenendwert` | hvac_setpoint | Weekend setpoint value | C | medium | `weekend_setpoint` | C |
| `greal_T_Server_EG` | indoor_temp | Server room temperature | C | high | `indoor_temperature` | C |
| `V_real_Nachtabsenkung` | night_setback | Night setback setpoint | C | high | `night_setback_setpoint` | C |
| `V_real_NachtabsenkungY4` | night_setback | Night setback setpoint | C | high | `night_setback_setpoint` | C |
| `greal_Nachtabsenkung` | night_setback | Night setback active state |  | high | `night_setback_active` | bool |
| `grealTempAussenGefiltert` | outdoor_temp | Outdoor temperature filtered | C | high | `outdoor_temperature` | C |
| `realLeistungsfaktorST24` | power_factor | Power factor |  | high | `power_factor` |  |
| `realLeistungsfaktorST25` | power_factor | Power factor |  | high | `power_factor` |  |
| `greal_E_PV1` | pv_energy | PV string 1 energy | kWh | high | `pv_energy` | kWh |
| `greal_E_PV2` | pv_energy | PV string 2 energy | kWh | high | `pv_energy` | kWh |
| `greal_E_PV3` | pv_energy | PV string 3 energy | kWh | high | `pv_energy` | kWh |
| `greal_E_PV4` | pv_energy | PV string 4 energy | kWh | high | `pv_energy` | kWh |
| `greal_E_PV5` | pv_energy | PV string 5 energy | kWh | high | `pv_energy` | kWh |
| `greal_E_PV6` | pv_energy | PV string 6 energy | kWh | high | `pv_energy` | kWh |
| `greal_E_PV7` | pv_energy | PV string 7 energy | kWh | high | `pv_energy` | kWh |
| `greal_E_PV_Gesamt` | pv_energy | PV total energy all strings | kWh | high | `pv_energy_total` | kWh |
| `greal_PV_Ges_prog` | pv_forecast | PV generation forecast | kWh | high | `pv_energy_forecast` | kWh |
| `greal_E_ErzeugungEnFa` | pv_generation | PV total energy generated | kWh | high | `pv_energy_total` | kWh |
| `real_PV_Gesamt` | pv_generation | PV total power output | kW | high | `pv_power_total` | kW |
| `real_WirkleistungErzeugungEnFa` | pv_generation | Active power generation PV+BHKW | kW | medium | `active_power_generation` | kW |
| `sun_alt` | solar | Sun altitude angle | deg | high | `sun_altitude` | deg |
| `sun_azi` | solar | Sun azimuth angle | deg | high | `sun_azimuth` | deg |
| `Vreal_maxSpeicher` | storage_setpoint | Max storage setpoint | C | medium | `max_storage_setpoint` | C |
| `Vreal_maxTempSpeicherUnten` | storage_setpoint | Max temp lower storage setpoint | C | medium | `max_temp_lower_storage_setpoint` | C |
| `Vreal_minSpeicher` | storage_setpoint | Min storage setpoint | C | medium | `min_storage_setpoint` | C |
| `real_E_VerlustEnFa` | system_loss | EnFa system loss energy | kWh | medium | `system_loss_energy` | kWh |
| `real_VerlustleistungEnFa` | system_loss | EnFa system loss power | kW | medium | `system_loss_power` | kW |
| `greal_EK_WMZ_WWout` | thermal_energy | Heat meter energy DHW output | kWh | high | `dhw_energy_output` | kWh |
| `greal_E__WMZ_BHKW` | thermal_energy | BHKW heat meter total energy | kWh | high | `thermal_energy` | kWh |
| `greal_E__WMZ_WWout` | thermal_energy | DHW heat meter output energy | kWh | high | `dhw_output_energy` | kWh |
| `greal_K_WMZ_E_Altbau` | thermal_energy | Thermal energy cooling circuit | kWh | high | `thermal_energy` | kWh |
| `greal_K_WMZ_E_Bespr` | thermal_energy | Thermal energy cooling circuit | kWh | high | `thermal_energy` | kWh |
| `greal_K_WMZ_E_GF` | thermal_energy | Thermal energy cooling circuit | kWh | high | `thermal_energy` | kWh |
| `greal_K_WMZ_E_Halle` | thermal_energy | Thermal energy cooling circuit | kWh | high | `thermal_energy` | kWh |
| `greal_K_WMZ_E_Nord` | thermal_energy | Thermal energy cooling circuit | kWh | high | `thermal_energy` | kWh |
| `greal_K_WMZ_E_Server` | thermal_energy | Thermal energy cooling circuit | kWh | high | `thermal_energy` | kWh |
| `greal_K_WMZ_E_Sued` | thermal_energy | Thermal energy cooling circuit | kWh | high | `thermal_energy` | kWh |
| `greal_K_WMZ_E_WP` | thermal_energy | Thermal energy cooling circuit | kWh | high | `thermal_energy` | kWh |
| `greal_K_WMZ_E_bhkw1` | thermal_energy | Thermal energy cooling circuit | kWh | high | `thermal_energy` | kWh |
| `greal_K_WMZ_E_bhkw2` | thermal_energy | Thermal energy cooling circuit | kWh | high | `thermal_energy` | kWh |
| `greal_WMZ_Hz_Erz_BHKW` | thermal_energy | Heat generation energy from BHKW | kWh | high | `heat_generation_energy` | kWh |
| `greal_WMZ_Hz_Erz_WP` | thermal_energy | Heat generation energy from heat pump | kWh | high | `heat_generation_energy` | kWh |
| `greal_WMZ_Hz_Erz_ges` | thermal_energy | Total heat generation energy | kWh | high | `heat_generation_energy_total` | kWh |
| `greal_WMZ_Kalt` | thermal_energy | Heat meter energy cooling total | kWh | high | `cooling_energy_total` | kWh |
| `greal_WMZ_Kalt_Erz_WP` | thermal_energy | Heat meter energy cooling total | kWh | high | `cooling_energy_total` | kWh |
| `greal_WMZ_Warm` | thermal_energy | Total heating circuit energy | kWh | high | `heating_energy_total` | kWh |
| `greal_W_WMZ_E_Altbau` | thermal_energy | Heating energy old building | kWh | high | `thermal_energy` | kWh |
| `greal_W_WMZ_E_Halle` | thermal_energy | Heating energy hall | kWh | high | `thermal_energy` | kWh |
| `greal_W_WMZ_E_Nord` | thermal_energy | Heating energy north zone | kWh | high | `thermal_energy` | kWh |
| `greal_W_WMZ_E_Sued` | thermal_energy | Heating energy south zone | kWh | high | `thermal_energy` | kWh |
| `greal_W_WMZ_E_WP` | thermal_energy | Heating energy heat pump circuit | kWh | high | `thermal_energy` | kWh |
| `greal_W_WMZ_E_bhkw1` | thermal_energy | Heating energy BHKW 1 circuit | kWh | high | `thermal_energy` | kWh |
| `greal_W_WMZ_E_bhkw2` | thermal_energy | Heating energy BHKW 2 circuit | kWh | high | `thermal_energy` | kWh |
| `grealThermLeistungWaermeFBH_Nord` | thermal_power | Underfloor heating power North | kW | high | `thermal_power` | kW |
| `grealThermLeistungWaermeFBH_Sued` | thermal_power | Underfloor heating power South | kW | high | `thermal_power` | kW |
| `grealThermLeistungWaermeHalle` | thermal_power | Underfloor heating power Hall | kW | high | `thermal_power` | kW |
| `greal_K_WMZ_P_Altbau` | thermal_power | Thermal power cooling circuit | kW | high | `thermal_power` | kW |
| `greal_K_WMZ_P_Bespr` | thermal_power | Thermal power cooling circuit | kW | high | `thermal_power` | kW |
| `greal_K_WMZ_P_GF` | thermal_power | Thermal power cooling circuit | kW | high | `thermal_power` | kW |
| `greal_K_WMZ_P_Halle` | thermal_power | Thermal power cooling circuit | kW | high | `thermal_power` | kW |
| `greal_K_WMZ_P_Nord` | thermal_power | Thermal power cooling circuit | kW | high | `thermal_power` | kW |
| `greal_K_WMZ_P_Server` | thermal_power | Thermal power cooling circuit | kW | high | `thermal_power` | kW |
| `greal_K_WMZ_P_Sued` | thermal_power | Thermal power cooling circuit | kW | high | `thermal_power` | kW |
| `greal_K_WMZ_P_WP` | thermal_power | Thermal power cooling circuit | kW | high | `thermal_power` | kW |
| `greal_K_WMZ_P_bhkw1` | thermal_power | Thermal power cooling circuit | kW | high | `thermal_power` | kW |
| `greal_K_WMZ_P_bhkw2` | thermal_power | Thermal power cooling circuit | kW | high | `thermal_power` | kW |
| `greal_W_WMZ_P_Altbau` | thermal_power | Thermal power heating circuit | kW | high | `thermal_power` | kW |
| `greal_W_WMZ_P_Halle` | thermal_power | Thermal power heating circuit | kW | high | `thermal_power` | kW |
| `greal_W_WMZ_P_Nord` | thermal_power | Thermal power heating circuit | kW | high | `thermal_power` | kW |
| `greal_W_WMZ_P_Sued` | thermal_power | Thermal power heating circuit | kW | high | `thermal_power` | kW |
| `greal_W_WMZ_P_WP` | thermal_power | Thermal power heating circuit | kW | high | `thermal_power` | kW |
| `greal_W_WMZ_P_bhkw1` | thermal_power | Thermal power heating circuit | kW | high | `thermal_power` | kW |
| `greal_W_WMZ_P_bhkw2` | thermal_power | Thermal power heating circuit | kW | high | `thermal_power` | kW |
| `TimerRuecklaufAltbau` | timer_schedule | Return flow timer schedule |  | medium | `return_flow_timer` | bool |
| `greal_LeistungTankStellen` | unknown | No rule matched |  | low | `` |  |
| `val1006` | unknown | Unknown control state -1/0/1 |  | low | `state_val1006` |  |
| `val1007` | unknown | Unknown control state -1/0/1 |  | low | `state_val1007` |  |
| `val1008` | unknown | Unknown analog signal 65-92 |  | low | `analog_val1008` |  |
| `val1009` | unknown | Unknown analog signal 65-92 |  | low | `analog_val1009` |  |
| `wind_now` | weather | Wind speed current | m/s | high | `wind_speed_now` | m/s |
| `wind_tomorrow` | weather_forecast | Wind speed tomorrow forecast | m/s | high | `wind_speed_forecast` | m/s |
| `greal_RL_TempFBH_OG` | zone_return_temp | Underfloor heating return temp upper floor | C | high | `return_temperature` | C |
| `realTempRuecklBKT_EG` | zone_return_temp | Concrete core return temp ground floor | C | high | `return_temperature` | C |
| `greal_Soll_T_BKT` | zone_setpoint | Concrete core activation setpoint | C | high | `setpoint` | C |
| `greal_VL_TempFBH_OG` | zone_supply_temp | Underfloor heating supply temp upper floor | C | high | `supply_temperature` | C |
| `greal_realTempVorlBKT_EG` | zone_supply_temp | Concrete core supply temp ground floor | C | high | `supply_temperature` | C |
