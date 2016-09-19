from pprint import pprint

from steemtools.base import Account
from steemtools.helpers import parse_payout, is_comment

# get all posts from August
account = Account("furion")
START_DATE = "2016-08-01T00:00:00"
END_DATE = "2016-09-01T00:00:00"

# get posts and comments from August
Account.filter_by_date(account.history(filter_by="comment"), START_DATE, END_DATE)

# get just the titles of only posts from August
print([x['op']['title'] for x in Account.filter_by_date(account.history(filter_by="comment"), START_DATE, END_DATE) if
       not is_comment(x['op'])])

for event in Account("furion").history(filter_by=["transfer"]):
    transfer = event['op']
    if transfer['to'] == "null":
        print("$%.1f :: %s" % (parse_payout(transfer['amount']), transfer['memo']))
