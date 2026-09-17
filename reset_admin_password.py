#!/usr/bin/env python3
# coding=utf-8

"""Local command-line tool for resetting an administrator password.

This module is intentionally standalone. It does not import the Flask
application and does not register any HTTP route. Run it directly on the
server from the application directory:

    python3 reset_admin_password.py

By default the SQLite database path is read from config.cfg. A database path
can also be supplied explicitly with --database when working with a copy of
the database.
"""

import argparse
import ast
from getpass import getpass
from pathlib import Path
import sqlite3
import sys

import bcrypt


def read_database_from_config(config_path):
    """Read the literal DATABASE assignment from Flask's config.cfg."""
    config_path = Path(config_path)
    try:
        source = config_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise RuntimeError("Kunde inte läsa {}: {}".format(config_path, exc))

    try:
        tree = ast.parse(source, filename=str(config_path))
    except SyntaxError as exc:
        raise RuntimeError("Kunde inte tolka {}: {}".format(config_path, exc))

    for statement in tree.body:
        if not isinstance(statement, ast.Assign):
            continue
        if not any(isinstance(target, ast.Name) and target.id == "DATABASE" for target in statement.targets):
            continue
        try:
            value = ast.literal_eval(statement.value)
        except (ValueError, TypeError):
            raise RuntimeError("DATABASE i {} måste vara ett strängvärde.".format(config_path))
        if not isinstance(value, str) or not value.strip():
            raise RuntimeError("DATABASE i {} saknar ett giltigt värde.".format(config_path))

        database_path = Path(value)
        if not database_path.is_absolute():
            database_path = config_path.parent / database_path
        return database_path.resolve()

    raise RuntimeError("Hittade ingen DATABASE-inställning i {}.".format(config_path))


def get_admins(connection):
    cursor = connection.cursor()
    cursor.execute(
        """
        SELECT seller_id, name, email
        FROM sellers
        WHERE lower(coalesce(isAdmin, '')) = 'yes'
        ORDER BY seller_id
        """
    )
    return cursor.fetchall()


def select_admin(admins):
    if not admins:
        raise RuntimeError("Det finns inga administratörskonton i databasen.")

    if len(admins) == 1:
        admin = admins[0]
        print("Administratör: {} - {} <{}>".format(admin[0], admin[1] or "", admin[2] or ""))
        return admin

    print("Administratörer:")
    for index, admin in enumerate(admins, start=1):
        print("  {}. {} - {} <{}>".format(index, admin[0], admin[1] or "", admin[2] or ""))

    while True:
        choice = input("Välj administratör (1-{}): ".format(len(admins))).strip()
        try:
            selected_index = int(choice)
        except ValueError:
            print("Ange numret på administratören.")
            continue

        if 1 <= selected_index <= len(admins):
            return admins[selected_index - 1]

        print("Välj ett nummer mellan 1 och {}.".format(len(admins)))


def read_new_password():
    while True:
        password = getpass("Nytt lösenord: ")
        if not password:
            print("Lösenordet får inte vara tomt.")
            continue

        confirmation = getpass("Bekräfta nytt lösenord: ")
        if password != confirmation:
            print("Lösenorden matchar inte. Försök igen.")
            continue

        return password


def reset_password(connection, seller_id, password):
    password_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
    cursor = connection.cursor()
    cursor.execute(
        "UPDATE sellers SET password = ? WHERE seller_id = ? AND lower(coalesce(isAdmin, '')) = 'yes'",
        (password_hash, seller_id),
    )
    if cursor.rowcount != 1:
        connection.rollback()
        raise RuntimeError("Lösenordet kunde inte uppdateras för vald administratör.")
    connection.commit()


def parse_args():
    script_dir = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(
        description="Återställ lösenordet för ett administratörskonto direkt i SQLite-databasen."
    )
    parser.add_argument(
        "--database",
        help="Sökväg till SQLite-databasen. Om den utelämnas läses DATABASE från config.cfg.",
    )
    parser.add_argument(
        "--config",
        default=str(script_dir / "config.cfg"),
        help="Sökväg till config.cfg (standard: %(default)s).",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    try:
        if args.database:
            database_path = Path(args.database).expanduser().resolve()
        else:
            database_path = read_database_from_config(args.config)

        if not database_path.is_file():
            raise RuntimeError("Databasen finns inte: {}".format(database_path))

        print("Databas: {}".format(database_path))

        connection = sqlite3.connect(str(database_path))
        try:
            admins = get_admins(connection)
            admin = select_admin(admins)
            password = read_new_password()
            reset_password(connection, admin[0], password)
        finally:
            connection.close()

        print("Lösenordet är återställt för {} (id {}).".format(admin[1] or admin[2] or "administratören", admin[0]))
        return 0
    except (RuntimeError, sqlite3.Error) as exc:
        print("Fel: {}".format(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
