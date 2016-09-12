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


def default():
    """
    This will try local node first, and automatically fallback to public node.
    :return:
    """
    return Steem(node=_nodes, apis=_apis)


def public():
    return Steem(node=_nodes[1])

