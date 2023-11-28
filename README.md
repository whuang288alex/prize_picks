# prize_picks

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