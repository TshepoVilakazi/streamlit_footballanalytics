import streamlit as st
import pandas as pd
from mplsoccer import VerticalPitch
from statsbombpy import sb
import json
import numpy as np

st.title("Football Shot Map")
st.subheader("Filter by Competition, Team, and Player to see all their shots!")

# Step 1: Load competitions and allow the user to select one
competitions = sb.competitions()
competition_options = competitions['competition_name'].sort_values().unique()
selected_competition = st.selectbox('Select a competition', competition_options)

# Step 2: Automatically select the latest season for the selected competition
competition_id = competitions[competitions['competition_name'] == selected_competition]['competition_id'].values[0]
latest_season = competitions[competitions['competition_name'] == selected_competition]['season_id'].max()

# Step 3: Fetch matches for the selected competition and latest season
matches = sb.matches(competition_id=competition_id, season_id=latest_season)

# Step 4: Get unique teams from matches and allow the user to select one
team_options = pd.concat([matches['home_team'],matches['away_team']]).unique()
selected_team = st.selectbox('Select a team', team_options)

# Step 5: Filter the matches for the selected team
team_matches = matches[(matches['home_team'] == selected_team) | (matches['away_team'] == selected_team)]
match_ids = team_matches['match_id'].unique()

# Step 6: Fetch events for all matches played by the selected team
events = pd.concat([sb.events(match_id=match_id) for match_id in match_ids])

# Step 7: Allow the user to select a player from the team
player_options = events[events['team'] == selected_team]['player'].sort_values().unique()
selected_player = st.selectbox('Select a player', player_options)

# Step 8: Filter events for the selected team and player
def safe_json_loads(val):
    if isinstance(val, (float, np.float64)) and np.isnan(val):
        return None
    elif isinstance(val, str):
        try:
            return json.loads(val)
        except json.JSONDecodeError:
            return None
    elif isinstance(val, (list, tuple)):
        return val
    else:
        return None

events['location'] = events['location'].apply(safe_json_loads)
events['shot_statsbomb_xg'] = events['shot_statsbomb_xg'].fillna(0)

# Filter events by team and player
filtered_events = events[(events['team'] == selected_team) & (events['player'] == selected_player)]

#total number of each shot type
if not filtered_events.empty:
    shot_outcome_counts = filtered_events['shot_outcome'].value_counts()
    
    #st.write("### Shot Outcome Summary")
    st.write(shot_outcome_counts)

# Step 9: Visualize the player's shots on the pitch
pitch = VerticalPitch(pitch_type='statsbomb', half=True)
fig, ax = pitch.draw(figsize=(7, 7))

def plot_shots(df, ax, pitch):
    for shot in df.to_dict(orient='records'):
        location = shot['location']
        if location is None or len(location) != 2:
            continue
        x_coord, y_coord = float(location[0]), float(location[1])
        pitch.scatter(
            x=x_coord,
            y=y_coord,
            ax=ax,
            s=1000 * shot['shot_statsbomb_xg'],
            color=(
                'green' if shot['shot_outcome'] == 'Goal' else
                'red' if shot['shot_outcome'] == 'Saved' else
                'yellow' if shot['shot_outcome'] == 'Blocked' else
                'white'
            ),
            edgecolors='black',
            alpha=1 if shot['type'] == 'goal' else 0.5,
            zorder=2 if shot['type'] == 'goal' else 1
        )

# Plot the filtered data
plot_shots(filtered_events, ax, pitch)

# Render the plot using Streamlit
st.pyplot(fig)

