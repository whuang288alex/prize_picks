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


# 1. Read the last update date from config file
with open('config.yaml', 'r') as file:
    config = yaml.safe_load(file)
    last_update = config['last_update']
    last_update = datetime.strptime(last_update, "%Y-%m-%d")
    last_update = last_update.strftime("%m/%d/%Y")
    print(f"Last update: {last_update}")


# 2. Connect to database
conn = sqlite3.connect('database.db')
c = conn.cursor()


# 3. Update Data one team at a time
timeout = 200
for team in tqdm(teams.get_teams()):
    
    # 3-1 UPDATE TeamStats table
    time.sleep(0.1)
    team_game_data = teamgamelog.TeamGameLog(team_id=team['id'], date_from_nullable=last_update, timeout=timeout).get_dict()["resultSets"][0]
    team_game_headers = team_game_data['headers']
    assert team_game_headers == ['Team_ID', 'Game_ID', 'GAME_DATE', 'MATCHUP', 'WL', 'W', 'L', 'W_PCT', 'MIN', 'FGM', 'FGA', 'FG_PCT', 'FG3M', 'FG3A', 'FG3_PCT', 'FTM', 'FTA', 'FT_PCT', 'OREB', 'DREB', 'REB', 'AST', 'STL', 'BLK', 'TOV', 'PF', 'PTS'], f"headers has changed format: {team_game_headers}"
    print(f"\n\nFound {len(team_game_data['rowSet'])} new team stats for {team['full_name']}")
    
    for this_game_result in team_game_data['rowSet']:
        
        # Get basic stats
        team_id = this_game_result[team_game_headers.index("Team_ID")]
        game_id = this_game_result[team_game_headers.index("Game_ID")]
        game_date = this_game_result[team_game_headers.index("GAME_DATE")]
        match_up = this_game_result[team_game_headers.index("MATCHUP")]
        
        game_date = datetime.strptime(game_date, "%b %d, %Y")
        game_date = game_date.strftime("%Y-%m-%d")
        home_game = 1 if match_up.split(" ")[1] == "vs." else 0
        opponent_team_id = teams.find_team_by_abbreviation(match_up.split(" ")[2])["id"]
        
        # Get advanced defensive stats this team for this game
        advanced_stats_data = boxscoreadvancedv2.BoxScoreAdvancedV2(game_id=game_id).get_dict()["resultSets"][1]
        advanced_stats_headers = advanced_stats_data['headers']
        assert advanced_stats_headers == ['GAME_ID', 'TEAM_ID', 'TEAM_NAME', 'TEAM_ABBREVIATION', 'TEAM_CITY', 'MIN', 'E_OFF_RATING', 'OFF_RATING', 'E_DEF_RATING', 'DEF_RATING', 'E_NET_RATING', 'NET_RATING', 'AST_PCT', 'AST_TOV', 'AST_RATIO', 'OREB_PCT', 'DREB_PCT', 'REB_PCT', 'E_TM_TOV_PCT', 'TM_TOV_PCT', 'EFG_PCT', 'TS_PCT', 'USG_PCT', 'E_USG_PCT', 'E_PACE', 'PACE', 'PACE_PER40', 'POSS', 'PIE'], f"advanced_stats_headers has changed format: {advanced_stats_headers}"
        
        this_team_advanced_stat = advanced_stats_data['rowSet'][0] if advanced_stats_data['rowSet'][0][1] == team_id  else advanced_stats_data['rowSet'][1]
        pace = this_team_advanced_stat[advanced_stats_headers.index("PACE")]
        effective_defensive_rating = this_team_advanced_stat[advanced_stats_headers.index("E_DEF_RATING")]
        defensive_rating = this_team_advanced_stat[advanced_stats_headers.index("DEF_RATING")]
        
        # Get opponent stats
        time.sleep(0.1)
        opponent_data = teamgamelog.TeamGameLog(team_id=opponent_team_id, timeout=timeout).get_dict()["resultSets"][0]
        opponent_stats_headers = opponent_data['headers']
        assert opponent_stats_headers == ['Team_ID', 'Game_ID', 'GAME_DATE', 'MATCHUP', 'WL', 'W', 'L', 'W_PCT', 'MIN', 'FGM', 'FGA', 'FG_PCT', 'FG3M', 'FG3A', 'FG3_PCT', 'FTM', 'FTA', 'FT_PCT', 'OREB', 'DREB', 'REB', 'AST', 'STL', 'BLK', 'TOV', 'PF', 'PTS'], f"opponent_stats_headers has changed format: {opponent_stats_headers}"
        for opponent_game_results in opponent_data["rowSet"]:
            if opponent_game_results[1] == game_id:
                opponent_stats = opponent_game_results
                break

        opponent_score = opponent_stats[opponent_stats_headers.index("PTS")]
        opponent_field_goals_made = opponent_stats[opponent_stats_headers.index("FGM")]
        opponent_field_goals_attempted = opponent_stats[opponent_stats_headers.index("FGA")]
        opponent_three_point_field_goals_made = opponent_stats[opponent_stats_headers.index("FG3M")]
        opponent_three_point_field_goals_attempted = opponent_stats[opponent_stats_headers.index("FG3A")]
        opponent_free_throws_made = opponent_stats[opponent_stats_headers.index("FTM")]
        opponent_free_throws_attempted = opponent_stats[opponent_stats_headers.index("FTA")]
        opponent_defensive_rebounds = opponent_stats[opponent_stats_headers.index("DREB")]
        opponent_offensive_rebounds = opponent_stats[opponent_stats_headers.index("OREB")]
        opponent_total_rebounds = opponent_stats[opponent_stats_headers.index("REB")]
        opponent_assists = opponent_stats[opponent_stats_headers.index("AST")]
        opponent_steals = opponent_stats[opponent_stats_headers.index("STL")]
        opponent_blocks = opponent_stats[opponent_stats_headers.index("BLK")]
        opponent_turnovers = opponent_stats[opponent_stats_headers.index("TOV")]

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
    
    # 3-2 UPDATE PlayerStats table
    time.sleep(0.1)
    roster_data = commonteamroster.CommonTeamRoster(team_id=team['id'], timeout=timeout).get_dict()["resultSets"][0]
    roster_headers = roster_data['headers']
    assert roster_headers == ['TeamID', 'SEASON', 'LeagueID', 'PLAYER', 'NICKNAME', 'PLAYER_SLUG', 'NUM', 'POSITION', 'HEIGHT', 'WEIGHT', 'BIRTH_DATE', 'AGE', 'EXP', 'SCHOOL', 'PLAYER_ID', 'HOW_ACQUIRED'], f"roster_headers has changed format: {roster_headers}"
    
    print(f"[{team['full_name']}]: {len(roster_data['rowSet'])} players")
    for player_info in roster_data['rowSet']:
        
        # get player name and id from player info
        player_name = player_info[roster_data["headers"].index("PLAYER")]
        player_id = player_info[roster_data["headers"].index("PLAYER_ID")]
        
        time.sleep(0.1)
        player_game_data = playergamelog.PlayerGameLog(player_id=player_id, date_from_nullable=last_update, timeout=timeout).get_dict()["resultSets"][0]
        player_game_headers = player_game_data['headers']
        assert player_game_headers  == ['SEASON_ID', 'Player_ID', 'Game_ID', 'GAME_DATE', 'MATCHUP', 'WL', 'MIN', 'FGM', 'FGA', 'FG_PCT', 'FG3M', 'FG3A', 'FG3_PCT', 'FTM', 'FTA', 'FT_PCT', 'OREB', 'DREB', 'REB', 'AST', 'STL', 'BLK', 'TOV', 'PF', 'PTS', 'PLUS_MINUS', 'VIDEO_AVAILABLE'], f"player_game_headers has changed format: {player_game_headers}"
        
        print(f"Found {len(player_game_data['rowSet'])} games for {player_name}")  
        for this_game_result in player_game_data['rowSet']:
            
            game_date = this_game_result[player_game_headers.index("GAME_DATE")]
            game_date = datetime.strptime(game_date, "%b %d, %Y")
            game_date = game_date.strftime("%Y-%m-%d")
            match_up = this_game_result[player_game_headers.index("MATCHUP")]
            opponent_team_id =  teams.find_team_by_abbreviation(match_up.split(" ")[2])["id"]
            home_game = 1 if match_up.split(" ")[1] == "vs." else 0
            
            # SQL INSERT statement
            data = (this_game_result[player_game_headers.index("SEASON_ID")],
                    player_id,
                    this_game_result[player_game_headers.index("Game_ID")],
                    game_date,
                    opponent_team_id,
                    this_game_result[player_game_headers.index("MIN")],
                    home_game,
                    this_game_result[player_game_headers.index("PTS")],
                    this_game_result[player_game_headers.index("FGM")],
                    this_game_result[player_game_headers.index("FGA")],
                    this_game_result[player_game_headers.index("FG3M")],
                    this_game_result[player_game_headers.index("FG3A")],
                    this_game_result[player_game_headers.index("FTM")],
                    this_game_result[player_game_headers.index("FTA")],
                    this_game_result[player_game_headers.index("OREB")],
                    this_game_result[player_game_headers.index("DREB")],
                    this_game_result[player_game_headers.index("REB")],
                    this_game_result[player_game_headers.index("AST")],
                    this_game_result[player_game_headers.index("STL")],
                    this_game_result[player_game_headers.index("BLK")],
                    this_game_result[player_game_headers.index("TOV")])
            insert_statement = '''INSERT OR IGNORE INTO PlayerStats(season_id, player_id, game_id, game_date, opponent_team_id, minutes, home_game,
                                points, field_goals_made, field_goals_attempted, three_point_field_goals_made,
                                three_point_field_goals_attempted, free_throws_made, free_throws_attempted,
                                offensive_rebounds, defensive_rebounds, total_rebounds, assists, steals, blocks, turnovers)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)'''
            c.execute(insert_statement, data)
            conn.commit()


# 4. Update config file
with open('config.yaml', 'w') as file:
    last_update = datetime.today() - timedelta(days=1)
    config['last_update'] = last_update.strftime("%Y-%m-%d")
    yaml.dump(config, file)