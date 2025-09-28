from typing import List, Dict, Any, Tuple
import pandas as pd
from collections import defaultdict

class StatsCalculator:
    def __init__(self):
        pass
    
    def calculate_aggregate_stats(self, games: List[Dict[str, Any]]) -> Tuple[List[Dict], List[Dict]]:
        """Calculate aggregate batting and pitching statistics from all games"""
        batting_stats = defaultdict(lambda: {
            'player_name': '',
            'team': '',
            'games': 0,
            'at_bats': 0,
            'hits': 0,
            'runs': 0,
            'rbis': 0,
            'doubles': 0,
            'triples': 0,
            'home_runs': 0,
            'walks': 0,
            'strikeouts': 0,
            'batting_average': 0.0,
            'on_base_percentage': 0.0,
            'slugging_percentage': 0.0,
            'ops': 0.0
        })
        
        pitching_stats = defaultdict(lambda: {
            'player_name': '',
            'team': '',
            'games': 0,
            'wins': 0,
            'losses': 0,
            'saves': 0,
            'innings_pitched': 0.0,
            'hits_allowed': 0,
            'runs_allowed': 0,
            'earned_runs': 0,
            'walks_allowed': 0,
            'strikeouts': 0,
            'home_runs_allowed': 0,
            'era': 0.0,
            'whip': 0.0
        })
        
        # Process each game
        for game in games:
            self._process_game_batting_stats(game, batting_stats)
            self._process_game_pitching_stats(game, pitching_stats)
        
        # Calculate derived statistics
        batting_list = self._calculate_batting_averages(batting_stats)
        pitching_list = self._calculate_pitching_averages(pitching_stats)
        
        return batting_list, pitching_list
    
    def _process_game_batting_stats(self, game: Dict[str, Any], batting_stats: defaultdict):
        """Process batting statistics from a single game"""
        # Process home team batting
        home_batting = game.get('home_team_batting', [])
        for player in home_batting:
            player_id = player.get('player_id', f"unknown_{player.get('name', 'unnamed')}")
            
            stats = batting_stats[player_id]
            stats['player_name'] = player.get('name', 'Unknown')
            stats['team'] = game.get('home_team', 'Unknown')
            stats['games'] += 1
            
            # Add batting statistics
            stats['at_bats'] += int(player.get('at_bats', 0))
            stats['hits'] += int(player.get('hits', 0))
            stats['runs'] += int(player.get('runs', 0))
            stats['rbis'] += int(player.get('rbis', 0))
            stats['doubles'] += int(player.get('doubles', 0))
            stats['triples'] += int(player.get('triples', 0))
            stats['home_runs'] += int(player.get('home_runs', 0))
            stats['walks'] += int(player.get('walks', 0))
            stats['strikeouts'] += int(player.get('strikeouts', 0))
        
        # Process away team batting
        away_batting = game.get('away_team_batting', [])
        for player in away_batting:
            player_id = player.get('player_id', f"unknown_{player.get('name', 'unnamed')}")
            
            stats = batting_stats[player_id]
            stats['player_name'] = player.get('name', 'Unknown')
            stats['team'] = game.get('away_team', 'Unknown')
            stats['games'] += 1
            
            # Add batting statistics
            stats['at_bats'] += int(player.get('at_bats', 0))
            stats['hits'] += int(player.get('hits', 0))
            stats['runs'] += int(player.get('runs', 0))
            stats['rbis'] += int(player.get('rbis', 0))
            stats['doubles'] += int(player.get('doubles', 0))
            stats['triples'] += int(player.get('triples', 0))
            stats['home_runs'] += int(player.get('home_runs', 0))
            stats['walks'] += int(player.get('walks', 0))
            stats['strikeouts'] += int(player.get('strikeouts', 0))
    
    def _process_game_pitching_stats(self, game: Dict[str, Any], pitching_stats: defaultdict):
        """Process pitching statistics from a single game"""
        # Process home team pitching
        home_pitching = game.get('home_team_pitching', [])
        for player in home_pitching:
            player_id = player.get('player_id', f"unknown_{player.get('name', 'unnamed')}")
            
            stats = pitching_stats[player_id]
            stats['player_name'] = player.get('name', 'Unknown')
            stats['team'] = game.get('home_team', 'Unknown')
            stats['games'] += 1
            
            # Add pitching statistics
            stats['wins'] += int(player.get('wins', 0))
            stats['losses'] += int(player.get('losses', 0))
            stats['saves'] += int(player.get('saves', 0))
            stats['innings_pitched'] += float(player.get('innings_pitched', 0))
            stats['hits_allowed'] += int(player.get('hits_allowed', 0))
            stats['runs_allowed'] += int(player.get('runs_allowed', 0))
            stats['earned_runs'] += int(player.get('earned_runs', 0))
            stats['walks_allowed'] += int(player.get('walks_allowed', 0))
            stats['strikeouts'] += int(player.get('strikeouts', 0))
            stats['home_runs_allowed'] += int(player.get('home_runs_allowed', 0))
        
        # Process away team pitching
        away_pitching = game.get('away_team_pitching', [])
        for player in away_pitching:
            player_id = player.get('player_id', f"unknown_{player.get('name', 'unnamed')}")
            
            stats = pitching_stats[player_id]
            stats['player_name'] = player.get('name', 'Unknown')
            stats['team'] = game.get('away_team', 'Unknown')
            stats['games'] += 1
            
            # Add pitching statistics
            stats['wins'] += int(player.get('wins', 0))
            stats['losses'] += int(player.get('losses', 0))
            stats['saves'] += int(player.get('saves', 0))
            stats['innings_pitched'] += float(player.get('innings_pitched', 0))
            stats['hits_allowed'] += int(player.get('hits_allowed', 0))
            stats['runs_allowed'] += int(player.get('runs_allowed', 0))
            stats['earned_runs'] += int(player.get('earned_runs', 0))
            stats['walks_allowed'] += int(player.get('walks_allowed', 0))
            stats['strikeouts'] += int(player.get('strikeouts', 0))
            stats['home_runs_allowed'] += int(player.get('home_runs_allowed', 0))
    
    def _calculate_batting_averages(self, batting_stats: defaultdict) -> List[Dict]:
        """Calculate batting averages and derived statistics"""
        batting_list = []
        
        for player_id, stats in batting_stats.items():
            # Calculate batting average
            if stats['at_bats'] > 0:
                stats['batting_average'] = round(stats['hits'] / stats['at_bats'], 3)
            
            # Calculate on-base percentage
            plate_appearances = stats['at_bats'] + stats['walks']
            if plate_appearances > 0:
                on_base = stats['hits'] + stats['walks']
                stats['on_base_percentage'] = round(on_base / plate_appearances, 3)
            
            # Calculate slugging percentage
            if stats['at_bats'] > 0:
                total_bases = (stats['hits'] - stats['doubles'] - stats['triples'] - stats['home_runs'] +
                              (stats['doubles'] * 2) + (stats['triples'] * 3) + (stats['home_runs'] * 4))
                stats['slugging_percentage'] = round(total_bases / stats['at_bats'], 3)
            
            # Calculate OPS
            stats['ops'] = round(stats['on_base_percentage'] + stats['slugging_percentage'], 3)
            
            batting_list.append(dict(stats))
        
        return batting_list
    
    def _calculate_pitching_averages(self, pitching_stats: defaultdict) -> List[Dict]:
        """Calculate pitching averages and derived statistics"""
        pitching_list = []
        
        for player_id, stats in pitching_stats.items():
            # Calculate ERA
            if stats['innings_pitched'] > 0:
                stats['era'] = round((stats['earned_runs'] * 9) / stats['innings_pitched'], 2)
            
            # Calculate WHIP
            if stats['innings_pitched'] > 0:
                stats['whip'] = round((stats['hits_allowed'] + stats['walks_allowed']) / stats['innings_pitched'], 2)
            
            pitching_list.append(dict(stats))
        
        return pitching_list
    
    def get_team_summary(self, games: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Get summary statistics for all teams"""
        team_records = defaultdict(lambda: {'wins': 0, 'losses': 0, 'games_seen': 0})
        
        for game in games:
            home_team = game.get('home_team', 'Unknown')
            away_team = game.get('away_team', 'Unknown')
            home_score = int(game.get('home_score', 0))
            away_score = int(game.get('away_score', 0))
            
            team_records[home_team]['games_seen'] += 1
            team_records[away_team]['games_seen'] += 1
            
            if home_score > away_score:
                team_records[home_team]['wins'] += 1
                team_records[away_team]['losses'] += 1
            elif away_score > home_score:
                team_records[away_team]['wins'] += 1
                team_records[home_team]['losses'] += 1
        
        return dict(team_records)
