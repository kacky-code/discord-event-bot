from discord_bot_mapalarm.db_ops.db_base import DBBaseConnection


class WRNotification(DBBaseConnection):
    # def __init__(self, logger, config, secrets):
    # def __init__(self, *args):
    # super().__init__(logger, config, secrets)
    #    super(WRNotification, self).__init__(*args)

    def get_new_wr(self):
        query = "SELECT id FROM worldrecords_discord_notify WHERE notified = 0;"
        self.cursor.execute(query)
        notify_ids = self.cursor.fetchall()
        # if result is empty list, return empty list
        if not notify_ids:
            return []

        # "else" we need to announce a new WR. collect data
        announcements = []
        for wr_id in notify_ids:
            query = (
                "SELECT maps.name, wr.nickname, wr.login, wr.score, wr.date, "
                "wr.source, wr_not.time_diff, maps.tmx_id, maps.tm_uid "
                "FROM worldrecords AS wr "
                "LEFT JOIN maps "
                "ON wr.map_id = maps.id "
                "LEFT JOIN worldrecords_discord_notify AS wr_not "
                "ON wr.id = wr_not.id "
                "WHERE wr.id = ?;"
            )
            self.cursor.execute(query, wr_id)
            announcements.append(self.cursor.fetchall()[0])
            self.cursor.execute(
                "UPDATE worldrecords_discord_notify SET notified = 1 WHERE id = ?",
                wr_id,
            )
            self.connection.commit()
        return announcements
