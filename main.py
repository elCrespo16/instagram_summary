import os
from instagram_controller import InstagramController
from commands import (CommandInvoker, AddUserCommand, RemoveUserCommand,
                      ListUsersCommand, InstagramConfig, UsersDoNotFollowBack)
from dotenv import load_dotenv
from telegram_controller import TelegramController
from datetime import datetime


def register_commands(command_invoker: CommandInvoker):
    command_invoker.register("adduser", AddUserCommand())
    command_invoker.register("deleteuser", RemoveUserCommand())
    command_invoker.register("listusers", ListUsersCommand())
    command_invoker.register("fakes", UsersDoNotFollowBack())



def answer_command(command_invoker, telegram_controller, update):
    response = command_invoker.run(update.message.text)
    telegram_controller.reply(update.message, response)


def main():
    # load environment variables
    load_dotenv()
    username = os.environ.get("USERNAME", "")
    password = os.environ.get("PASSWORD", "")
    test = os.environ.get("TEST", "")
    # initialize controllers
    config = InstagramConfig.load()
    telegram_controller = TelegramController(update_id=config.update_id)
    instagram_controller = InstagramController(
        username, password, config.last_updated)
    instagram_controller.login_user()
    command_invoker = CommandInvoker(config, instagram_controller)
    telegram_controller.notify(
        f"Instagram summary {datetime.today().strftime('%d-%m-%Y')}")
    register_commands(command_invoker)
    # handle commands
    handle_commands(config, telegram_controller, command_invoker)
    # handle instagram news
    handle_instagram_news(config, telegram_controller, instagram_controller)
    # save settings
    config.last_updated = datetime.now() if not test else None
    config.save()
    instagram_controller.save_settings()


def handle_instagram_news(config: InstagramConfig,
                          telegram_controller: TelegramController,
                          instagram_controller: InstagramController):
    for user in config.users:
        stories_url, posts_url = instagram_controller.get_user_news(user)
        stories_message = f"New stories from {user.username}: " if stories_url else ""
        stories_message += "\n".join(stories_url)
        telegram_controller.notify(stories_message)
        for post in posts_url:
            telegram_controller.notify(
                f"New post from {user.username}: {post}")


def handle_commands(config: InstagramConfig,
                    telegram_controller: TelegramController,
                    command_invoker: CommandInvoker):
    updates = telegram_controller.get_new_messages()
    for update in updates:
        config.update_id = update.update_id + 1
        if update.message and not update.message.from_user.is_bot:
            answer_command(command_invoker, telegram_controller, update)


if __name__ == "__main__":
    main()
