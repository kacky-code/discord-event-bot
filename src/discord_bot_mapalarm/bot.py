import logging
import pathlib
from pathlib import Path

import discord
import yaml
from discord.ext import commands

TOKEN = ""
GUILD_ID = ""

intents = discord.Intents.default()
intents.members = True
bot = commands.Bot(command_prefix="THEREISnoFUCKINGprefix!", intents=intents)
logger = None


@bot.event
async def on_ready():
    for guild in bot.guilds:
        if guild.name == GUILD_ID:
            break

    logger.debug(
        f"{bot.user} is connected to the following guild: "
        f"{guild.name} (id: {guild.id})"
    )

    # just trying to debug here
    for guild in bot.guilds:
        for member in guild.members:
            # print(member.name, " ")
            pass

    # members = '\n - '.join([member.name for member in guild.members])
    # print(f'Guild Members:\n - {members}')
    # await guild.members[1].send("hey u")


def main():
    try:
        print(Path(__file__))
        with open(Path(__file__).parents[2] / "secrets.yaml") as s:
            secrets = yaml.load(s, yaml.FullLoader)
    except FileNotFoundError:
        raise FileNotFoundError(
            "Bot needs a bot.py with 'token' and 'guild' keys, containing the token for"
            " the bot and the ID of the guild to connect to!"
        )
    TOKEN = secrets["token"]
    GUILD_ID = secrets["guild"]
    if TOKEN == "" or GUILD_ID == "":
        raise RuntimeError("Bad values in secrets.yaml!")

    with open(Path(__file__).parents[2] / "config.yaml") as c:
        config = yaml.load(c, yaml.FullLoader)

        # Set up logging
        if config["logtype"] == "STDOUT":
            pass
            logging.basicConfig(
                format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
        elif config["logtype"] == "FILE":
            # Create logfile if not exists and use append mode
            f = open(pathlib.Path(config["logfile"]), "a+")
            f.close()
            logging.basicConfig(
                format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                filename=config["logfile"],
            )
        else:
            print("ERROR: Logging not correctly configured!")
            exit(1)

        global logger
        logger = logging.getLogger(config["logger_name"])
        logger.setLevel(eval("logging." + config["loglevel"]))

    if config["enable_map_alarm"]:
        bot.load_extension("discord_bot_mapalarm.cogs.kacky_notifier_cog")
    bot.run(TOKEN)


if __name__ == "__main__":
    main()
