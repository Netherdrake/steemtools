## Installation
```
pip install -U steemtools
```

## Documentation
[> Blockchain parsing, Posts and Accounts](https://steemit.com/steemtools/@furion/ann-steemtools-a-high-level-python-library-for-steem)  
[> Witness Fees and Markets](https://steemit.com/steem/@furion/witness-feed-publishing-with-automatic-sbd-usd-peg)  
[> Updating your Witness](https://steemit.com/witness-category/@furion/updating-you-witness-with-python)

## Examples
Please see [examples](https://github.com/Netherdrake/steemtools/tree/master/examples).

## 3rd party
[> Automatic failover for witnesses by @jesta](https://steemit.com/witness-category/@jesta/steemtools-automatic-failover-for-witness-nodes)


------------

## Known Issues
### Currently, a develop version of Piston is required
You can install it by running this after installing `steemtools`:
```
pip install --upgrade --no-deps --force-reinstall  git+git://github.com/xeroc/piston@develop
pip install --upgrade --no-deps --force-reinstall  git+git://github.com/xeroc/python-steemlib@develop
pip install --upgrade --no-deps --force-reinstall  git+git://github.com/xeroc/python-graphenelib@develop
```

### Websocket issue
If you run into this error:
```
ImportError: cannot import name 'create_connection'`
```

You need to reinstall websocket:
```
pip uninstall websocket
pip uninstall websocket-client
pip install websocket
pip install websocket-client
```

------------

## Install a local node (optional)
>Having a local node is highly recommended for blockchain parsing, or applications that need low latency/high reliability.

Pull the docker images:
```
docker pull teego/steem-wallet
docker pull teego/steem-blockchain
```

Initiate the blockchain image:
```
docker create --name steem-blockchain teego/steem-blockchain /bin/true
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