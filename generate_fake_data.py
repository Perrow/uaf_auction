# coding=utf-8

"""Populate a development auction database with fake sellers and posts."""

import argparse
import ast
import random
import sqlite3
import sys
import time
from pathlib import Path

import bcrypt

from faker import Faker


REQUIRED_TABLES = {"sellers", "posts", "used_types"}


def parse_args():
    parser = argparse.ArgumentParser(
        description="Lägg till fejksäljare och poster i utvecklingsdatabasen."
    )
    parser.add_argument(
        "--sellers",
        type=int,
        default=10,
        help="Antal nya säljare att skapa (standard: 10).",
    )
    parser.add_argument(
        "--posts",
        type=int,
        default=100,
        help="Antal nya poster att skapa (standard: 100).",
    )
    parser.add_argument(
        "--config",
        default="config.cfg",
        help="Sökväg till config.cfg (standard: config.cfg).",
    )
    parser.add_argument(
        "--seed",
        type=int,
        help="Valfritt seed-värde för reproducerbar fejkgenerering.",
    )
    return parser.parse_args()


def get_database_from_config(config_path):
    """Read only the DATABASE assignment from a Flask-style config file."""
    config_path = Path(config_path).expanduser().resolve()
    if not config_path.is_file():
        raise RuntimeError("Configfilen hittades inte: {}".format(config_path))

    try:
        tree = ast.parse(config_path.read_text(encoding="utf-8"), filename=str(config_path))
    except (OSError, SyntaxError) as exc:
        raise RuntimeError("Kunde inte läsa configfilen: {}".format(exc)) from exc

    database_value = None
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        if not any(isinstance(target, ast.Name) and target.id == "DATABASE" for target in node.targets):
            continue
        try:
            database_value = ast.literal_eval(node.value)
        except (ValueError, TypeError, SyntaxError) as exc:
            raise RuntimeError("DATABASE i config.cfg måste vara en vanlig textsträng.") from exc
        break

    if not isinstance(database_value, str) or not database_value.strip():
        raise RuntimeError("DATABASE saknas i {}.".format(config_path))

    database_path = Path(database_value).expanduser()
    if not database_path.is_absolute():
        database_path = config_path.parent / database_path
    return database_path.resolve()


def validate_database(conn):
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = {row[0] for row in cur.fetchall()}
    missing = REQUIRED_TABLES - tables
    if missing:
        raise RuntimeError(
            "Databasen saknar nödvändiga tabeller: {}".format(
                ", ".join(sorted(missing))
            )
        )

    cur.execute("SELECT type_id, description, sale_type FROM used_types ORDER BY type_id")
    used_types = cur.fetchall()
    if not used_types:
        raise RuntimeError("Det finns inga aktiva godstyper i used_types.")
    return used_types


def make_unique_email(conn, email):
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM sellers WHERE lower(email) = lower(?) LIMIT 1", (email,))
    if cur.fetchone() is None:
        return email

    local_part, separator, domain = email.partition("@")
    if not separator:
        local_part = email
        domain = "mail.com"

    counter = 1
    while True:
        candidate = "{}+fake{}@{}".format(local_part, counter, domain)
        cur.execute(
            "SELECT 1 FROM sellers WHERE lower(email) = lower(?) LIMIT 1",
            (candidate,),
        )
        if cur.fetchone() is None:
            return candidate
        counter += 1


def create_sellers(conn, fake, count):
    created = []
    cur = conn.cursor()

    for _ in range(count):
        generated = fake.generate_seller()
        name = generated[0]
        address = generated[1]
        email = make_unique_email(conn, generated[2])
        phone = generated[3]
        aquarium_club = generated[4]
        password = generated[6]
        password_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())

        cur.execute(
            """
            INSERT INTO sellers (
                name, address, email, phone, aquarium_club, password, isAdmin,
                time_stamp, accepts_cookies, accepts_database, has_checked_in,
                is_closed
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                name,
                address,
                email,
                phone,
                aquarium_club,
                password_hash,
                "no",
                time.strftime("%Y-%m-%d %H:%M:%S"),
                "yes",
                "yes",
                "no",
                "no",
            ),
        )
        created.append((cur.lastrowid, name, email, password))

    return created


def generate_post_values(fake, seller_id, used_type):
    type_id, description, sale_type = used_type
    quantity = random.randint(1, 10)
    minimum_price = None
    fixed_price = None

    description_lower = (description or "").lower()
    if "växt" in description_lower or "plant" in description_lower:
        plain_name, scientific_name = fake.get_plant_name()
        comment = fake.get_plant_comment() or ""
    elif "räk" in description_lower or "shrimp" in description_lower:
        plain_name, scientific_name = fake.get_shrimp_name()
        comment = fake.get_animal_comment() or ""
    else:
        scientific_name, plain_name = fake.get_fish_name()
        comment = fake.get_animal_comment() or ""

    if sale_type == "fixed_price":
        fixed_price = random.randint(1, 10) * 10
    else:
        if random.randint(0, 100) < 35:
            minimum_price = random.randint(1, 10) * 10

    return (
        seller_id,
        scientific_name,
        plain_name,
        quantity,
        comment,
        type_id,
        minimum_price,
        fixed_price,
        time.strftime("%Y-%m-%d %H:%M:%S"),
        "no",
        "no",
        "no",
    )


def create_posts(conn, fake, sellers, used_types, count):
    cur = conn.cursor()
    seller_ids = [seller[0] for seller in sellers]

    for index in range(count):
        # Round-robin gives every generated seller posts even for small data sets.
        seller_id = seller_ids[index % len(seller_ids)]
        used_type = random.choice(used_types)
        values = generate_post_values(fake, seller_id, used_type)
        cur.execute(
            """
            INSERT INTO posts (
                seller_id, scientific_name, plain_name, quantity, description,
                type, minimum_price, fixed_price, time_stamp_registration,
                label_printed, is_checked_in, is_closed
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            values,
        )


def main():
    args = parse_args()
    if args.sellers < 0 or args.posts < 0:
        raise RuntimeError("--sellers och --posts får inte vara negativa.")
    if args.posts > 0 and args.sellers == 0:
        raise RuntimeError("Minst en ny säljare krävs när --posts är större än 0.")

    if args.seed is not None:
        random.seed(args.seed)

    database_path = get_database_from_config(args.config)
    if not database_path.is_file():
        raise RuntimeError("Databasfilen hittades inte: {}".format(database_path))

    fake = Faker()
    with sqlite3.connect(str(database_path)) as conn:
        used_types = validate_database(conn)
        sellers = create_sellers(conn, fake, args.sellers)
        if args.posts:
            create_posts(conn, fake, sellers, used_types, args.posts)
        conn.commit()

    print("Databas: {}".format(database_path))
    print("Skapade {} säljare och {} poster.".format(len(sellers), args.posts))
    if sellers:
        print("\nInloggningsuppgifter för skapade säljare:")
        for seller_id, name, email, password in sellers:
            print("  {:>4}  {}  {}  lösenord: {}".format(seller_id, name, email, password))


if __name__ == "__main__":
    try:
        main()
    except (RuntimeError, sqlite3.Error) as exc:
        print("Fel: {}".format(exc), file=sys.stderr)
        sys.exit(1)
