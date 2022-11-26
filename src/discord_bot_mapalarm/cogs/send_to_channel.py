import datetime
import logging
import random
from pathlib import Path

import discord
import yaml
from discord.ext import tasks, commands

from src.discord_bot_mapalarm.db_ops.wr_notification_check import WRNotification
from src.discord_bot_mapalarm.tm_string.tm_format_resolver import TMstr


class MyCog(commands.Cog, name="SendCog"):
    def __init__(self, bot, config, secrets):
        self._ready = False
        self.bot = bot
        self.config = config
        self.secrets = secrets
        # printer should technically be started in on_ready(), but that is super slow.
        # For some reason this is faster, although it might send messages when not
        # connected yet (yielding channel = None in printer)
        self.printer.start()
        self.logger = logging.getLogger(self.config["logger_name"])

        self.logger.info("Setting up SendCog")
        self.wrnotifier = WRNotification()

        with open(Path(__file__).parents[3] / "secrets.yaml") as b:
            self.guild_id = yaml.load(b, yaml.FullLoader)["guild"]
        if self.guild_id == "":
            raise RuntimeError("Bad values in secrets.yaml!")

    def cog_unload(self):
        self.printer.cancel()
        self._ready = False

    def on_ready(self):
        self.logger.info("SendCog ready")
        self._ready = True

    @tasks.loop(seconds=10.0)
    async def printer(self):
        channel = self.bot.get_channel(1044146248422264852)
        self.logger.info(f"Sending message to channel {channel}")

        new_wrs = self.wrnotifier.get_new_wr()
        if not new_wrs:
            try:
                await channel.send("no new wr :(")
            except Exception as e:
                pass

        pogs = discord.utils.get(self.bot.emojis, name='POGSLIDE')

        for wr in new_wrs:
            embed_msg = discord.Embed(
                title=f"{pogs} {TMstr(wr[0]).string} - {wr.score / 1000}s {pogs}",
                url="https://kacky.info",
                description=f"New World Record!",
                color=random.randint(0, 0xffffff)
            )
            embed_msg.set_thumbnail(
                url="https://cdn.discordapp.com/avatars/206080696442159104/0fe4a7a12a729ca16a340eb4421cad15.webp?size=100")
            embed_msg.add_field(name=f"Player", value=f"{TMstr(wr[1]).string if wr[1] != '' else wr[2]}", inline=False)
            embed_msg.add_field(name=f"Achieved on", value=f"{wr[4]}", inline=False)
            embed_msg.add_field(name=f"WR found in", value=f"{wr[5]}", inline=False)
            try:
                await channel.send(embed=embed_msg)
            except Exception as e:
                self.logger.info(self._ready)
                if self._ready:  # this is a problem
                    self.logger.error(e)
                else:
                    # else for comment
                    # Exception might be raised because channel = None, but bot is not
                    # connected yet.
                    pass
        """
        holord = discord.utils.get(self.bot.emojis, name='HolyOverlord')
        noot = discord.utils.get(self.bot.emojis, name='LAnoot')
        pogs = discord.utils.get(self.bot.emojis, name='POGSLIDE')
        embed_msg = discord.Embed(
            title=f"{pogs} Some great Title",
            url="https://kacky.info",
            description=f"Text 1 {holord}",
            # color=0xfc03c6 pink
            color=random.randint(0, 0xffffff)
        )
        embed_msg.set_thumbnail(url="https://cdn.discordapp.com/avatars/206080696442159104/0fe4a7a12a729ca16a340eb4421cad15.webp?size=100")
        embed_msg.add_field(name=f"Info 2 {holord}", value=f"Extended Info 2{noot}", inline=False)
        embed_msg.add_field(name="Info 4", value="Extended Info 3", inline=True)
        embed_msg.add_field(name="Info 4", value="Extended Info 4", inline=True)
        embed_msg.set_footer(text=f"Brought to you by Yours Truly and {holord}", icon_url="https://cdn.discordapp.com/avatars/206080696442159104/0fe4a7a12a729ca16a340eb4421cad15.webp?size=20")
        try:
            await channel.send(embed=embed_msg)
        except Exception as e:
            self.logger.info(self._ready)
            if self._ready:         # this is a problem
                self.logger.error(e)
            else:
                # else for comment
                # Exception might be raised because channel = None, but bot is not
                # connected yet.
                pass
        """


async def setup(bot):
    with open(Path(__file__).parents[3] / "config.yaml") as c:
        config = yaml.load(c, yaml.FullLoader)
    with open(Path(__file__).parents[3] / "secrets.yaml") as s:
        secrets = yaml.load(s, yaml.FullLoader)

    await bot.add_cog(MyCog(bot, config, secrets))