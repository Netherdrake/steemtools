import stopwatch
from steemtools.node import Node
from steemtools.base import Account

# # default node overloading
# from steemtools.node import Node
#
# _apis = [
#     "database_api",
#     "login_api",
#     "network_broadcast_api",
#     "follow_api",
#     "market_history_api",
#     "tag_api",
# ]
# node.custom_node = Steem(
#      node=os.getenv('STEEM_NODE', "wss://node.steem.ws"),
#      apis=_apis,
#      expires=600,
# )



def benchmark_find_local_nodes_impact():

    sw = stopwatch.StopWatch()
    with sw.timer('connection_speed'):
        for i in range(100):
            with sw.timer('default'):
                Node().default()
        # for i in range(100):
        #     with sw.timer('preselected'):
        #         Node().default2()
    print(stopwatch.format_report(sw.get_last_aggregated_report()))

# self.find_local_nodes() does not significantly slow down default()
# ************************
# *** StopWatch Report ***
# ************************
# connection_speed        727.397ms (100%)
#                     default               100  391.350ms (54%)
#                     preselected           100  331.776ms (46%)
# Annotations:


def benchmark_steem_passtrough():
    sw = stopwatch.StopWatch()
    steem = Node().default()
    with sw.timer('connection_speed'):
        for i in range(1000):
            with sw.timer('default'):
                print(i)
                Account("furion")
        for i in range(1000):
            with sw.timer('passtrough'):
                Account("furion", steem=steem)
        # for i in range(100):
        #     with sw.timer('preselected'):
        #         Node().default2()
    print(stopwatch.format_report(sw.get_last_aggregated_report()))
# passing vs initiating a new doesn't make much difference
# ************************
# *** StopWatch Report ***
# ************************
# connection_speed        3054.388ms (100%)
#                     default              1000  1525.720ms (50%)
#                     passtrough           1000  1501.971ms (49%)
# Annotations: