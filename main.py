import streamlit as st
import requests
from datetime import datetime
import google.generativeai as genai

# ---------------- CONFIGURATION ----------------
SERPAPI_API_KEY = st.secrets["SERPAPI_API_KEY"]
GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]

# Configure Gemini
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")  # stable, available model

# ---------------- AIRPORT → CURRENCY ----------------
def get_currency_from_airport_code(code):
    airport_currency_map = {
        "ATL": "USD", "LAX": "USD", "JFK": "USD", "LHR": "GBP", "CDG": "EUR",
        "FRA": "EUR", "AMS": "EUR", "NRT": "JPY", "HND": "JPY", "DEL": "INR",
        "BOM": "INR", "SYD": "AUD", "MEL": "AUD", "DXB": "AED", "DOH": "QAR",
        "SIN": "SGD", "BKK": "THB", "HKG": "HKD", "ICN": "KRW", "YYZ": "CAD"
    }
    return airport_currency_map.get(code.upper(), "USD")

currency_symbols = {
    "USD": "$", "INR": "₹", "EUR": "€", "GBP": "£", "AUD": "A$", "JPY": "¥", "CAD": "C$",
    "CNY": "¥", "AED": "د.إ", "QAR": "ر.ق", "SGD": "S$", "THB": "฿", "HKD": "HK$", "KRW": "₩"
}

# ---------------- STYLE ----------------
st.set_page_config(page_title="AeroScout", layout="wide", page_icon="✈️")
st.markdown("""
<style>
.flight-card {
    border: 1.5px solid #0a9396;
    border-radius: 12px;
    padding: 20px;
    background-color: #121212;
    margin-bottom: 20px;
    box-shadow: 0 4px 15px rgba(10, 147, 150, 0.3);
    color: #d0e8f2;
}
.flight-card h4 { color: #56cfe1; }
.flight-card p, .flight-card ul, .flight-card li { color: #a8dadc; }
</style>
""", unsafe_allow_html=True)

st.title("✈️ AeroScout")

# ---------------- ABOUT ----------------
with st.expander("ℹ️ About AeroScout"):
    st.markdown("""
    **AeroScout** combines **real-time flight search**, **AI summarization**, and a **travel chatbot** 
    to help you plan trips faster and smarter.
    """)

# ---------------- LAYOUT ----------------
left_col, right_col = st.columns(2)

with left_col:
    st.subheader("🌍 Search Flights")
    with st.form("flight_form"):
        from_city = st.text_input("From (IATA Code)", value="DEL")
        to_city = st.text_input("To (IATA Code)", value="BOM")
        date = st.date_input("Departure Date")
        include_return = st.checkbox("Add return date?")
        return_date = None
        if include_return:
            return_date = st.date_input("Return Date")
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
                st.session_state["cached_flights"] = flights
                st.session_state["cached_symbol"] = symbol

                flight_summaries = []
                for flight in flights[:5]:
                    price = flight.get("price", "N/A")
                    duration = flight.get("total_duration", "N/A")
                    flight_type = flight.get("type", "Unknown").title()
                    segments = flight.get("flights", [])
                    seg_info = ", ".join(
                        f"{seg.get('airline', '')} {seg.get('departure_airport', {}).get('id', '')}→{seg.get('arrival_airport', {}).get('id', '')}"
                        for seg in segments
                    )
                    flight_summaries.append(
                        f"{flight_type} flight costing {symbol}{price}, duration {duration} minutes, segments: {seg_info}."
                    )

                policy_prompt = """
                Summarize the following flights and include:
                - Price, duration, stops, and airlines
                - Baggage policy, seat comfort, amenities, and cancellation rules for each airline
                - Recommendation for best overall, best value, and most comfortable
                """
                full_summary_prompt = policy_prompt + "\n\nFlights:\n" + "\n".join(flight_summaries)

                try:
                    summary_response = model.generate_content([full_summary_prompt])
                    summary_text = summary_response.text
                except Exception as e:
                    summary_text = f"Error generating summary: {str(e)}"

                st.session_state["gemini_summary"] = summary_text
                st.session_state["gemini_chat"] = model.start_chat(history=[
                    {"role": "user", "parts": [full_summary_prompt]},
                    {"role": "model", "parts": [summary_text]}
                ])

    if "gemini_summary" in st.session_state:
        st.info(f"**Gemini Summary:**\n\n{st.session_state['gemini_summary']}")

    if "cached_flights" in st.session_state:
        cached_flights = st.session_state["cached_flights"]
        cached_symbol = st.session_state["cached_symbol"]
        for flight in cached_flights[:5]:
            price = flight.get("price", "N/A")
            duration = flight.get("total_duration", "N/A")
            try:
                mins = int(duration)
                hours = mins // 60
                minutes = mins % 60
                duration_formatted = f"{hours}h {minutes}m"
            except:
                duration_formatted = f"{duration} min"

            segments_html = "<ul>" + "".join(
                f"<li><strong>{seg.get('airline', 'Unknown')}</strong>: "
                f"{seg.get('departure_airport', {}).get('name', '')} ({seg.get('departure_airport', {}).get('id', '')}) "
                f"{seg.get('departure_airport', {}).get('time', '')} → "
                f"{seg.get('arrival_airport', {}).get('name', '')} ({seg.get('arrival_airport', {}).get('id', '')}) "
                f"{seg.get('arrival_airport', {}).get('time', '')}</li>"
                for seg in flight.get("flights", [])
            ) + "</ul>"

            st.markdown(f"""
            <div class="flight-card">
                <h4>✈️ <strong>{flight.get('type', 'Unknown').title()}</strong> - <span style="color:#0a9396;">{cached_symbol}{price}</span></h4>
                <p><strong>Total Duration:</strong> {duration_formatted}</p>
                {segments_html}
            </div>
            """, unsafe_allow_html=True)

with right_col:
    st.subheader("💬 Travel Chatbot")
    if "gemini_chat" not in st.session_state:
        st.warning("Search for flights to start chatting.")
    else:
        query = st.text_input("Ask about these flights or airline policies...")
        if query:
            allowed_keywords = ["flight", "airline", "baggage", "cancellation", "travel", "airport", "boarding", "ticket", "visa", "transit", "itinerary"]
            if any(k in query.lower() for k in allowed_keywords):
                try:
                    chat = st.session_state["gemini_chat"]
                    response = chat.send_message(query)
                    reply = response.text
                except Exception as e:
                    reply = f"Error: {str(e)}"

                st.session_state.setdefault("chat_history", []).append(("You", query))
                st.session_state["chat_history"].append(("AeroScout AI", reply))
            else:
                st.warning("❌ Only travel-related questions are supported.")

        for speaker, msg in reversed(st.session_state.get("chat_history", [])):
            st.markdown(f"**{speaker}:** {msg}")
