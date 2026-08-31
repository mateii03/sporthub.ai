import os
import json
import requests
import google.generativeai as genai

# Configure Gemini API
genai.configure(api_key=os.environ["GEMINI_API_KEY"])
model = genai.GenerativeModel('gemini-2.5-flash')

# 1. Fetch live odds from The Odds API
ODDS_API_KEY = os.environ["ODDS_API_KEY"]
sports = ['soccer_epl', 'soccer_spain_la_liga', 'soccer_italy_serie_a', 'basketball_nba']
all_odds = []

for sport in sports:
    try:
        url = f"https://api.the-odds-api.com/v4/sports/{sport}/odds/?apiKey={ODDS_API_KEY}&regions=eu&markets=h2h,totals"
        res = requests.get(url, timeout=10)
        if res.status_code == 200:
            all_odds.extend(res.json()[:5])
    except Exception as e:
        print(f"Error fetching {sport}: {e}")

# 2. Prompt Gemini to analyze fixtures and format output for frontend
prompt = f"""
You are a predictive sports analytics engine. Analyze these incoming match odds data:
{json.dumps(all_odds[:15])}

Generate a JSON object matching this EXACT schema with NO markdown code blocks, NO extra text:
{{
  "tickets": [
    {{
      "title": "Safe Anchor Slip",
      "target_odds": "5.20",
      "risk": "Low",
      "picks": ["Arsenal vs Villa - Over 1.5 Goals", "Barcelona - Win", "Djokovic - Match Winner"]
    }},
    {{
      "title": "Value Combo Slip",
      "target_odds": "10.50",
      "risk": "Medium",
      "picks": ["Selection 1", "Selection 2", "Selection 3", "Selection 4"]
    }},
    {{
      "title": "High-Yield Slip",
      "target_odds": "24.80",
      "risk": "High",
      "picks": ["Selection 1", "Selection 2", "Selection 3", "Selection 4"]
    }},
    {{
      "title": "Speculative Loto Ticket",
      "target_odds": "52.00",
      "risk": "Extreme",
      "picks": ["Selection 1", "Selection 2", "Selection 3", "Selection 4"]
    }}
  ],
  "matches": [
    {{
      "category": "football",
      "country": "ENG",
      "match": "Aston Villa vs Arsenal",
      "pick": "Arsenal 1X & Over 1.5 Goals",
      "odds": 1.45,
      "confidence": 84,
      "market": "Goals/Safety"
    }}
  ]
}}

Include picks for football (countries: ENG, ESP, ITA, GER, FRA, ROU), tennis, nba, and cs2.
"""

# 3. Call AI Model & Write File
try:
    response = model.generate_content(prompt)
    clean_json = response.text.replace("```json", "").replace("```", "").strip()
    parsed = json.loads(clean_json)
    
    with open("data.json", "w") as f:
        json.dump(parsed, f, indent=2)
    print("Successfully updated data.json!")
    
except Exception as e:
    print(f"Failed to generate predictions: {e}")
