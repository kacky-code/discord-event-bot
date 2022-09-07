import datetime
import logging
import random
from pathlib import Path

import discord
import requests
import yaml
from discord.ext import commands, tasks

from discord_bot_mapalarm.db_ops.alarm_checker import AlarmChecker


class MyCog(commands.Cog, name="AlarmsCog"):
    def __init__(self, bot, config, secrets, quotes=None):
        self.index = 0
        self.bot = bot
        self.config = config
        self.secrets = secrets
        self.quotes = quotes
        self.printer.start()
        self.logger = logging.getLogger(self.config["logger_name"])

        self.logger.info("Setting up Alarms Cog")

        with open(Path(__file__).parents[3] / "secrets.yaml") as b:
            self.guild_id = yaml.load(b, yaml.FullLoader)["guild"]
        if self.guild_id == "":
            raise RuntimeError("Bad values in secrets.yaml!")

    def cog_unload(self):
        self.printer.cancel()

    def on_ready(self):
        self.logger.info("mapalarm cog ready")

    @tasks.loop(seconds=60.0)
    async def printer(self):
        if self.index == 0:  # skip first execution, bot is not set up yet
            self.index += 1
            return

        # Skip, if competition has ended
        if datetime.datetime.now() > datetime.datetime.strptime(
            self.config["compend"], "%d.%m.%Y %H:%M"
        ):
            self.logger.warning("{AlarmsCog} Competition is over! No more alarms!")
            return

        guild = self.bot.get_guild(self.guild_id)

        # get next maps
        try:
            schedule_data = requests.get("https://api.kacky.info/dashboard").json()
        except requests.exceptions.ConnectionError:
            await self.notify_admin("Could not resolve Scheduler API!", guild)
            self.logger.error("Could not resolve Scheduler API!")
            return
        except requests.exceptions.JSONDecodeError:
            await self.notify_admin("Scheduler API did return malformed data!", guild)
            self.logger.error("Scheduler API did return malformed data!")
            return
        except Exception as e:
            await self.notify_admin(f"An unspecified Error occurred! {e}", guild)
            self.logger.error(f"An unspecified Error occurred! {e}")
            return

        servers = schedule_data["servers"]
        comptime = schedule_data["comptimeLeft"]
        ac = AlarmChecker(self.logger, self.config, self.secrets)

        if comptime < 0:
            # stop, competition is over!
            return

        for server in servers:
            servernum = server["serverNumber"]
            # get time limit and find when 10 min remain (else use timelimit)
            serv_timelimit = server["timeLimit"]
            nextmapin = server["timeLimit"] * 60 - (server["timeLimit"] * 60 - server["timeLeft"])
            if serv_timelimit > 10:
                alarm_mark = 60 * 10  # 10 min in s
            else:
                alarm_mark = (serv_timelimit - 1) * 60  # timelimit - 1min in s

            if alarm_mark + 30 > nextmapin > alarm_mark - 29:
                next_map = server["maps"][1]["number"]
                discord_ids_for_alarm = ac.get_discord_ids_for_map(next_map)

                for userid in discord_ids_for_alarm:
                    userid = userid[0]
                    self.logger.debug(f"processing {userid}")
                    try:
                        # user = await self.bot.fetch_user(userid)
                        user = discord.utils.get(
                            guild.members,
                            name=userid.split("#")[0],
                            discriminator=userid.split("#")[1],
                        )
                        self.logger.debug(f"user: {user}    {user.id}")
                        if user is None:
                            # bad user credentials
                            self.logger.error(f"ID {userid} is a bad Discord ID!")
                            continue
                        if self.quotes and random.randint(1, 100) < self.config["map_alarm_quotes_freq"]:
                            await user.send(
                                f"Hey, map **{next_map}** is coming up on **{servernum}**! "
                                f"Take this quote as motivation:\n"
                                f"> {random.choices(self.quotes)[0].strip()}"
                            )
                        else:
                            await user.send(
                                f"Hey, map **{next_map}** is coming up on **{servernum}**! "
                                f"Roughly 10 min until it's played, glhf!"
                            )
                    except discord.errors.HTTPException:
                        self.logger.error(f"ID {userid} is a bad Discord ID!")
                    except IndexError:
                        self.logger.error(f"ID {userid} has bad format (no '#')!")
                    except AttributeError:
                        self.logger.error(f"ID {userid} is a bad Discord ID!")
                    except Exception as e:
                        await self.notify_admin(
                            "Unkown Error :/ mapalarm.py threw Exception "
                            "in sending loop!",
                            guild,
                        )
                        self.logger.error(
                            f"Some error happened: {e}.\nLet's continue and hope "
                            f"this thing still works"
                        )

    async def notify_admin(self, errormsg, guild):
        if self.config["notify_admins_on_error"]:
            for admin in self.config["admins"]:
                try:
                    user = discord.utils.get(
                        guild.members,
                        name=admin.split("#")[0],
                        discriminator=admin.split("#")[1],
                    )
                    self.logger.debug(f"user: {user}    {user.id}")
                    if user is None:
                        # bad user credentials
                        self.logger.error(f"ID {admin} is a bad Discord ID!")
                        continue
                    await user.send(
                        f"Something is wrong with Kacky Alarm Bot! {errormsg}"
                    )
                except discord.errors.HTTPException:
                    self.logger.error(f"ID {admin} is a bad Discord ID!")
                except IndexError:
                    self.logger.error(f"ID {admin} has bad format (no '#')!")
                except AttributeError:
                    self.logger.error(f"ID {admin} is a bad Discord ID!")
                except Exception as e:
                    self.logger.error(
                        f"Some error happened: {e}.\nLet's continue and hope "
                        f"this thing still works"
                    )


async def setup(bot):
    with open(Path(__file__).parents[3] / "config.yaml") as c:
        config = yaml.load(c, yaml.FullLoader)
    with open(Path(__file__).parents[3] / "secrets.yaml") as s:
        secrets = yaml.load(s, yaml.FullLoader)
    quotes = None
    if config["map_alarm_quotes"]:
        with open(Path(__file__).parents[3] / "quotes.txt") as q:
            quotes = q.readlines()

    await bot.add_cog(MyCog(bot, config, secrets, quotes))
