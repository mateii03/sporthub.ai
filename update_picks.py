import os
import json
import re
import requests
from datetime import datetime, timezone

# 1. Retrieve current UTC date dynamically
now_utc = datetime.now(timezone.utc)
today_str = now_utc.strftime('%Y-%m-%d')
today_readable = now_utc.strftime('%A, %B %d, %Y')

gemini_key = os.getenv("GEMINI_API_KEY", "")
odds_key = os.getenv("ODDS_API_KEY", "")

api_status = {"api_quota_exceeded": False, "error_msg": ""}
all_odds = []

# 2. Query Odds API if key is present
if odds_key:
    sports = ['soccer_epl', 'soccer_spain_la_liga', 'soccer_italy_serie_a', 'soccer_germany_bundesliga', 'basketball_nba']
    for sport in sports:
        try:
            url = f"https://api.the-odds-api.com/v4/sports/{sport}/odds/?apiKey={odds_key}&regions=eu&markets=h2h,totals"
            res = requests.get(url, timeout=10)
            if res.status_code in [401, 403, 429]:
                api_status["api_quota_exceeded"] = True
                api_status["error_msg"] = f"Odds API HTTP {res.status_code}: Quota limits reached."
            elif res.status_code == 200:
                all_odds.extend(res.json()[:4])
        except Exception as e:
            print(f"Skipping {sport} network call: {e}")

output_data = None

# 3. Request dynamic predictions from Gemini
if gemini_key:
    try:
        import google.generativeai as genai
        genai.configure(api_key=gemini_key)
        model = genai.GenerativeModel('gemini-2.5-flash')
        
        prompt = f"""
        You are a sports analytics AI. Today's Date is {today_readable} ({today_str}).
        Live Odds sample: {json.dumps(all_odds[:15])}
        
        Generate a JSON object with strictly two top-level keys: "tickets" and "matches".
        DO NOT use static placeholder teams (e.g. do not repeat Villa vs Arsenal unless playing today).
        
        REQUIREMENTS:
        1. "tickets": Array of exactly 4 accumulators:
           - "Safe Anchor Slip": target_odds ~5.00, risk "Low", date_range "Today Only", 3-4 picks.
           - "Value Combo Slip": target_odds ~10.00, risk "Medium", date_range "Today Only", 4 picks.
           - "High-Yield Slip": target_odds ~25.00, risk "High", date_range "Next 3 Days", 4 picks.
           - "Speculative Loto Ticket": target_odds ~50.00+, risk "Extreme", date_range "Next 3 Days", 4 picks.
        
        2. "matches": Array of AT LEAST 16 DISTINCT single picks for TODAY ({today_readable}).
           Categories to include:
           - Football: Top European Leagues (ENG, ESP, ITA, GER, FRA) + Romanian SuperLiga (ROU)
           - Tennis: ATP/WTA current events
           - Basketball: NBA
           - Esports: CS2
           
           Each item schema:
           {{
             "category": "football" | "tennis" | "nba" | "cs2",
             "country": "ENG" | "ESP" | "ITA" | "GER" | "FRA" | "ROU" | "GLOBAL" | "USA",
             "match": "Team A vs Team B",
             "pick": "Specific Bet Name",
             "odds": 1.65,
             "confidence": 82,
             "market": "Market Name",
             "date_badge": "Today"
           }}

        Return ONLY valid JSON wrapped inside ```json ... ``` code tags.
        """
        response = model.generate_content(prompt)
        text = response.text
        clean_json = re.sub(r'```(?:json)?\s*', '', text).strip().rstrip('`')
        parsed = json.loads(clean_json)
        if "tickets" in parsed and "matches" in parsed and len(parsed["matches"]) >= 8:
            output_data = parsed
    except Exception as e:
        print(f"Gemini AI exception: {e}")
        api_status["api_quota_exceeded"] = True
        api_status["error_msg"] = str(e)

# 4. Save JSON safely
if not output_data:
    output_data = {
        "api_quota_exceeded": True,
        "error_msg": api_status["error_msg"] or "GEMINI_API_KEY missing or quota exceeded in GitHub Secrets.",
        "last_updated": today_str,
        "tickets": [],
        "matches": []
    }
else:
    output_data["api_quota_exceeded"] = api_status["api_quota_exceeded"]
    output_data["error_msg"] = api_status["error_msg"]
    output_data["last_updated"] = today_str

with open("data.json", "w") as f:
    json.dump(output_data, f, indent=2)

print(f"Successfully generated data.json for {today_str}.")
