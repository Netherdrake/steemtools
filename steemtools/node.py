import ssl

import websocket
from piston.steem import Steem


class Node(object):
    # this allows us to override the steam instance for all instances of Node
    # and therefore all users of Node().default()
    _default = None

    def __init__(self):
        self._nodes = {
            "local": ["ws://127.0.0.1:8090"],
            "public": ["wss://node.steem.ws", "wss://this.piston.rocks"],
        }

        self._apis = [
            "database_api",
            "login_api",
            "network_broadcast_api",
            "follow_api",
            "market_history_api",
            "tag_api",
        ]

    def default(self, **kwargs):
        """
        This will try local node first, and automatically fallback to public nodes.
        """
        if self._default:
            return self._default
        nodes = self.find_local_nodes() + self._nodes['public']
        return Steem(node=nodes, apis=self._apis, **kwargs)

    def public(self, **kwargs):
        return Steem(node=self._nodes['public'], apis=self._apis, **kwargs)

    def _prioritize(self, priority_node):
        return [priority_node].extend([x for x in self._nodes if x != priority_node])

    @staticmethod
    def find_local_nodes():
        local_nodes = []
        for node in ["ws://127.0.0.1:8090"]:
            if node[:3] == "wss":
                sslopt_ca_certs = {'cert_reqs': ssl.CERT_NONE}
                ws = websocket.WebSocket(sslopt=sslopt_ca_certs)
            else:
                ws = websocket.WebSocket()
            try:
                ws.connect(node)
                ws.close()
                local_nodes.append(node)
            except:
                ws.close()

        return local_nodes


# legacy method
def default():
    print("WARN: default() has been discontinued, please use Node().default() instead")
    return Node().default()
