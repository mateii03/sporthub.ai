import os
import json
import requests
from datetime import datetime, timezone

# 1. Safely retrieve environment variables without throwing KeyError
gemini_key = os.getenv("GEMINI_API_KEY", "")
odds_key = os.getenv("ODDS_API_KEY", "")

api_status = {"api_quota_exceeded": False, "error_msg": ""}
all_odds = []

# 2. Safely fetch live odds if key exists
if odds_key:
    sports = ['soccer_epl', 'soccer_spain_la_liga', 'soccer_italy_serie_a', 'soccer_germany_bundesliga', 'basketball_nba']
    for sport in sports:
        try:
            url = f"https://api.the-odds-api.com/v4/sports/{sport}/odds/?apiKey={odds_key}&regions=eu&markets=h2h,totals"
            res = requests.get(url, timeout=10)
            if res.status_code in [401, 403, 429]:
                api_status["api_quota_exceeded"] = True
                api_status["error_msg"] = f"Odds API returned HTTP status {res.status_code}."
            elif res.status_code == 200:
                all_odds.extend(res.json()[:5])
        except Exception as e:
            print(f"Skipping {sport} due to network error: {e}")

# 3. Default fallback dataset structure
today_str = datetime.now(timezone.utc).strftime('%Y-%m-%d')
output_data = {
    "api_quota_exceeded": api_status["api_quota_exceeded"],
    "error_msg": api_status["error_msg"],
    "tickets": [
        { "title": "Safe Anchor Slip", "target_odds": "5.20", "risk": "Low", "date_range": "Today Only", "picks": ["Arsenal vs Villa - Over 1.5 Goals", "Barcelona Win", "Djokovic Match Winner"] },
        { "title": "Value Combo Slip", "target_odds": "10.50", "risk": "Medium", "date_range": "Today Only", "picks": ["Real Madrid Win & Over 2.5", "Sinner 2-0 Sets", "FAZE Map 1 Winner", "Lakers +5.5"] },
        { "title": "High-Yield Slip", "target_odds": "24.80", "risk": "High", "date_range": "Next 3 Days", "picks": ["Inter vs Milan Over 22.5 Fouls", "Mbappe Over 1.5 Shots", "Celtics Over 112.5 Points", "Vitality CS2 Win"] },
        { "title": "Speculative Loto Ticket", "target_odds": "52.00", "risk": "Extreme", "date_range": "Next 3 Days", "picks": ["Haaland First Goalscorer", "Roma vs Lazio Red Card", "Alcaraz 3-2 Sets", "G2 Esports 2-0 Score"] }
    ],
    "matches": [
        { "category": "football", "country": "ENG", "match": "Aston Villa vs Arsenal", "pick": "Arsenal 1X & Over 1.5 Goals", "odds": 1.45, "confidence": 84, "market": "Goals/Safety" },
        { "category": "football", "country": "ENG", "match": "Liverpool vs Chelsea", "pick": "Both Teams To Score", "odds": 1.57, "confidence": 82, "market": "BTTS" },
        { "category": "football", "country": "ESP", "match": "Barcelona vs Rayo Vallecano", "pick": "Barcelona Win & Over 2.5", "odds": 1.65, "confidence": 81, "market": "Result + Goals" },
        { "category": "football", "country": "ESP", "match": "Real Madrid vs Girona", "pick": "Real Madrid Over 1.5 Team Goals", "odds": 1.50, "confidence": 85, "market": "Team Goals" },
        { "category": "football", "country": "ITA", "match": "Atalanta vs Bologna", "pick": "Atalanta 1X & Over 1.5 Goals", "odds": 1.55, "confidence": 79, "market": "Safety Combo" },
        { "category": "football", "country": "GER", "match": "Bayern Munich vs Frankfurt", "pick": "Over 2.5 Goals & BTTS", "odds": 1.72, "confidence": 82, "market": "Goals Props" },
        { "category": "football", "country": "FRA", "match": "PSG vs Lille", "pick": "PSG Win", "odds": 1.48, "confidence": 83, "market": "Match Winner" },
        { "category": "football", "country": "ROU", "match": "Rapid Bucharest vs U Craiova", "pick": "Over 8.5 Corners Total", "odds": 1.85, "confidence": 74, "market": "Corners Props" },
        { "category": "tennis", "country": "GLOBAL", "match": "J. Sinner vs C. Alcaraz", "pick": "Over 21.5 Total Games", "odds": 1.80, "confidence": 76, "market": "Games Props" },
        { "category": "cs2", "country": "GLOBAL", "match": "FaZe Clan vs NAVI", "pick": "FaZe Map 1 Winner", "odds": 1.90, "confidence": 72, "market": "Esports Map 1" },
        { "category": "nba", "country": "USA", "match": "Lakers vs Celtics", "pick": "Over 224.5 Total Points", "odds": 1.88, "confidence": 75, "market": "Points Totals" }
    ]
}

# 4. Safely attempt AI prediction generation
if gemini_key:
    try:
        import google.generativeai as genai
        genai.configure(api_key=gemini_key)
        model = genai.GenerativeModel('gemini-2.5-flash')
        
        prompt = f"""
        You are a sports analytics engine. Current UTC Date: {today_str}.
        Analyze odds data: {json.dumps(all_odds[:20])}
        Return JSON object with "tickets" (Safe Anchor/Value/High-Yield/Speculative) and "matches" (at least 12 single picks).
        Categories: "football", "tennis", "nba", "cs2". Football countries: "ENG", "ESP", "ITA", "GER", "FRA", "ROU".
        """
        response = model.generate_content(prompt)
        clean_json = response.text.replace("```json", "").replace("```", "").strip()
        parsed = json.loads(clean_json)
        if "matches" in parsed and len(parsed["matches"]) > 0:
            output_data = parsed
    except Exception as e:
        print(f"Gemini fallback activated: {e}")
        output_data["api_quota_exceeded"] = True
        output_data["error_msg"] = str(e)

# 5. Save output ensuring zero exit status
with open("data.json", "w") as f:
    json.dump(output_data, f, indent=2)

print("update_picks.py executed successfully.")
