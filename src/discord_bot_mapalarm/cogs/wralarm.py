import logging
import random
from pathlib import Path

import discord
import yaml
from discord.ext import commands, tasks

from discord_bot_mapalarm.db_ops.wr_notification_check import WRNotification
from discord_bot_mapalarm.tm_string.tm_format_resolver import TMstr


class MyCog(commands.Cog, name="WRCog"):
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

        self.logger.info("Setting up WRCog")

        with open(Path(__file__).parents[3] / "secrets.yaml") as b:
            self.guild_id = yaml.load(b, yaml.FullLoader)["guild"]
        if self.guild_id == "":
            raise RuntimeError("Bad values in secrets.yaml!")

    def cog_unload(self):
        self.printer.cancel()
        self._ready = False

    def on_ready(self):
        self.logger.info("WRCog ready")
        self._ready = True

    @tasks.loop(seconds=1 * 60)
    async def printer(self):
        channel = self.bot.get_channel(self.config["wr_channel_id"])
        if channel is None:
            if self.printer.current_loop != 0 and not self._ready:
                self.logger.error(
                    "WR Notifier did fail, because bot is not connected to channel!"
                )
                return
            elif self.printer.current_loop == 0:
                # skip first iteration to give time for set up
                return
        self.logger.debug(f"Sending message to channel {channel}")

        wrnotifier = WRNotification(self.logger, self.config, self.secrets)
        new_wrs = wrnotifier.get_new_wr()
        if not new_wrs:
            self.logger.info("No new WR")

        pogs = discord.utils.get(self.bot.emojis, name="POGSLIDE")

        for wr in new_wrs:
            mapname = TMstr(wr[0])
            mapurl = (
                f"https://tmnf.exchange/trackshow/{wr[7]}"
                if "Kackiest" in mapname.string
                else f"https://trackmania.io/#/leaderboard/{wr[8]}"
            )
            embed_msg = discord.Embed(
                title=f"{pogs} {mapname.string} - {wr[3] / 1000}s {pogs}",
                url=mapurl,
                description="New World Record!",
                color=random.randint(0, 0xFFFFFF),
            )
            kackyid = mapname.string.split("#")[1].replace("\u2013", "-")
            thumbnail = (
                f"https://static.kacky.info/kk/thumbs/{kackyid}.jpg"
                if "Kackiest" in mapname.string
                else f"https://static.kacky.info/kr/thumbs/{kackyid.split(' ')[0]}.jpg"
            )
            embed_msg.set_thumbnail(url=thumbnail)
            self.logger.info(wr[1])
            embed_msg.add_field(
                name="Player",
                value=f"{TMstr(wr[1]).string if wr[1] != '' else wr[2]}",
                inline=False,
            )
            embed_msg.add_field(
                name="New WR Time", value=f"{wr[3] / 1000:.3f}s", inline=True
            )
            embed_msg.add_field(name="Diff", value=f"-{wr[6] / 1000:.3f}s", inline=True)
            embed_msg.add_field(name="\u200b", value="\u200b", inline=True)
            srcstr = "unknown"
            if wr[5] in ["KKDB", "KRDB"]:
                srcstr = "Online"
            if wr[5] == "TMX":
                srcstr = "TMX/MX"
            if wr[5] == "DEDI":
                srcstr = "Dedimania"
            if wr[5] == "NADO":
                srcstr = "Nadeo"
            embed_msg.add_field(
                name="Date",
                value=f"<t:{int(wr[4].timestamp())}:d><t:{int(wr[4].timestamp())}:t>"
                + " \u200b" * 10,
                inline=True,
            )
            embed_msg.add_field(name="Source", value=f"{srcstr}", inline=True)
            embed_msg.add_field(name="\u200b", value="\u200b", inline=True)
            guild = self.bot.get_guild(self.guild_id)
            cork_user = discord.utils.get(
                guild.members,
                name="corkscrew",
                discriminator="0874",
            )
            embed_msg.set_footer(
                text=f"Bot by {cork_user.display_name}",
                icon_url=cork_user.display_avatar.url,
            )

            firstfin_msg = None
            if wr[3] + wr[6] == 1800000:
                firstfin_msg = discord.Embed(
                    title=f"First Finish on {mapname.string}",
                    description=f"First Fin by {TMstr(wr[1]).string if wr[1] != '' else wr[2]}!",
                    color=random.randint(0, 0xFFFFFF),
                )
                firstfin_msg.set_footer(
                    text=f"Bot by {cork_user.display_name}",
                    icon_url=cork_user.display_avatar.url,
                )

            try:
                if firstfin_msg:
                    await channel.send(embed=firstfin_msg)
                await channel.send(embed=embed_msg)
            except Exception as e:
                self.logger.info("Exception when sending")
                self.logger.info(e)
                self.logger.info(self._ready)
                if self._ready:  # this is a problem
                    self.logger.error(e)
                else:
                    # else for comment
                    # Exception might be raised because channel = None, but bot is not
                    # connected yet.
                    pass

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        channel = await self.bot.fetch_channel(payload.channel_id)
        message = await channel.fetch_message(payload.message_id)
        user = await self.bot.fetch_user(payload.user_id)
        emoji = payload.emoji
        guild = self.bot.get_guild(self.guild_id)
        user_member = discord.utils.get(
            guild.members,
            name=user.name,
            discriminator=user.discriminator,
        )

        # [Kacky Krew, Kacky Jury, Contributor]
        deletion_roles = [615883012755947531, 833357930237132830, 683322616404246606]

        for role in user_member.roles:
            if role.id in deletion_roles and emoji.id == 1049783249964105729:
                self.logger.info(
                    f"User {user} deleted " f"message {message.embeds[0].fields}"
                )
                for admin in self.config["tm_server_admins"]:
                    um = discord.utils.get(
                        guild.members,
                        name=admin.split("#")[0],
                        discriminator=admin.split("#")[1],
                    )
                    mapname = message.embeds[0].title.split(" ")[1:5]
                    mapname = mapname if mapname[3] != "-" else mapname[0:3]
                    await um.send(
                        "Cheated WR Reported:\n"
                        f"- Player: {message.embeds[0].fields[0].value}\n"
                        f"- Map: {' '.join(mapname)}\n"
                        f"- Time: {message.embeds[0].fields[1].value}\n"
                        f"Pls remove or something!"
                    )
                await message.delete()


async def setup(bot):
    with open(Path(__file__).parents[3] / "config.yaml") as c:
        config = yaml.load(c, yaml.FullLoader)
    with open(Path(__file__).parents[3] / "secrets.yaml") as s:
        secrets = yaml.load(s, yaml.FullLoader)

    await bot.add_cog(MyCog(bot, config, secrets))
