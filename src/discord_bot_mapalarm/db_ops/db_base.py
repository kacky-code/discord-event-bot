import logging

import mariadb


class DBBaseConnection:
    def __init__(self, host, port, dbname, user, pwd, loggername):
        logger = logging.getLogger(loggername)
        # set up database connection to manage projects
        try:
            self.connection = mariadb.connect(
                host=host,
                port=port,
                user=user,
                passwd=pwd,
                database=dbname,
            )
        except mariadb.Error as e:
            logger.error(f"Connecting to database failed! {e}")
            raise e
        self.cursor = self.connection.cursor()
        self.logger = logger

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Exit hook, closes DB connection if object is destroyed

        Parameters
        ----------
        exc_type
        exc_val
        exc_tb
        """
        self.connection.close()

    def __enter__(self):
        """
        Required for "with" instantiation to work correctly
        """
        return self
