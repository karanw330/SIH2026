import streamlit as st
import os
import json
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
import pydeck as pdk

# Import custom AI Agent Tools
from tools.reroute_corridor_tool import reroute_corridor_tool
from tools.localized_alert_dispatch_tool import localized_alert_dispatch_tool
from tools.resource_allocation_tool import resource_allocation_tool

st.set_page_config(page_title="NE Landslide Risk Engine",
                   page_icon="🗺️", layout="wide")

st.title("NORTH EAST INDIA LANDSLIDE RISK & RESPONSE SYSTEM")
st.caption(
    "IIT Delhi ILSM WebGL Engine with Quantized Offline Tool-Based Reasoning")

# --- HELPER FUNCTIONS FOR EXIF EXTRACTION ---


def get_decimal_from_dms(dms, ref):
    degrees, minutes, seconds = dms
    decimal = float(degrees) + float(minutes)/60.0 + float(seconds)/3600.0
    if ref in ['S', 'W']:
        decimal = -decimal
    return decimal


def extract_exif_gps(image_file):
    try:
        image = Image.open(image_file)
        exif_data = image._getexif()
        if not exif_data:
            return None

        gps_info = {}
        for tag, value in exif_data.items():
            tag_name = TAGS.get(tag, tag)
            if tag_name == "GPSInfo":
                for key in value:
                    sub_tag = GPSTAGS.get(key, key)
                    gps_info[sub_tag] = value[key]

        if "GPSLatitude" in gps_info and "GPSLongitude" in gps_info:
            lat = get_decimal_from_dms(
                gps_info["GPSLatitude"], gps_info.get("GPSLatitudeRef", "N"))
            lng = get_decimal_from_dms(
                gps_info["GPSLongitude"], gps_info.get("GPSLongitudeRef", "E"))
            return [lat, lng]
    except Exception as e:
        return None
    return None


# --- SIDEBAR: DYNAMIC SIMULATION CONTROLS ---
with st.sidebar:
    st.header("🎮 Live Control Panel")

    # Rainfall Simulation Slider (Milestone 3)
    rainfall = st.slider("Live Rainfall Simulation (mm/hr)",
                         min_value=0, max_value=100, value=15, step=5)

    # Dynamic Risk Formula Calculation
    base_risk = 0.45
    current_risk = min(1.0, round(base_risk * (1 + (rainfall / 50.0)), 2))

    st.markdown(f"**Calculated Corridor Risk:** `{current_risk}`")

    if current_risk >= 0.75:
        st.error("⚠️ RISK CRITICAL (> 0.75): Hazard Breach Triggered!")
    else:
        st.success("🟢 RISK NORMAL: Corridor Safe")

    st.divider()

    # Geotagged Photo Upload (Milestone 4)
    st.subheader("📷 Field Incident Photo Upload")
    uploaded_photo = st.file_uploader(
        "Upload Geotagged Hazard Photo", type=["jpg", "jpeg", "png"])
    extracted_coords = None

    if uploaded_photo:
        extracted_coords = extract_exif_gps(uploaded_photo)
        if extracted_coords:
            st.success(
                f"GPS Coordinates Found: {extracted_coords[0]:.4f}, {extracted_coords[1]:.4f}")
        else:
            # Fallback mock coordinates if image lacks EXIF tags
            extracted_coords = [28.06, 95.32]
            st.warning(
                "No EXIF GPS tags found. Using fallback coordinates: [28.06, 95.32]")

# --- MAIN UI LAYOUT ---
col_map, col_agent = st.columns([2, 1])

# Baseline Route Data (Guwahati -> Tezpur -> Upper Siang)
primary_route = [[26.14, 91.73], [26.63, 92.79], [28.06, 95.32]]
active_route = primary_route
route_color = [0, 255, 0, 200]  # Green

# Trigger automatic rerouting if risk breaches threshold
reroute_info = None
if current_risk >= 0.75:
    route_color = [255, 0, 0, 200]  # Red for unsafe primary route
    reroute_response = reroute_corridor_tool(
        primary_route[0], primary_route[2], ["NE_HAZ_402"])
    reroute_info = json.loads(reroute_response)
    active_route = reroute_info["geometry"]

with col_map:
    st.subheader("🗺️ Deck.gl MapLibre WebGL Layer")

    # Layer 1: Active Corridor Route
    route_layer = pdk.Layer(
        "PathLayer",
        data=[{"path": [[pt[1], pt[0]] for pt in active_route]}],
        get_path="path",
        get_color=route_color if current_risk < 0.75 else [0, 200, 255, 200],
        get_width=5,
        width_min_pixels=4,
    )

    # Layer 2: Field Hazard Marker (If photo uploaded)
    map_layers = [route_layer]
    map_center_lat, map_center_lng = 26.80, 93.50

    if extracted_coords:
        map_center_lat, map_center_lng = extracted_coords[0], extracted_coords[1]
        photo_layer = pdk.Layer(
            "ScatterplotLayer",
            data=[{"position": [extracted_coords[1],
                                extracted_coords[0]], "name": "Hazard Upload"}],
            get_position="position",
            get_fill_color=[255, 255, 0, 255],  # Yellow Warning Marker
            get_radius=15000,
            pickable=True
        )
        map_layers.append(photo_layer)

    # Render Deck.gl Map
    st.pydeck_chart(pdk.Deck(
        map_style="mapbox://styles/mapbox/dark-v10",
        initial_view_state=pdk.ViewState(
            latitude=map_center_lat,
            longitude=map_center_lng,
            zoom=7,
            pitch=45,
        ),
        layers=map_layers
    ))

with col_agent:
    st.subheader("🤖 Agent Reasoning & Tool Dispatch")

    # Execute Tool 3 if Photo Uploaded
    if extracted_coords:
        if st.button("Query Nearest Emergency Assets"):
            with st.spinner("Executing resource_allocation_tool..."):
                res_output = resource_allocation_tool(extracted_coords)
                res_json = json.loads(res_output)
                st.success("Matching Resources Found:")
                st.json(res_json["resources"])

    st.divider()

    # Executive Briefing & SMS Dispatch (Milestones 3 & 5)
    st.subheader("📢 Alert Dispatcher")
    selected_district = st.selectbox("Select Target District", [
                                     "Upper Siang", "Tezpur", "Guwahati", "Papum Pare"])

    if st.button("Generate Localized Dispatches", type="primary"):
        with st.spinner("Generating Multilingual SMS Alerts..."):
            dispatch_output = localized_alert_dispatch_tool(
                selected_district, current_risk, "Landslide & Debris Flow")
            dispatch_json = json.loads(dispatch_output)

            st.markdown("### Preview Localized SMS Cards:")
            for lang, message in dispatch_json["dispatched_templates"].items():
                st.info(f"**{lang}:** {message}")
