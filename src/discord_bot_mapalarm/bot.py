import asyncio
import logging
import pathlib
from pathlib import Path

import discord
import yaml
from discord.ext import commands

intents = discord.Intents.default()
intents.members = True
intents.message_content = True
bot = commands.Bot(command_prefix="THEREISnoFUCKINGprefix!", intents=intents)
logger = None


@bot.event
async def on_ready():
    """
    Leave this here for debugging in the future

    Returns:

    """
    try:
        print(Path(__file__))
        with open(Path(__file__).parents[2] / "secrets.yaml") as s:
            secrets = yaml.load(s, yaml.FullLoader)
    except FileNotFoundError:
        raise FileNotFoundError(
            "Bot needs a bot.py with 'token' and 'guild' keys, containing the token for"
            " the bot and the ID of the guild to connect to!"
        )
    for guild in bot.guilds:
        # if guild.id != secrets["guild"]:
            # await guild.leave()
            # print(f"leaving guild.name")
            # exit()
        print(
            f"{bot.user} is connected to the following guild: "
            f"{guild.name} (id: {guild.id})"
        )

    # print(bot.guilds)

    # just trying to debug here
    # for guild in bot.guilds:
    #    for member in guild.members:
    #        print(member.name, " ")
    #        pass

    # members = "\n - ".join([member.name for member in guild.members])
    # print(f"Guild Members:\n - {members}")
    # await guild.members[1].send("hey u")


async def main():
    try:
        print(Path(__file__))
        with open(Path(__file__).parents[2] / "secrets.yaml") as s:
            secrets = yaml.load(s, yaml.FullLoader)
    except FileNotFoundError:
        raise FileNotFoundError(
            "Bot needs a bot.py with 'token' and 'guild' keys, containing the token for"
            " the bot and the ID of the guild to connect to!"
        )
    TOKEN = secrets.get("token", "")
    if TOKEN == "":
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

    async with bot:
        if config["enable_map_alarm"]:
            await bot.load_extension("cogs.mapalarm")
        if config["enable_wr_alarm"]:
            await bot.load_extension("cogs.wralarm")
        if config["enable_event_roles"]:
            await bot.load_extension("cogs.eventroles")
        await bot.start(TOKEN)


if __name__ == "__main__":
    asyncio.run(main())
