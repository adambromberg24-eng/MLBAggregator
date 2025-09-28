import statsapi
from typing import List, Dict, Any, Optional
from datetime import datetime
import json

class MLBApiClient:
    def __init__(self):
        self.teams_cache = None
    
    def get_teams(self) -> List[Dict[str, Any]]:
        """Get list of all MLB teams"""
        if self.teams_cache is not None:
            return self.teams_cache
        
        try:
            # Get teams using statsapi
            teams_data = statsapi.get('teams', {'sportId': 1})
            teams = []
            
            if teams_data and 'teams' in teams_data:
                for team in teams_data['teams']:
                    teams.append({
                        'id': team.get('id'),
                        'name': team.get('name', ''),
                        'abbreviation': team.get('abbreviation', ''),
                        'teamName': team.get('teamName', ''),
                        'locationName': team.get('locationName', ''),
                        'division': team.get('division', {}).get('name', ''),
                        'league': team.get('league', {}).get('name', '')
                    })
            
            # Sort teams by name
            teams.sort(key=lambda x: x['name'])
            self.teams_cache = teams
            return teams
            
        except Exception as e:
            print(f"Error fetching teams: {e}")
            return []
    
    def get_game_data(self, home_team_id: int, away_team_id: int, game_date: str) -> Optional[Dict[str, Any]]:
        """Get game data for specific teams and date"""
        try:
            # Convert date to string format if it's a date object
            if hasattr(game_date, 'strftime'):
                date_str = game_date.strftime('%Y-%m-%d')
            else:
                date_str = str(game_date)
            
            # Get schedule for the date
            schedule = statsapi.schedule(date=date_str)
            
            target_game = None
            for game in schedule:
                if (game.get('home_id') == home_team_id and 
                    game.get('away_id') == away_team_id):
                    target_game = game
                    break
            
            if not target_game:
                return None
            
            game_id = target_game.get('game_id')
            if not game_id:
                return None
            
            # Get detailed box score
            box_score = statsapi.boxscore_data(game_id)
            
            # Extract game information
            game_data = {
                'game_id': game_id,
                'date': date_str,
                'home_team': target_game.get('home_name', ''),
                'away_team': target_game.get('away_name', ''),
                'home_team_id': home_team_id,
                'away_team_id': away_team_id,
                'home_score': target_game.get('home_score', 0),
                'away_score': target_game.get('away_score', 0),
                'game_status': target_game.get('status', ''),
                'venue': target_game.get('venue_name', ''),
                'home_team_batting': [],
                'away_team_batting': [],
                'home_team_pitching': [],
                'away_team_pitching': []
            }
            
            # Extract batting statistics from homeBatters and awayBatters
            if 'homeBatters' in box_score:
                for player_stats in box_score['homeBatters']:
                    if player_stats.get('personId', 0) > 0:  # Skip header row (personId = 0)
                        batting_data = self._extract_batting_stats(player_stats, box_score)
                        if batting_data:
                            game_data['home_team_batting'].append(batting_data)
            
            if 'awayBatters' in box_score:
                for player_stats in box_score['awayBatters']:
                    if player_stats.get('personId', 0) > 0:  # Skip header row (personId = 0)
                        batting_data = self._extract_batting_stats(player_stats, box_score)
                        if batting_data:
                            game_data['away_team_batting'].append(batting_data)
            
            # Extract pitching statistics from homePitchers and awayPitchers
            if 'homePitchers' in box_score:
                for player_stats in box_score['homePitchers']:
                    if player_stats.get('personId', 0) > 0:  # Skip header row (personId = 0)
                        pitching_data = self._extract_pitching_stats(player_stats, box_score)
                        if pitching_data:
                            game_data['home_team_pitching'].append(pitching_data)
            
            if 'awayPitchers' in box_score:
                for player_stats in box_score['awayPitchers']:
                    if player_stats.get('personId', 0) > 0:  # Skip header row (personId = 0)
                        pitching_data = self._extract_pitching_stats(player_stats, box_score)
                        if pitching_data:
                            game_data['away_team_pitching'].append(pitching_data)
            
            return game_data
            
        except Exception as e:
            print(f"Error fetching game data: {e}")
            return None
    
    def _extract_batting_stats(self, player_stats: Dict, box_score: Dict) -> Optional[Dict[str, Any]]:
        """Extract batting statistics for a player"""
        try:
            player_id = str(player_stats.get('personId', ''))
            
            # Get player name from roster data
            player_name = self._get_player_name(player_id, box_score)
            
            # Convert string values to integers, handling empty strings
            def safe_int(value):
                try:
                    return int(value) if value and value != '' else 0
                except (ValueError, TypeError):
                    return 0
            
            # Get batting order and position
            batting_order = player_stats.get('battingOrder', '')
            position = player_stats.get('position', '')  # Position is a direct string in this API response
            substitution = bool(player_stats.get('substitution', False))
            
            # Convert batting order to number (1-9) for starters
            try:
                # MLB API uses string like '100' for 1st, '200' for 2nd, etc.
                order_num = int(batting_order[0]) if batting_order and not substitution else None
            except (ValueError, IndexError):
                order_num = None
                
            return {
                'order': order_num,
                'player_id': player_id,
                'name': player_name,
                'position': position,
                'sub': substitution,
                'at_bats': safe_int(player_stats.get('ab', 0)),
                'hits': safe_int(player_stats.get('h', 0)),
                'runs': safe_int(player_stats.get('r', 0)),
                'rbis': safe_int(player_stats.get('rbi', 0)),
                'doubles': safe_int(player_stats.get('doubles', 0)),
                'triples': safe_int(player_stats.get('triples', 0)),
                'home_runs': safe_int(player_stats.get('hr', 0)),
                'walks': safe_int(player_stats.get('bb', 0)),
                'strikeouts': safe_int(player_stats.get('k', 0)),
                'stolen_bases': safe_int(player_stats.get('sb', 0)),
                'caught_stealing': 0  # Not available in this format
            }
        except Exception as e:
            print(f"Error extracting batting stats: {e}")
            return None
    
    def _extract_pitching_stats(self, player_stats: Dict, box_score: Dict) -> Optional[Dict[str, Any]]:
        """Extract pitching statistics for a player"""
        try:
            player_id = str(player_stats.get('personId', ''))
            
            # Get player name from roster data
            player_name = self._get_player_name(player_id, box_score)
            
            # Convert string values to appropriate types, handling empty strings
            def safe_int(value):
                try:
                    return int(value) if value and value != '' else 0
                except (ValueError, TypeError):
                    return 0
            
            def safe_float(value):
                try:
                    return float(value) if value and value != '' else 0.0
                except (ValueError, TypeError):
                    return 0.0
            
            def parse_innings(innings_str):
                """Parse baseball innings notation (e.g., '6.1' = 6⅓ innings)"""
                try:
                    if not innings_str or innings_str == '':
                        return 0.0
                    
                    innings_str = str(innings_str)
                    if '.' in innings_str:
                        whole, fraction = innings_str.split('.')
                        whole_innings = int(whole) if whole else 0
                        
                        # Convert baseball fractional notation to decimal
                        if fraction == '1':
                            fraction_decimal = 1/3  # 1 out = 1/3 inning
                        elif fraction == '2':
                            fraction_decimal = 2/3  # 2 outs = 2/3 inning
                        else:
                            # Handle other cases (shouldn't happen in baseball)
                            fraction_decimal = int(fraction) / 3 if fraction.isdigit() else 0
                        
                        return whole_innings + fraction_decimal
                    else:
                        return float(innings_str)
                except (ValueError, TypeError):
                    return 0.0
            
            # Parse wins/losses from namefield (e.g., "Lodolo  (W, 9-8)")
            wins = 0
            losses = 0
            saves = 0
            namefield = player_stats.get('namefield', '')
            if '(W,' in namefield:
                wins = 1
            elif '(L,' in namefield:
                losses = 1
            elif '(S,' in namefield:
                saves = 1
            
            return {
                'player_id': player_id,
                'name': player_name,
                'wins': wins,
                'losses': losses,
                'saves': saves,
                'innings_pitched': parse_innings(player_stats.get('ip', 0)),
                'hits_allowed': safe_int(player_stats.get('h', 0)),
                'runs_allowed': safe_int(player_stats.get('r', 0)),
                'earned_runs': safe_int(player_stats.get('er', 0)),
                'walks_allowed': safe_int(player_stats.get('bb', 0)),
                'strikeouts': safe_int(player_stats.get('k', 0)),
                'home_runs_allowed': safe_int(player_stats.get('hr', 0)),
                'pitches_thrown': safe_int(player_stats.get('p', 0))
            }
        except Exception as e:
            print(f"Error extracting pitching stats: {e}")
            return None
    
    def _get_player_name(self, player_id: str, box_score: Dict) -> str:
        """Get player name from box score data"""
        try:
            # Look in player info section using the correct key format
            if 'playerInfo' in box_score:
                player_key = f'ID{player_id}'
                if player_key in box_score['playerInfo']:
                    player_info = box_score['playerInfo'][player_key]
                    return player_info.get('fullName', f'Player {player_id}')
            
            # Fallback to generic name
            return f'Player {player_id}'
            
        except Exception as e:
            print(f"Error getting player name: {e}")
            return f'Player {player_id}'
    
    def get_player_info(self, player_id: int) -> Optional[Dict[str, Any]]:
        """Get detailed player information"""
        try:
            player_data = statsapi.get('person', {'personId': player_id})
            
            if player_data and 'people' in player_data and len(player_data['people']) > 0:
                player = player_data['people'][0]
                return {
                    'id': player.get('id'),
                    'fullName': player.get('fullName', ''),
                    'firstName': player.get('firstName', ''),
                    'lastName': player.get('lastName', ''),
                    'position': player.get('primaryPosition', {}).get('name', ''),
                    'jersey_number': player.get('primaryNumber', ''),
                    'team': player.get('currentTeam', {}).get('name', ''),
                    'birthDate': player.get('birthDate', ''),
                    'height': player.get('height', ''),
                    'weight': player.get('weight', ''),
                    'bats': player.get('batSide', {}).get('description', ''),
                    'throws': player.get('pitchHand', {}).get('description', '')
                }
            
            return None
            
        except Exception as e:
            print(f"Error fetching player info: {e}")
            return None
