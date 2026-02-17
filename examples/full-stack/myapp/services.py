from pico_ioc import component

from .config import DatabaseConfig, AppConfig


@component
class DatabaseService:
    """Simulates database operations."""

    def __init__(self, config: DatabaseConfig):
        self.host = config.host
        self.port = config.port
        self.db_name = config.name

    def get_user(self, user_id: int) -> dict:
        return {"id": user_id, "name": "Alice", "email": "alice@example.com"}

    def save_user(self, user: dict) -> bool:
        print(f"  [DB {self.host}:{self.port}/{self.db_name}] Saving user: {user}")
        return True


@component
class UserService:
    """Business logic for user operations."""

    def __init__(self, db: DatabaseService, config: AppConfig):
        self.db = db
        self.debug = config.debug

    def get_user_profile(self, user_id: int) -> dict:
        if self.debug:
            print(f"  [DEBUG] Fetching user {user_id}")
        user = self.db.get_user(user_id)
        return {
            "id": user["id"],
            "display_name": user["name"],
            "contact": user["email"],
        }

    def update_email(self, user_id: int, new_email: str) -> bool:
        user = self.db.get_user(user_id)
        user["email"] = new_email
        return self.db.save_user(user)
