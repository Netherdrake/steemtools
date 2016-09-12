from piston.steem import Steem

_nodes = ["ws://127.0.0.1:8090", "wss://node.steem.ws"]
_apis = [
        "database_api",
        "login_api",
        "network_broadcast_api",
        "follow_api",
        "market_history_api",
        "tag_api",
]


def steem_default():
    return Steem(node=_nodes[0], apis=_apis)


def steem_light():
    return Steem(node=_nodes[1])


def steem_local():
    return Steem(node=_nodes[0],apis=_apis)
