import os
import sqlite3
import numpy as np
import pandas as pd
import streamlit as st
import plotly.express as px
from nba_api.stats.static import teams
from nba_api.stats.static import players


STATS = ["combo", "minutes", "points", "field_goals_made", "field_goals_attempted", "three_point_field_goals_made", "three_point_field_goals_attempted", "free_throws_made", "free_throws_attempted", "offensive_rebounds", "defensive_rebounds", "total_rebounds", "assists", "steals", "blocks", "turnovers"]
STATS_FOR_DISPLAY = ["Combo", "Minutes", "Points", "Field Goals Made", "Field Goals Attempted", "3-Point Field Goals Made", "3-Point Field Goals Attempted", "Free Throws Made", "Free Throws Attempted", "Offensive Rebounds", "Defensive Rebounds", "Total Rebounds", "Assists", "Steals", "Blocks", "Turnovers"]
TEAMS = ["Atlanta Hawks", "Boston Celtics", "Brooklyn Nets", "Charlotte Hornets", "Chicago Bulls", "Cleveland Cavaliers", "Dallas Mavericks", "Denver Nuggets", "Detroit Pistons", "Golden State Warriors", "Houston Rockets", "Indiana Pacers", "Los Angeles Clippers", "Los Angeles Lakers", "Memphis Grizzlies", "Miami Heat", "Milwaukee Bucks", "Minnesota Timberwolves", "New Orleans Pelicans", "New York Knicks", "Oklahoma City Thunder", "Orlando Magic", "Philadelphia 76ers", "Phoenix Suns", "Portland Trail Blazers", "Sacramento Kings", "San Antonio Spurs", "Toronto Raptors", "Utah Jazz", "Washington Wizards"]
TEAM_STATS = ["defensive_rating", "effective_defensive_rating", "pace", "opponent_score", "opponent_field_goals_made", "opponent_field_goals_attempted", "opponent_three_point_field_goals_made", "opponent_three_point_field_goals_attempted", "opponent_free_throws_made", "opponent_free_throws_attempted", "opponent_defensive_rebounds", "opponent_offensive_rebounds", "opponent_total_rebounds", "opponent_assists", "opponent_steals", "opponent_blocks", "opponent_turnovers"]
TEAM_STATS_FOR_DISPLAY = ["Defensive Rating", "Effective Defensive Rating", "Pace", "Opponent Score", "Opponent Field Goals Made", "Opponent Field Goals Attempted", "Opponent 3-Point Field Goals Made", "Opponent 3-Point Field Goals Attempted", "Opponent Free Throws Made", "Opponent Free Throws Attempted", "Opponent Defensive Rebounds", "Opponent Offensive Rebounds", "Opponent Total Rebounds", "Opponent Assists", "Opponent Steals", "Opponent Blocks", "Opponent Turnovers"]


# Set the width of the charts
st.set_page_config(page_title="NBA Stats Visualizer", page_icon=":basketball:")
# width = 500
# st.set_page_config(layout="wide")


# Create two columns, one for player and one for team stats
# player_stats_col, team_stats_col = st.columns(2)
conn = sqlite3.connect('database.db')
c = conn.cursor()

# Player Stats Selection in the first column
# with player_stats_col:
    
st.title("Player Stats")

# User input: Player name and stat category
player_name = st.text_input("Enter player's name:", "LeBron James")
stat_category = st.selectbox("Select a stat category:", STATS_FOR_DISPLAY, index=1)
last_n_games = st.slider("Select number of games:", 1, 15, 10)
players_list = players.find_players_by_full_name(player_name)
home_game = st.selectbox("Home or Away:", ["All", "Home", "Away"], index=0)

if stat_category == "Combo":
    options = ["points", "assists", "total_rebounds", "steals", "blocks", "turnovers"]
    options_to_display = ["Points", "Assists", "Rebounds", "Steals", "Blocks", "Turnovers"]
    selected_options = st.multiselect('Select your options:', options_to_display, default=["Points", "Assists", "Rebounds"])
    fields = ""
    fields_to_display = ""
    for option in selected_options:
        fields += options[options_to_display.index(option)] + " + "
        fields_to_display += option + " + "
    fields = fields[:-2]
    fields_to_display = fields_to_display[:-2]
else:
    fields = STATS[STATS_FOR_DISPLAY.index(stat_category)]
    fields_to_display = stat_category
    
if len(players_list) > 0:

    # Home game or away game
    if home_game == "All":
        home_game_clause = "(home_game = 1 OR home_game = 0)"
    elif home_game == "Home":
        home_game_clause = "home_game = 1"
    else:
        home_game_clause = "home_game = 0"
    
    if fields != "":
        # Get this stats for the player
        pid = players_list[0]['id']
        c.execute(f'''SELECT game_date, {fields} from PlayerStats WHERE player_id={pid} AND {home_game_clause} ORDER BY game_date DESC LIMIT {last_n_games}''')
        player_stats = c.fetchall()
        conn.commit()
        
        # Create a list of the stats
        dates = [stat[0] for stat in player_stats]
        data = [stat[1] for stat in player_stats]
        
        # pick a threshold, default to the mean of the stats
        threshold = st.slider("Select a threshold:", 0.0, 50.0, np.mean(data), 0.5)
        
        # STATS_FOR_DISPLAY the average stat value
        st.markdown(
            f'<div style="text-align:center; padding: 20px; background-color: #f0f0f0; border-radius: 10px;">'
            f'<p style="font-size:24px; font-family: Arial, sans-serif; margin: 0;">'
            f'Average {fields_to_display}:</p>'
            f'<p style="font-size:32px; font-weight: bold; margin: 0;">'
            f'{np.mean(data):.2f}</p>'
            '</div>',
            unsafe_allow_html=True # so html will not be treated as text
        )
        
        # Create a DataFrame for the stats
        df = pd.DataFrame({
            "Game": dates,
            "Stat Value": data
        })
        
        # Create a line chart with point traces, and add a threshold line
        fig1 = px.line(df, x="Game", y="Stat Value", title=f"{fields_to_display} Over the Past {last_n_games} Games")
        fig1.update_traces(mode='markers+lines', marker=dict(size=8, line=dict(width=2, color='DarkSlateGrey')))
        fig1.add_hline(y=threshold, line_dash="dot", annotation_text="Threshold", annotation_position="top right")
        fig1.update_yaxes(tickvals=list(range(int(min(data)), int(max(data)) + 1, 1)))
        # fig1.update_layout(width = width)
            
        # STATS_FOR_DISPLAY the chart
        st.plotly_chart(fig1)
else:
    st.warning("Player not found. Please enter a valid player's name.")


# Team Stats Selection in the second column
# with team_stats_col:
    
st.title("Team Defensive Stats")
team_name = st.selectbox("Select a team:", TEAMS, index=0)
team_stats_category = st.selectbox("Select a stat category for team data:", TEAM_STATS_FOR_DISPLAY, index=1)
team_last_n_games = st.slider("Select number of games for team_data:", 1, 15, 10)
team_home_game = st.selectbox("Home or Away for team data:", ["All", "Home", "Away"], index=0)

# Home game or away game
if team_home_game == "All":
    team_home_game_clause = "(home_game = 1 OR home_game=0)"
elif team_home_game == "Home":
    team_home_game_clause = "home_game = 1"
else:
    team_home_game_clause = "home_game = 0"

# Get this stats for the team    
team_id = teams.find_teams_by_full_name(team_name)[0]['id']
c.execute(f'''SELECT game_date, {TEAM_STATS[TEAM_STATS_FOR_DISPLAY.index(team_stats_category)]} from TeamStats WHERE team_id={team_id} AND {team_home_game_clause} ORDER BY game_date DESC LIMIT {team_last_n_games}''')
team_stats = c.fetchall()
conn.commit()

# baseline 
c.execute(f'''SELECT {TEAM_STATS[TEAM_STATS_FOR_DISPLAY.index(team_stats_category)]} from TeamStats''') 
this_stat_for_all_games = c.fetchall()
this_stat_mean = np.mean(this_stat_for_all_games)
this_stat_std = np.std(this_stat_for_all_games)
    
# Create a list of the stats
team_dates = [stat[0] for stat in team_stats]
team_data = [(stat[1]- this_stat_mean)/this_stat_std for stat in team_stats]

# pick a threshold, default to the mean of the stats
# team_threshold = st.slider("Select a threshold for team data:", 0.0, 50.0, np.mean(team_data), 0.5)

# STATS_FOR_DISPLAY the average stat value
st.markdown(
    f'<div style="text-align:center; padding: 20px; background-color: #f0f0f0; border-radius: 10px;">'
    f'<p style="font-size:24px; font-family: Arial, sans-serif; margin: 0;">'
    f'Average {team_stats_category}:</p>'
    f'<p style="font-size:32px; font-weight: bold; margin: 0;">'
    f'{np.mean(team_data):.2f}</p>'
    '</div>',
    unsafe_allow_html=True # so html will not be treated as text
)

# Create a DataFrame for the stats
team_df = pd.DataFrame({
    "Game": team_dates,
    "Stat Value": team_data
})


# Create a line chart with point traces, and add a threshold line
fig2 = px.line(team_df, x="Game", y="Stat Value", title=f"{team_stats_category} Over the Past {team_last_n_games} Games")
fig2.update_traces(mode='markers+lines', marker=dict(size=8, line=dict(width=2, color='DarkSlateGrey')))
# fig2.add_hline(y=team_threshold, line_dash="dot", annotation_text="Threshold", annotation_position="top right")
# fig2.update_layout(width = width)

# STATS_FOR_DISPLAY the chart
st.plotly_chart(fig2)

