import streamlit as st
import requests
from datetime import datetime
import google.generativeai as genai
# ---------------- CONFIGURATION ----------------
SERPAPI_API_KEY = "3e5215c3caba0576366215ec845c69029e2258d8f9a3e058fe10d0ce34d8a2e4"
GEMINI_API_KEY = "AIzaSyCo2ijp1xaC9fE97PogEHUL2ywywAPDuNY"
# Initialize Gemini
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-2.5-flash")
# ---------------- AIRPORT → CURRENCY ----------------
def get_currency_from_airport_code(code):
    airport_currency_map = {
        "ATL": "USD", "LAX": "USD", "ORD": "USD", "DFW": "USD", "DEN": "USD", "JFK": "USD", "SFO": "USD",
        "SEA": "USD", "MIA": "USD", "CLT": "USD", "LAS": "USD", "PHX": "USD", "IAH": "USD", "BOS": "USD",
        "MSP": "USD", "DTW": "USD", "PHL": "USD", "FLL": "USD", "BWI": "USD", "SLC": "USD", "LHR": "GBP",
        "LGW": "GBP", "MAN": "GBP", "CDG": "EUR", "ORY": "EUR", "FRA": "EUR", "MUC": "EUR", "BER": "EUR",
        "AMS": "EUR", "BRU": "EUR", "MAD": "EUR", "BCN": "EUR", "ZRH": "CHF", "VIE": "EUR", "DUB": "EUR",
        "CPH": "DKK", "OSL": "NOK", "ARN": "SEK", "HEL": "EUR", "IST": "TRY", "ATH": "EUR", "MXP": "EUR",
        "FCO": "EUR", "LIS": "EUR", "PRG": "CZK", "WAW": "PLN", "BUD": "HUF", "PEK": "CNY", "PVG": "CNY",
        "CAN": "CNY", "HND": "JPY", "NRT": "JPY", "ICN": "KRW", "SYD": "AUD", "MEL": "AUD", "BNE": "AUD",
        "DEL": "INR", "BOM": "INR", "BLR": "INR", "DXB": "AED", "AUH": "AED", "DOH": "QAR", "JNB": "ZAR",
        "CPT": "ZAR", "GRU": "BRL", "GIG": "BRL", "EZE": "ARS", "SCL": "CLP", "LIM": "PEN", "BOG": "COP",
        "MEX": "MXN", "CUN": "MXN", "YYZ": "CAD", "YVR": "CAD", "YUL": "CAD", "AKL": "NZD", "WLG": "NZD",
        "SGN": "VND", "HAN": "VND", "BKK": "THB", "KUL": "MYR", "SIN": "SGD", "CGK": "IDR", "MNL": "PHP",
        "HKG": "HKD", "TPE": "TWD", "RUH": "SAR", "JED": "SAR", "NBO": "KES", "CAI": "EGP", "ADD": "ETB"
    }
    return airport_currency_map.get(code.upper(), "USD")
# ---------------- CURRENCY → SYMBOL ----------------
currency_symbols = {
    "USD": "$", "INR": "₹", "EUR": "€", "GBP": "£", "AUD": "A$", "JPY": "¥", "CAD": "C$",
    "CNY": "¥", "CHF": "CHF", "DKK": "kr", "NOK": "kr", "SEK": "kr", "TRY": "₺", "CZK": "Kč",
    "PLN": "zł", "HUF": "Ft", "AED": "د.إ", "QAR": "ر.ق", "ZAR": "R", "BRL": "R$", "ARS": "$",
    "CLP": "$", "PEN": "S/", "COP": "$", "MXN": "$", "NZD": "NZ$", "VND": "₫", "THB": "฿",
    "MYR": "RM", "SGD": "S$", "IDR": "Rp", "PHP": "₱", "HKD": "HK$", "TWD": "NT$", "SAR": "﷼",
    "KES": "KSh", "EGP": "E£", "ETB": "Br"
}
# ---------------- STYLE ----------------
st.set_page_config(page_title="AeroScout", layout="wide", page_icon=":airplane:")
st.markdown("""
<style>
body {
    background-color: #F5F5DC;
    color: #1B4332;
}
h1, h2, h3, h4 {
    color: #1B4332;
}
div.stButton > button {
    background-color: #2D6A4F;
    color: white;
    border-radius: 10px;
    padding: 0.6em 1em;
    border: none;
}
div.stButton > button:hover {
    background-color: #40916C;
}
.flight-card {
    border: 2px solid #2D6A4F;
    border-radius: 12px;
    padding: 16px;
    background-color: #D8F3DC;
    margin-bottom: 20px;
    box-shadow: 2px 4px 10px rgba(0,0,0,0.1);
}
</style>
""", unsafe_allow_html=True)
# ---------------- TITLE ----------------
st.title(":airplane: AeroScout")
# ---------------- LAYOUT ----------------
left_col, right_col = st.columns(2)
# ---------------- LEFT COLUMN ----------------
with left_col:
    st.subheader(":earth_africa: Search Flights")
    with st.form("flight_form"):
        from_city = st.text_input("From (IATA Code)", value="DEL")
        to_city = st.text_input("To (IATA Code)", value="BOM")
        date = st.date_input("Departure Date")
        return_date = st.date_input("Return Date (optional)", value=None)
        passengers = st.number_input("Passengers", min_value=1, value=1)
        submit = st.form_submit_button(":mag: Search Flights")
    if submit:
        selected_currency = get_currency_from_airport_code(from_city)
        symbol = currency_symbols.get(selected_currency, selected_currency)
        params = {
            "engine": "google_flights",
            "departure_id": from_city,
            "arrival_id": to_city,
            "outbound_date": date.strftime("%Y-%m-%d"),
            "currency": selected_currency,
            "hl": "en",
            "api_key": SERPAPI_API_KEY
        }
        if return_date:
            params["return_date"] = return_date.strftime("%Y-%m-%d")
        response = requests.get("https://serpapi.com/search.json", params=params)
        if response.status_code == 200:
            results = response.json()
            flights = results.get("best_flights", [])
            if flights:
                flight_summaries = []
                for flight in flights[:5]:
                    price = flight.get("price", "N/A")
                    duration = flight.get("total_duration", "N/A")
                    flight_type = flight.get("type", "Unknown").title()
                    segments = flight.get("flights", [])
                    seg_info = ", ".join(
                        f"{seg.get('airline', '')} from {seg.get('departure_airport', {}).get('id', '')} to {seg.get('arrival_airport', {}).get('id', '')}"
                        for seg in segments
                    )
                    flight_summaries.append(f"{flight_type} flight costing {symbol}{price}, duration {duration} minutes, segments: {seg_info}.")
                policy_prompt = """
                Summarize the following flights and include:
                - Price, duration, stops, and airlines
                - Baggage policy, seat comfort, amenities, and cancellation rules for each airline
                - Recommendation for best overall, best value, and most comfortable
                """
                full_summary_prompt = policy_prompt + "\n\nFlights:\n" + "\n".join(flight_summaries)
                summary_response = model.generate_content(full_summary_prompt)
                summary_text = summary_response.text
                st.info(f"**Gemini Summary:**\n\n{summary_text}")
                st.session_state["gemini_chat"] = model.start_chat(history=[
                    {"role": "user", "parts": [full_summary_prompt]},
                    {"role": "model", "parts": [summary_text]}
                ])
                for flight in flights[:5]:
                    price = flight.get("price", "N/A")
                    duration = flight.get("total_duration", "N/A")
                    flight_type = flight.get("type", "Unknown").title()
                    segments = flight.get("flights", [])
                    try:
                        mins = int(duration)
                        hours = mins // 60
                        minutes = mins % 60
                        duration_formatted = f"{hours}h {minutes}m"
                    except:
                        duration_formatted = f"{duration} min"
                    segment_items = []
                    for seg in segments:
                        airline = seg.get("airline", "Unknown Airline")
                        dep = seg.get("departure_airport", {})
                        arr = seg.get("arrival_airport", {})
                        segment_items.append(f"<li><strong>{airline}</strong>: {dep.get('name', '')} ({dep.get('id', '')}) {dep.get('time', '')} → {arr.get('name', '')} ({arr.get('id', '')}) {arr.get('time', '')}</li>")
                    segments_html = "<ul>" + "".join(segment_items) + "</ul>"
                    st.markdown(f"""
                    <div class="flight-card">
                        <h4>:airplane: <strong>{flight_type}</strong> - <span style="color:#2d6a4f;">{symbol}{price}</span></h4>
                        <p><strong>Total Duration:</strong> {duration_formatted}</p>
                        {segments_html}
                        <button style="background-color:#2d6a4f; color:white; padding:8px 16px; border:none; border-radius:6px; cursor:pointer;">Select</button>
                    </div>
                    """, unsafe_allow_html=True)
# ---------------- RIGHT COLUMN ----------------
with right_col:
    st.subheader(":speech_balloon: Travel Chatbot")
    if "gemini_chat" not in st.session_state:
        st.warning("Search for flights to start chatting.")
    else:
        query = st.text_input("Ask about these flights, airline policies, or travel tips...")
        if query:
            allowed_keywords = [
                "flight", "airline", "baggage", "seat", "layover", "ticket", "visa", "passport",
                "check-in", "departure", "arrival", "duration", "price", "travel", "cancellation",
                "airport", "boarding", "time", "delay", "schedule", "policy", "round trip"
            ]
            if any(word in query.lower() for word in allowed_keywords):
                chat = st.session_state["gemini_chat"]
                response = chat.send_message(query)
                reply = response.text
                st.session_state.setdefault("chat_history", []).append(("You", query))
                st.session_state["chat_history"].append(("AeroScout AI", reply))
            else:
                st.session_state.setdefault("chat_history", []).append(("You", query))
                st.session_state["chat_history"].append((
                    "AeroScout AI",
                    ":warning: I can only assist with questions related to flights, airlines, travel policies, or tips. Please ask something travel-related."
                ))
        for speaker, msg in reversed(st.session_state.get("chat_history", [])):
            st.markdown(f"**{speaker}:** {msg}")
