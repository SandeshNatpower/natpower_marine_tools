import streamlit as st
import geopandas as gpd
from shapely import wkb
import folium
from streamlit_folium import folium_static
import binascii
import pandas as pd
from folium import GeoJson, Popup, GeoJsonTooltip
from datetime import timedelta
import datetime
from datetime import datetime

# Sample DataFrame (already provided)
st.set_page_config(layout="wide")
st.image("images/LinkedIn Header - NatPower Marine.png", caption='© Natpower Marine', use_container_width =True)

st.sidebar.image("images/natpowermarine.png", caption='© Natpower Marine', use_container_width =True)

# Cached database connection and query execution
@st.cache_resource(ttl="10m")
def get_connection():
    return st.connection("postgresql", type="sql")

@st.cache_data(ttl="10m")
def get_data(queryval):
    return conn.query(queryval)


conn = get_connection()
queryval = "select distinct vessel_category FROM reference.ref_vessel_type_category;"
df = get_data(queryval)

# Sidebar filters
st.sidebar.title("Vessel Types - Verticals")

# Filter by Vessel
vessel_cat_list = df["vessel_category"].unique()
if 'Cargo vessels' in vessel_cat_list:
    vessel_index = list(vessel_cat_list).index('Cargo vessels')
else:
    vessel_index = 0 

vessel_options =  st.sidebar.selectbox("Vessel Category", options=vessel_cat_list,index=vessel_index)

queryval = f"select * FROM public.ref_cold_ironing where  vessel_category = '{vessel_options}';"
df_cold = get_data(queryval)
df_cold['min_gt'] = pd.to_numeric(df_cold['min_gt'], errors='coerce')


# Propulsion 
queryval = f"select * FROM public.ref_vessel_propulsion_consumption where  vessel_category = '{vessel_options}';"
df_prop = get_data(queryval)
df_prop['min_dwt'] = pd.to_numeric(df_prop['min_dwt'], errors='coerce')

st.title('Energy Calculator')
maincol1,maincol2 = st.columns(2)
with  maincol1:
    st.title('Cold Ironing - Hoteling - KW')
    col1,col2 = st.columns(2)
    with  col1:
        min_gt = int(st.number_input("Gross Weight Tonnage",value = 150)) 
    with col2:
        average_hoteling_kw = df_cold[(df_cold['min_gt'] >= min_gt) ]['average_hoteling_kw'].iloc[0] #(df_cold['max_gt'] <= max_gt) & 
        average_hoteling_kw = st.number_input("average_hoteling_kw",value = average_hoteling_kw)

with maincol2:
    st.title('Propulsion Consumption MW')
    col1,col2 = st.columns(2)
    with col1:
        min_dwt = int(st.number_input("Dead Weight Tonnage",value = 14001))
    with col2:
        propulsion_consumption = df_prop[(df_prop['min_dwt'] >= min_gt)  ]['propulsion_consumption'].iloc[0] #& (df_prop['max_dwt'] <= max_gt)
        propulsion_consumption = st.number_input("propulsion_consumption",value = propulsion_consumption)        

# Display formulas
st.markdown("### Energy Calculation Formulas")
st.latex("\\text{Average Hoteling MW/h} = \\frac{\\text{Average Hoteling kW}}{1000} \\times \\text{Berth Docking Time (hours)}")
st.latex("\\text{Propulsion Consumption (MWh)} = \\text{Propulsion Consumption Rate (MW)} \\times \\text{Travel Distance (NM)}")


# Title of the app
st.title('Interactive Data Editor for Docking Management')

# Define default values
col1,col2,col3 =st.columns(3)
with col1:
    num_terminals = int(st.number_input("Number Of Terminals ",value = 1))
with col2:
    num_berths = int(st.number_input("Number Of Berth ",value = 1))
with col3:
    num_vessels = int(st.number_input("Number Of Vessels Visited ",value = 1))
col1,col2,col3 =st.columns(3)
with col1:
    plug_unplug_time = int(st.number_input("Time To Plug & Unplug Minutes:",value = 15))
with col2:
    port_dock_time = int(st.number_input("Berth Docking Time Minutes:",value = 60))
with col3:
    nm_distance = int(st.number_input("Nautical Mile Distance:",value = 100))

current_time = datetime.now()

# Calculate start_time and end_time
start_datetime = current_time
end_datetime = start_datetime + pd.to_timedelta(port_dock_time, unit='h')

# Generate default data
@st.cache_data(ttl="10m")
def generate_default_data(num_vessels, num_terminals, num_berths, plug_unplug_time,port_dock_time):
    data = []
    index = 1
    prev_berth_departure = ''
    for vessel in range(1, num_vessels + 1):
        vessel_start_time = start_datetime
        prev_berth_departure =''
        for terminal in range(1, num_terminals + 1):
            for berth in range(1, num_berths + 1):

                # Set berth arrival and departure times within the start and end times
                berth_arrival = vessel_start_time + timedelta(minutes=plug_unplug_time)
                berth_departure = berth_arrival + timedelta(minutes=port_dock_time)
                if prev_berth_departure == '':
                    prev_berth_departure = vessel_start_time
                if berth_departure > end_datetime:
                    berth_departure = end_datetime
                
                data.append({
                    "Vessel ID": f"Vessel_{vessel}",
                    # "Port_Arrival": start_datetime,
                    # "Port_Departure": end_datetime,
                    "Terminal": f"Terminal {terminal}",
                    "Berth": f"Berth {berth}",
                    "Berth_Arrival": berth_arrival,
                    "Berth_Departure": berth_departure,
                    "Berth_Docking_Time": (berth_departure - berth_arrival).total_seconds() / 3600 ,
                    "average_hoteling_MW" : average_hoteling_kw/1000,
                    "average_hoteling_MW/h" : average_hoteling_kw/1000 * (berth_departure - berth_arrival).total_seconds() / 3600,
                    "propulsion_consumption_MWh": propulsion_consumption,
                    "Next_Destination_Nautical_Miles":nm_distance,
                    "propulsion_consumption_mwh/NM": propulsion_consumption * nm_distance,
                    # "Total_energy_consumption_mw/h": (average_hoteling_kw/1000 * (berth_departure - berth_arrival).total_seconds() / 3600 ) + (propulsion_consumption * (berth_arrival - prev_berth_departure).total_seconds() / 3600),
                })
                index += 1
                # Increment the vessel start time for the next berth
                vessel_start_time = berth_departure + timedelta(minutes=plug_unplug_time)
                prev_berth_departure = berth_departure#
    return pd.DataFrame(data)

# Generate default DataFrame
default_df = generate_default_data(num_vessels, num_terminals, num_berths,plug_unplug_time,port_dock_time)

# Initialize the default DataFrame in the session state if it doesn't exist
if 'default_df' not in st.session_state:
    st.session_state.default_df = default_df

# Function to update the values based on edits
@st.cache_data(ttl="10m")
def change_val():
    st.session_state.default_df = st.session_state.default_df
    st.session_state.edited_df = edited_df.copy()
    df = edited_df.copy()  # Work with a copy to avoid in-place modifications
    df['Berth_Docking_Time'] = (df['Berth_Departure'] - df['Berth_Arrival']) / pd.Timedelta(hours=1)
    df['average_hoteling_MW/h'] = df['average_hoteling_MW'] * df['Berth_Docking_Time']
    df['propulsion_consumption_mwh/NM'] = df['propulsion_consumption_MWh'] * df['Next_Destination_Nautical_Miles']
    st.session_state.edited_df = df.copy()
    return df
    # edited_df = df.copy()

# Display editable DataFrame and synchronize edits
st.title('Editable DataFrame')
edited_df = st.data_editor(
    st.session_state.default_df, 
    use_container_width=True, 
    key="data_editor"
)

# Manually trigger the calculation function
change_val()
# Trigger recalculations
updated_df = change_val()
# Update session state with recalculated values
st.session_state.edited_df = change_val().copy()

# Function to highlight changes
@st.cache_data(ttl="10m")
def highlight_changes(val):
    original_val = st.session_state.default_df.loc[val.name, val.index]
    return ['background-color: yellow' if val[col] != original_val[col] else '' for col in val.index]

# Store the editable DataFrame in the session state if it hasn't been stored yet
if 'edited_df' not in st.session_state:
    st.session_state.edited_df = edited_df.copy()
    # st.session_state.default_df = edited_df.copy()
else:
    # If already stored, update it to reflect changes
    st.session_state.edited_df = edited_df.copy()
    # st.session_state.default_df = default_df.copy()

# After Calculation Title
st.title('After Calculation')
# Apply the highlighting and display the DataFrame
# st.session_state.edited_df = updated_df.copy()
styled_df = st.session_state.edited_df.style.apply(highlight_changes, axis=1)

st.dataframe(styled_df)
new_df = styled_df.data

columns_list =['Berth_Docking_Time', 'average_hoteling_MW/h',
                      'propulsion_consumption_mwh/NM']

# Calculate the average (mean) of the specified columns
mean_values = new_df[columns_list].mean()

# Calculate the sum of the specified columns
sum_values = new_df[columns_list].sum()

# Combine the mean and sum into a new DataFrame
result_df = pd.DataFrame({
    'Average Value': mean_values,
    'Total Value': sum_values
})

st.title('Summary Table')
st.dataframe(result_df)
total_hours = new_df["Berth_Docking_Time"].sum()

# Emission
st.title('Emission Calculator')
# df = get_data(f"SELECT engine_group, pollutant_name, fuel_type, engine_type, emission_factor_formula, values_g_per_kwh FROM reporting.ref_emission_factors where pollutant_name = 'CO2';")
df = get_data(f"SELECT engine_group, pollutant_name, fuel_type, engine_type, emission_factor_formula, values_g_per_kwh FROM reporting.ref_emission_factors;")
df['Selection'] = False

# # Initialize session state for tracking previous Auxiliary and Propulsion indices for all pollutants
# pollutants = ['CO2', 'SO2', 'CH4', 'NOx', 'PM10']
# print(df['pollutant_name'].unique())
# if 'pollutant_state' not in st.session_state:
#     st.session_state.pollutant_state = {pollutant: {'prev_auxiliary_idx': None, 'prev_propulsion_idx': None} for pollutant in pollutants}

# # Auxiliary & Propulsion selection logic for each pollutant
# def update_selection(df, pollutant):
#     auxiliary_selected = False
#     propulsion_selected = False
    
#     for index, row in df.iterrows():
#         if row['engine_group'] == 'Auxiliary' and row['pollutant_name'] == pollutant and not auxiliary_selected:
#             df.at[index, 'Selection'] = True
#             auxiliary_selected = True  # Mark auxiliary as selected
#         elif row['engine_group'] == 'Propulsion' and row['pollutant_name'] == pollutant and not propulsion_selected:
#             propulsion_selected = True
#             df.at[index, 'Selection'] = True
#     return df

# # Display pollutant details for Auxiliary and Propulsion
# def display_pollutant_values(df, pollutant):
#     col1, col2 = st.columns(2)
    
#     with col1:
#         emission_df = st.data_editor(
#             df, disabled=('engine_group', 'pollutant_name', 'fuel_type', 'engine_type', 'emission_factor_formula'))
#         st.session_state.emission_df = emission_df
    
#     with col2:
#         selected_auxiliary_value = None
#         selected_propulsion_value = None

#         # Auxiliary selection handling
#         aux_selection = emission_df[(emission_df['Selection'] == True) & (emission_df['engine_group'] == 'Auxiliary') & (emission_df['pollutant_name'] == pollutant)]
#         if not aux_selection.empty:
#             selected_auxiliary_value = aux_selection['values_g_per_kwh'].iloc[0]
#             current_auxiliary_idx = aux_selection.index[0]

#             # Unselect the previous Auxiliary if a new one is selected
#             if st.session_state.pollutant_state[pollutant]['prev_auxiliary_idx'] is not None and st.session_state.pollutant_state[pollutant]['prev_auxiliary_idx'] != current_auxiliary_idx:
#                 emission_df.at[st.session_state.pollutant_state[pollutant]['prev_auxiliary_idx'], 'Selection'] = False

#             # Update session state for Auxiliary
#             st.session_state.pollutant_state[pollutant]['prev_auxiliary_idx'] = current_auxiliary_idx

#         # Propulsion selection handling
#         prop_selection = emission_df[(emission_df['Selection'] == True) & (emission_df['engine_group'] == 'Propulsion') & (emission_df['pollutant_name'] == pollutant)]
#         if not prop_selection.empty:
#             selected_propulsion_value = prop_selection['values_g_per_kwh'].iloc[0]
#             current_propulsion_idx = prop_selection.index[0]

#             # Unselect the previous Propulsion if a new one is selected
#             if st.session_state.pollutant_state[pollutant]['prev_propulsion_idx'] is not None and st.session_state.pollutant_state[pollutant]['prev_propulsion_idx'] != current_propulsion_idx:
#                 emission_df.at[st.session_state.pollutant_state[pollutant]['prev_propulsion_idx'], 'Selection'] = False

#             # Update session state for Propulsion
#             st.session_state.pollutant_state[pollutant]['prev_propulsion_idx'] = current_propulsion_idx

#         # Display selected values
#         st.title(f'{pollutant} Emission')
#         st.write("Selected Auxiliary Value:", selected_auxiliary_value if selected_auxiliary_value is not None else "None")
#         st.write("Selected Propulsion Value:", selected_propulsion_value if selected_propulsion_value is not None else "None")

# # Process and display each pollutant
# for pollutant in pollutants:
#     st.write(pollutant)
#     try:
#         df_filtered = df[df['pollutant_name'] == pollutant].copy()  # Filter dataframe for the specific pollutant
#         df_filtered = update_selection(df_filtered, pollutant)  # Update selection for auxiliary and propulsion
#         display_pollutant_values(df_filtered, pollutant)  # Display the values
#     except:
#         st.write("No data available for this pollutant")  # Display a message if no data


# Initialize session state for tracking previous Auxiliary and Propulsion indices for all pollutants
pollutants = ['CO2', 'SO2', 'CH4', 'NOx', 'PM10']
if 'pollutant_state' not in st.session_state:
    st.session_state.pollutant_state = {pollutant: {'prev_auxiliary_idx': None, 'prev_propulsion_idx': None} for pollutant in pollutants}

# Auxiliary & Propulsion selection logic for each pollutant
def update_selection(df, pollutant):
    auxiliary_selected = False
    propulsion_selected = False
    
    for index, row in df.iterrows():
        if row['engine_group'] == 'Auxiliary' and row['pollutant_name'] == pollutant and not auxiliary_selected:
            df.at[index, 'Selection'] = True
            auxiliary_selected = True  # Mark auxiliary as selected
        elif row['engine_group'] == 'Propulsion' and row['pollutant_name'] == pollutant and not propulsion_selected:
            df.at[index, 'Selection'] = True
            propulsion_selected = True
    return df

# Display pollutant details for Auxiliary and Propulsion
def display_pollutant_values(df, pollutant):
    col1, col2 = st.columns(2)
    
    with col1:
        emission_df = st.data_editor(
            df, disabled=('engine_group', 'pollutant_name', 'fuel_type', 'engine_type', 'emission_factor_formula'))
        st.session_state.emission_df = emission_df
    
    with col2:
        selected_auxiliary_value = None
        selected_propulsion_value = None

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

        # Display selected values
        st.title(f'{pollutant} Emission')
        st.write("Selected Auxiliary Value:", selected_auxiliary_value if selected_auxiliary_value is not None else "None")
        st.write("Selected Propulsion Value:", selected_propulsion_value if selected_propulsion_value is not None else "None")

    return selected_auxiliary_value, selected_propulsion_value

# Process and display each pollutant, and compute emissions
pollutant_emissions = {}

st.markdown("### Source: United States Environmental Protection Agency")
st.markdown("[Emission Factors Reference](https://nepis.epa.gov/Exe/ZyPDF.cgi?Dockey=P1014J1S.pdf)")

# Display Emission Calculation Formulas
st.markdown("### Emission Calculation Formulas")
st.latex("\\text{Pollutant Emission} = \\text{Energy Consumption} \\times \\text{Emission Factor (g/kWh)}")
st.latex("\\text{Total Emission} = \\text{Cold Ironing Emission} + \\text{Propulsion Emission}")

for pollutant in pollutants:
    df_filtered = df[df['pollutant_name'] == pollutant].copy()  # Filter dataframe for the specific pollutant
    df_filtered = update_selection(df_filtered, pollutant)  # Update selection for auxiliary and propulsion
    
    selected_auxiliary_value, selected_propulsion_value = display_pollutant_values(df_filtered, pollutant)  # Display the values
    
    if selected_auxiliary_value is not None and selected_propulsion_value is not None:
        # st.dataframe(new_df)
        # Calculate emissions based on selections and store them
        pollutant_emissions[f'{pollutant}_cold_ironing_emission'] = new_df['average_hoteling_MW/h'] * selected_auxiliary_value
        pollutant_emissions[f'{pollutant}_propulsion_emission'] = new_df['propulsion_consumption_mwh/NM'] * selected_propulsion_value
        pollutant_emissions[f'Total_{pollutant}_propulsion_emission'] = pollutant_emissions[f'{pollutant}_cold_ironing_emission']  +  pollutant_emissions[f'{pollutant}_propulsion_emission']


# Add pollutant emissions to the DataFrame
for pollutant, emission_values in pollutant_emissions.items():
    new_df[pollutant] = emission_values

st.title('Emission Calculations')
# Display the final DataFrame with calculated emissions
st.dataframe(new_df)


@st.cache_data(ttl="10m")
def co2_change_val():
    # Add code here to display the records
    print('x')
   
@st.cache_data(ttl="10m")
def highlight_changes_co2(val):
    original_val = st.session_state.emission_df.loc[val.name, val.index]
    return ['background-color: yellow' if val[col] != original_val[col] else '' for col in val.index]


# Manually trigger the calculation function
co2_change_val()