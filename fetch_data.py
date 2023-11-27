import time
import yaml
import sqlite3
from tqdm import tqdm
from datetime import datetime, timedelta
from nba_api.stats.static import teams
from nba_api.stats.endpoints import teamgamelog
from nba_api.stats.endpoints import playergamelog
from nba_api.stats.endpoints import commonteamroster
from nba_api.stats.endpoints import boxscoreadvancedv2

with open('config.yaml', 'r') as file:
    config = yaml.safe_load(file)
    last_update = config['last_update']
    last_update = datetime.strptime(last_update, "%Y-%m-%d")
    last_update = last_update - timedelta(days=1)
    last_update = last_update.strftime("%m/%d/%Y")
    print(f"Last update: {last_update}")

conn = sqlite3.connect('database.db')
c = conn.cursor()
nba_teams = teams.get_teams()
for team in tqdm(nba_teams):
    # 1. UPDATE TeamStats table
    time.sleep(0.06)
    game_log = teamgamelog.TeamGameLog(team_id=team['id'], date_from_nullable=last_update)
    data_dict = game_log.get_dict()
    for game_results in data_dict["resultSets"]:
        for this_game_result in game_results['rowSet']:
            
            # Get basic stats
            headers = game_results['headers']
            assert headers[0].upper() == "TEAM_ID", f"TEAM_ID is not the first column: {headers[0]}"
            assert headers[1].upper() == "GAME_ID", f"GAME_ID is not the second column: {headers[1]}"
            assert headers[2].upper() == "GAME_DATE", f"GAME_DATE is not the third column: {headers[2]}"
            assert headers[3].upper() == "MATCHUP", f"MATCHUP is not the fourth column: {headers[3]}"
            
            team_id = this_game_result[0]
            game_id = this_game_result[1]
            game_date = this_game_result[2]
            game_date = datetime.strptime(game_date, "%b %d, %Y")
            game_date = game_date.strftime("%Y-%m-%d")
            home_game = 1 if this_game_result[3].split(" ")[1] == "vs." else 0
            opponent_team_id = teams.find_team_by_abbreviation(this_game_result[3].split(" ")[2])["id"]
            
            # Get advanced stats
            advanced_stats = boxscoreadvancedv2.BoxScoreAdvancedV2(game_id=game_id)
            player_stats, team_stats = advanced_stats.get_dict()["resultSets"]
            advanced_stats_headers = team_stats['headers']
            assert advanced_stats_headers[25].upper() == "PACE", f"PACE is not the 25th column: {advanced_stats_headers[25]}"
            assert advanced_stats_headers[8].upper() == "E_DEF_RATING", f"E_DEF_RATING is not the 8th column: {advanced_stats_headers[8]}"
            assert advanced_stats_headers[9].upper() == "DEF_RATING", f"DEF_RATING is not the 9th column: {advanced_stats_headers[9]}"
            
            this_team_stat = team_stats['rowSet'][0] if team_stats['rowSet'][0][1] == team_id  else team_stats['rowSet'][1]
            pace = this_team_stat[-4]
            effective_defensive_rating = this_team_stat[8]
            defensive_rating = this_team_stat[9]
            
            # Get opponent stats
            time.sleep(0.06)
            game_log = teamgamelog.TeamGameLog(team_id=opponent_team_id)
            data_dict = game_log.get_dict()
            for temp_results in data_dict["resultSets"][0]["rowSet"]:
                if temp_results[1] == game_id:
                    opponent_stats = temp_results
                    break

            opponent_stats_headers = data_dict["resultSets"][0]['headers']
            assert opponent_stats_headers[26].upper() == "PTS", f"PTS is not the 26th last column: {opponent_stats_headers[26]}"
            assert opponent_stats_headers[9].upper() == "FGM", f"FGM is not the 9th last column: {opponent_stats_headers[9]}"
            assert opponent_stats_headers[10].upper() == "FGA", f"FGA is not the 10th last column: {opponent_stats_headers[10]}"
            assert opponent_stats_headers[12].upper() == "FG3M", f"FG3M is not the 12th last column: {opponent_stats_headers[12]}"
            assert opponent_stats_headers[13].upper() == "FG3A", f"FG3A is not the 13th last column: {opponent_stats_headers[13]}"
            assert opponent_stats_headers[15].upper() == "FTM", f"FTM is not the 15th last column: {opponent_stats_headers[15]}"
            assert opponent_stats_headers[16].upper() == "FTA", f"FTA is not the 16th last column: {opponent_stats_headers[16]}"
            assert opponent_stats_headers[18].upper() == "OREB", f"OREB is not the 18th last column: {opponent_stats_headers[18]}"
            assert opponent_stats_headers[19].upper() == "DREB", f"DREB is not the 19th last column: {opponent_stats_headers[19]}"
            assert opponent_stats_headers[20].upper() == "REB", f"REB is not the 20th last column: {opponent_stats_headers[20]}"
            assert opponent_stats_headers[21].upper() == "AST", f"AST is not the 21st last column: {opponent_stats_headers[21]}"
            assert opponent_stats_headers[22].upper() == "STL", f"STL is not the 22nd last column: {opponent_stats_headers[22]}"
            assert opponent_stats_headers[23].upper() == "BLK", f"BLK is not the 23rd last column: {opponent_stats_headers[23]}"
            assert opponent_stats_headers[24].upper() == "TOV", f"TOV is not the 24th last column: {opponent_stats_headers[24]}"
            opponent_score = opponent_stats[26]
            opponent_field_goals_made = opponent_stats[9]
            opponent_field_goals_attempted = opponent_stats[10]
            opponent_three_point_field_goals_made = opponent_stats[12]
            opponent_three_point_field_goals_attempted = opponent_stats[13]
            opponent_free_throws_made = opponent_stats[15]
            opponent_free_throws_attempted = opponent_stats[16]
            opponent_defensive_rebounds = opponent_stats[19]
            opponent_offensive_rebounds = opponent_stats[18]
            opponent_total_rebounds = opponent_stats[20]
            opponent_assists = opponent_stats[21]
            opponent_steals = opponent_stats[22]
            opponent_blocks = opponent_stats[23]
            opponent_turnovers = opponent_stats[24]
    
            # SQL INSERT statement
            insert_data = (game_id, team_id, opponent_team_id, game_date, home_game, defensive_rating, effective_defensive_rating, pace, opponent_score, opponent_field_goals_made, opponent_field_goals_attempted, opponent_three_point_field_goals_made, opponent_three_point_field_goals_attempted, opponent_free_throws_made, opponent_free_throws_attempted, opponent_defensive_rebounds, opponent_offensive_rebounds, opponent_total_rebounds, opponent_assists, opponent_steals, opponent_blocks, opponent_turnovers)
            insert_statement = '''INSERT OR IGNORE INTO TeamStats(
                                    game_id, team_id, opponent_team_id, game_date, home_game,
                                    defensive_rating, effective_defensive_rating, pace, opponent_score, opponent_field_goals_made,
                                    opponent_field_goals_attempted, opponent_three_point_field_goals_made, opponent_three_point_field_goals_attempted, opponent_free_throws_made, opponent_free_throws_attempted,
                                    opponent_defensive_rebounds, opponent_offensive_rebounds, opponent_total_rebounds, opponent_assists, opponent_steals,
                                    opponent_blocks, opponent_turnovers)
                                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)'''      
            c.execute(insert_statement, insert_data)
            conn.commit()
    
    # 2. UPDATE PlayerStats table
    roster = commonteamroster.CommonTeamRoster(team_id=team['id'])
    roster_data_dict = roster.get_dict()
    roster_headers = roster_data_dict["resultSets"][0]["headers"]
    players = roster_data_dict["resultSets"][0]["rowSet"]
    print(f"\n[{team['full_name']}]: {len(players)} players")
    print("-"*50)
   
    for player in players:
        player_name = player[roster_headers.index("PLAYER")]
        player_id = player[roster_headers.index("PLAYER_ID")]
        
        time.sleep(0.06)
        print(f"\nViewing stats for {player_name}")
        game_log = playergamelog.PlayerGameLog(player_id=player_id, date_from_nullable=last_update)
        data_dict = game_log.get_dict()
        
        for game_results in data_dict["resultSets"]:
            if len(game_results['rowSet']) == 0:
                print(f"No game data found for {player_name}")
                continue
            else:
                print(f"Found {len(game_results['rowSet'])} games for {player_name}")
                
                for this_game_result in game_results['rowSet']:
                    d = {}
                    for key, value in zip(game_results['headers'], this_game_result):
                       d[key] = value
                    
                    game_date = d["GAME_DATE"]
                    game_date = datetime.strptime(game_date, "%b %d, %Y")
                    game_date = game_date.strftime("%Y-%m-%d")
                    opponent_team_id =  teams.find_team_by_abbreviation(d["MATCHUP"].split(" ")[2])["id"]
                    home_game = 1 if d["MATCHUP"].split(" ")[1] == "vs." else 0
                    
                    # SQL INSERT statement
                    data = (d["SEASON_ID"], d["Player_ID"], d["Game_ID"], game_date, opponent_team_id, d["MIN"], home_game, d["PTS"], d["FGM"], d["FGA"], d["FG3M"], d["FG3A"], d["FTM"], d["FTA"], d["OREB"], d["DREB"], d["REB"], d["AST"], d["STL"], d["BLK"], d["TOV"])
                    insert_statement = '''INSERT OR IGNORE INTO PlayerStats(season_id, player_id, game_id, game_date, opponent_team_id, minutes, home_game,
                                        points, field_goals_made, field_goals_attempted, three_point_field_goals_made,
                                        three_point_field_goals_attempted, free_throws_made, free_throws_attempted,
                                        offensive_rebounds, defensive_rebounds, total_rebounds, assists, steals, blocks, turnovers)
                                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)'''
                    c.execute(insert_statement, data)
                    conn.commit()

with open('config.yaml', 'w') as file:
    config['last_update'] = datetime.today().strftime("%Y-%m-%d")
    yaml.dump(config, file)