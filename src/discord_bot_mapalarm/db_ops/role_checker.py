from discord_bot_mapalarm.db_ops.db_base import DBBaseConnection


class RoleChecker(DBBaseConnection):
    def __init__(self, config, secrets):
        super().__init__(config["kdbhost"], config["kdbport"], config["kdbname"], secrets["kdbuser"], secrets["kdbpwd"], config["logger_name"])

    def get_fins_count(self):
        query = """
            SELECT
                COUNT(DISTINCT challenge_uid) as fins,
                MAX(date) as lastfin,
                player_id,
                players.login
            FROM records
            INNER JOIN challenges ON records.challenge_uid = challenges.uid
            INNER JOIN players ON players.id = player_id
            WHERE edition = 8
            GROUP BY player_id
            ORDER BY fins DESC;
        """
        self.cursor.execute(query, ())
        return self.cursor.fetchall()