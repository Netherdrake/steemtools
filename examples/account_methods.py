from steemtools.base import Account

account = Account("furion")

account.get_sp()
# outputs: 6211.590278675119

account.reputation()
# outputs: 62.76

blog = account.get_blog()
for post in blog[:3]:
    print(post['title'])
# outputs:
# A quick look at @null, and the profitability of Promoted Posts
# A quick look at the top curators and their rewards
# Homepage Payout Distribution, Power Law and Project Curie


# In[3]: Account('furion').get_conversion_requests()
# Out[3]:
#
# [{'amount': '1000.000 SBD',
#   'conversion_date': '2016-09-22T09:31:12',
#   'id': '2.15.7302',
#   'owner': 'furion',
#   'requestid': 1473931867}]


# In[4]: Account('furion').get_withdraw_routes()
# Out[4]:
#
# [{'auto_vest': True,
#   'from_account': 'ch0c0latechip',
#   'percent': 10000,
#   'to_account': 'furion'},