import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

# Page configuration
st.set_page_config(layout="wide")
st.image("images/LinkedIn Header - NatPower Marine.png", caption='\u00a9 Natpower Marine', use_container_width=True)
st.sidebar.image("images/natpowermarine.png", caption='\u00a9 Natpower Marine', use_container_width=True)

# Cached database connection
@st.cache_resource(ttl="10m")
def get_connection():
    return st.connection("postgresql", type="sql")

@st.cache_data(ttl="10m")
def get_data(query):
    return conn.query(query)

conn = get_connection()
queryval = "SELECT DISTINCT vessel_category FROM reference.ref_cold_ironing_kw;"
df = get_data(queryval)

# Sidebar Filters
vessel_options = st.selectbox("Vessel Category", options=df["vessel_category"].unique(), index=list(df["vessel_category"].unique()).index("Ferry"))

# **Toggle Options for Calculations**
st.sidebar.markdown("### Calculation Options")
enable_cold_ironing = st.sidebar.toggle("Enable Cold Ironing Calculation", value=True)

if enable_cold_ironing:
    if st.sidebar.button('Display Cold Ironing Reference Data'):
        conn = get_connection()
        queryval = "SELECT * FROM reference.ref_cold_ironing_kw;"
        df = get_data(queryval) 
        # Define GT Class Ranges
        gt_ranges = {
            "Less Than 150": (0, 150),
            "GT 150-4999": (150, 4999),
            "GT 5000-10000": (5000, 9999),
            "GT 10000-20000": (10000, 19999),
            "GT 20000-25000": (20000, 24999),
            "GT 25000-50000": (25000, 49999),
            "GT 50000-100000": (50000, 99999),
            "GT 100000 >": (100000, 999999999)
        }

        # Unique vessel categories from the data
        vessel_categories = [
            "Auto Carrier", "Cargo vessels", "Chemical Tankers", "Container vessels",
            "Crude oil tanker", "Cruise ships", "Ferry", "non-serviceble in out business model",
            "Offshore Supply", "not identified", "Service Vessles"
        ]

        # Initialize transformed DataFrame
        transformed_data = { "GT Class": list(gt_ranges.keys()) }

        # Populate vessel categories with default value 0
        for category in vessel_categories:
            transformed_data[category] = [0] * len(gt_ranges)

        # Convert transformed data into DataFrame
        df_transformed = pd.DataFrame(transformed_data)
        # Populate values based on the GT range
        for index, row in df.iterrows():
            for gt_class, (min_gt, max_gt) in gt_ranges.items():
                if row["min_gt"] >= min_gt and row["max_gt"] <= max_gt:
                    # st.write(min_gt,row["min_gt"],max_gt,row["max_gt"],gt_class, row["vessel_category"], row["average_hoteling_kw"])
                    df_transformed.loc[df_transformed["GT Class"] == gt_class, row["vessel_category"]] = row["average_hoteling_kw"]

        st.title("GT Class Cold Ironing Data")
        st.dataframe(df_transformed)

enable_propulsion = st.sidebar.toggle("Enable Propulsion Consumption Calculation", value=False)


if enable_propulsion:
    if st.sidebar.button('Display Propulsion Consumption Reference Data'):
        conn = get_connection()
        queryval = "SELECT * FROM  public.ref_vessel_propulsion_consumption;"
        df_propulsion  = get_data(queryval) 
        # Define GT Class Ranges
        # Define DWT Class Ranges
        dwt_ranges = {
            "0 - 14,000": (0, 14000),
            "14,001 - 30,000": (14001, 30000),
            "30,001 - 50,000": (30001, 50000),
            "50,001 - 82,000": (50001, 82000),
            "82,001 - 135,000": (82001, 135000),
            "135,001 - 160,000": (135001, 160000),
            "160,001 - 200,000": (160001, 200000),
            "200,001 - 320,000": (200001, 320000),
            "320,001 - 999,999,999": (320001, 999999999)
        }

        # Unique vessel categories from the data
        vessel_categories = [
            "Auto Carrier", "Cargo vessels", "Chemical Tankers", "Container vessels",
            "Crude oil tanker", "Cruise ships", "Ferry", "non-serviceble in out business model",
            "Offshore Supply", "not identified", "Service Vessles"
        ]

        # Initialize transformed DataFrame
        transformed_propulsion_data = {
            "Min DWT": [val[0] for val in dwt_ranges.values()],
            "Max DWT": [val[1] for val in dwt_ranges.values()]
        }

        # Populate vessel categories with default value "-"
        for category in vessel_categories:
            transformed_propulsion_data[category] = ["-"] * len(dwt_ranges)

        # Convert transformed data into DataFrame
        df_transformed_propulsion = pd.DataFrame(transformed_propulsion_data)

        # Populate values based on the DWT range
        for index, row in df_propulsion.iterrows():
            for dwt_class, (min_dwt, max_dwt) in dwt_ranges.items():
                if row["min_dwt"] >= min_dwt and row["max_dwt"] <= max_dwt:
                    df_transformed_propulsion.loc[df_transformed_propulsion["Min DWT"] == min_dwt, row["vessel_category"]] = row["propulsion_consumption"]

        st.title("DWT Class Propulsion Consumption Data")
        st.dataframe(df_transformed_propulsion)

if enable_cold_ironing:
    # Fetch Data for Cold Ironing and Propulsion
    cold_iron_query = f"SELECT * FROM reference.ref_cold_ironing_kw WHERE vessel_category = '{vessel_options}';"
    df_cold = get_data(cold_iron_query)
    df_cold['min_gt'] = pd.to_numeric(df_cold['min_gt'], errors='coerce')
    # **Cold Ironing Section*
    st.title('Cold Ironing Calculation')
    st.markdown('## Cold Ironing in kW/h with resepective Gross Tonnage')
    df_cold1 = df_cold.rename(columns={
            "min_gt": "Minimum GT",
            "max_gt": "Maximum GT",
            "vessel_category": "Vessel Category",
            "average_hoteling_kw": "Cold Ironing kW/h"
        })
    st.dataframe(df_cold1)
    col1, col2 = st.columns(2)
    with col1:
        min_gt = int(st.number_input("Select Gross Tonnage (GT)", value=150))
    with col2:
        avg_hoteling_kw = df_cold[(df_cold['min_gt'] <= min_gt) & (df_cold['max_gt'] >= min_gt)]['average_hoteling_kw'].iloc[0]
        avg_hoteling_kw = st.number_input("Cold Ironing kW/h", value=avg_hoteling_kw)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown('## Number of Hours stay at Dock')
        st.markdown('#### Note: Maximum 72hrs is conisder')
    with col2:
        num_stays = st.number_input("Number of Hours of Stay", value=10, min_value=1)

if enable_propulsion:
    propulsion_query = f"SELECT * FROM public.ref_vessel_propulsion_consumption WHERE vessel_category = '{vessel_options}';"
    df_prop = get_data(propulsion_query)
    df_prop['min_dwt'] = pd.to_numeric(df_prop['min_dwt'], errors='coerce')

    # **Propulsion Section**
    st.title('Propulsion Consumption')
    st.markdown('## Propulsion in MWh/NM with resepective Dead Weight Tonnage')
    df_prop1 = df_prop.rename(columns={
            "min_dwt": "Minimum DWT",
            "max_dwt": "Maximum DWT",
            "vessel_category": "Vessel Category",
            "propulsion_consumption": "Propulsion Consumption MWh/NM"
        })
    st.dataframe(df_prop1)
    col1, col2 = st.columns(2)
    with col1:
        min_dwt = int(st.number_input("Select Deadweight Tonnage (DWT)", value=14001))
    with col2:
        propulsion_consumption = df_prop[(df_prop['min_dwt'] <= min_dwt) & (df_prop['max_dwt'] >= min_dwt)]['propulsion_consumption'].iloc[0]
        propulsion_consumption = st.number_input("Propulsion Consumption MWh/NM", value=propulsion_consumption)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown('## Enter Distance in Nuatical Miles')
    with col2:
        distance_NM = st.number_input("Total Distance (NM)", value=100, min_value=1)

st.divider()

# Display formulas
st.markdown(f"## Vessel Categotry {vessel_options}")
if enable_cold_ironing:
    dock_time = num_stays-0.5
    if dock_time >= 72:
        dock_time = 72
    st.markdown("### Docking Time Formula")
    st.latex(r"\text{Berth Docking Time (Hours)} = \text{Number of Stays (Hours)} - \text{Plug-In/Out 30 Minutes (0.5 Hours)}")
    st.markdown("#### Note: Maximum 72hrs is considered.")
    st.success(f"### Berth Docking Time (Hours): {dock_time} hrs")
    st.markdown("### Cold Ironing Calculation Formula")
    st.latex("\\text{Cold Ironing MWh} = \\frac{\\text{Cold Ironing kW/h}}{1000} \\times \\text{Berth Docking Time (hours)}")
    ci = round(avg_hoteling_kw / 1000 * dock_time,3)
    st.success(f"### Cold Ironing MWh: {ci} MWh")

if enable_propulsion:
    st.markdown("### Propulsion Consumption Calculation Formula")
    st.latex("\\text{Propulsion Consumption (MWh)} = \\text{Propulsion Consumption Rate (MWh/nm)} \\times \\text{Travel Distance (NM)}")
    prop = round(propulsion_consumption * distance_NM,3)
    st.success(f"### Propulsion Consumption MWh: {prop} MWh")


# **Emission Calculation Section**
st.divider()
col1, col2,col3 = st.columns(3)
with col1:
    st.title('Emission Calculator')
with col2:
    st.markdown("### Source: United States Environmental Protection Agency")    
with col3:
    st.markdown("### Ref: [Emission Factors Reference](https://nepis.epa.gov/Exe/ZyPDF.cgi?Dockey=P1014J1S.pdf)")
st.divider()
# Display Emission Calculation Formulas
st.title("Emission Calculation Formulas")
if enable_cold_ironing:
    st.markdown("#### Cold Ironing Engine Group: Auxillary")
    st.latex("\\text{Pollutant Emission (g)} = \\text{Cold Ironing Energy (MWh)} \\times \\text{1000} \\times \\text{AVG(Emission Factor) (g/kWh)}")

if enable_propulsion:    
    st.markdown("#### Propulsion Engine Group: Propulsion")
    st.latex("\\text{Pollutant Emission (g)} = \\text{Propulsion Energy (MWh)} \\times \\text{1000} \\times \\text{AVG(Emission Factor) (g/kWh)}")


st.latex("\\text{Total Pollutant Emission (g)} = \\text{Cold Ironing Emission (g)} + \\text{Propulsion Emission (g)}")
st.warning('Note: We are currently selecting the average value. Please choose a different option to reflect another value.')
query_emissions = "SELECT engine_group, pollutant_name, fuel_type, engine_type, emission_factor_formula, values_g_per_kwh FROM reporting.ref_emission_factors;"
df_emissions = get_data(query_emissions)
df_emissions['Selection'] = False


# Initialize session state for pollutant selection tracking
if 'pollutant_state' not in st.session_state:
    st.session_state.pollutant_state = {}

# List of pollutants
pollutants = ['CO2', 'SO2', 'CH4', 'NOx', 'PM10']
st.divider()
# Display pollutant details for Auxiliary and Propulsion
def display_pollutant_values(df, pollutant):
    total_poll_emission = 0 
    col1, col2 = st.columns(2)
    
    with col1:
        # Ensure session state for the pollutant
        if pollutant not in st.session_state.pollutant_state:
            st.session_state.pollutant_state[pollutant] = {'prev_auxiliary_idx': None, 'prev_propulsion_idx': None}
        
        if enable_cold_ironing:
            # Select first available Auxiliary and Propulsion rows by default
            default_aux_index = df[(df['engine_group'] == 'Auxiliary')  & (df['pollutant_name'] == pollutant)].index.min() 

            # # Set default selection in the DataFrame
            # if default_aux_index is not None:
            #     df.at[default_aux_index, 'Selection'] = True

        if enable_propulsion:        
            default_prop_index = df[(df['engine_group'] == 'Propulsion') & (df['pollutant_name'] == pollutant)].index.min()
            
            # if default_prop_index is not None:
            #     df.at[default_prop_index, 'Selection'] = True
        
        # Data editor for selecting values
        emission_df = st.data_editor(
            df, disabled=['emission_factor_formula','engine_group', 'pollutant_name', 'fuel_type', 'engine_type'])
        
    
    with col2:
        selected_auxiliary_value = 0
        selected_propulsion_value = 0

        if enable_cold_ironing:
            # Auxiliary selection handling
            aux_selection = emission_df[(emission_df['Selection'] == True) & (emission_df['engine_group'] == 'Auxiliary') & (emission_df['pollutant_name'] == pollutant)]
            if not aux_selection.empty:
                selected_auxiliary_value = aux_selection['values_g_per_kwh'].iloc[0]
                current_auxiliary_idx = aux_selection.index[0]

                # Unselect the previous Auxiliary if a new one is selected
                if st.session_state.pollutant_state[pollutant]['prev_auxiliary_idx'] is not None and st.session_state.pollutant_state[pollutant]['prev_auxiliary_idx'] != current_auxiliary_idx:
                    emission_df.at[st.session_state.pollutant_state[pollutant]['prev_auxiliary_idx'], 'Selection'] = False

                # Update session state for Auxiliary
                st.session_state.pollutant_state[pollutant]['prev_auxiliary_idx'] = current_auxiliary_idx
            else:
                selected_auxiliary_value = round(emission_df[(emission_df['engine_group'] == 'Auxiliary') & (emission_df['pollutant_name'] == pollutant)]['values_g_per_kwh'].mean() ,2)
                st.warning(f'Cold Ironing - Average Value Calculated : {selected_auxiliary_value}')

        if enable_propulsion:  
            # Propulsion selection handling
            prop_selection = emission_df[(emission_df['Selection'] == True) & (emission_df['engine_group'] == 'Propulsion') & (emission_df['pollutant_name'] == pollutant)]
            if not prop_selection.empty:
                selected_propulsion_value = prop_selection['values_g_per_kwh'].iloc[0]
                current_propulsion_idx = prop_selection.index[0]

                # Unselect the previous Propulsion if a new one is selected
                if st.session_state.pollutant_state[pollutant]['prev_propulsion_idx'] is not None and st.session_state.pollutant_state[pollutant]['prev_propulsion_idx'] != current_propulsion_idx:
                    emission_df.at[st.session_state.pollutant_state[pollutant]['prev_propulsion_idx'], 'Selection'] = False

                # Update session state for Propulsion
                st.session_state.pollutant_state[pollutant]['prev_propulsion_idx'] = current_propulsion_idx
            else:
                selected_propulsion_value = round(emission_df[(emission_df['engine_group'] == 'Propulsion') & (emission_df['pollutant_name'] == pollutant)]['values_g_per_kwh'].mean() ,2)
                st.warning(f'Propulsion - Average Value Calculated : {selected_propulsion_value}')

        cold_ironing_emission = 0
        if enable_cold_ironing:
            cold_ironing_emission = round(ci * selected_auxiliary_value,2)
            # Display selected values
            st.subheader(f'{pollutant} Emission Factors')
            st.success(f"**Selected Cold Ironing Value(g/kWh):** {selected_auxiliary_value if selected_auxiliary_value is not None else 'None'}")
            st.success(f"- **{pollutant} Cold Ironing Emission:** {cold_ironing_emission} g")
        
        propulsion_emission = 0
        
        if enable_propulsion:   
            propulsion_emission = round(prop * selected_propulsion_value,2)
            st.info(f"**Selected Propulsion Value(g/kWh):** {selected_propulsion_value if selected_propulsion_value is not None else 'None'}")
            st.info(f"- **{pollutant} Propulsion Emission:** {propulsion_emission} g")
        
        total_emission = round(cold_ironing_emission + propulsion_emission,2)
        total_poll_emission = total_poll_emission + total_emission
        st.error(f"- **Total {pollutant} Emission:** {total_emission} g")
    st.divider()
    return selected_auxiliary_value, selected_propulsion_value

# Iterate through pollutants and display the UI
for pollutant in pollutants:
    df_filtered = df_emissions[df_emissions['pollutant_name'] == pollutant].copy()

    if enable_cold_ironing == True and enable_propulsion ==False:
        df_filtered = df_filtered[(df_filtered['engine_group'] == 'Auxiliary')]
    elif enable_cold_ironing == False and enable_propulsion ==True:
        df_filtered = df_filtered[(df_filtered['engine_group'] == 'Propulsion')]
    else:
        df_filtered = df_filtered[df_filtered['engine_group'].isin(['Propulsion', 'Auxiliary'])]
    df_filtered  = df_filtered[['Selection','values_g_per_kwh','emission_factor_formula','engine_group', 'pollutant_name', 'fuel_type', 'engine_type']]

    display_pollutant_values(df_filtered, pollutant)

# st.info(f"Total Pollutant Emission{total_poll_emission}")