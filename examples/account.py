from pprint import pprint

from steemtools.base import Account
from steemtools.helpers import parse_payout

for event in Account("furion").history(filter_by=["transfer"]):
    transfer = event['op']
    if transfer['to'] == "null":
        print("$%.1f :: %s" % (parse_payout(transfer['amount']), transfer['memo']))
