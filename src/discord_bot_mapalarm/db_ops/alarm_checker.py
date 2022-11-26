from src.discord_bot_mapalarm.db_ops.db_base import DBBaseConnection


class AlarmChecker(DBBaseConnection):
    def get_alarms_for_user(self, user):
        query = "SELECT alarms FROM user_fields WHERE id = ?;"
        self.cursor.execute(query, (user,))
        req = self.cursor.fetchone()
        if not req:  # no values
            return []
        alarmlist = req[0].split(";")
        return alarmlist

    def set_alarms_for_user(self, user, alarmlist):
        query = "UPDATE user_fields SET alarms = ? WHERE id = ?"
        self.cursor.execute(query, (";".join(alarmlist), user))
        self.connection.commit()

    def get_users_for_map(self, mapid):
        query = (
            "SELECT kack_users.username "
            "FROM kack_users "
            "LEFT JOIN user_fields uf ON kack_users.id = uf.id "
            "WHERE uf.alarms LIKE ?;"
        )
        req = self.cursor.execute(query, ("%" + str(mapid) + "%",)).fetchall()
        return req

    def get_discord_ids_for_map(self, mapid):
        query = "SELECT discord_handle FROM user_fields WHERE alarms LIKE ?;"
        self.cursor.execute(query, ("%" + str(mapid) + "%",))
        return self.cursor.fetchall()
