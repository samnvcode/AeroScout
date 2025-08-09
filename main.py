import streamlit as st
import requests
from datetime import datetime
import google.generativeai as genai

# ---------------- CONFIGURATION ----------------
SERPAPI_API_KEY = st.secrets["SERPAPI_API_KEY"]
GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]

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
st.set_page_config(page_title="AeroScout", layout="wide", page_icon="✈️")
st.markdown("""
<style>
body {
    background-color: #000000;
    color: #e0e0e0;
}
h1, h2, h3, h4 {
    color: #a0d8ef;
}
div.stButton > button {
    background-color: #005f73;
    color: white;
    border-radius: 10px;
    padding: 0.6em 1em;
    border: none;
}
div.stButton > button:hover {
    background-color: #0a9396;
}
.flight-card {
    border: 1.5px solid #0a9396;
    border-radius: 12px;
    padding: 20px;
    background-color: #121212;
    margin-bottom: 20px;
    box-shadow: 0 4px 15px rgba(10, 147, 150, 0.3);
    color: #d0e8f2;
}
.flight-card h4 {
    color: #56cfe1;
}
.flight-card p, .flight-card ul, .flight-card li {
    color: #a8dadc;
}
</style>
""", unsafe_allow_html=True)

# ---------------- TITLE ----------------
st.title("✈️ AeroScout")

# ---------------- ABOUT SECTION ----------------
with st.expander("ℹ️ About AeroScout"):
    st.markdown("""
    **AeroScout** is an intelligent flight search and travel assistant powered by **Google's Gemini AI** and **SerpAPI**.

    🔍 **Search & Compare Flights**  
    Enter your departure and destination airport codes, travel dates, and number of passengers. AeroScout fetches the best flight options in real-time.

    🧠 **AI Summarized Insights**  
    Gemini provides a clear summary of flight options, including prices, durations, stops, airline amenities, and more — helping you choose the best flight effortlessly.

    💬 **Travel Chatbot**  
    Ask questions about baggage policies, cancellation rules, airline services, or general travel tips.

    This app was created to simplify flight research and enhance travel planning with the power of AI.
    """)

# ---------------- LAYOUT ----------------
left_col, right_col = st.columns(2)

# ---------------- LEFT COLUMN ----------------
with left_col:
    st.subheader("🌍 Search Flights")
    with st.form("flight_form"):
        from_city = st.text_input("From (IATA Code)", value="DEL")
        to_city = st.text_input("To (IATA Code)", value="BOM")
        date = st.date_input("Departure Date")
        return_date = st.date_input("Return Date (optional)", value=None)
        passengers = st.number_input("Passengers", min_value=1, value=1)
        submit = st.form_submit_button("🔍 Search Flights")

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
                # Cache flights and symbol
                st.session_state["cached_flights"] = flights
                st.session_state["cached_symbol"] = symbol

                # Gemini Summary Prompt
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

                # Cache the summary persistently
                st.session_state["gemini_summary"] = summary_text

                # Save chat session
                st.session_state["gemini_chat"] = model.start_chat(history=[
                    {"role": "user", "parts": [full_summary_prompt]},
                    {"role": "model", "parts": [summary_text]}
                ])



    # Show flight cards (either new search or cached)
    if "cached_flights" in st.session_state and "cached_symbol" in st.session_state:
        cached_flights = st.session_state["cached_flights"]
        cached_symbol = st.session_state["cached_symbol"]
        for flight in cached_flights[:5]:
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
                <h4>✈️ <strong>{flight_type}</strong> - <span style="color:#0a9396;">{cached_symbol}{price}</span></h4>
                <p><strong>Total Duration:</strong> {duration_formatted}</p>
                {segments_html}
            </div>
            """, unsafe_allow_html=True)

# ---------------- RIGHT COLUMN ----------------
with right_col:
    st.subheader("💬 Travel Chatbot")
    if "gemini_chat" not in st.session_state:
        st.warning("Search for flights to start chatting.")
    else:
        query = st.text_input("Ask about these flights, airline policies, or travel tips...")
        if query:
            allowed_keywords = ["flight", "airline", "baggage", "cancellation", "travel", "airport", "boarding", "ticket", "visa", "transit", "itinerary"]
            if any(keyword in query.lower() for keyword in allowed_keywords):
                chat = st.session_state["gemini_chat"]
                response = chat.send_message(query)
                reply = response.text
                st.session_state.setdefault("chat_history", []).append(("You", query))
                st.session_state["chat_history"].append(("AeroScout AI", reply))
            else:
                st.warning("❌ This assistant only answers flight, airline, and travel-related questions.")

        for speaker, msg in reversed(st.session_state.get("chat_history", [])):
            st.markdown(f"**{speaker}:** {msg}")
