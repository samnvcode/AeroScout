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

# (airport_currency_map and currency_symbols unchanged)

# ---------------- STYLE ----------------
st.set_page_config(page_title="AeroScout", layout="wide", page_icon="✈️")
st.markdown("""
<style>
body {
    background-color: #000000;  /* black background */
    color: #f0f0f0;             /* light text */
}
h1, h2, h3, h4 {
    color: #ade8f4;
}
div.stButton > button {
    background-color: #2d6a4f;
    color: white;
    border-radius: 10px;
    padding: 0.6em 1em;
    border: none;
}
div.stButton > button:hover {
    background-color: #40916c;
}
.flight-card {
    border: 2px solid #2d6a4f;
    border-radius: 12px;
    padding: 16px;
    background-color: #d8f3dc;  /* lighter cream-green */
    margin-bottom: 20px;
    box-shadow: 2px 4px 10px rgba(0,0,0,0.1);
    color: #1b4332; /* dark green text for readability */
}
</style>
""", unsafe_allow_html=True)

# ---------------- TITLE ----------------
st.title("✈️ AeroScout")

# Utility function to display flight cards
def display_flight_cards(flights, symbol):
    for flight in flights:
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
            segment_items.append(
                f"<li><strong>{airline}</strong>: {dep.get('name', '')} ({dep.get('id', '')}) {dep.get('time', '')} → {arr.get('name', '')} ({arr.get('id', '')}) {arr.get('time', '')}</li>"
            )

        segments_html = "<ul>" + "".join(segment_items) + "</ul>"

        st.markdown(f"""
        <div class="flight-card">
            <h4>✈️ <strong>{flight_type}</strong> - <span style="color:#2d6a4f;">{symbol}{price}</span></h4>
            <p><strong>Total Duration:</strong> {duration_formatted}</p>
            {segments_html}
        </div>
        """, unsafe_allow_html=True)

# ---------------- LEFT COLUMN ----------------
left_col, right_col = st.columns(2)

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

                # Generate summary once
                summary_response = model.generate_content(full_summary_prompt)
                summary_text = summary_response.text

                # Cache flights and summary in session state
                st.session_state["cached_flights"] = flights[:5]
                st.session_state["cached_symbol"] = symbol
                st.session_state["gemini_summary"] = summary_text

        # Display summary above cards
        if "gemini_summary" in st.session_state:
            st.info(f"**Gemini Summary:**\n\n{st.session_state['gemini_summary']}")

        # Display cards from cache (so they persist after form submit)
        if "cached_flights" in st.session_state and "cached_symbol" in st.session_state:
            display_flight_cards(st.session_state["cached_flights"], st.session_state["cached_symbol"])

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
