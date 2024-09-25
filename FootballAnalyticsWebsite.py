import streamlit as st
import pandas as pd
from mplsoccer import VerticalPitch
from statsbombpy import sb
import json
import numpy as np
from streamlit_option_menu import option_menu
import matplotlib.patches as mpatches
import requests_cache

# Uninstall any existing request cache
requests_cache.uninstall_cache()

# Safe JSON loader function
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

# Pass Network option
#if selected == "Pass Network":
    # The rest of the Pass Network code

# Sidebar menu
with st.sidebar:
    selected = option_menu(
        menu_title="Main Menu",
        options=["Home", "Shot Map", "Player Pass Map", "AI Football Scout", "Pass Network"],
        icons=["house", "ball", "arrow-right", "rocket", "share"],
        menu_icon="cast",
        default_index=0,
        key="main_menu"  # Unique key for the main menu
    )

# Home menu option
if selected == "Home":
    st.title(f"You have selected {selected}")
    st.subheader("Welcome to the Data Football Analytics Website")
    
# AI Football Scout menu option
if selected == "AI Football Scout":
    st.title(f"You have selected {selected}")

if selected == "Shot Map":
    st.title(f"{selected} ⚽️")
    st.subheader("Filter by Competition, Team, and Player to see all their shots!")

    # Load competitions
    competitions = sb.competitions()
    competition_options = competitions['competition_name'].sort_values().unique()
    selected_competition = st.selectbox('Select a competition', competition_options, key="shot_map_competition")

    # Automatically select the latest season for the selected competition
    competition_id = competitions[competitions['competition_name'] == selected_competition]['competition_id'].values[0]
    latest_season = competitions[competitions['competition_name'] == selected_competition]['season_id'].max()

    # Fetch matches for the selected competition and latest season
    matches = sb.matches(competition_id=competition_id, season_id=latest_season)

    # Get unique teams from matches
    team_options = pd.concat([matches['home_team'], matches['away_team']]).unique()
    selected_team = st.selectbox('Select a team', team_options, key="shot_map_team")

    # Filter matches for the selected team
    team_matches = matches[(matches['home_team'] == selected_team) | (matches['away_team'] == selected_team)]
    match_ids = team_matches['match_id'].unique()

    # Fetch events for all matches played by the selected team
    if not match_ids.any():
        st.error("No match data found for the selected team.")
    else:
        events = pd.concat([sb.events(match_id=match_id) for match_id in match_ids])

        if events.empty:
            st.error("No events found for the selected matches.")
        else:
            # Allow the user to select a player from the team
            player_options = events[events['team'] == selected_team]['player'].sort_values().unique()
            selected_player = st.selectbox('Select a player', player_options, key="shot_map_player")

            # Filter events for the selected team and player
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

            filtered_events = events[(events['team'] == selected_team) & (events['player'] == selected_player)]

            # Visualize the player's shots on the pitch
            pitch = VerticalPitch(pitch_type='statsbomb', half=True)
            fig, ax = pitch.draw(figsize=(10, 10))

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
                        alpha=1 if shot['shot_outcome'] == 'Goal' else 0.5,
                        zorder=2 if shot['shot_outcome'] == 'Goal' else 1
                    )

                    # Only annotate player names for goals to reduce clutter
                    if shot['shot_outcome'] == 'Goal':
                        ax.text(x_coord, y_coord, shot['player'], fontsize=10, ha='center', va='center')

            # Plot the filtered data
            plot_shots(filtered_events, ax, pitch)

            # Add player's name at the top of the plot
            ax.set_title(f"{selected_player}'s Shot Map", fontsize=20)

            # Create a legend for shot outcomes with totals
            shot_outcome_counts = filtered_events['shot_outcome'].value_counts().to_dict()

            legend_labels = {
                'Goal': 'green',
                'Saved': 'red',
                'Blocked': 'yellow',
                'Off Target': 'white'
            }

            # Update the legend labels with counts
            legend_patches = [
                mpatches.Patch(
                    color=color,
                    label=f"{outcome}: {shot_outcome_counts.get(outcome, 0)}"
                )
                for outcome, color in legend_labels.items()
            ]
            ax.legend(handles=legend_patches, loc='upper left')

            # Render the plot using Streamlit
            st.pyplot(fig)

# Player Pass Map option
if selected == "Player Pass Map":
    st.title(f"{selected} ⚽️")
    st.subheader("Filter by Competition, Team, Player, and Game to see all their passes!")

    # Load competitions
    competitions = sb.competitions()
    competition_options = competitions['competition_name'].sort_values().unique()
    selected_competition = st.selectbox('Select a competition', competition_options, key="pass_map_competition")  # Unique key

    # Automatically select the latest season for the selected competition
    competition_id = competitions[competitions['competition_name'] == selected_competition]['competition_id'].values[0]
    latest_season = competitions[competitions['competition_name'] == selected_competition]['season_id'].max()

    # Fetch matches for the selected competition and latest season
    matches = sb.matches(competition_id=competition_id, season_id=latest_season)

    # Get unique home and away teams from matches
    team_options = pd.concat([matches['home_team'], matches['away_team']]).unique()
    selected_team = st.selectbox('Select a team', team_options, key="pass_map_team")  # Unique key

    # Filter matches for the selected team
    team_matches = matches[(matches['home_team'] == selected_team) | (matches['away_team'] == selected_team)]

    # Create a formatted match list for selection
    match_options = team_matches[['match_id', 'home_team', 'away_team']].copy()
    match_options['match_display'] = match_options['home_team'] + " vs " + match_options['away_team']
    
    selected_match = st.selectbox('Select a match', match_options['match_display'].tolist(), key="pass_map_match")  # Unique key

    # Get the match_id corresponding to the selected display
    selected_match_id = match_options.loc[match_options['match_display'] == selected_match, 'match_id'].values[0]

    # Fetch events for the selected match
    events = sb.events(match_id=selected_match_id)

    if events.empty:
        st.error("No events found for the selected match.")
    else:
        # Allow the user to select a player from the team
        player_options = events[events['team'] == selected_team]['player'].sort_values().unique()
        selected_player = st.selectbox('Select a player', player_options, key="pass_map_player")  # Unique key

        # Filter events for passes by the selected player
        player_passes = events[(events['player'] == selected_player) & (events['type'] == 'Pass')]

        # Debug: Show the number of passes found
        st.write(f"Total passes found: {len(player_passes)}")

        if player_passes.empty:
            st.error("No passes found for the selected player.")
        else:
            # Create the pitch for the pass map
            pitch = VerticalPitch(pitch_type='statsbomb')
            fig, ax = pitch.draw(figsize=(7, 7))

            # Count total and successful passes
            total_passes = len(player_passes)
            successful_passes = len(player_passes[player_passes['pass_outcome'].isnull()])
            failed_passes = total_passes - successful_passes

            # Display player name and pass stats at the top of the pass map
            ax.text(50, 70, f"{selected_player} Pass Map", fontsize=16, ha='center', va='center')

            # Display a legend for total passes, successful passes, and failed passes
            legend_text = f"Total Passes: {total_passes} | Successful Passes: {successful_passes} | Failed Passes: {failed_passes}"
            ax.text(50, 65, legend_text, fontsize=12, ha='center', va='center')

            # Plot passes with direction arrows
            for pass_event in player_passes.to_dict(orient='records'):
                start_location = pass_event['location']
                end_location = pass_event.get('pass_end_location')

                if start_location is None or len(start_location) != 2:
                    continue
                if end_location is None or len(end_location) != 2:
                    continue

                x_start, y_start = float(start_location[0]), float(start_location[1])
                x_end, y_end = float(end_location[0]), float(end_location[1])

                # Draw the pass line
                ax.plot([x_start, x_end], [y_start, y_end], color='blue', linewidth=2, alpha=0.6)

                # Optionally, draw arrows to indicate the direction of the pass
                ax.annotate('', xy=(x_end, y_end), xytext=(x_start, y_start),
                            arrowprops=dict(arrowstyle='->', color='blue', lw=2),
                            fontsize=12)

            # Render the pass map plot
            st.pyplot(fig)
            
            
import pandas as pd
import matplotlib.pyplot as plt
from mplsoccer import VerticalPitch
import streamlit as st

# Assuming you've already loaded your dataframes
# competitions_df, matches_df, events_df must be loaded from appropriate data sources (CSV, JSON, etc.)

# Example for loading if needed
# competitions_df = pd.read_csv('competitions.csv')
# matches_df = pd.read_csv('matches.csv')
# events_df = pd.read_csv('events.csv')




if selected == "Pass Network":
    st.title(f"{selected} ⚽️")
    st.subheader("Filter by Competition, Team, and Game to see the team's pass network!")

    # Load competitions
    competitions = sb.competitions()
    competition_options = competitions['competition_name'].sort_values().unique()
    selected_competition = st.selectbox('Select a competition', competition_options, key="pass_network_competition")  # Unique key

    # Automatically select the latest season for the selected competition
    competition_id = competitions[competitions['competition_name'] == selected_competition]['competition_id'].values[0]
    latest_season = competitions[competitions['competition_name'] == selected_competition]['season_id'].max()

    # Fetch matches for the selected competition and latest season
    matches = sb.matches(competition_id=competition_id, season_id=latest_season)

    # Get unique home and away teams from matches
    team_options = pd.concat([matches['home_team'], matches['away_team']]).unique()
    selected_team = st.selectbox('Select a team', team_options, key="pass_network_team")  # Unique key

    # Filter matches for the selected team
    team_matches = matches[(matches['home_team'] == selected_team) | (matches['away_team'] == selected_team)]

    # Create a formatted match list for selection
    match_options = team_matches[['match_id', 'home_team', 'away_team']].copy()
    match_options['match_display'] = match_options['home_team'] + " vs " + match_options['away_team']
    
    selected_match = st.selectbox('Select a match', match_options['match_display'].tolist(), key="pass_network_match")  # Unique key

    # Get the match_id corresponding to the selected display
    selected_match_id = match_options.loc[match_options['match_display'] == selected_match, 'match_id'].values[0]

    # Fetch events for the selected match
    events = sb.events(match_id=selected_match_id)

    if events.empty:
        st.error("No events found for the selected match.")
    else:
        # Filter events for passes by the selected team
        team_passes = events[(events['team'] == selected_team) & (events['type'] == 'Pass')]

        if team_passes.empty:
            st.error("No passes found for the selected team.")
        else:
            # Group by player pairs to count pass links
            pass_links = team_passes.groupby(['player', 'pass_recipient']).size().reset_index(name='pass_count')

            # Prepare the data for the pass network visualization
            player_positions = team_passes.groupby('player')[['location']].first().reset_index()
            player_positions['location'] = player_positions['location'].apply(safe_json_loads)

            # Create a pitch for the pass network
            pitch = VerticalPitch(pitch_type='statsbomb')
            fig, ax = pitch.draw(figsize=(12, 12))

            # Add player nodes (circles) and rotate positions 90 degrees clockwise
            for idx, player in player_positions.iterrows():
                location = player['location']
                if location and len(location) == 2:
                    # Rotate the position 90 degrees clockwise
                    rotated_x = location[1]         # New x is the original y
                    rotated_y = 100 - location[0]   # New y is 100 - original x
                    ax.scatter(rotated_x, rotated_y, s=200, color='blue', edgecolors='black', zorder=3)
                    ax.text(rotated_x, rotated_y, player['player'], fontsize=12, ha='center', va='center', zorder=4)

            # Add pass links (edges)
            for idx, row in pass_links.iterrows():
                passer = row['player']
                recipient = row['pass_recipient']
                pass_count = row['pass_count']

                # Get positions of the passer and recipient
                passer_pos = player_positions[player_positions['player'] == passer]['location']
                recipient_pos = player_positions[player_positions['player'] == recipient]['location']

                if not passer_pos.empty and not recipient_pos.empty:
                    passer_pos = passer_pos.values[0]  # Get the position array
                    recipient_pos = recipient_pos.values[0]  # Get the position array

                    if passer_pos is not None and recipient_pos is not None:
                        # Rotate positions for passer and recipient 90 degrees clockwise
                        passer_rotated_x = passer_pos[1]         # New x is the original y
                        passer_rotated_y = 100 - passer_pos[0]   # New y is 100 - original x

                        recipient_rotated_x = recipient_pos[1]         # New x is the original y
                        recipient_rotated_y = 100 - recipient_pos[0]   # New y is 100 - original x

                        # Draw the pass link
                        ax.plot([passer_rotated_x, recipient_rotated_x], [passer_rotated_y, recipient_rotated_y],
                                linewidth=2 + pass_count / 2, color='green', alpha=0.6, zorder=2)

            # Add the title
            ax.set_title(f"{selected_team} Pass Network", fontsize=20)

            # Render the pass network plot
            st.pyplot(fig)
