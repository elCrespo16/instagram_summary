from typing import Tuple, Optional
from datetime import UTC, datetime, timedelta
import logging
from user_config import InstagramUserConfig
from pathlib import Path
from instagrapi import Client
from instagrapi.exceptions import LoginRequired
from instagrapi.types import Media

MAX_DAYS = 1
MAX_POSTS = 5

logger = logging.getLogger(__name__)
ConsoleOutputHandler = logging.StreamHandler()
logger.addHandler(ConsoleOutputHandler)
logger.setLevel(logging.INFO)
session_path = Path("session.json")


class InstagramController:
    def __init__(self, USERNAME: str, PASSWORD: str, last_updated: Optional[datetime] = None):
        self.client = Client()
        self.client.delay_range = [1, 3]
        self.username = USERNAME
        self.password = PASSWORD
        self.last_updated = last_updated.astimezone(UTC) if last_updated else None

    def get_user_news(self, user: InstagramUserConfig) -> Tuple[list[str], list[str]]:
        """
        Fetches the latest news for a given user.
        Returns a tuple with the stories and posts URLs.
        """
        logger.info(f"Getting news for user {user.username}")
        if not user.user_id:
            try:
                user.user_id = self.client.user_id_from_username(user.username)
            except Exception as e:
                logger.info(f"Could not get user id for {user.username}: {e}")
                return ([], [])
        stories_urls = self.get_stories(user) if user.stories else []
        posts_urls = self.get_posts(user) if user.posts else []
        return (stories_urls, posts_urls)

    def get_users_that_do_not_follow_back(self) -> list[str]:
        """
        Fetches the users that do not follow back.
        """
        logger.info("Getting users that do not follow back")
        try:
            following = self.client.user_following(self.client.user_id)
            followers = self.client.user_followers(self.client.user_id)
            followers_ids = followers.keys()
            not_following_back = [
                user.username for user_id, user in following.items() if user_id not in followers_ids]
        except Exception as e:
            logger.info(f"Could not get users that do not follow back: {e}")
            return []
        return not_following_back

    def build_story_url(self, username) -> str:
        """
        Builds the URL for a given story.
        """
        return f"https://www.instagram.com/stories/{username}/"

    def build_media_url(self, media: Media) -> str:
        """
        Builds the URL for a given post.
        """
        return f"https://www.instagram.com/p/{media.code}/"

    def get_stories(self, user: InstagramUserConfig) -> list[str]:
        """
        Fetches the latest stories for a given user.
        """
        logger.info(f"Getting stories for user {user.username}")
        stories_url = []
        try:
            stories = self.client.user_stories(user.user_id, 1)
            if stories and self.media_is_recent(stories[0]):
                stories_url = [self.build_story_url(username=user.username)]
        except Exception as e:
            logger.info(f"Could not get stories for user {user.username}: {e}")
        return stories_url

    def media_is_recent(self, media) -> bool:
        """
        Checks if a media is recent. If the media was taken after the last update, it is considered recent.
        """
        return ((not self.last_updated and media.taken_at > datetime.now(tz=UTC) - timedelta(MAX_DAYS))
                 or (self.last_updated and media.taken_at > self.last_updated))

    def get_posts(self, user: InstagramUserConfig) -> list[str]:
        """
        Fetches the latest posts for a given user.
        """
        logger.info(f"Getting posts for user {user.username}")
        try:
            posts = self.client.user_medias(user.user_id, MAX_POSTS, 3)
            return [self.build_media_url(post) for post in posts if self.media_is_recent(post)]
        except Exception as e:
            logger.info(f"Could not get posts for user {user.username}: {e}")
            return []

    def login_user(self):
        """
        Attempts to login to Instagram using either the provided session information
        or the provided username and password.
        """
        session = self.client.load_settings(
            session_path) if session_path.exists() else None

        login_via_session = False
        login_via_pw = False

        if session:
            try:
                self.client.set_settings(session)
                self.client.login(self.username, self.password)

                # check if session is valid
                try:
                    self.client.get_timeline_feed()
                except LoginRequired:
                    logger.info(
                        "Session is invalid, need to login via username and password")

                    old_session = self.client.get_settings()

                    # use the same device uuids across logins
                    self.client.set_settings({})
                    self.client.set_uuids(old_session["uuids"])

                    self.client.login(self.username, self.password)
                login_via_session = True
            except Exception as e:
                logger.info(
                    "Couldn't login user using session information: %s" % e)

        if not login_via_session:
            try:
                logger.info(
                    "Attempting to login via username and password. username: %s" % self.username)
                if self.client.login(self.username, self.password):
                    login_via_pw = True
            except Exception as e:
                logger.info(
                    "Couldn't login user using username and password: %s" % e)

        if not login_via_pw and not login_via_session:
            raise Exception(
                "Couldn't login user with either password or session")

    def save_settings(self):
        """
        Saves the current session information to a file.
        """
        self.client.dump_settings(session_path)
