import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date
import json
import os
from data_manager import DataManager
from stats_calculator import StatsCalculator
from mlb_api_client import MLBApiClient
from auth_manager import AuthManager

def main():
    st.set_page_config(
        page_title="Baseball Statistics Aggregator",
        page_icon="⚾",
        layout="wide"
    )

    auth_manager = AuthManager()

    if not auth_manager.is_authenticated():
        st.title("Login to Baseball Statistics Aggregator")

        tab1, tab2 = st.tabs(["Login", "Register"])

        with tab1:
            auth_status, username = auth_manager.login()
            if auth_status:
                st.success(f"Logged in as {username}")
                st.rerun()
            elif auth_status == False:
                st.error("Invalid username or password")

        with tab2:
            with st.form("register_form"):
                new_username = st.text_input("Username")
                new_name = st.text_input("Full Name")
                new_email = st.text_input("Email")
                new_password = st.text_input("Password", type="password")
                submitted = st.form_submit_button("Register")
                if submitted:
                    if auth_manager.register_user(new_username, new_name, new_password, new_email):
                        st.success("Registration successful! Please login with your credentials.")
                    else:
                        st.error("Username already exists or registration failed.")
    else:
        # Authenticated user
        user = auth_manager.get_current_user()

        # Initialize user-specific session state
        if 'data_manager' not in st.session_state or st.session_state.data_manager.user_id != user:
            st.session_state.data_manager = DataManager(user_id=user)
        if 'stats_calculator' not in st.session_state:
            st.session_state.stats_calculator = StatsCalculator()
        if 'mlb_client' not in st.session_state:
            st.session_state.mlb_client = MLBApiClient()

        # Sidebar with logout
        st.sidebar.write(f"Logged in as: {user}")
        auth_manager.logout()

        st.title("⚾ Baseball Statistics Aggregator")
        st.markdown("Track and analyze player statistics from MLB games you've attended")

        # Sidebar navigation
        if 'page' not in st.session_state:
            st.session_state.page = "Add Game"

        pages = ["Add Game", "My Games", "Player Stats", "Dashboard", "Export Data"]
        for p in pages:
            if st.sidebar.button(p, use_container_width=True):
                st.session_state.page = p
                st.rerun()

        page = st.session_state.page

        if page == "Add Game":
            add_game_page()
        elif page == "My Games":
            my_games_page()
        elif page == "Player Stats":
            player_stats_page()
        elif page == "Dashboard":
            dashboard_page()
        elif page == "Export Data":
            export_data_page()

def add_game_page():
    st.header("Add New Game")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Get list of MLB teams
        teams = st.session_state.mlb_client.get_teams()
        if teams:
            team_options = {f"{team['name']} ({team['abbreviation']})": team['id'] for team in teams}
            
            home_team = st.selectbox(
                "Home Team",
                options=list(team_options.keys()),
                help="Select the home team"
            )
            
            away_team = st.selectbox(
                "Away Team", 
                options=list(team_options.keys()),
                help="Select the away team"
            )
        else:
            st.error("Unable to load team data. Please check your connection.")
            return
    
    with col2:
        game_date = st.date_input(
            "Game Date",
            value=date.today(),
            max_value=date.today(),
            help="Select the date of the game you attended"
        )
        
        notes = st.text_area(
            "Notes (Optional)",
            placeholder="Add any notes about the game..."
        )
    
    if st.button("Add Game", type="primary"):
        if home_team and away_team and game_date:
            if home_team == away_team:
                st.error("Home and away teams cannot be the same!")
                return
            home_team_id = team_options[home_team]
            away_team_id = team_options[away_team]
            with st.spinner("Fetching game data from MLB API..."):
                game_data = st.session_state.mlb_client.get_game_data(
                    home_team_id, away_team_id, game_date
                )
                # Box score is already included in game_data from get_game_data
                if game_data:
                    st.write("Debug - Game data structure:", list(game_data.keys()))
            if game_data:
                # Save the game
                success = st.session_state.data_manager.add_game(
                    game_data, notes
                )
                
                if success:
                    st.success("Game added successfully!")
                    st.rerun()
                else:
                    st.error("Failed to save game data.")
            else:
                st.error("No game found for the selected teams and date. Please verify the details.")

def my_games_page():
    st.header("My Attended Games")
    games = st.session_state.data_manager.get_all_games()
    if not games:
        st.info("No games added yet. Go to 'Add Game' to start tracking your attended games.")
        return

    # Detect Streamlit theme (dark/light)
    theme = st.get_option("theme.base")
    is_dark = theme == "dark"
    card_bg = "#23272f" if is_dark else "#f8f9fa"
    card_text = "#f8f9fa" if is_dark else "#23272f"
    card_shadow = "0 2px 8px rgba(0,0,0,0.18)" if is_dark else "0 2px 8px rgba(0,0,0,0.04)"

    cols = st.columns(3)

    for idx, game in enumerate(games):
        with cols[idx % 3]:
            home_team = game.get('home_team', 'N/A')
            away_team = game.get('away_team', 'N/A')
            home_score = game.get('home_score', 'N/A')
            away_score = game.get('away_score', 'N/A')
            date_str = game.get('date', 'N/A')
            notes = game.get('notes', '')

            st.markdown(f"""
            <div style='background: {card_bg}; color: {card_text}; border-radius: 12px; padding: 1em 1.2em; margin-bottom: 1.2em; box-shadow: {card_shadow};'>
                <h4 style='margin-bottom:0.2em;'>📅 {date_str}</h4>
                <div style='font-size:1.1em; margin-bottom:0.5em;'>
                    <div style='font-weight:600; margin-bottom:0.2em;'>{away_team} <span style='color:#888;'>({away_score})</span></div>
                    <div style='color:#666; margin-bottom:0.2em;'>@</div>
                    <div style='font-weight:600;'>{home_team} <span style='color:#888;'>({home_score})</span></div>
                </div>
                {f'<div style="margin-bottom:0.5em; color:#bbb;">📝 {notes}</div>' if notes else ''}
            </div>
            """, unsafe_allow_html=True)
            # Working remove button below the card
            remove_btn_label = f"Remove Game {idx+1} ({away_team} @ {home_team})"
            if st.button("🗑️ Remove Game", key=f"remove_game_{idx}"):
                if st.session_state.data_manager.remove_game(idx):
                    st.success("Game removed successfully!")
                    st.rerun()

    # Optionally, keep the detailed info section if needed
    if st.checkbox("Show detailed game information"):
        selected_game_idx = st.selectbox(
            "Select a game to view details",
            range(len(games)),
            format_func=lambda x: f"{games[x].get('date')} - {games[x].get('away_team')} @ {games[x].get('home_team')}"
        )
        if selected_game_idx is not None:
            game = games[selected_game_idx]
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("Game Summary")
                st.write(f"**Date:** {game.get('date')}")
                st.write(f"**Teams:** {game.get('away_team')} @ {game.get('home_team')}")
                st.write(f"**Final Score:** {game.get('away_score')} - {game.get('home_score')}")
                if game.get('notes'):
                    st.write(f"**Notes:** {game.get('notes')}")
                # Display box score data
                if game:
                    st.markdown("### Box Score")
                    tabs = st.tabs(["Batting", "Pitching", "Game Info"])
                    
                    with tabs[0]:  # Batting Stats
                        # Display away team batting
                            st.markdown("#### Away Team Batting")
                            away_batting = None
                            
                            # Get away team batting stats
                            away_batting_data = game.get('away_team_batting', [])
                            
                            if away_batting_data:
                                # Create DataFrame and sort by batting order
                                away_batting = pd.DataFrame(away_batting_data)
                                
                                # Ensure required columns exist before processing
                                required_columns = ['name', 'order', 'sub', 'position']
                                for col in required_columns:
                                    if col not in away_batting.columns:
                                        away_batting[col] = None
                                
                                # Format player names with indentation for substitutes
                                def format_player_name(row):
                                    try:
                                        name = str(row['name']) if pd.notnull(row['name']) else 'Unknown'
                                        position = str(row['position']) if pd.notnull(row['position']) and row['position'] != '' else ''
                                        
                                        # Determine if this is a substitute
                                        is_sub = pd.notnull(row.get('sub')) and bool(row.get('sub'))
                                        
                                        # Get batting order
                                        order_num = row.get('order')
                                        has_order = pd.notnull(order_num) and order_num is not None
                                        
                                        # Build the display string
                                        prefix = "    " if is_sub else ""  # Four spaces for indentation
                                        order_str = f"{int(order_num)}. " if not is_sub and has_order else ""
                                        pos_str = f" ({position})" if position else ""
                                        
                                        return f"{prefix}{order_str}{name}{pos_str}"
                                    except Exception as e:
                                        st.write(f"Debug - Error formatting player: {e}")
                                        st.write("Debug - Row data:", row.to_dict())
                                        return f"{row.get('name', 'Unknown')}"
                                
                                # Ensure required columns exist
                                if 'order' not in away_batting.columns:
                                    away_batting['order'] = None
                                if 'sub' not in away_batting.columns:
                                    away_batting['sub'] = False
                                if 'position' not in away_batting.columns:
                                    away_batting['position'] = ''
                                
                                # Convert order to numeric, keeping NaN values
                                away_batting['order'] = pd.to_numeric(away_batting['order'], errors='coerce')
                                
                                # Sort by batting order first
                                away_batting = away_batting.sort_values(
                                    by=['order'],
                                    na_position='last'
                                )
                                
                                # Create ordered display DataFrame
                                rows = []
                                sub_groups = {}  # Dictionary to hold substitutes for each batting order
                                other_subs = []  # For substitutes without a batting order
                                
                                # First pass: identify starters and build a map of who replaced whom
                                player_subs = {}  # Dictionary to map players to their substitutes
                                starter_by_position = {}  # Keep track of starters by position
                                
                                for _, row in away_batting.iterrows():
                                    if not row['sub']:
                                        # It's a starter
                                        rows.append(row)
                                        if pd.notnull(row['position']) and row['position']:
                                            starter_by_position[row['position']] = row['name']
                                    else:
                                        # It's a substitute, find who they replaced
                                        if pd.notnull(row['position']) and row['position'] in starter_by_position:
                                            # Find the starter they replaced
                                            starter_name = starter_by_position[row['position']]
                                            if starter_name not in player_subs:
                                                player_subs[starter_name] = []
                                            player_subs[starter_name].append(row)
                                        else:
                                            other_subs.append(row)
                                
                                # Second pass: create the final order with subs right after their starters
                                final_rows = []
                                for row in rows:
                                    final_rows.append(row)
                                    # Add any substitutes for this player right after them
                                    if row['name'] in player_subs:
                                        final_rows.extend(player_subs[row['name']])
                                
                                # Add any unmatched substitutes at the end
                                final_rows.extend(other_subs)
                                
                                # Create new DataFrame with correct order
                                away_batting = pd.DataFrame(final_rows)
                                
                                away_batting['Player'] = away_batting.apply(format_player_name, axis=1)
                                
                                # Reorder columns for better presentation
                                columns_order = ['Player', 'at_bats', 'hits', 'runs', 'rbis', 
                                               'doubles', 'triples', 'home_runs', 'walks', 
                                               'strikeouts', 'stolen_bases', 'caught_stealing']
                                
                                # Create final DataFrame for display
                                display_columns = ['Player'] + [col for col in columns_order if col in away_batting.columns and col != 'Player']
                                away_batting_display = away_batting[display_columns].copy()
                                
                                # Rename columns for better presentation
                                column_names = {
                                    'at_bats': 'AB',
                                    'hits': 'H',
                                    'runs': 'R',
                                    'rbis': 'RBI',
                                    'doubles': '2B',
                                    'triples': '3B',
                                    'home_runs': 'HR',
                                    'walks': 'BB',
                                    'strikeouts': 'SO',
                                    'stolen_bases': 'SB',
                                    'caught_stealing': 'CS'
                                }
                                away_batting_display.rename(columns=column_names, inplace=True)
                                
                                st.dataframe(away_batting_display, 
                                           use_container_width=True,
                                           hide_index=True)
                                
                                # Calculate and display game totals and notes
                                doubles = away_batting['doubles'].sum() if 'doubles' in away_batting.columns else 0
                                triples = away_batting['triples'].sum() if 'triples' in away_batting.columns else 0
                                homers = away_batting['home_runs'].sum() if 'home_runs' in away_batting.columns else 0
                                stolen = away_batting['stolen_bases'].sum() if 'stolen_bases' in away_batting.columns else 0
                                caught = away_batting['caught_stealing'].sum() if 'caught_stealing' in away_batting.columns else 0
                                gidp = away_batting['gidp'].sum() if 'gidp' in away_batting.columns else 0
                                errors = away_batting['errors'].sum() if 'errors' in away_batting.columns else 0
                                lob = away_batting['lob'].sum() if 'lob' in away_batting.columns else 0
                                
                                # Calculate total bases
                                singles = away_batting['hits'].sum() - (doubles + triples + homers) if 'hits' in away_batting.columns else 0
                                total_bases = singles + (2 * doubles) + (3 * triples) + (4 * homers)
                                
                                # Display game notes in MLB standard format
                                notes = []
                                if doubles > 0:
                                    notes.append(f"2B ({doubles}): {', '.join([row['name'] for _, row in away_batting.iterrows() if row.get('doubles', 0) > 0])}")
                                if triples > 0:
                                    notes.append(f"3B ({triples}): {', '.join([row['name'] for _, row in away_batting.iterrows() if row.get('triples', 0) > 0])}")
                                if homers > 0:
                                    notes.append(f"HR ({homers}): {', '.join([row['name'] for _, row in away_batting.iterrows() if row.get('home_runs', 0) > 0])}")
                                if stolen > 0:
                                    notes.append(f"SB ({stolen}): {', '.join([row['name'] for _, row in away_batting.iterrows() if row.get('stolen_bases', 0) > 0])}")
                                if caught > 0:
                                    notes.append(f"CS ({caught}): {', '.join([row['name'] for _, row in away_batting.iterrows() if row.get('caught_stealing', 0) > 0])}")
                                if gidp > 0:
                                    notes.append(f"GIDP ({gidp}): {', '.join([row['name'] for _, row in away_batting.iterrows() if row.get('gidp', 0) > 0])}")
                                if errors > 0:
                                    notes.append(f"E ({errors}): {', '.join([row['name'] for _, row in away_batting.iterrows() if row.get('errors', 0) > 0])}")
                                
                                st.markdown("---")
                                st.markdown("**Game Notes:**")
                                if notes:
                                    st.markdown(" • " + "\n • ".join(notes))
                                st.markdown(f"**TB:** {total_bases} • **LOB:** {lob}")
                            else:
                                st.info("No away team batting data available")
                            
                            # Display home team batting
                            st.markdown("#### Home Team Batting")
                            home_batting_data = game.get('home_team_batting', [])
                            if home_batting_data:
                                # Create DataFrame and sort by batting order
                                home_batting = pd.DataFrame(home_batting_data)
                                
                                # Ensure required columns exist before processing
                                required_columns = ['name', 'order', 'sub', 'position']
                                for col in required_columns:
                                    if col not in home_batting.columns:
                                        home_batting[col] = None
                                
                                # Add order column if not present
                                home_batting['order'] = pd.to_numeric(home_batting['order'], errors='coerce')
                                home_batting['sub'] = home_batting['sub'].fillna(False)
                                
                                # Sort by batting order first
                                home_batting = home_batting.sort_values(
                                    by=['order'],
                                    na_position='last'
                                )
                                
                                # Create ordered display DataFrame
                                rows = []
                                sub_groups = {}  # Dictionary to hold substitutes for each batting order
                                other_subs = []  # For substitutes without a batting order
                                
                                # First pass: identify starters and build a map of who replaced whom
                                player_subs = {}  # Dictionary to map players to their substitutes
                                starter_by_position = {}  # Keep track of starters by position
                                
                                for _, row in home_batting.iterrows():
                                    if not row['sub']:
                                        # It's a starter
                                        rows.append(row)
                                        if pd.notnull(row['position']) and row['position']:
                                            starter_by_position[row['position']] = row['name']
                                    else:
                                        # It's a substitute, find who they replaced
                                        if pd.notnull(row['position']) and row['position'] in starter_by_position:
                                            # Find the starter they replaced
                                            starter_name = starter_by_position[row['position']]
                                            if starter_name not in player_subs:
                                                player_subs[starter_name] = []
                                            player_subs[starter_name].append(row)
                                        else:
                                            other_subs.append(row)
                                
                                # Second pass: create the final order with subs right after their starters
                                final_rows = []
                                for row in rows:
                                    final_rows.append(row)
                                    # Add any substitutes for this player right after them
                                    if row['name'] in player_subs:
                                        final_rows.extend(player_subs[row['name']])
                                
                                # Add any unmatched substitutes at the end
                                final_rows.extend(other_subs)
                                
                                # Create new DataFrame with correct order
                                home_batting = pd.DataFrame(final_rows)
                                
                                # Format player names with indentation for substitutes
                                def format_player_name(row):
                                    try:
                                        prefix = "    " if row.get('sub', False) else ""
                                        order = f"{int(row['order'])}. " if 'order' in row and pd.notnull(row['order']) else "   "
                                        pos = f" ({row['position']})" if 'position' in row and row['position'] else ""
                                        return f"{prefix}{order}{row['name']}{pos}"
                                    except:
                                        return f"{row.get('name', 'Unknown')}"
                                
                                home_batting['Player'] = home_batting.apply(format_player_name, axis=1)
                                
                                # Create final DataFrame for display
                                display_columns = ['Player'] + [col for col in columns_order if col in home_batting.columns and col != 'Player']
                                home_batting_display = home_batting[display_columns].copy()
                                
                                # Use same column names as away team
                                home_batting_display.rename(columns=column_names, inplace=True)
                                
                                st.dataframe(home_batting_display, 
                                           use_container_width=True,
                                           hide_index=True)
                                
                                # Calculate and display game totals and notes
                                doubles = home_batting['doubles'].sum() if 'doubles' in home_batting.columns else 0
                                triples = home_batting['triples'].sum() if 'triples' in home_batting.columns else 0
                                homers = home_batting['home_runs'].sum() if 'home_runs' in home_batting.columns else 0
                                stolen = home_batting['stolen_bases'].sum() if 'stolen_bases' in home_batting.columns else 0
                                caught = home_batting['caught_stealing'].sum() if 'caught_stealing' in home_batting.columns else 0
                                gidp = home_batting['gidp'].sum() if 'gidp' in home_batting.columns else 0
                                errors = home_batting['errors'].sum() if 'errors' in home_batting.columns else 0
                                lob = home_batting['lob'].sum() if 'lob' in home_batting.columns else 0
                                
                                # Calculate total bases
                                singles = home_batting['hits'].sum() - (doubles + triples + homers) if 'hits' in home_batting.columns else 0
                                total_bases = singles + (2 * doubles) + (3 * triples) + (4 * homers)
                                
                                # Display game notes in MLB standard format
                                notes = []
                                if doubles > 0:
                                    notes.append(f"2B ({doubles}): {', '.join([row['name'] for _, row in home_batting.iterrows() if row.get('doubles', 0) > 0])}")
                                if triples > 0:
                                    notes.append(f"3B ({triples}): {', '.join([row['name'] for _, row in home_batting.iterrows() if row.get('triples', 0) > 0])}")
                                if homers > 0:
                                    notes.append(f"HR ({homers}): {', '.join([row['name'] for _, row in home_batting.iterrows() if row.get('home_runs', 0) > 0])}")
                                if stolen > 0:
                                    notes.append(f"SB ({stolen}): {', '.join([row['name'] for _, row in home_batting.iterrows() if row.get('stolen_bases', 0) > 0])}")
                                if caught > 0:
                                    notes.append(f"CS ({caught}): {', '.join([row['name'] for _, row in home_batting.iterrows() if row.get('caught_stealing', 0) > 0])}")
                                if gidp > 0:
                                    notes.append(f"GIDP ({gidp}): {', '.join([row['name'] for _, row in home_batting.iterrows() if row.get('gidp', 0) > 0])}")
                                if errors > 0:
                                    notes.append(f"E ({errors}): {', '.join([row['name'] for _, row in home_batting.iterrows() if row.get('errors', 0) > 0])}")
                                
                                st.markdown("---")
                                st.markdown("**Game Notes:**")
                                if notes:
                                    st.markdown(" • " + "\n • ".join(notes))
                                st.markdown(f"**TB:** {total_bases} • **LOB:** {lob}")
                            else:
                                st.info("No home team batting data available")
                        
                    with tabs[1]:  # Pitching Stats
                        # Display away team pitching
                        st.markdown("#### Away Team Pitching")
                        away_pitching = None
                        
                        # Get away team pitching stats
                        away_pitching_data = game.get('away_team_pitching', [])
                        if away_pitching_data:
                            away_pitching = pd.DataFrame(away_pitching_data)
                            # Reorder columns for better presentation
                            columns_order = ['name', 'innings_pitched', 'hits_allowed', 'runs_allowed', 
                                           'earned_runs', 'walks', 'strikeouts', 'home_runs_allowed']
                            away_pitching = away_pitching.reindex(columns=[col for col in columns_order if col in away_pitching.columns])
                            st.dataframe(away_pitching, use_container_width=True)
                        else:
                            st.info("No away team pitching data available")
                        
                        # Display home team pitching
                        st.markdown("#### Home Team Pitching")
                        home_pitching = None                        # Get home team pitching stats
                        home_pitching_data = game.get('home_team_pitching', [])
                        if home_pitching_data:
                            home_pitching = pd.DataFrame(home_pitching_data)
                            # Reorder columns for better presentation
                            home_pitching = home_pitching.reindex(columns=[col for col in columns_order if col in home_pitching.columns])
                            st.dataframe(home_pitching, use_container_width=True)
                        else:
                            st.info("No home team pitching data available")
                    
                    with tabs[2]:  # Game Info
                        # Display general game information
                        st.markdown("#### Game Details")
                        game_info = {
                            "Date": game.get('date'),
                            "Venue": game.get('venue'),
                            "Status": game.get('game_status'),
                            "Final Score": f"{game.get('away_team')} {game.get('away_score')} @ {game.get('home_team')} {game.get('home_score')}"
                        }
                        if game.get('notes'):
                            game_info["Notes"] = game.get('notes')
                        
                        if game_info:
                            if isinstance(game_info, dict):
                                for key, value in game_info.items():
                                    key_display = key.replace('_', ' ').title()
                                    st.markdown(f"**{key_display}:** {value}")
                            elif isinstance(game_info, list):
                                st.dataframe(pd.DataFrame(game_info), use_container_width=True)
                            else:
                                st.write(game_info)
                        else:
                            st.info("No additional game information available")
                else:
                    st.info("No box score available for this game.")

def player_stats_page():
    st.header("Player Statistics")
    
    games = st.session_state.data_manager.get_all_games()
    
    if not games:
        st.info("No games added yet. Add some games to see player statistics.")
        return
    
    # Calculate aggregated stats
    batting_stats, pitching_stats = st.session_state.stats_calculator.calculate_aggregate_stats(games)
    
    tab1, tab2 = st.tabs(["Batting Stats", "Pitching Stats"])
    
    with tab1:
        if batting_stats:
            st.subheader("Batting Statistics")
            
            # Convert to DataFrame for better display
            batting_df = pd.DataFrame(batting_stats)
            
            # Sort by games played
            if 'games' in batting_df.columns:
                batting_df = batting_df.sort_values('games', ascending=False)
            
            # Display top performers
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric("Total Players Seen", len(batting_df))
                if 'at_bats' in batting_df.columns:
                    total_at_bats = batting_df['at_bats'].sum()
                    st.metric("Total At Bats", total_at_bats)
            
            with col2:
                if 'hits' in batting_df.columns:
                    total_hits = batting_df['hits'].sum()
                    st.metric("Total Hits", total_hits)
                if 'home_runs' in batting_df.columns:
                    total_hrs = batting_df['home_runs'].sum()
                    st.metric("Total Home Runs", total_hrs)
            
            # Filter options
            max_games = int(batting_df['games'].max()) if 'games' in batting_df.columns and len(batting_df) > 0 else 1
            if max_games > 1:
                min_games = st.slider("Minimum games played", 1, max_games, 1)
            else:
                min_games = 1
                st.info("All players have played 1 game or less. Showing all available data.")
            filtered_batting = batting_df[batting_df['games'] >= min_games] if 'games' in batting_df.columns else batting_df
            
            st.dataframe(filtered_batting, use_container_width=True)
        else:
            st.info("No batting statistics available.")
    
    with tab2:
        if pitching_stats:
            st.subheader("Pitching Statistics")
            
            # Convert to DataFrame for better display
            pitching_df = pd.DataFrame(pitching_stats)
            
            # Sort by games played
            if 'games' in pitching_df.columns:
                pitching_df = pitching_df.sort_values('games', ascending=False)
            
            # Display summary stats
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric("Total Pitchers Seen", len(pitching_df))
                if 'innings_pitched' in pitching_df.columns:
                    total_ip = pitching_df['innings_pitched'].sum()
                    st.metric("Total Innings Pitched", f"{total_ip:.1f}")
            
            with col2:
                if 'strikeouts' in pitching_df.columns:
                    total_ks = pitching_df['strikeouts'].sum()
                    st.metric("Total Strikeouts", total_ks)
                if 'earned_runs' in pitching_df.columns:
                    total_er = pitching_df['earned_runs'].sum()
                    st.metric("Total Earned Runs", total_er)
            
            # Filter options
            max_games = int(pitching_df['games'].max()) if 'games' in pitching_df.columns and len(pitching_df) > 0 else 1
            if max_games > 1:
                min_games = st.slider("Minimum games pitched", 1, max_games, 1, key="pitching_filter")
            else:
                min_games = 1
                st.info("All pitchers have pitched 1 game or less. Showing all available data.")
            filtered_pitching = pitching_df[pitching_df['games'] >= min_games] if 'games' in pitching_df.columns else pitching_df
            
            st.dataframe(filtered_pitching, use_container_width=True)
        else:
            st.info("No pitching statistics available.")

def dashboard_page():
    st.header("Statistics Dashboard")
    
    games = st.session_state.data_manager.get_all_games()
    
    if not games:
        st.info("No games added yet. Add some games to see visualizations.")
        return
    
    # Calculate stats for visualization
    batting_stats, pitching_stats = st.session_state.stats_calculator.calculate_aggregate_stats(games)
    

    # Games summary table (by month)
    st.subheader("Games Attended by Month")
    games_by_month = {}
    for g in games:
        d = g.get('date', 'Unknown')
        try:
            dt = datetime.strptime(d, '%Y-%m-%d')
            month_str = dt.strftime('%Y-%m')
        except Exception:
            month_str = 'Unknown'
        games_by_month[month_str] = games_by_month.get(month_str, 0) + 1
    games_by_month_list = [{"Month": k, "Games Attended": v} for k, v in sorted(games_by_month.items())]
    st.table(games_by_month_list)

    # Top teams by games attended (table)
    st.subheader("Top Teams by Games Attended")
    team_counts = {}
    for g in games:
        home = g.get('home_team')
        away = g.get('away_team')
        for t in (home, away):
            if t:
                team_counts[t] = team_counts.get(t, 0) + 1
    teams_list = [{"Team": t, "Games Attended": c} for t, c in sorted(team_counts.items(), key=lambda x: -x[1])]
    st.table(teams_list[:20])

    # Aggregated Team-by-Team Record
    st.subheader("Aggregated Team-by-Team Record")
    records = {}
    for g in games:
        home = g.get('home_team')
        away = g.get('away_team')
        hs = g.get('home_score')
        ascore = g.get('away_score')
        # skip if scores missing
        if home is None or away is None or hs is None or ascore is None:
            continue
        # initialize
        for t in (home, away):
            if t not in records:
                records[t] = {"Games":0, "Wins":0, "Losses":0, "Ties":0, "Runs For":0, "Runs Against":0}
        # update games and runs
        records[home]["Games"] += 1
        records[away]["Games"] += 1
        records[home]["Runs For"] += int(hs)
        records[home]["Runs Against"] += int(ascore)
        records[away]["Runs For"] += int(ascore)
        records[away]["Runs Against"] += int(hs)
        # determine result
        if int(hs) > int(ascore):
            records[home]["Wins"] += 1
            records[away]["Losses"] += 1
        elif int(hs) < int(ascore):
            records[away]["Wins"] += 1
            records[home]["Losses"] += 1
        else:
            records[home]["Ties"] += 1
            records[away]["Ties"] += 1

    # convert to list and compute win%
    records_list = []
    for t, r in records.items():
        win_pct = (r["Wins"] / r["Games"]) if r["Games"] > 0 else 0
        records_list.append({
            "Team": t,
            "Games": r["Games"],
            "Wins": r["Wins"],
            "Losses": r["Losses"],
            "Ties": r["Ties"],
            "Runs For": r["Runs For"],
            "Runs Against": r["Runs Against"],
            "Win%": f"{win_pct:.3f}"
        })
    # show sorted by Win%
    records_list_sorted = sorted(records_list, key=lambda x: (-float(x["Win%"]), -x["Games"]))
    st.dataframe(records_list_sorted, use_container_width=True)

    # Replace player performance charts with tables of top performances (fall back to existing stats)
    # Player performance charts
    if batting_stats:
        st.subheader("Top Batting Performances")
        
        batting_df = pd.DataFrame(batting_stats)
        
        if len(batting_df) > 0 and 'games' in batting_df.columns:
            # Filter for players with at least 3 games
            eligible_players = batting_df[batting_df['games'] >= 3]
            if len(eligible_players) > 0:
                col1, col2 = st.columns(2)
                
                with col1:
                    if 'batting_average' in eligible_players.columns:
                        top_avg = eligible_players.nlargest(10, 'batting_average')
                        fig_avg = px.bar(top_avg, x='batting_average', y='player_name',
                                        orientation='h', title='Top 10 Batting Averages (Min 3 Games)')
                        st.plotly_chart(fig_avg, use_container_width=True)
                
                with col2:
                    if 'home_runs' in eligible_players.columns:
                        top_hr = eligible_players.nlargest(10, 'home_runs')
                        fig_hr = px.bar(top_hr, x='home_runs', y='player_name',
                                       orientation='h', title='Top 10 Home Run Totals (Min 3 Games)')
                        st.plotly_chart(fig_hr, use_container_width=True)
            else:
                st.info("No players with at least 3 games for batting average leaderboard.")

def export_data_page():
    st.header("Export Player Statistics")

    games = st.session_state.data_manager.get_all_games()

    if not games:
        st.info("No data to export. Add some games first.")
        return

    st.write("Export aggregated player statistics from all your attended games.")

    # Calculate aggregated stats
    batting_stats, pitching_stats = st.session_state.stats_calculator.calculate_aggregate_stats(games)

    export_format = st.selectbox(
        "Select export format",
        ["JSON", "CSV"]
    )

    if st.button("Generate Export", type="primary"):
        try:
            if export_format == "JSON":
                # Export aggregated player stats as JSON
                export_data = {
                    "batting_stats": batting_stats,
                    "pitching_stats": pitching_stats,
                    "export_date": datetime.now().isoformat(),
                    "total_games": len(games),
                    "total_batters": len(batting_stats),
                    "total_pitchers": len(pitching_stats)
                }

                json_str = json.dumps(export_data, indent=2, default=str)

                st.download_button(
                    label="Download JSON",
                    data=json_str,
                    file_name=f"player_stats_{datetime.now().strftime('%Y%m%d')}.json",
                    mime="application/json"
                )

            elif export_format == "CSV":
                # Export batting stats as CSV
                if batting_stats:
                    batting_df = pd.DataFrame(batting_stats)
                    batting_csv = batting_df.to_csv(index=False)

                    st.download_button(
                        label="Download Batting Stats CSV",
                        data=batting_csv,
                        file_name=f"batting_stats_{datetime.now().strftime('%Y%m%d')}.csv",
                        mime="text/csv",
                        key="batting_csv"
                    )

                # Export pitching stats as CSV
                if pitching_stats:
                    pitching_df = pd.DataFrame(pitching_stats)
                    pitching_csv = pitching_df.to_csv(index=False)

                    st.download_button(
                        label="Download Pitching Stats CSV",
                        data=pitching_csv,
                        file_name=f"pitching_stats_{datetime.now().strftime('%Y%m%d')}.csv",
                        mime="text/csv",
                        key="pitching_csv"
                    )

        except Exception as e:
            st.error(f"Error generating export: {str(e)}")

    # Display summary statistics
    st.subheader("Export Summary")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Total Games", len(games))

    with col2:
        st.metric("Total Batters", len(batting_stats))

    with col3:
        st.metric("Total Pitchers", len(pitching_stats))

if __name__ == "__main__":
    main()
