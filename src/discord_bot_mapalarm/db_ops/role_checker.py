from discord_bot_mapalarm.db_ops.db_base import DBBaseConnection


class RoleChecker(DBBaseConnection):
    def __init__(self, config, secrets):
        super().__init__(
            config["kdbhost"],
            config["kdbport"],
            config["kdbname"],
            secrets["kdbuser"],
            secrets["kdbpwd"],
            config["logger_name"],
        )

    def get_fins_count(self):
        query = """
            SELECT
                COUNT(DISTINCT t.challenge_id) as fins,
                MAX(t.date) as lastfin,
                t.player_id,
                p.login
            FROM times as t
            INNER JOIN challenges as c ON t.challenge_id = c.id
            INNER JOIN players as p ON p.id = t.player_id
            WHERE c.edition = 8 AND t.server_id IN (1,22,23,24,25,62)
            GROUP BY t.player_id
            ORDER BY fins DESC;
        """
        self.cursor.execute(query, ())
        return self.cursor.fetchall()
