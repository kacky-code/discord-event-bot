class WRNotification:
    def get_new_wr(self):
        query = "SELECT id FROM worldrecords_discord_notify WHERE notified = 0;"
        notify_ids = self.cursor.fetchall(query)
        # if result is empty list, return empty list
        if not notify_ids:
            return []

        # "else" we need to announce a new WR. collect data
        announcements = []
        for wr_id in notify_ids:
            query = "SELECT maps.name, wr.nickname, wr.login, wr.score, wr.date, wr.source " \
                    "FROM worldrecords AS wr " \
                    "LEFT JOIN maps " \
                    "ON wr.map_id = maps.id" \
                    "WHERE wr.id = ?;"
            announcements.append(self.cursor.fetchall(query, (wr_id, ))[0])
        return announcements
