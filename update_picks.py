import os
import json
import requests
import google.generativeai as genai

genai.configure(api_key=os.environ["GEMINI_API_KEY"])
model = genai.GenerativeModel('gemini-2.5-flash')

ODDS_API_KEY = os.getenv("ODDS_API_KEY", "")
sports = ['soccer_epl', 'soccer_spain_la_liga', 'soccer_italy_serie_a', 'basketball_nba']
all_odds = []

# Fetch live odds if key exists
if ODDS_API_KEY:
    for sport in sports:
        try:
            url = f"https://api.the-odds-api.com/v4/sports/{sport}/odds/?apiKey={ODDS_API_KEY}&regions=eu&markets=h2h,totals"
            res = requests.get(url, timeout=10)
            if res.status_code == 200:
                all_odds.extend(res.json()[:5])
        except Exception as e:
            print(f"Error fetching {sport}: {e}")

prompt = f"""
You are a predictive sports analytics engine. Analyze these incoming odds (or use active today's fixtures across top sports if empty):
{json.dumps(all_odds[:15])}

Generate a JSON object matching this EXACT schema with NO markdown formatting, NO extra prose:
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
      "picks": ["Real Madrid - Win & Over 2.5", "Sinner 2-0 Sets", "FAZE vs NAVI - Map 1", "Lakers +5.5"]
    }},
    {{
      "title": "High-Yield Slip",
      "target_odds": "24.80",
      "risk": "High",
      "picks": ["Inter vs Milan - Over 22.5 Fouls", "Mbappe Over 1.5 Shots on Target", "Celtics Over 112.5 Points", "Vitality CS2 Win"]
    }},
    {{
      "title": "Speculative Loto Ticket",
      "target_odds": "52.00",
      "risk": "Extreme",
      "picks": ["Haaland First Goalscorer", "Roma vs Lazio Red Card", "Alcaraz 3-2 Sets", "G2 Esports 2-0 Score"]
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
    }},
    {{
      "category": "football",
      "country": "ESP",
      "match": "Barcelona vs Rayo Vallecano",
      "pick": "Barcelona Win & Over 2.5",
      "odds": 1.65,
      "confidence": 81,
      "market": "Result + Goals"
    }},
    {{
      "category": "tennis",
      "country": "GLOBAL",
      "match": "J. Sinner vs C. Alcaraz",
      "pick": "Over 21.5 Total Games",
      "odds": 1.80,
      "confidence": 76,
      "market": "Games Props"
    }},
    {{
      "category": "cs2",
      "country": "GLOBAL",
      "match": "FaZe Clan vs NAVI",
      "pick": "FaZe Map 1 Winner",
      "odds": 1.90,
      "confidence": 72,
      "market": "Esports Map 1"
    }},
    {{
      "category": "nba",
      "country": "USA",
      "match": "Lakers vs Celtics",
      "pick": "Over 224.5 Total Points",
      "odds": 1.88,
      "confidence": 75,
      "market": "Points Totals"
    }}
  ]
}}

CRITICAL INSTRUCTIONS FOR KEYS:
1. "category" MUST strictly be one of: "football", "tennis", "nba", "cs2".
2. "country" for football MUST strictly be one of: "ENG", "ESP", "ITA", "GER", "FRA", "ROU".
"""

try:
    response = model.generate_content(prompt)
    clean_json = response.text.replace("```json", "").replace("```", "").strip()
    parsed = json.loads(clean_json)
    
    with open("data.json", "w") as f:
        json.dump(parsed, f, indent=2)
    print("Successfully populated data.json!")
    
except Exception as e:
    print(f"Generation error: {e}")
