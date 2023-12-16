# prize_picks

This is an App that visualizes data from NBA.com through NBA API. The goal is to make picking entries for <a href="https://www.prizepicks.com/"> PrizePicks </a> as easy as possible!
Stay tuned for the prediction model in the future! 

## Requirements

To set up the environment with conda, use the following commands:

```sh
conda create --name prize_picks python=3.9
conda activate prize_picks
python -m pip install -r requirements.txt
```

### To Update the database

```
python fetch_data.py
```

### To Run the App

```
streamlit run --server.address 0.0.0.0 app.py
```

# TODO:

1. Add the record of this player against this team

2. Show adjusted stats for a player according to opponent team defensive stats

3. Add regular expression search for player name

4. Build RandomForest for predictiing player stats
