import streamlit as st
import requests
import plotly.graph_objects as go

# === CONFIG ===
API_URL = "https://gateway.saxobank.com/sim/openapi/trade/v1/optionschain/subscriptions"
ACCOUNT_KEY = "0YjLF1Y-JKcSsNThRzEETA=="
IDENTIFIER = 151 #1698 
CONTEXT_ID = "plotlyVolContext"
REFERENCE_ID_BASE = "PorscheVol"
REFRESH_RATE = 1000

# === STREAMLIT UI ===
st.title("📊 Porsche Options Volatility Surface (Interactive)")
access_token = st.text_input("Enter Saxo Access Token", type="password")

start_expiry = st.slider("Start Expiry Index", 0, 7, 0)
end_expiry = st.slider("End Expiry Index", start_expiry, 7, min(start_expiry + 2, 7))
strike_start = st.slider("Strike Start Index", 0, 30, 0)
max_strikes = st.slider("Max Strikes Per Expiry", 5, 45, 30)

headers = {
    "Authorization": f"Bearer {access_token}",
    "Content-Type": "application/json"
}   

# === Fetch and Parse Data ===
X, Y, Z = [], [], []

if access_token:
    with st.spinner("Fetching options data..."):
        for expiry_index in range(start_expiry, end_expiry + 1):
            payload = {
                "Arguments": {
                    "AccountKey": ACCOUNT_KEY,
                    "AssetType": "StockOption",
                    "Expiries": [{
                        "Index": expiry_index,
                        "StrikeStartIndex": strike_start
                    }],
                    "Identifier": IDENTIFIER,
                    "MaxStrikesPerExpiry": max_strikes
                },
                "ContextId": CONTEXT_ID,
                "ReferenceId": f"{REFERENCE_ID_BASE}_{expiry_index}",
                "RefreshRate": REFRESH_RATE
            }

            res = requests.post(API_URL, headers=headers, json=payload)
            if res.status_code == 201:
                snapshot = res.json().get("Snapshot", {})
                for expiry in snapshot.get("Expiries", []):
                    dte = expiry.get("DisplayDaysToExpiry")
                    for strike_data in expiry.get("Strikes", []):
                        strike = strike_data.get("Strike")
                        greeks = strike_data.get("Call", {}).get("Greeks", {})
                        iv = greeks.get("AskVolatility")
                        if iv and iv > 0:
                            X.append(dte)
                            Y.append(strike)
                            Z.append(iv)

    if X:
        fig = go.Figure(data=[go.Scatter3d(
            x=X,
            y=Y,
            z=Z,
            mode='markers',
            marker=dict(size=4, color=Z, colorscale='Viridis', opacity=0.8),
        )])
        fig.update_layout(
            scene=dict(
                xaxis_title="Days to Expiry",
                yaxis_title="Strike Price",
                zaxis_title="Implied Volatility"
            ),
            margin=dict(l=0, r=0, b=0, t=40),
            title="Interactive 3D Volatility Surface"
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("No valid IV data found.")
else:
    st.info("🔐 Enter your Saxo access token to begin.")
