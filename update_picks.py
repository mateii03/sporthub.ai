import os
import json
import requests
from datetime import datetime, timezone
import google.generativeai as genai

# Track API status flags
api_status = {"api_quota_exceeded": False, "error_msg": ""}

# Configure Gemini API
gemini_key = os.environ.get("GEMINI_API_KEY", "")
odds_key = os.environ.get("ODDS_API_KEY", "")

if gemini_key:
    genai.configure(api_key=gemini_key)
    model = genai.GenerativeModel('gemini-2.5-flash')

# 1. Fetch larger odds volume across multiple leagues
sports = ['soccer_epl', 'soccer_spain_la_liga', 'soccer_italy_serie_a', 'soccer_germany_bundesliga', 'soccer_france_ligue_one', 'basketball_nba']
all_odds = []

if odds_key:
    for sport in sports:
        try:
            url = f"https://api.the-odds-api.com/v4/sports/{sport}/odds/?apiKey={odds_key}&regions=eu&markets=h2h,totals"
            res = requests.get(url, timeout=10)
            if res.status_code in [401, 403, 429]:
                api_status["api_quota_exceeded"] = True
                api_status["error_msg"] = "The Odds API key is out of credits or invalid."
            elif res.status_code == 200:
                all_odds.extend(res.json()[:10])
        except Exception as e:
            print(f"Error fetching {sport}: {e}")

today_str = datetime.now(timezone.utc).strftime('%Y-%m-%d')

# 2. Construct AI Prompt with Strict Date & Quantity Rules
prompt = f"""
You are a predictive sports analytics engine. Current UTC Date: {today_str}.
Analyze these match odds:
{json.dumps(all_odds[:30])}

Generate a JSON object matching this EXACT schema with NO markdown block markers:
{{
  "api_quota_exceeded": false,
  "error_msg": "",
  "tickets": [
    {{
      "title": "Safe Anchor Slip",
      "target_odds": "5.20",
      "risk": "Low",
      "date_range": "Today Only",
      "picks": ["Arsenal vs Villa - Over 1.5 Goals", "Barcelona - Win", "Djokovic - Match Winner"]
    }},
    {{
      "title": "Value Combo Slip",
      "target_odds": "10.50",
      "risk": "Medium",
      "date_range": "Today Only",
      "picks": ["Real Madrid Win", "Sinner 2-0 Sets", "FAZE Win Map 1", "Lakers +5.5"]
    }},
    {{
      "title": "High-Yield Slip",
      "target_odds": "24.80",
      "risk": "High",
      "date_range": "Next 3 Days",
      "picks": ["Inter vs Milan Over 22.5 Fouls", "Mbappe Over 1.5 Shots", "Celtics Over 112.5", "Vitality Win"]
    }},
    {{
      "title": "Speculative Loto Ticket",
      "target_odds": "52.00",
      "risk": "Extreme",
      "date_range": "Next 3 Days",
      "picks": ["Haaland First Goalscorer", "Roma Red Card Issued", "Alcaraz 3-2 Sets", "G2 2-0 Score"]
    }}
  ],
  "matches": [
    // Provide AT LEAST 12 to 16 individual single picks here across all categories.
  ]
}}

CRITICAL INSTRUCTIONS:
1. "Safe Anchor Slip" (~5x) and "Value Combo Slip" (~10x) MUST contain ONLY matches taking place TODAY ({today_str}).
2. "High-Yield Slip" (~25x) and "Speculative Loto Ticket" (~50x) CAN contain matches scheduled over the NEXT 3 DAYS from {today_str}.
3. ALL entries in "matches" (Today's Approved Single Picks) MUST strictly be matches playing TODAY ({today_str}).
4. Ensure at least 12 total single matches are returned.
5. "category" MUST strictly be one of: "football", "tennis", "nba", "cs2".
6. "country" for football MUST strictly be one of: "ENG", "ESP", "ITA", "GER", "FRA", "ROU".
"""

# 3. Call Gemini & Save File
try:
    response = model.generate_content(prompt)
    clean_json = response.text.replace("```json", "").replace("```", "").strip()
    parsed = json.loads(clean_json)
    
    if api_status["api_quota_exceeded"]:
        parsed["api_quota_exceeded"] = True
        parsed["error_msg"] = api_status["error_msg"]

    with open("data.json", "w") as f:
        json.dump(parsed, f, indent=2)
    print("Successfully generated expanded dataset.")

except Exception as e:
    err_text = str(e)
    is_quota = "429" in err_text or "ResourceExhausted" in err_text or api_status["api_quota_exceeded"]
    
    fallback_data = {
        "api_quota_exceeded": is_quota,
        "error_msg": "API Key quota limit reached. Please update key." if is_quota else err_text,
        "tickets": [
            { "title": "Safe Anchor Slip", "target_odds": "5.20", "risk": "Low", "date_range": "Today Only", "picks": ["Arsenal vs Villa - Over 1.5 Goals", "Barcelona Win", "Djokovic Match Winner"] },
            { "title": "Value Combo Slip", "target_odds": "10.50", "risk": "Medium", "date_range": "Today Only", "picks": ["Real Madrid Win & Over 2.5", "Sinner 2-0 Sets", "FAZE Map 1 Winner", "Lakers +5.5"] },
            { "title": "High-Yield Slip", "target_odds": "24.80", "risk": "High", "date_range": "Next 3 Days", "picks": ["Inter vs Milan Over 22.5 Fouls", "Mbappe Over 1.5 Shots", "Celtics Over 112.5", "Vitality CS2 Win"] },
            { "title": "Speculative Loto Ticket", "target_odds": "52.00", "risk": "Extreme", "date_range": "Next 3 Days", "picks": ["Haaland First Goalscorer", "Roma vs Lazio Red Card", "Alcaraz 3-2 Sets", "G2 Esports 2-0"] }
        ],
        "matches": [
            { "category": "football", "country": "ENG", "match": "Aston Villa vs Arsenal", "pick": "Arsenal 1X & Over 1.5 Goals", "odds": 1.45, "confidence": 84, "market": "Goals/Safety" },
            { "category": "football", "country": "ENG", "match": "Liverpool vs Chelsea", "pick": "Both Teams To Score", "odds": 1.57, "confidence": 82, "market": "BTTS" },
            { "category": "football", "country": "ESP", "match": "Barcelona vs Rayo Vallecano", "pick": "Barcelona Win & Over 2.5", "odds": 1.65, "confidence": 81, "market": "Result + Goals" },
            { "category": "football", "country": "ESP", "match": "Real Madrid vs Girona", "pick": "Real Madrid Over 1.5 Team Goals", "odds": 1.50, "confidence": 85, "market": "Team Goals" },
            { "category": "football", "country": "ITA", "match": "Atalanta vs Bologna", "pick": "Atalanta 1X & Over 1.5 Goals", "odds": 1.55, "confidence": 79, "market": "Safety Combo" },
            { "category": "football", "country": "ITA", "match": "Inter vs Juventus", "pick": "Under 3.5 Goals", "odds": 1.40, "confidence": 86, "market": "Under/Over" },
            { "category": "football", "country": "GER", "match": "Bayern Munich vs Frankfurt", "pick": "Over 2.5 Goals & BTTS", "odds": 1.72, "confidence": 82, "market": "Goals Props" },
            { "category": "football", "country": "FRA", "match": "PSG vs Lille", "pick": "PSG Win", "odds": 1.48, "confidence": 83, "market": "Match Winner" },
            { "category": "football", "country": "ROU", "match": "Rapid Bucharest vs U Craiova", "pick": "Over 8.5 Corners Total", "odds": 1.85, "confidence": 74, "market": "Corners Props" },
            { "category": "tennis", "country": "GLOBAL", "match": "J. Sinner vs C. Alcaraz", "pick": "Over 21.5 Total Games", "odds": 1.80, "confidence": 76, "market": "Games Props" },
            { "category": "tennis", "country": "GLOBAL", "match": "N. Djokovic vs A. Zverev", "pick": "Djokovic Match Winner", "odds": 1.62, "confidence": 80, "market": "Match Winner" },
            { "category": "cs2", "country": "GLOBAL", "match": "FaZe Clan vs NAVI", "pick": "FaZe Map 1 Winner", "odds": 1.90, "confidence": 72, "market": "Esports Map 1" },
            { "category": "cs2", "country": "GLOBAL", "match": "Vitality vs Spirit", "pick": "Over 2.5 Total Maps", "odds": 2.05, "confidence": 70, "market": "Map Totals" },
            { "category": "nba", "country": "USA", match: "Lakers vs Celtics", "pick": "Over 224.5 Total Points", "odds": 1.88, "confidence": 75, "market": "Points Totals" },
            { "category": "nba", "country": "USA", match: "Warriors vs Mavericks", "pick": "Curry Over 24.5 Points", "odds": 1.75, "confidence": 78, "market": "Player Props" }
        ]
    }
    with open("data.json", "w") as f:
        json.dump(fallback_data, f, indent=2)
