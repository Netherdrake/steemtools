## Install a local node (optional)
Pull the docker images:
```
docker pull teego/steem-wallet
docker pull teego/steem-blockchain
```

Initiate the blockchain image:
```
docker create --name steem-blockchain teego/steem_blockchain /bin/true
```

Run our node:
```
docker run --name steem-node --rm -it --volumes-from steem-blockchain -v ~/steem/node.config.ini:/witness_node_data_dir/config.ini -p 8090:8090 teego/steem-wallet
```
*Note: You can find the `node.config.ini` in `steemtools/sample`.*

You can also pass custom parameters by appending this to the previous command:
```
/usr/local/bin/steemd --rpc-endpoint = 0.0.0.0:8090 --replay
```


Get into CLI Wallet (optional):
```
docker exec -it steem-wallet /usr/local/bin/cli_wallet
```


## Install Development branch of Piston (optional)

Casual:
`pip install steem-piston`

Master:
```
pip install --upgrade --no-deps --force-reinstall  git+git://github.com/xeroc/piston@master
pip install --upgrade --no-deps --force-reinstall  git+git://github.com/xeroc/python-steemlib@master
pip install --upgrade --no-deps --force-reinstall  git+git://github.com/xeroc/python-graphenelib@master
```

Develop:
```
pip install --upgrade --no-deps --force-reinstall  git+git://github.com/xeroc/piston@develop
pip install --upgrade --no-deps --force-reinstall  git+git://github.com/xeroc/python-steemlib@develop
pip install --upgrade --no-deps --force-reinstall  git+git://github.com/xeroc/python-graphenelib@develop
```