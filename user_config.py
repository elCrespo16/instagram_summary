from pydantic import BaseModel
import yaml
from typing import Optional
from datetime import datetime

CONFIG_FILE = "config.yaml"


class InstagramUserConfig(BaseModel):
    username: str
    stories: bool = True
    posts: bool = True
    user_id: Optional[int] = None


class InstagramConfig(BaseModel):
    users: list[InstagramUserConfig]
    update_id: Optional[int] = None
    last_updated: Optional[datetime] = None

    @classmethod
    def load(cls):
        with open(CONFIG_FILE, "r") as file:
            config = yaml.load(file.read(), Loader=yaml.FullLoader)
        return cls.model_validate(config)

    def save(self):
        with open(CONFIG_FILE, "w") as file:
            yaml.dump(self.model_dump(), file, default_flow_style=False)