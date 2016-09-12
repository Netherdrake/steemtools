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


