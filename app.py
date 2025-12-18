import streamlit as st
import pandas as pd
import numpy as np
import time
import random
from datetime import datetime
from queue import Queue
from pathlib import Path
import altair as alt

import paho.mqtt.client as mqtt
import json
import threading # Required for mqtt client in background thread

# For GIS map
import folium
from streamlit_folium import st_folium
from fastkml import kml, Placemark, Point

# --- Configuration ---
st.set_page_config(
    page_title="HybridFuel Dashboard",
    page_icon="🔥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Custom CSS for Sidebar ---
st.markdown("""
<style>
    /* Target the sidebar's button container */
    [data-testid="stSidebar"] .stButton {
        /* Set a large minimum height for each button */
        min-height: 25vh; /* Each button takes ~25% of viewport height */
        flex-grow: 1; /* Allow them to grow and fill space */
        margin: 0.5rem 0; /* Add a little vertical spacing */
    }

    /* Target the actual button element inside the container */
    [data-testid="stSidebar"] .stButton > button {
        display: flex;
        flex-direction: column; /* Stack content vertically */
        justify-content: center;
        align-items: center;
        width: 100%;
        height: 100%; /* Make button fill its container */
        padding: 1rem 0; /* Add some padding */
    }

    /* Target the text (as a <p> tag) inside the button */
    [data-testid="stSidebar"] .stButton p {
        font-size: 1rem !important; /* Force normal size text */
        line-height: 1.3;
        text-align: center; /* Ensure text is centered */
    }

    /* Add the giant emoji using ::before pseudo-element */
    /* We must target them by their order in the sidebar */

    /* 1st Button: IoT */
    [data-testid="stSidebar"] .stButton:nth-of-type(1) button::before {
        content: '🏭'; /* The emoji */
        font-size: 4.5rem; /* HUGE emoji */
        line-height: 1.1; /* Adjust spacing */
        margin-bottom: 0.5rem; /* Space between emoji and text */
    }

    /* 2nd Button: AI */
    [data-testid="stSidebar"] .stButton:nth-of-type(2) button::before {
        content: '🤖'; /* The emoji */
        font-size: 4.5rem; /* HUGE emoji */
        line-height: 1.1;
        margin-bottom: 0.5rem;
    }

    /* 3rd Button: GIS */
    [data-testid="stSidebar"] .stButton:nth-of-type(3) button::before {
        content: '🗺️'; /* The emoji */
        font-size: 4.5rem; /* HUGE emoji */
        line-height: 1.1;
        margin-bottom: 0.5rem;
    }

    /* Align columns to bottom */
    [data-testid="column"] {
        align-items: flex-end !important;
        min-height: 80px;
    }
</style>
""", unsafe_allow_html=True)


# --- Language/Translation Setup ---
LANGUAGES = {
    "English": {
        "app_title": "HybridFuel: Biogas-Coal Optimization System",
        "page_iot": "IoT Sensor Dashboard",
        "page_ai": "Blend Optimizer",
        "page_gis": "GIS Feedstock Map",
        "iot_header": "Real-time Combustion Monitoring",
        "iot_subheader": "Live data from IoT sensors (via MQTT)",
        "current_temp": "Current Temperature",
        "current_co2": "Current CO2 (Gas)",
        
        "current_pm25": "Current PM2.5 (Dust)",
        "historical_temp": "Historical Temperature (°C)",
        "historical_emissions": "Historical Emissions (ppm / µg/m³)",
        "historical_data_header": "Historical Data Log",
        "ai_header": "Fuel Blend Optimization",
        "coal_input": "Coal Input (Tons/hour)",
        "biogas_mix": "Biogas Mix (%)",
        "optimize_button": "Run Optimization",
        "ai_recommendation": "AI Recommendation",
        "pred_power": "Predicted Power Output (MW)",
        "pred_reduction": "Predicted PM2.5 Reduction",
        "safety_check": "Safety & Feasibility Check",
        "safety_ok": "✅ Biogas percentage is within safe operational parameters.",
        "safety_warn": "⚠️ High biogas percentage (>40%) may require equipment retrofitting. Proceed with caution.",
        "optimal_blend_is": "Optimal blend for max efficiency & min pollution:",
        "gis_header": "GIS Feedstock & Logistics Dashboard",
        "gis_subheader": "This dashboard will map regional waste feedstock sources, biogas generation potential, and industrial fuel demand.",
        "gis_placeholder": "Simple map of India. Full GIS data will be integrated later.",
    },
    "Hindi (हिन्दी)": {
        "app_title": "HybridFuel: बायोगैस-कोयला अनुकूलन प्रणाली",
        "page_iot": "IoT सेंसर डैशबोर्ड",
        "page_ai": "ब्लेंड ऑप्टिमाइज़र",
        "page_gis": "GIS फीडस्टॉक मानचित्र",

        "iot_header": "वास्तविक समय दहन निगरानी",
        "iot_subheader": "IoT सेंसर से लाइव डेटा (MQTT के माध्यम से)",

        "current_temp": "वर्तमान तापमान",
        "current_co2": "वर्तमान CO2 (गैस)",
        "current_pm25": "वर्तमान PM2.5 (धूल)",

        "historical_temp": "ऐतिहासिक तापमान (°C)",
        "historical_emissions": "ऐतिहासिक उत्सर्जन (ppm / µg/m³)",
        "historical_data_header": "ऐतिहासिक डेटा लॉग",

        "ai_header": "ईंधन मिश्रण अनुकूलन",
        "coal_input": "कोयला इनपुट (टन/घंटा)",
        "biogas_mix": "बायोगैस मिश्रण (%)",
        "optimize_button": "अनुकूलन चलाएँ",

        "ai_recommendation": "AI सिफ़ारिश",
        "pred_power": "अनुमानित विद्युत उत्पादन (MW)",
        "pred_reduction": "अनुमानित PM2.5 में कमी",

        "safety_check": "सुरक्षा और व्यवहार्यता जांच",
        "safety_ok": "✅ बायोगैस प्रतिशत सुरक्षित परिचालन सीमा के भीतर है।",
        "safety_warn": "⚠️ उच्च बायोगैस प्रतिशत (>40%) के लिए उपकरणों में संशोधन आवश्यक हो सकता है। सावधानी से आगे बढ़ें।",

        "optimal_blend_is": "अधिकतम दक्षता और न्यूनतम प्रदूषण के लिए इष्टतम मिश्रण:",

        "gis_header": "GIS फीडस्टॉक और लॉजिस्टिक्स डैशबोर्ड",
        "gis_subheader": "यह डैशबोर्ड क्षेत्रीय अपशिष्ट फीडस्टॉक स्रोतों, बायोगैस उत्पादन क्षमता और औद्योगिक ईंधन मांग को मैप करेगा।",
        "gis_placeholder": "भारत का सरल मानचित्र। पूर्ण GIS डेटा बाद में एकीकृत किया जाएगा।",
    }
}

# --- Language Selection in Top Right (using columns) ---
col1, col_spacer, col2 = st.columns([5, 1, 1])

with col1:
    # This will be set after language is selected
    pass

with col2:
    if 'lang' not in st.session_state:
        st.session_state.lang = "English"

    st.session_state.lang = st.selectbox(
        "Language / भाषा",
        options=LANGUAGES.keys(),
        label_visibility="collapsed",
        index=0 if st.session_state.lang == "English" else 1
    )

# Get translated text
T = LANGUAGES[st.session_state.lang]

# Initialize current_page if not set
if 'current_page' not in st.session_state:
    st.session_state.current_page = "iot"

# Set the main app title and page header in the first column
with col1:
    if st.session_state.current_page == "iot":
        st.header(T["iot_header"])
    elif st.session_state.current_page == "ai":
        st.header(T["ai_header"])
    elif st.session_state.current_page == "gis":
        st.header(T["gis_header"])

# --- MQTT Client Setup with Queue ---
BROKER = "broker.hivemq.com"
PORT = 1883

# MQTT Topics for different sensor locations (currently all use the same topic)
MQTT_TOPICS = {
    "Jharkhand": "proyek/iot/sl2_ignis",
    "Chhattisgarh": "proyek/iot/sl2_ignis",  # Same topic for now
    "Odisha": "proyek/iot/sl2_ignis"  # Same topic for now
}

# Global variable for current subscribed topic (to avoid session state in callbacks)
current_subscribed_topic = "proyek/iot/sl2_ignis"

# Initialize session state variables
if 'mqtt_client_initialized' not in st.session_state:
    st.session_state.mqtt_client_initialized = False
    st.session_state.mqtt_data_queue = Queue()
    st.session_state.latest_mqtt_data = {
        "timestamp": datetime.now(),
        "Temperature": 0.0,
          "CO2": 0.0, 
          "PM2_5": 0, 
        "status": "NOT FOUND"
    }

# Get queue reference (thread-safe, no session state access needed)
if 'mqtt_data_queue' not in st.session_state:
    st.session_state.mqtt_data_queue = Queue()

# Use a module-level variable for the queue to avoid session state access in callbacks
_mqtt_queue = st.session_state.mqtt_data_queue

# File to persist history between restarts
DATA_FILE = Path(__file__).parent / "iot_history.csv"

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("MQTT: Connected to Broker!")
        client.subscribe(current_subscribed_topic)
    else:
        print(f"MQTT: Failed to connect, return code {rc}")

def on_message(client, userdata, msg):
    try:
        raw_data = msg.payload.decode()
        # print(f"\n[RAW DATA TERIMA]: {raw_data}")
        data = json.loads(raw_data)

        # AMBIL DATA SATU PER SATU (FETCHING)
        dust = data.get('pm25', 0.0)      # Debu level (%)
        gas = data.get('gas', 0.0)        # Udara quality (ppb)
        temp = data.get('temp', 0.0)      # Suhu (°C)
        status = data.get('status', 'UNKNOWN')

        # # --- DISINI TEMANMU OLAH DATANYA ---
        # print(f"--- PARSED DATA ---")
        # print(f"Debu   : {dust} %")
        # print(f"Udara  : {gas} ppb")
        # print(f"Suhu   : {temp} C")
        # print(f"Status : {status}")

        # Contoh Logic Olah Data:
        if status == "DANGER":
            print(">>> WARNING: DATA BAHAYA TERCATAT KE DATABASE! <<<")

        new_iot_data = {
            "timestamp": datetime.now(),
            "Temperature": temp,
            "CO2": gas, 
            "PM2_5": dust,
            "status": status
        }

        # Put data in queue (thread-safe, no session state access)
        _mqtt_queue.put(new_iot_data)
        
    except Exception as e:
        print(f"MQTT: Error parsing message: {e}")

if st.session_state.mqtt_client_initialized == False:
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message

    try:
        client.connect(BROKER, PORT, 60)
        client.loop_start() # Start background thread for MQTT
        st.session_state.mqtt_client_instance = client # Store client instance
        st.session_state.mqtt_client_initialized = True
        print("MQTT client setup complete and loop started.")
    except Exception as e:
        print(f"MQTT: Failed to connect to broker: {e}")
        st.error(f"Failed to connect to MQTT broker: {e}")

# --- Initialize Session State for IoT Data ---
if 'iot_history' not in st.session_state:
    # Try to load persisted history from CSV
    if DATA_FILE.exists():
        try:
            df = pd.read_csv(DATA_FILE, parse_dates=['timestamp'])
            # Ensure expected columns exist
            expected = ["timestamp", "Temperature", "CO2", "PM2_5", "status"]
            for c in expected:
                if c not in df.columns:
                    df[c] = 0 if c != 'timestamp' else pd.NaT
            st.session_state.iot_history = df[ ["timestamp", "Temperature", "CO2", "PM2_5", "status"] ]
        except Exception:
            st.session_state.iot_history = pd.DataFrame(columns=["timestamp", "Temperature", "CO2", "PM2_5", "status"])
    else:
        st.session_state.iot_history = pd.DataFrame(columns=["timestamp", "Temperature", "CO2", "PM2_5", "status"])

# --- Helper Function for IoT Data ---
def get_new_iot_data():
    """Generates a new row of fake IoT data (now unused, data comes from MQTT)."""
    # This function is now effectively replaced by MQTT data, but kept for structure if needed
    return {
        "timestamp": datetime.now(),
        "Temperature": 0.0,
        "CO2": 0.0,
        "PM2_5": 0
    }

def append_to_history(new_data_row):
    """Appends new data to the session state history."""
    new_df_row = pd.DataFrame([new_data_row])
    # Use a lock if iot_history is modified from non-Streamlit thread
    # For simplicity, assuming Streamlit's rerun mechanism handles eventual consistency
    st.session_state.iot_history = pd.concat(
        [st.session_state.iot_history, new_df_row],
        ignore_index=True
    )
    # Unlimited history

# --- Page 1: IoT Sensor Dashboard ---
def page_iot():
    st.subheader(T["iot_subheader"])
    # Sensor Location Selection and Monitoring in one row
    st.markdown("""
    <style>
    .sensor-row {
        display: flex;
        align-items: flex-end;
        gap: 1rem;
    }
    </style>
    """, unsafe_allow_html=True)
    
    with st.container():
        col_sel, col_mon = st.columns([1, 1])
        
        with col_sel:
            sensor_locations = ["Jharkhand", "Chhattisgarh", "Odisha"]
            if 'selected_sensor' not in st.session_state:
                st.session_state.selected_sensor = "Jharkhand"
            
            st.session_state.selected_sensor = st.selectbox(
                "Select Sensor Location:",
                options=sensor_locations,
                index=sensor_locations.index(st.session_state.selected_sensor)
            )
        
        with col_mon:
            st.info(f"📍 Currently monitoring: **{st.session_state.selected_sensor}**")
    
    # Handle topic change if sensor location changed
    global current_subscribed_topic
    new_topic = MQTT_TOPICS[st.session_state.selected_sensor]
    if new_topic != current_subscribed_topic:
        # Unsubscribe from old topic and subscribe to new one
        if st.session_state.mqtt_client_instance:
            st.session_state.mqtt_client_instance.unsubscribe(current_subscribed_topic)
            st.session_state.mqtt_client_instance.subscribe(new_topic)
            print(f"MQTT: Switched topic from {current_subscribed_topic} to {new_topic}")
        current_subscribed_topic = new_topic
    
    # (Import moved below historical data table)

    # Process all pending messages from MQTT queue
    while not st.session_state.mqtt_data_queue.empty():
        try:
            latest_data = st.session_state.mqtt_data_queue.get_nowait()
            st.session_state.latest_mqtt_data = latest_data
            
            # Add to history if it's new
            if len(st.session_state.iot_history) == 0 or latest_data['timestamp'] != st.session_state.iot_history.iloc[-1]['timestamp']:
                new_df_row = pd.DataFrame([latest_data])
                st.session_state.iot_history = pd.concat(
                    [st.session_state.iot_history, new_df_row],
                    ignore_index=True
                )
                # Unlimited history
                # Persist history to CSV so data survives restarts
                try:
                    st.session_state.iot_history.to_csv(DATA_FILE, index=False)
                except Exception as e:
                    print(f"Failed to save history to CSV: {e}")
        except:
            pass
    
    latest_data = st.session_state.latest_mqtt_data
    
    col1, col2 = st.columns(2)

    # =====================
    # STATUS CARD
    # =====================
    status = latest_data["status"]

    if status == "DANGER":
        status_color = "#ff4d4f"
        status_icon = "⚠️"
    elif status == "WARNING":
        status_color = "#faad14"
        status_icon = "⚠️"
    else:
        status_color = "#52c41a"
        status_icon = "✅"

    with col1:
        st.markdown(f"""
        <div style="
            border: 2px solid {status_color};
            border-radius: 12px;
            padding: 20px;
            background-color: #ffffff;
        ">
            <h3>System Status</h3>
            <p style="
                color:{status_color};
                font-size:20px;
                font-weight:bold;
                margin-top:10px;
            ">
                {status_icon} {status}
            </p>
        </div>
        """, unsafe_allow_html=True)

    temp = latest_data['Temperature']
    gas = latest_data['CO2']
    dust = latest_data['PM2_5']

    recommendations = []

    if temp > 30.0:
        recommendations.append("🔥 High temperature detected. Reduce fuel input or increase cooling.")
    elif temp < 16.4:
        recommendations.append("❄️ Low temperature. Increase fuel or check insulation.")

    if gas > 100:
        recommendations.append("💨 High CO₂ levels. Improve ventilation or reduce emissions.")

    if dust > 50:
        recommendations.append("🌫️ High dust levels. Clean filters or reduce particulate sources.")

    if not recommendations:
        recommendations.append("✅ All parameters within optimal range. System operating normally.")

    rec_html = "".join(f"<li>{r}</li>" for r in recommendations)

    with col2:
        st.markdown(f"""
        <div style="
            border: 2px solid #ddd;
            border-radius: 12px;
            padding: 20px;
            background-color: #ffffff;
        ">
            <h3>AI Recommendations</h3>
            <ul style="margin-top:10px;">
                {rec_html}
            </ul>
        </div>
        """, unsafe_allow_html=True)


    # Display current metrics
    st.divider()
    col1, col2, col3 = st.columns(3)

    # Calculate deltas for metrics. Handle initial state where history might be empty or short.
    prev_temp = st.session_state.iot_history.iloc[-2]['Temperature'] if len(st.session_state.iot_history) > 1 else latest_data['Temperature']
    prev_gas = st.session_state.iot_history.iloc[-2]['CO2'] if len(st.session_state.iot_history) > 1 else latest_data['CO2']
    prev_dust = st.session_state.iot_history.iloc[-2]['PM2_5'] if len(st.session_state.iot_history) > 1 else latest_data['PM2_5']

    col1.metric(T["current_temp"], f"{latest_data['Temperature']:.1f} °C", f"{latest_data['Temperature'] - prev_temp:+.1f}")
    col2.metric(T["current_co2"], f"{latest_data['CO2']:.1f} ppb", f"{latest_data['CO2'] - prev_gas:+.1f}") # Air quality (gas in ppb)
    col3.metric(T["current_pm25"], f"{latest_data['PM2_5']:.1f} %", f"{latest_data['PM2_5'] - prev_dust:+.1f}") # Dust level in %
    st.divider()

    # Display historical charts
    history_df = st.session_state.iot_history.set_index("timestamp")

    if not history_df.empty:
        st.subheader(T["historical_temp"])
        # Altair chart with y-axis starting at 10
        temp_df = history_df["Temperature"].reset_index().rename(columns={'timestamp': 'timestamp', 'Temperature': 'Temperature'})
        try:
            chart = alt.Chart(temp_df).mark_line().encode(
                x=alt.X('timestamp:T', title='Timestamp'),
                y=alt.Y('Temperature:Q', scale=alt.Scale(domain=[10, temp_df['Temperature'].max() if not temp_df['Temperature'].isnull().all() else 10])),
                tooltip=['timestamp:T','Temperature']
            ).interactive()
            st.altair_chart(chart, use_container_width=True)
        except Exception:
            # Fallback
            st.line_chart(history_df["Temperature"])

        st.subheader("Historical Gas (CO2) - ppb")
        st.line_chart(history_df[["CO2"]])

        st.subheader("Historical Dust (PM2.5) - %")
        st.line_chart(history_df[["PM2_5"]])

        st.subheader(T["historical_data_header"])
        st.dataframe(st.session_state.iot_history.sort_values('timestamp', ascending=False), use_container_width=True, height=400)

        # CSV importer placed below historical data table
        uploaded = st.file_uploader("Import history CSV", type=["csv"], accept_multiple_files=False)
        if uploaded is not None:
            try:
                imported_df = pd.read_csv(uploaded, parse_dates=['timestamp'])
                # Normalize columns
                if 'PM2_5' not in imported_df.columns and 'PM2.5' in imported_df.columns:
                    imported_df = imported_df.rename(columns={'PM2.5': 'PM2_5'})
                expected = ["timestamp", "Temperature", "CO2", "PM2_5"]
                missing = [c for c in expected if c not in imported_df.columns]
                if missing:
                    st.error(f"Imported CSV is missing columns: {missing}")
                else:
                    mode = st.radio("Import mode", ["append (merge)", "replace"], index=0)
                    if st.button("Apply import"):
                        imported_df = imported_df[["timestamp", "Temperature", "CO2", "PM2_5"]]
                        # ensure timestamp dtype
                        imported_df['timestamp'] = pd.to_datetime(imported_df['timestamp'])
                        if mode == 'replace':
                            st.session_state.iot_history = imported_df
                        else:
                            combined = pd.concat([st.session_state.iot_history, imported_df], ignore_index=True)
                            combined = combined.drop_duplicates(subset=['timestamp'])
                            combined = combined.sort_values('timestamp')
                            st.session_state.iot_history = combined
                        # persist
                        try:
                            st.session_state.iot_history.to_csv(DATA_FILE, index=False)
                            st.success('Import applied and saved')
                            st.rerun()  # Refresh charts with new data
                        except Exception as e:
                            st.error(f'Import applied but failed to save: {e}')
            except Exception as e:
                st.error(f"Failed to parse uploaded CSV: {e}")

    # Removed periodic rerun to allow proper navigation

# --- Page 2: AI Blend Optimizer ---
def page_ai_optimizer():
    # ---------------------------------------------------
    # 1. REAL COAL PLANT DATA (YOUR PROVIDED DATA)
    # ---------------------------------------------------
    plants_data = [
        {'plant_name':'North Karanpura STPP','coal_tons':7969147,'TSP':23907,'PM10':14344,'PM2.5':12910,'SO2':55784},
        {'plant_name':'Patratu STPP','coal_tons':8229144,'TSP':28802,'PM10':17281,'PM2.5':15553,'SO2':41146},
        {'plant_name':'Tenughat TPS','coal_tons':2233800,'TSP':15637,'PM10':9382,'PM2.5':8444,'SO2':13403},
        {'plant_name':'Talcher Kaniha','coal_tons':10704720,'TSP':42819,'PM10':25691,'PM2.5':23122,'SO2':85638},
        {'plant_name':'Darlipali','coal_tons':8563776,'TSP':29117,'PM10':17470,'PM2.5':15723,'SO2':33913},
        {'plant_name':'IB Thermal','coal_tons':9493650,'TSP':34177,'PM10':20506,'PM2.5':18456,'SO2':28196},
        {'plant_name':'Korba Super Thermal','coal_tons':9825216,'TSP':29476,'PM10':17685,'PM2.5':15917,'SO2':29181},
        {'plant_name':'Sipat Super Thermal','coal_tons':10233432,'TSP':34794,'PM10':20876,'PM2.5':18789,'SO2':50655}
    ]

    df_plants = pd.DataFrame(plants_data)

    # ---------------------------------------------------
    # LEARN AVERAGE COAL EMISSION FACTORS
    # ---------------------------------------------------
    pollutants = ["TSP", "PM10", "PM2.5", "SO2"]
    coal_EF_real = {pol: (df_plants[pol] / df_plants["coal_tons"]).mean() for pol in pollutants}

    # ---------------------------------------------------
    # BIOGAS EMISSION FACTORS (tons/ton fuel)
    # ---------------------------------------------------
    biogas_EF = {
        'TSP':   0.05/1000,
        'PM10':  0.05/1000,
        'PM2.5': 0.02/1000,
        'SO2':   0.01/1000,
        'NOx':   0.50/1000
    }

    # ---------------------------------------------------
    # STREAMlit UI
    # ---------------------------------------------------
    st.write("Calculate your emissions after blending biogas with coal")

    st.markdown("---")

    st.subheader("Plant Input Data")

    col1, col2 = st.columns(2)

    with col1:
        coal_consumption = st.number_input("Coal consumption (tons/year):", min_value=0.0, value=1000000.0)

    with col2:
        biogas_frac = st.slider("Biogas blending fraction:", 0.0, 1.0, 0.1)

    st.subheader("Baseline Emissions (tons/year)")
    col3, col4, col5, col6 = st.columns(4)

    with col3:
        st.write("Total Suspended Particulates")
        TSP_in = st.number_input("TSP", min_value=0.0, value=500.0)
    with col4:
        PM10_in = st.number_input("PM10", min_value=0.0, value=400.0)
    with col5:
        PM25_in = st.number_input("PM2.5", min_value=0.0, value=300.0)
    with col6:
        SO2_in = st.number_input("SO2", min_value=0.0, value=800.0)

    st.subheader("Pollution Control Systems")

    col7, col8 = st.columns(2)

    with col7:
        st.write("Electrostatic Precipitator")
        ESP = st.slider("ESP Efficiency (%)", 0, 100, 90)
    with col8:
        st.write("Flue Gas Desulfurization")
        FGD = st.slider("FGD Efficiency (%)", 0, 100, 70)

    # ---------------------------------------------------
    # CALCULATE OUTPUTS
    # ---------------------------------------------------
    coal_share = 1 - biogas_frac
    bio_share = biogas_frac

    coal_baseline = {
        "TSP": TSP_in,
        "PM10": PM10_in,
        "PM2.5": PM25_in,
        "SO2": SO2_in,
        "NOx": 0.0
    }

    results = {}

    for pol in coal_baseline:
        coal_part = coal_baseline[pol] * coal_share
        bio_part = biogas_EF[pol] * coal_consumption * bio_share
        total = coal_part + bio_part

        if pol in ["TSP","PM10","PM2.5"]:
            total *= (1 - ESP/100)

        if pol == "SO2":
            total *= (1 - FGD/100)

        results[pol] = total

    # ---------------------------------------------------
    # OUTPUT TABLE DISPLAY
    # ---------------------------------------------------
    df_out = pd.DataFrame({
        "Pollutant": list(coal_baseline.keys()),
        "Baseline_Emissions (tons)": list(coal_baseline.values()),
        "Blended_Emissions (tons)": [results[p] for p in coal_baseline],
        "Reduction (%)": [
            round((1 - results[p]/coal_baseline[p])*100,2) if coal_baseline[p] > 0 else "N/A"
            for p in coal_baseline.keys()
        ]
    })

    st.subheader("Final Results")

    st.dataframe(df_out, use_container_width=True)

    st.subheader("Summary")

    for pol in ["TSP", "PM10", "PM2.5", "SO2"]:
        reduction = df_out.loc[df_out["Pollutant"] == pol, "Reduction (%)"].values[0]
        st.success(f"**{pol} Reduction:** {reduction}%")


# --- Page 3: GIS Feedstock Map ---
def page_gis_map():
    st.write("Interactive GIS Feedstock & Logistics Dashboard")
    st.write("Map showing industries, coal mines, biomass villages, waste sites, pollution hotspots, and transport routes.")
    
    # Sample data - replace with your actual geocoded data from Google My Maps
    # Industries (power plants)
    industries = [
        {"name": "North Karanpura STPP", "lat": 23.8, "lon": 85.5},
        {"name": "Patratu STPP", "lat": 23.7, "lon": 85.3},
        {"name": "Tenughat TPS", "lat": 23.6, "lon": 85.1},
    ]
    
    # Coal mines
    coal_mines = [
        {"name": "Coal Mine 1", "lat": 23.9, "lon": 85.6},
        {"name": "Coal Mine 2", "lat": 23.5, "lon": 85.2},
    ]
    
    # Biomass villages
    biomass_villages = [
        {"name": "Biomass Village A", "lat": 23.4, "lon": 85.0},
        {"name": "Biomass Village B", "lat": 23.3, "lon": 84.9},
    ]
    
    # Waste sites
    waste_sites = [
        {"name": "Waste Site 1", "lat": 23.2, "lon": 84.8},
    ]
    
    # Pollution hotspots
    pollution_hotspots = [
        {"name": "Hotspot 1", "lat": 23.1, "lon": 84.7},
    ]
    
    # Transport routes (lines connecting sources to destinations)
    routes = [
        {"from": biomass_villages[0], "to": industries[0], "color": "green"},
        {"from": biomass_villages[1], "to": industries[1], "color": "blue"},
        {"from": coal_mines[0], "to": industries[0], "color": "black"},
    ]
    
    # Create folium map
    import folium
    from streamlit_folium import st_folium
    import fastkml
    
    m = folium.Map(location=[23.5, 85.0], zoom_start=8)
    
    # Load KML file
    kml_file = 'Only 2 checked KORBA (1).kml'
    try:
        k = kml.KML()
        with open(kml_file, 'r', encoding='utf-8') as f:
            k.from_string(f.read())
        for feature in k.features():
            for subfeature in feature.features:
                if isinstance(subfeature, Placemark) and subfeature.geometry:
                    geom = subfeature.geometry
                    if isinstance(geom, Point):
                        lon, lat, alt = geom.coords[0]  # Note: KML is lon, lat
                        folium.Marker(
                            location=[lat, lon],
                            popup=subfeature.name
                        ).add_to(m)
    except Exception as e:
        st.error(f"Error loading KML: {e}")
    
    # # Add markers for industries
    # for ind in industries:
    #     folium.Marker(
    #         location=[ind["lat"], ind["lon"]],
    #         popup=f"Industry: {ind['name']}",
    #         icon=folium.Icon(color="red")
    #     ).add_to(m)
    
    # # Add markers for coal mines
    # for mine in coal_mines:
    #     folium.Marker(
    #         location=[mine["lat"], mine["lon"]],
    #         popup=f"Coal Mine: {mine['name']}",
    #         icon=folium.Icon(color="black")
    #     ).add_to(m)
    
    # # Add markers for biomass villages
    # for village in biomass_villages:
    #     folium.Marker(
    #         location=[village["lat"], village["lon"]],
    #         popup=f"Biomass Village: {village['name']}",
    #         icon=folium.Icon(color="green")
    #     ).add_to(m)
    
    # # Add markers for waste sites
    # for waste in waste_sites:
    #     folium.Marker(
    #         location=[waste["lat"], waste["lon"]],
    #         popup=f"Waste Site: {waste['name']}",
    #         icon=folium.Icon(color="orange")
    #     ).add_to(m)
    
    # # Add markers for pollution hotspots
    # for hotspot in pollution_hotspots:
    #     folium.Marker(
    #         location=[hotspot["lat"], hotspot["lon"]],
    #         popup=f"Pollution Hotspot: {hotspot['name']}",
    #         icon=folium.Icon(color="purple")
    #     ).add_to(m)
    
    # Add routes as polylines (commented out to avoid serialization issues)
    # for route in routes:
    #     folium.PolyLine(
    #         locations=[[route["from"]["lat"], route["from"]["lon"]], [route["to"]["lat"], route["to"]["lon"]]],
    #         color=route["color"],
    #         weight=3,
    #         popup=f"Route from {route['from']['name']} to {route['to']['name']}"
    #     ).add_to(m)
    
    # Display the map
    st_folium(m, width=700, height=500)
    
    st.write("### Routing Logic")
    st.write("To automate routing, you can integrate APIs like OpenRouteService or Google Directions API.")
    st.write("For example, select a source and destination to calculate the optimal route:")
    
    # Simple routing demo (placeholder)
    source_options = [v["name"] for v in biomass_villages + coal_mines]
    dest_options = [i["name"] for i in industries]
    
    col1, col2 = st.columns(2)
    with col1:
        source = st.selectbox("Select Source", source_options)
    with col2:
        dest = st.selectbox("Select Destination", dest_options)
    
    if st.button("Calculate Route"):
        # Placeholder for API call
        st.write(f"Calculating route from {source} to {dest}...")
        st.write("Distance: ~50 km, Time: ~1.5 hours (example)")
        # In real implementation, call routing API here

# --- Page Navigation (Replaced with Sidebar) ---

st.sidebar.title("Navigation")

# Use button type to show active page
page_iot_type = "primary" if st.session_state.current_page == "iot" else "secondary"
page_ai_type = "primary" if st.session_state.current_page == "ai" else "secondary"
page_gis_type = "primary" if st.session_state.current_page == "gis" else "secondary"

if st.sidebar.button(T["page_iot"], use_container_width=True, type=page_iot_type):
    st.session_state.current_page = "iot"
    st.rerun()

if st.sidebar.button(T["page_ai"], use_container_width=True, type=page_ai_type):
    st.session_state.current_page = "ai"
    st.rerun()

if st.sidebar.button(T["page_gis"], use_container_width=True, type=page_gis_type):
    st.session_state.current_page = "gis"
    st.rerun()

# --- Page Runner ---
if st.session_state.current_page == "iot":
    page_iot()
elif st.session_state.current_page == "ai":
    page_ai_optimizer()
elif st.session_state.current_page == "gis":
    page_gis_map()