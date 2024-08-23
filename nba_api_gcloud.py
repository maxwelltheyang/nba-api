"""
Responds to GET commands by the API using custom web domain
GCloud to invoke function globally
"""
import functions_framework
import requests
from bs4 import BeautifulSoup
import pandas as pd
from pymongo import MongoClient
import ssl
import certifi
import os
from dotenv import load_dotenv

"""
Example usage:
nbametrics.com/team/BOS/stats/pergame/alltime/total
nbametrics.com/team/GSW/stats/perseason/alltime/total
"""

load_dotenv()
MONGO_DB = os.environ.get("MONGO_DB")

def format_response(command):
    sections = command.split("/")
    if sections[0] == "team" and sections[2] == "stats":
        return process_team_stats(sections[1], sections[3], sections[4], sections[5], command)


def process_team_stats(team, stat_type, time, aggtype, command):
    ca = certifi.where()
    client = MongoClient(f'mongodb+srv://maxwellbyang04:{MONGO_DB}@nba-api.gajy9.mongodb.net/', tlsCAFile=ca)
    db = client['nba_stats']
    collection = db['teams']
    query = {"team_name": team}

    document = collection.find_one(query)
    if not document or stat_type not in document:
        web_to_db(team, stat_type)
        document = collection.find_one(query)

    if stat_type not in document:
        return {"status": 404, "message": "Stat type invalid"}
    
    df = pd.DataFrame(document.get(stat_type, []))

    if df.empty:
        return {"status": 404, "message": "No data found"}

    if "Ht." in df.columns and not df["Ht."].str.contains('%').any():
        df["Ht."] = df["Ht."].apply(lambda x: int(x.split("-")[0]) * 12 + int(x.split("-")[1]) if isinstance(x, str) and "-" in x else x)

    to_correct = []
    for col in df.columns:
        if df[col].str.contains('%', na=False).any():
            df[col] = df[col].apply(lambda x: str(float(x.replace('%', '')) / 100) if isinstance(x, str) and '%' in x else x)
            to_correct.append(col)

    df = df.dropna()
    seasons = []

    if aggtype == "total":
        omit = ['Season', 'Lg', 'Tm', 'Finish', 'FG%', '3P%', '2P%', 'FT%']
        sum_dict = {}
        for col in df.columns:
            if col not in omit:
                if time == "alltime":
                    sum_dict[col] = df[col].replace("", 0).dropna().astype(float).sum().round(2)
                    seasons = df["Season"]
                else:
                    sum_dict[col] = df[(df['Season'].str[:4].astype(int) >= int(time[:4])) & 
                                       (df['Season'].str[:4].astype(int) < int(time[5:]))][col].replace("", 0).dropna().astype(float).sum().round(2)
                    seasons = df[(df['Season'].str[:4].astype(int) >= int(time[:4])) & 
                                 (df['Season'].str[:4].astype(int) < int(time[5:]))]['Season']
        if "Ht." in df.columns:
            sum_dict["Ht."] = f"{int(sum_dict['Ht.'] // 12)}'{round(sum_dict['Ht.'] % 12, 1)}" if "Ht." in sum_dict and sum_dict["Ht."] > 1 else sum_dict.get("Ht.", None)

        for col in to_correct:
            if col in sum_dict:
                sum_dict[col] = f"{round(sum_dict[col] * 100, 2)}%"
        response = {
            "status": 200,
            "command": f"GET {command}",
            "type": "total",
            "team": team,
            "seasons": seasons.tolist(),
            "stats": sum_dict
        }
        return response
    
    elif aggtype == "average":
        omit = ['Season', 'Lg', 'Tm']
        avg_dict = {}
        for col in df.columns:
            if col not in omit:
                if time == "alltime":
                    avg_dict[col] = df[col].replace("", pd.NA).astype("Float64").mean().round(2)
                    seasons = df["Season"]
                else:
                    avg_dict[col] = df[(df['Season'].str[:4].astype(int) >= int(time[:4])) & 
                                       (df['Season'].str[:4].astype(int) < int(time[5:]))][col].replace("", pd.NA).astype("Float64").mean().round(2)
                    seasons = df[(df['Season'].str[:4].astype(int) >= int(time[:4])) & 
                                 (df['Season'].str[:4].astype(int) < int(time[5:]))]['Season']
        if "Ht." in df.columns:
            avg_dict["Ht."] = f"{int(avg_dict['Ht.'] // 12)}'{round(avg_dict['Ht.'] % 12, 1)}" if "Ht." in avg_dict and avg_dict["Ht."] > 1 else avg_dict.get("Ht.", None) 
        response = {
            "status": 200,
            "command": f"GET {command}",
            "type": "average",
            "team": team,
            "seasons": seasons.tolist(),
            "stats": avg_dict
        }
        for col in to_correct:
            if col in avg_dict:
                avg_dict[col] = f"{round(avg_dict[col] * 100, 2)}%"
        return response
    
    else:
        return {"status": 400, "message": "Invalid aggregation type"}
    
def web_to_db(team, stat_type):
    types = {
        "perseason": "stats_basic_totals",
        "pergame": "stats_per_game_totals",
        "opp_perseason": "opp_stats_basic_totals",
        "opp_pergame": "opp_stats_per_game_totals",
        "perseason_rank": "stats_basic_ranks",
        "pergame_rank": "stats_per_game_ranks",
        "opp_perseason_rank": "opp_stats_basic_ranks",
        "opp_pergame_rank": "opp_stats_per_game_ranks",
        "perseason_yoy": "stats_basic_yr_yr",
        "pergame_yoy": "stats_per_game_yr_yr",
        "opp_perseason_yoy": "opp_stats_basic_yr_yr",
        "opp_pergame_yoy": "opp_stats_per_game_yr_yr"
    }
    url = f"https://www.basketball-reference.com/teams/{team}/{types[stat_type]}.html#stats"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    data = []
    list_header = []
    header = soup.find_all("table")[0].find("tr")
    for items in header:
        try:
            txt = items.get_text().strip().replace("\n", "")
            if (txt != ''):
                list_header.append(txt)
        except:
            continue
    HTML_data = soup.find_all("table")[0].find_all("tr")[1:]
    for element in HTML_data:
        sub_data = []
        for sub_element in element.find_all(['td', 'th']):
            if (sub_element.get("data-stat") != "foo" and not sub_element.has_attr('aria-label')):
                try:
                    txt = sub_element.get_text().strip().replace("\n", "")
                    sub_data.append(txt)
                except:
                    continue
        data.append(sub_data)
    df = pd.DataFrame(data = data, columns = list_header)
    data_dict = df.to_dict("records")
    ca = certifi.where()
    client = MongoClient(f'mongodb+srv://maxwellbyang04:{MONGO_DB}@nba-api.gajy9.mongodb.net/', tlsCAFile=ca)
    db = client['nba_stats']
    collection = db['teams']
    collection.update_one(
        {"team_name": team},
        {"$set": {stat_type: data_dict}},
        upsert=True
    )

@functions_framework.http
def hello_http(request):
    path = request.path
    parts = path.strip('/').split('/')
    if len(parts) != 6 or parts[0] != "team" or parts[2] != "stats":
        return {"status": 400}
    team_name = parts[1]
    stat_type = parts[3]
    time = parts[4]
    aggtype = parts[5]
    command = f"team/{team_name}/stats/{stat_type}/{time}/{aggtype}"
    return format_response(command)
