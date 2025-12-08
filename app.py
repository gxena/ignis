
import streamlit as st
import pandas as pd
import numpy as np
import time
import random
from datetime import datetime

# --- Configuration ---
st.set_page_config(
    page_title="HybridFuel AI Dashboard",
    page_icon="🔥",
    layout="wide",
    initial_sidebar_state="expanded"  # Make sidebar visible by default
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
</style>
""", unsafe_allow_html=True)


# --- Language/Translation Setup ---
LANGUAGES = {
    "English": {
        "app_title": "HybridFuel AI: Biogas-Coal Optimization System",
        "page_iot": "IoT Sensor Dashboard",  # Removed emoji
        "page_ai": "AI Blend Optimizer",  # Removed emoji
        "page_gis": "GIS Feedstock Map",  # Removed emoji
        "iot_header": "Real-time Combustion Monitoring",
        "iot_subheader": "Simulated data from IoT sensors in the combustion system.",
        "current_temp": "Current Temperature",
        "current_co2": "Current CO2",
        "current_nox": "Current NOx",
        "current_pm25": "Current PM2.5",
        "historical_temp": "Historical Temperature (°C)",
        "historical_emissions": "Historical Emissions (ppm / µg/m³)",
        "historical_data_header": "Historical Data Log",
        "ai_header": "AI-Powered Fuel Blend Optimization",
        "ai_subheader": "This is a placeholder model. A real model will be trained on sensor data.",
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
        "app_title": "हाइब्रिडफ्यूल एआई: बायोगैस-कोयला अनुकूलन प्रणाली",
        "page_iot": "IoT सेंसर डैशबोर्ड",  # Removed emoji
        "page_ai": "AI मिश्रण ऑप्टिमाइज़र",  # Removed emoji
        "page_gis": "GIS फीडस्टॉक मानचित्र",  # Removed emoji
        "iot_header": "वास्तविक समय दहन निगरानी",
        "iot_subheader": "दहन प्रणाली में IoT सेंसर से नकली डेटा।",
        "current_temp": "वर्तमान तापमान",
        "current_co2": "वर्तमान CO2",
        "current_nox": "वर्तमान NOx",
        "current_pm25": "वर्तमान PM2.5",
        "historical_temp": "ऐतिहासिक तापमान (°C)",
        "historical_emissions": "ऐतिहासिक उत्सर्जन (ppm / µg/m³)",
        "historical_data_header": "ऐतिहासिक डेटा लॉग",
        "ai_header": "AI-संचालित ईंधन मिश्रण अनुकूलन",
        "ai_subheader": "यह एक प्लेसहोल्डर मॉडल है। सेंसर डेटा पर एक वास्तविक मॉडल को प्रशिक्षित किया जाएगा।",
        "coal_input": "कोयला इनपुट (टन/घंटा)",
        "biogas_mix": "बायोगैस मिश्रण (%)",
        "optimize_button": "अनुकूलन चलाएँ",
        "ai_recommendation": "AI सिफ़ारिश",
        "pred_power": "अनुमानित बिजली उत्पादन (MW)",
        "pred_reduction": "अनुमानित PM2.5 कमी",
        "safety_check": "सुरक्षा और व्यवहार्यता जांच",
        "safety_ok": "✅ बायोगैस प्रतिशत सुरक्षित परिचालन मापदंडों के भीतर है।",
        "safety_warn": "⚠️ उच्च बायोगैस प्रतिशत (>40%) के लिए उपकरण रेट्रोफिटिंग की आवश्यकता हो सकती है। सावधानी से आगे बढ़ें।",
        "optimal_blend_is": "अधिकतम दक्षता और न्यूनतम प्रदूषण के लिए इष्टतम मिश्रण:",
        "gis_header": "GIS फीडस्टॉक और लॉजिस्टिक्स डैशबोर्ड",
        "gis_subheader": "यह डैशबोर्ड क्षेत्रीय अपशिष्ट फीडस्टॉक स्रोतों, बायोगैस उत्पादन क्षमता और औद्योगिक ईंधन की मांग को मैप करेगा।",
        "gis_placeholder": "भारत का सरल नक्शा। पूर्ण GIS डेटा बाद में एकीकृत किया जाएगा।",
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
        label_visibility="collapsed",  # Hides the label, shows only the box
        index=0 if st.session_state.lang == "English" else 1
    )

# Get translated text
T = LANGUAGES[st.session_state.lang]

# Set the main app title in the first column
with col1:
    st.title(T["app_title"])

# --- Initialize Session State for IoT Data ---
if 'iot_history' not in st.session_state:
    st.session_state.iot_history = pd.DataFrame(columns=[
        "timestamp", "Temperature", "CO2", "NOx", "PM2_5"
    ])

# --- Helper Function for IoT Data ---
def get_new_iot_data():
    """Generates a new row of fake IoT data."""
    new_data = {
        "timestamp": datetime.now(),
        "Temperature": random.uniform(20, 35),
        "CO2": random.uniform(12, 18),
        "NOx": random.uniform(150, 300),
        "PM2_5": random.uniform(20, 50)
    }
    return new_data

def append_to_history(new_data_row):
    """Appends new data to the session state history."""
    new_df_row = pd.DataFrame([new_data_row])
    st.session_state.iot_history = pd.concat(
        [st.session_state.iot_history, new_df_row],
        ignore_index=True
    )
    # Keep only the last 100 entries
    if len(st.session_state.iot_history) > 100:
        st.session_state.iot_history = st.session_state.iot_history.tail(100)

# --- Page 1: IoT Sensor Dashboard ---
def page_iot():
    st.header(T["iot_header"])
    st.subheader(T["iot_subheader"])

    # Simulate real-time data update
    new_data = get_new_iot_data()
    append_to_history(new_data)

    # Display current metrics
    st.divider()
    col1, col2, col3, col4 = st.columns(4)
    col1.metric(T["current_temp"], f"{new_data['Temperature']:.1f} °C", f"{new_data['Temperature'] - st.session_state.iot_history.iloc[-2]['Temperature']:.1f}" if len(st.session_state.iot_history) > 1 else "0.0")
    col2.metric(T["current_co2"], f"{new_data['CO2']:.1f} %", f"{new_data['CO2'] - st.session_state.iot_history.iloc[-2]['CO2']:.1f}" if len(st.session_state.iot_history) > 1 else "0.0")
    col3.metric(T["current_nox"], f"{new_data['NOx']:.0f} ppm", f"{new_data['NOx'] - st.session_state.iot_history.iloc[-2]['NOx']:.0f}" if len(st.session_state.iot_history) > 1 else "0")
    col4.metric(T["current_pm25"], f"{new_data['PM2_5']:.0f} µg/m³", f"{new_data['PM2_5'] - st.session_state.iot_history.iloc[-2]['PM2_5']:.0f}" if len(st.session_state.iot_history) > 1 else "0")
    st.divider()

    # Display historical charts
    history_df = st.session_state.iot_history.set_index("timestamp")

    if not history_df.empty:
        st.subheader(T["historical_temp"])
        st.line_chart(history_df["Temperature"])

        st.subheader(T["historical_emissions"])
        st.line_chart(history_df[["CO2", "NOx", "PM2_5"]])

        st.subheader(T["historical_data_header"])
        st.dataframe(history_df.tail(20), use_container_width=True)

    # Pause for 10 seconds to simulate data coming in every 10 seconds
    time.sleep(10)
    # Rerun the page to simulate live data
    st.rerun()

# --- Page 2: AI Blend Optimizer ---
def page_ai_optimizer():
    st.header(T["ai_header"])
    st.info(T["ai_subheader"])

    col1, col2 = st.columns([1, 2])

    with col1:
        st.subheader(T["ai_recommendation"])
        coal_input = st.slider(T["coal_input"], 50, 500, 200)
        biogas_mix = st.slider(T["biogas_mix"], 0, 100, 10)

        # Simple Linear Regression (Placeholder Model)
        # Power = Base(Coal) + Bonus(Biogas)
        pred_power = (coal_input * 0.8) + (biogas_mix * 1.5)
        # Pollution = Base(Coal) - Reduction(Biogas)
        pred_pollution_base = coal_input * 0.1
        pred_pollution_reduction = (biogas_mix / 100) * (pred_pollution_base * 0.9) # 90% reduction at 100% biogas
        pred_pollution_final = pred_pollution_base - pred_pollution_reduction

        st.metric(T["pred_power"], f"{pred_power:.1f} MW")
        st.metric(
            T["pred_reduction"],
            f"{pred_pollution_reduction / (pred_pollution_base + 0.01) * 100:.0f}%",
            f"~ {pred_pollution_final:.1f} PM2.5 Index"
        )

        st.subheader(T["safety_check"])
        if biogas_mix > 40:
            st.warning(T["safety_warn"])
        else:
            st.success(T["safety_ok"])

    with col2:
        if st.button(T["optimize_button"], use_container_width=True):
            with st.spinner("Calculating optimal blend..."):
                time.sleep(1) # Simulate calculation
                best_blend = 0
                best_score = 0

                for blend_perc in range(0, 101): # 0 to 100%
                    if blend_perc <= 40: # Only check "safe" range
                        power = (coal_input * 0.8) + (blend_perc * 1.5)
                        pollution_base = coal_input * 0.1
                        reduction = (blend_perc / 100) * (pollution_base * 0.9)
                        pollution_final = pollution_base - reduction

                        # Simple score: (Power) / (Pollution + 0.1 to avoid div by zero)
                        # We want to maximize this score
                        score = power / (pollution_final + 0.1)

                        if score > best_score:
                            best_score = score
                            best_blend = blend_perc

                st.subheader(T["optimal_blend_is"])
                st.info(f"**{best_blend}% Biogas**")
                st.write("This maximizes power output while minimizing pollution within the 'safe' operating range.")


# --- Page 3: GIS Feedstock Map ---
def page_gis_map():
    st.header(T["gis_header"])
    st.info(T["gis_subheader"])
    st.write(T["gis_placeholder"])

    # Create a simple DataFrame for points in India
    # Coordinates for major cities
    map_data = pd.DataFrame(
        {
            "lat": [19.0760, 28.6139, 13.0827, 22.5726, 20.5937],
            "lon": [72.8777, 77.2090, 80.2707, 88.3639, 78.9629],
            "size": [30, 30, 30, 30, 100], # Center point is bigger
            "color": [[255, 0, 0, 160], [0, 255, 0, 160], [0, 0, 255, 160], [255, 255, 0, 160], [0, 0, 0, 100]]
        }
    )

    # Display the map using st.map()
    st.map(map_data,
           latitude=20.5937,
           longitude=78.9629,
           zoom=4,
           use_container_width=True,
           size="size",
           color="color"
           )

# --- Page Navigation (Replaced with Sidebar) ---
if 'current_page' not in st.session_state:
    st.session_state.current_page = T["page_iot"]

st.sidebar.title("Navigation")

# Use button type to show active page
page_iot_type = "primary" if st.session_state.current_page == T["page_iot"] else "secondary"
page_ai_type = "primary" if st.session_state.current_page == T["page_ai"] else "secondary"
page_gis_type = "primary" if st.session_state.current_page == T["page_gis"] else "secondary"

if st.sidebar.button(T["page_iot"], use_container_width=True, type=page_iot_type):
    st.session_state.current_page = T["page_iot"]
    # We need to rerun to switch the page immediately if not already on it
    if page_iot_type == "secondary":
        st.rerun()

if st.sidebar.button(T["page_ai"], use_container_width=True, type=page_ai_type):
    st.session_state.current_page = T["page_ai"]
    if page_ai_type == "secondary":
        st.rerun()

if st.sidebar.button(T["page_gis"], use_container_width=True, type=page_gis_type):
    st.session_state.current_page = T["page_gis"]
    if page_gis_type == "secondary":
        st.rerun()

# --- Page Runner ---
if st.session_state.current_page == T["page_iot"]:
    page_iot()
elif st.session_state.current_page == T["page_ai"]:
    page_ai_optimizer()
elif st.session_state.current_page == T["page_gis"]:
    page_gis_map()


# --- Page 1: IoT Sensor Dashboard ---
# (This section is now defined above)

# --- Page 2: AI Blend Optimizer ---
# (This section is now defined above)

# --- Page 3: GIS Feedstock Map ---
# (This section is now defined above)
