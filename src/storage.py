
import mysql.connector
from mysql.connector import Error

from config import DB_CONFIG


def get_connection():
    """Create and return a MySQL database connection."""

    if not DB_CONFIG["password"]:
        raise ValueError(
            "MySQL password is missing. Check your .env file."
        )

    try:
        connection = mysql.connector.connect(**DB_CONFIG)

        if connection.is_connected():
            return connection

    except Error as error:
        raise RuntimeError(
            f"MySQL connection failed: {error}"
        ) from error
