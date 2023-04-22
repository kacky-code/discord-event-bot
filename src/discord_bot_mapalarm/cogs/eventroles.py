import datetime
import logging
from pathlib import Path

import discord
import yaml
from discord.ext import commands, tasks

from discord_bot_mapalarm.db_ops.role_checker import RoleChecker


class MyCog(commands.Cog, name="EventrolesCog"):
    def __init__(self, bot, config, secrets):
        self._ready = False
        self.bot = bot
        self.config = config
        self.secrets = secrets
        self.logger = logging.getLogger(self.config["logger_name"])
        self._last_check = datetime.datetime.utcnow()

        self.logger.info("Setting up EventrolesCog")

        with open(Path(__file__).parents[3] / "secrets.yaml") as b:
            self.guild_id = yaml.load(b, yaml.FullLoader)["guild"]
        if self.guild_id == "":
            raise RuntimeError("Bad values in secrets.yaml!")

        with open(Path(__file__).parents[3] / "discord_tm_rel.yaml", "r") as dtmr:
            self.discord_users = yaml.load(dtmr, yaml.FullLoader)
            if self.discord_users is None:
                self.discord_users = {}

        self.printer.start()

    def cog_unload(self):
        self.printer.cancel()
        self._ready = False

    def on_ready(self):
        self.logger.info("EventrolesCog ready")
        self._ready = True

    def check_reply_to_bot(self, msg):
        if (
            msg.reference and msg.author != self.bot.user
        ):  # and msg.reference.resolved.author == self.bot.user:
            return True
        return False

    @commands.Cog.listener()
    async def on_message(self, message):
        if not message.channel.id == self.config["event_roles_channel_id"]:
            return
        if not self.check_reply_to_bot(message):
            # message is not a reply. delete
            await message.delete()
            return
        guild = self.bot.get_guild(self.guild_id)
        # todo: check message content
        rank_member = guild.get_member(int(message.content[2:-1]))
        # bronze, silver, gold, kacky
        event_roles = [
            920474813246627841,
            859891083789074435,
            859891619821912104,
            878646582839480361,
        ]
        # event_roles = [860857854482579518, 860855067380940811, 867881172957003796]
        tmlogin = " ".join(
            message.reference.resolved.embeds[0].description.split(" ")[2:]
        )
        self.logger.debug(f"working on tmlogin: {tmlogin}")
        with open(Path(__file__).parents[3] / "discord_tm_rel.yaml", "a+") as dtmr:
            self.logger.debug(self.discord_users)
            if self.discord_users is not {} and tmlogin not in self.discord_users:
                self.discord_users[tmlogin] = {
                    "discord_user": str(rank_member),
                    "snowflake": rank_member.id,
                }
                yaml.dump(
                    {
                        tmlogin: {
                            "discord_user": str(rank_member),
                            "snowflake": rank_member.id,
                        }
                    },
                    dtmr,
                )
            else:
                self.logger.error(
                    f"{tmlogin} already exists in discord_user dict! {self.discord_users[tmlogin]}"
                )
                # raise AssertionError(f"{tmlogin} already exists in discord_user dict!")
        # we can assume this happens when a user has no event rank yet.
        # still, double check to be safe
        common_elements = [
            role for role in event_roles if role in [r.id for r in rank_member.roles]
        ]
        if common_elements:
            channel = self.bot.get_channel(self.config["event_roles_channel_id"])
            await channel.send(
                f"{str(rank_member)} already has an event role. I've stored the tm login and "
                "discord name, but I need you to fix their roles. Thank you for your cooperation."
            )
            return
        await rank_member.add_roles(guild.get_role(event_roles[0]))
        # change tmlogin to discord name in message
        upd_embed = message.reference.resolved.embeds[0]
        upd_embed.description = f"Congratulations to {rank_member.mention}"
        await message.reference.resolved.edit(embed=upd_embed)
        await message.delete()
        # await rank_user.remove_roles(guild.get_role(test_role[0]))

    @tasks.loop(seconds=1 * 60)
    async def printer(self):
        checker = RoleChecker(self.config, self.secrets)
        fins = checker.get_fins_count()
        newfins = [f for f in fins if f[1] > self._last_check]
        self._last_check = datetime.datetime.utcnow()

        for fin in newfins:
            # check if last fin happened after last check
            self.logger.debug(f"checking fin {fin}")
            if fin[0] in [50, 40, 25, 15]:
                # might have a rank change
                self.logger.debug(f"updating {fin}")
                await self.send_rank_msg(fin)
                self.logger.debug("awaited sending")
            # no rank change needed
        return

    async def send_rank_msg(self, fin_info):
        channel = self.bot.get_channel(self.config["event_roles_channel_id"])
        if channel is None:
            if self.printer.current_loop != 0 and not self._ready:
                self.logger.error(
                    "Eventrole Cog did fail because bot is not connected to channel!"
                )
                return
            elif self.printer.current_loop == 0:
                # skip first iteration to give time for set up
                return

        ranks = {
            50: ["Kacky", 0xA000FF],
            40: ["Gold", 0xEFB310],
            25: ["Silver", 0xAACEE3],
            15: ["Bronze", 0xB06050],
        }

        # bronze, silver, gold, kacky
        event_roles = [
            920474813246627841,
            859891083789074435,
            859891619821912104,
            878646582839480361,
        ]
        # event_roles = [860857854482579518, 860855067380940811, 867881172957003796]

        tmlogin = fin_info[3]
        guild = self.bot.get_guild(self.guild_id)
        self.logger.debug(tmlogin)
        # check if we know this tmlogin and the user's roles
        if tmlogin in self.discord_users:
            self.logger.debug("known login")
            user = discord.utils.get(
                guild.members,
                name=self.discord_users[tmlogin]["discord_user"].split("#")[0],
                discriminator=self.discord_users[tmlogin]["discord_user"].split("#")[1],
            )
            # await user.remove_roles(guild.get_role(event_roles[1]))
            # return
            user_roles = [r.id for r in user.roles]
            self.logger.debug(user_roles)

            # check if change of role is needed
            if (
                (event_roles[0] in user_roles and fin_info[0] == 15)
                or (event_roles[1] in user_roles and fin_info[0] == 25)
                or (event_roles[2] in user_roles and fin_info[0] == 40)
                or (event_roles[3] in user_roles and fin_info[0] == 50)
            ):
                # user finished a map they already had, nothing to do
                self.logger.debug("user already has correct role.")
                return

            #
            if event_roles[0] in user_roles and fin_info[0] == 25:
                self.logger.debug("upgrading bronze to silver")
                oldrole = event_roles[0]
                newrole = event_roles[1]
            elif event_roles[1] in user_roles and fin_info[0] == 40:
                oldrole = event_roles[1]
                newrole = event_roles[2]
                self.logger.debug("upgrading silver to gold")
            elif event_roles[2] in user_roles and fin_info[0] == 50:
                oldrole = event_roles[2]
                newrole = event_roles[3]
            else:
                oldrole = None
                newrole = event_roles[0]
                self.logger.debug("no role yet, giving bronze")

        if tmlogin in self.discord_users:
            user = discord.utils.get(
                guild.members,
                name=self.discord_users[tmlogin]["discord_user"].split("#")[0],
                discriminator=self.discord_users[tmlogin]["discord_user"].split("#")[1],
            )
            name = user.mention
            self.logger.debug(f"known login, giving {name} role {newrole}")
            if oldrole:
                await user.remove_roles(guild.get_role(oldrole))
            await user.add_roles(guild.get_role(newrole))
        else:
            name = tmlogin

        embed_msg = discord.Embed(
            title=f"New {ranks[fin_info[0]][0]} Andy!",
            description=f"Congratulations to {name}",
            color=ranks[fin_info[0]][1],
        )

        if fin_info[0] == 15:
            medal = "bronze"
        elif fin_info[0] == 25:
            medal = "silver"
        elif fin_info[0] == 40:
            medal = "gold"
        elif fin_info[0] == 50:
            medal = "cattoilettophant"
        medal = "https://static.kacky.info/misc/" + medal + ".jpg"
        embed_msg.set_thumbnail(url=medal)

        cork_user = discord.utils.get(
            guild.members,
            name="corkscrew",
            discriminator="0874",
        )

        embed_msg.set_footer(
            text=f"Bot by {cork_user.display_name}",
            icon_url=cork_user.display_avatar.url,
        )
        try:
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


async def setup(bot):
    with open(Path(__file__).parents[3] / "config.yaml") as c:
        config = yaml.load(c, yaml.FullLoader)
    with open(Path(__file__).parents[3] / "secrets.yaml") as s:
        secrets = yaml.load(s, yaml.FullLoader)

    await bot.add_cog(MyCog(bot, config, secrets))
