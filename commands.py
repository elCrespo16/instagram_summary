from abc import abstractmethod, ABC
import string
from typing import Optional
from utils import Singleton
from telebot.util import extract_arguments, extract_command
import logging

from instagram_controller import InstagramController
from user_config import InstagramConfig, InstagramUserConfig

logger = logging.getLogger(__name__)
ConsoleOutputHandler = logging.StreamHandler()
logger.addHandler(ConsoleOutputHandler)
logger.setLevel(logging.INFO)


class CommandResponse:
    def __init__(self, message: str = "", success: bool = True):
        self.message = message
        self.success = success

    def __str__(self):
        message = self.message
        if not message:
            message = "Success" if self.success else "Failed"
        return message

    def __bool__(self):
        return self.success


class Command(ABC):
    @abstractmethod
    def execute(self, *args, **kwargs) -> CommandResponse:
        pass

    def validate(self, *args, **kwargs) -> bool:
        return True


class AddUserCommand(Command):
    def execute(self, instagram_config: InstagramConfig, username: str, *args, **kwargs) -> CommandResponse:
        logger.info(f"Adding user {username}")
        for arg in args:
            kwargs["posts"] = not (arg == "posts")
            kwargs["stories"] = not (arg == "stories")
        instagram_config.users.append(InstagramUserConfig(username=username, **kwargs))
        return CommandResponse()

    def validate(self, instagram_config: InstagramConfig, username: Optional[str]=None, *args, **kwargs) -> bool:
        if not username:
            logger.info("No username provided")
            return False
        if username in [user.username for user in instagram_config.users]:
            logger.info(f"User {username} already exists")
            return False
        return super().validate(*args, **kwargs)


class RemoveUserCommand(Command):
    def execute(self, instagram_config: InstagramConfig, username: str,  *args, **kwargs):
        logger.info(f"Removing user {username}")
        instagram_config.users = [
            user for user in instagram_config.users if user.username != username]
        return CommandResponse()

    def validate(self, instagram_config: InstagramConfig, username: Optional[str]=None, *args, **kwargs) -> bool:
        if not username:
            logger.info("No username provided")
            return False
        if username not in [user.username for user in instagram_config.users]:
            logger.info(f"User {username} does not exist")
            return False
        return super().validate(*args, **kwargs)


class ListUsersCommand(Command):
    def execute(self, instagram_config: InstagramConfig, *args, **kwargs):
        logger.info("Listing users")
        return CommandResponse("\n".join([f"{user.username} post: {user.posts} stories: {user.stories}"
                                          for user in instagram_config.users]))

class UsersDoNotFollowBack(Command):
    def execute(self, *args, instagram_controller: InstagramController, **kwargs):
        logger.info("Listing users that do not follow back")
        users = instagram_controller.get_users_that_do_not_follow_back()
        return CommandResponse("\n".join(users))


class CommandInvoker(metaclass=Singleton):
    def __init__(self, instagram_config: InstagramConfig, instagram_controller: InstagramController):
        self._commands = {}
        self.instagram_config = instagram_config
        self.instagram_controller = instagram_controller

    def register(self, command_name, command):
        self._commands[command_name] = command

    def execute(self, command_name, command_args):
        command = self._commands.get(command_name)
        if command and command.validate(self.instagram_config, *command_args):
            return command.execute(self.instagram_config, instagram_controller=self.instagram_controller, *command_args)
        else:
            logger.info(f"Command {command_name} not found")
            return CommandResponse("Command not found", False)

    def parse_command(self, command_string) -> tuple[str, list[str]]:
        command_name = extract_command(command_string)
        command_args = extract_arguments(command_string)
        return command_name, command_args.split()

    def is_command(self, command_string):
        return self.parse_command(command_string)[0] in self._commands

    def run(self, command_string) -> CommandResponse:
        if self.is_command(command_string):
            command_name, command_args = self.parse_command(command_string)
            return self.execute(command_name, command_args)
        logger.info(f"Command {command_string} not found")
        return CommandResponse("Command not found", False)
