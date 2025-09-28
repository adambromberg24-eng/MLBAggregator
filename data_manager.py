import json
import os
from typing import List, Dict, Any, Optional
from datetime import datetime

class DataManager:
    def __init__(self, data_file: str = "baseball_data.json", user_id: str = None):
        self.user_id = user_id
        self.data_file = f"baseball_data_{user_id}.json" if user_id else data_file
        self.data = self._load_data()
    
    def _load_data(self) -> Dict[str, Any]:
        """Load data from JSON file or create empty structure"""
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                return {"games": [], "created_at": datetime.now().isoformat()}
        except Exception as e:
            print(f"Error loading data: {e}")
            return {"games": [], "created_at": datetime.now().isoformat()}
    
    def _save_data(self) -> bool:
        """Save data to JSON file"""
        try:
            self.data["updated_at"] = datetime.now().isoformat()
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, indent=2, default=str)
            return True
        except Exception as e:
            print(f"Error saving data: {e}")
            return False
    
    def add_game(self, game_data: Dict[str, Any], notes: str = "") -> bool:
        """Add a new game to the database"""
        try:
            # Check if game already exists
            game_id = f"{game_data.get('date')}_{game_data.get('home_team_id')}_{game_data.get('away_team_id')}"
            
            for existing_game in self.data["games"]:
                existing_id = f"{existing_game.get('date')}_{existing_game.get('home_team_id')}_{existing_game.get('away_team_id')}"
                if existing_id == game_id:
                    return False  # Game already exists
            
            # Add notes to game data
            game_data["notes"] = notes
            game_data["added_at"] = datetime.now().isoformat()
            
            self.data["games"].append(game_data)
            return self._save_data()
        except Exception as e:
            print(f"Error adding game: {e}")
            return False
    
    def get_all_games(self) -> List[Dict[str, Any]]:
        """Get all games from the database"""
        return self.data.get("games", [])
    
    def remove_game(self, index: int) -> bool:
        """Remove a game by index"""
        try:
            if 0 <= index < len(self.data["games"]):
                self.data["games"].pop(index)
                return self._save_data()
            return False
        except Exception as e:
            print(f"Error removing game: {e}")
            return False
    
    def get_game_by_date_and_teams(self, date: str, home_team: str, away_team: str) -> Optional[Dict[str, Any]]:
        """Get a specific game by date and teams"""
        for game in self.data["games"]:
            if (game.get("date") == date and 
                game.get("home_team") == home_team and 
                game.get("away_team") == away_team):
                return game
        return None
    
    def get_games_by_team(self, team_name: str) -> List[Dict[str, Any]]:
        """Get all games involving a specific team"""
        games = []
        for game in self.data["games"]:
            if team_name in [game.get("home_team"), game.get("away_team")]:
                games.append(game)
        return games
    
    def get_games_by_date_range(self, start_date: str, end_date: str) -> List[Dict[str, Any]]:
        """Get games within a date range"""
        games = []
        for game in self.data["games"]:
            game_date = game.get("date", "")
            if start_date <= game_date <= end_date:
                games.append(game)
        return games
    
    def clear_all_data(self) -> bool:
        """Clear all game data"""
        try:
            self.data = {"games": [], "created_at": datetime.now().isoformat()}
            return self._save_data()
        except Exception as e:
            print(f"Error clearing data: {e}")
            return False
