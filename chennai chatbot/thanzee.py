import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import difflib
import os
from datetime import datetime

# Page config
st.set_page_config(page_title="Chennai Risk Chatbot", page_icon="🌆")
st.markdown("""
    <style>
        .big-font { font-size:24px !important; }
        .highlight { color: #FF4B4B; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

st.title("🤖 Chennai AI Risk Chatbot")
st.markdown("<p class='big-font'>Ask about <span class='highlight'>accidents, pollution, crime, heat, flood, population, or risk factors</span>.</p>", unsafe_allow_html=True)

# Load data
accident_df = pd.read_excel("accident1.xlsx")
flood_df = pd.read_excel("flood.xlsx")
crime_df = pd.read_excel("crime details 1.xlsx")
air_df = pd.read_excel("air pollution.xlsx")
heat_df = pd.read_excel("heat.xlsx")
population_df = pd.read_excel("population.xlsx")
risk_df = pd.read_excel("riskanalysis.xlsx")

# Clean column headers
for df in [accident_df, flood_df, crime_df, air_df, heat_df, population_df, risk_df]:
    df.columns = df.columns.str.strip()

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []

# Fuzzy zone matcher
def find_zone(query_text, zone_list):
    query_text = query_text.lower()
    for zone in zone_list:
        if zone.lower() in query_text:
            return zone
    for word in query_text.split():
        match = difflib.get_close_matches(word, zone_list, n=1, cutoff=0.6)
        if match:
            return match[0]
    return difflib.get_close_matches(query_text, zone_list, n=1, cutoff=0.6)[0] if difflib.get_close_matches(query_text, zone_list, n=1, cutoff=0.6) else None

# Plotting
def plot_bar(df, xcol, ycol, title, color='blue'):
    df = df[[xcol, ycol]].dropna()
    df[ycol] = pd.to_numeric(df[ycol], errors='coerce')
    df = df.groupby(xcol).sum().sort_values(ycol, ascending=False)
    fig, ax = plt.subplots(figsize=(10, 5))
    bars = ax.bar(df.index, df[ycol], color=color)
    ax.set_title(title)
    ax.set_ylabel(ycol)
    plt.xticks(rotation=45, ha='right')
    for bar in bars:
        ax.annotate(f"{int(bar.get_height())}", xy=(bar.get_x()+bar.get_width()/2, bar.get_height()),
                    ha='center', va='bottom', fontsize=8)
    st.pyplot(fig)

# Display previous messages with visual responses
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        timestamp = msg.get("time", "")
        role_icon = "🧑" if msg["role"] == "user" else "🤖"
        role_name = "You" if msg["role"] == "user" else "AI"
        st.markdown(f"{role_icon} {role_name} {timestamp}")
        st.markdown(msg["content"])

        if msg["role"] == "assistant":
            zone = msg.get("zone", "")
            mtype = msg.get("type", "")
            if mtype == "flood":
                st.dataframe(flood_df[flood_df["Area"] == zone])
                plot_bar(flood_df, "Area", "People Affected", "Flood Impact", "blue")
            elif mtype == "accident":
                st.dataframe(accident_df[accident_df["Zone / Area"] == zone])
                plot_bar(accident_df, "Zone / Area", "No. of Cases", "Accident Cases", "red")
            elif mtype == "crime":
                st.dataframe(crime_df[crime_df["Zone Name"] == zone])
                plot_bar(crime_df, "Zone Name", "Total Crimes", "Crime by Zone", "orange")
            elif mtype == "pollution":
                st.dataframe(air_df[air_df["Zone / Area"] == zone])
                plot_bar(air_df, "Zone / Area", "Avg. Value (µg/m³) or AQI", "Air Pollution", "grey")
            elif mtype == "heat":
                st.dataframe(heat_df[heat_df["Area"] == zone])
                plot_bar(heat_df, "Area", "Heatstroke Cases", "Heatstroke Cases", "green")
            elif mtype == "population":
                st.dataframe(population_df[population_df["Zone Name"] == zone])
                plot_bar(population_df, "Zone Name", "Population", "Population by Zone", "purple")
            elif mtype == "risk":
                zone_data = risk_df[risk_df["Area"] == zone]
                st.dataframe(zone_data)
                risk_cols = ["Accident", "Air Pollution", "Flood", "Heat", "Crime", "Population"]
                values = zone_data[risk_cols].iloc[0].values.astype(int)
                fig, ax = plt.subplots(figsize=(8, 5))
                bars = ax.bar(risk_cols, values, color='pink')
                ax.set_ylabel("Risk Level (1=Low, 2=Medium, 3=High)")
                plt.xticks(rotation=45)
                for bar in bars:
                    ax.annotate(f'{int(bar.get_height())}', 
                        xy=(bar.get_x() + bar.get_width()/2, bar.get_height()), 
                        xytext=(0, 3), textcoords="offset points", ha='center')
                st.pyplot(fig)

# Chat input
query = st.chat_input("Type your query here...")
if query:
    timestamp = datetime.now().strftime("%I:%M %p")
    st.session_state.messages.append({
        "role": "user", "content": query, "time": timestamp
    })
    
    q = query.lower()
    zone, reply_type, bot_reply = None, None, ""

    # Check each category
    if "flood" in q or "rain" in q:
        zones = flood_df["Area"].dropna().unique()
        zone = find_zone(q, zones)
        reply_type = "flood"
        bot_reply = f"🌊 Flood Data for {zone}" if zone else "❗ Mention a valid area."

    elif "accident" in q:
        zones = accident_df["Zone / Area"].dropna().unique()
        zone = find_zone(q, zones)
        reply_type = "accident"
        bot_reply = f"🚧 Accidents in {zone}" if zone else "❗ Mention a valid area."

    elif "crime" in q:
        zones = crime_df["Zone Name"].dropna().unique()
        zone = find_zone(q, zones)
        reply_type = "crime"
        bot_reply = f"🚔 Crimes in {zone}" if zone else "❗ Mention a valid zone."

    elif "pollution" in q or "air" in q:
        zones = air_df["Zone / Area"].dropna().unique()
        zone = find_zone(q, zones)
        reply_type = "pollution"
        bot_reply = f"🌫 Air Quality in {zone}" if zone else "❗ Mention a valid zone."

    elif "heat" in q or "temperature" in q:
        zones = heat_df["Area"].dropna().unique()
        zone = find_zone(q, zones)
        reply_type = "heat"
        bot_reply = f"🥵 Heat Impact in {zone}" if zone else "❗ Mention a valid zone."

    elif "population" in q:
        zones = population_df["Zone Name"].dropna().unique()
        zone = find_zone(q, zones)
        reply_type = "population"
        bot_reply = f"👥 Population in {zone}" if zone else "❗ Mention a valid zone."

    elif "risk" in q or "riskfactor" in q or "risk factor" in q:
        zones = risk_df["Area"].dropna().unique()
        zone = find_zone(q, zones)
        reply_type = "risk"
        bot_reply = f"🚨 Risk Factors in {zone}" if zone else "❗ Mention a valid zone."

    else:
        bot_reply = "❓ Try asking about accidents, air pollution, crime, heat, flood, population, or risk."

    # Save assistant reply
    st.session_state.messages.append({
        "role": "assistant",
        "content": bot_reply,
        "time": timestamp,
        "type": reply_type,
        "zone": zone
    })

    st.rerun()  # Re-render immediately with new message