import logging
import os
import sys
from datetime import time, datetime
from typing import Set, Optional, List
import redis


def get_environment_args() -> dict:

    arguments = dict()

    try:
        arguments['TOKEN'] = os.environ["MENSTRUATION_TOKEN"].strip()
    except KeyError:
        print("Please specify bot token in variable MENSTRUATION_TOKEN.", file=sys.stderr)
        sys.exit(1)

    try:
        arguments['ENDPOINT'] = os.environ["MENSTRUATION_ENDPOINT"]
        if not arguments['ENDPOINT']:
            raise KeyError
    except KeyError:
        arguments['ENDPOINT'] = "http://127.0.0.1:80"

    try:
        arguments['REDIS_HOST'] = os.environ["MENSTRUATION_REDIS"]
    except KeyError:
        arguments['REDIS_HOST'] = "localhost"

    arguments['NOTIFICATION_TIME']: time = datetime.strptime(
        os.environ.get("MENSTRUATION_TIME", "09:00"), "%H:%M"
    ).time()

    try:
        arguments['MODERATORS'] = list((os.environ["MENSTRUATION_MODERATORS"]).split(","))
    except KeyError:
        arguments['MODERATORS'] = []

    arguments['DEBUG'] = "MENSTRUATION_DEBUG" in os.environ

    return arguments


def set_logging_level(is_debug):
    logging.basicConfig(
        level=logging.DEBUG if is_debug else logging.INFO
    )


class UserDatabase(object):

    def __init__(self, host: str) -> None:
        self.redis = redis.Redis(host, decode_responses=True)

    def allergens_of(self, user_id: int) -> Set[str]:
        value = self.redis.hget(str(user_id), "allergens")
        if value is not None:
            return set(value.split(","))
        else:
            return set()

    def set_allergens_for(self, user_id: int, allergens: Set[str]) -> None:
        self.redis.hset(str(user_id), "allergens", ",".join(allergens))

    def reset_allergens_for(self, user_id: int) -> None:
        self.redis.hdel(str(user_id), "allergens")

    def mensa_of(self, user_id: int) -> Optional[int]:
        value = self.redis.hget(str(user_id), "mensa")
        if value is not None:
            return int(value)
        else:
            return None

    def set_mensa_for(self, user_id: int, mensa_str: str) -> None:
        self.redis.hset(str(user_id), "mensa", mensa_str)

    def is_subscriber(self, user_id: int) -> bool:
        return self.redis.hget(str(user_id), "subscribed") == "yes"

    def set_subscription(self, user_id: int, subscribed: bool) -> None:
        self.redis.hset(str(user_id), "subscribed", "yes" if subscribed else "no")

    def menu_filter_of(self, user_id: int) -> Optional[str]:
        return self.redis.hget(str(user_id), "menu_filter")

    def set_menu_filter(self, user_id: int, menu_filter: str) -> None:
        self.redis.hset(str(user_id), "menu_filter", menu_filter)

    def users(self) -> List[int]:
        return [int(user_id_str) for user_id_str in self.redis.keys()]

    def remove_user(self, user_id: int) -> int:
        return self.redis.hdel(str(user_id), 'mensa', 'subscribed', 'menu_filter')


args = get_environment_args()

token: str = args['TOKEN']
endpoint: str = args['ENDPOINT']
redis_host: str = args['REDIS_HOST']
moderators: list = args['MODERATORS']
notification_time: time = args['NOTIFICATION_TIME']
debug: bool = args['DEBUG']
user_db = UserDatabase(redis_host)

set_logging_level(debug)
