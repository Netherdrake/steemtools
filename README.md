## Install a node (optional)
mkdir ~/steem and put in config files

docker pull teego/steem-wallet

docker pull teego/steem-blockchain

docker create --name steem-blockchain teego/steem_blockchain /bin/true

docker run --name steem-wallet --rm -it --volumes-from steem-blockchain -v ~/steem/node.config.ini:/witness_node_data_dir/config.ini -p 8090:8090 -p 8091:8091 -p 8093:8093 -p 2001:2001 teego/steem-wallet /usr/local/bin/steemd --rpc-endpoint = 0.0.0.0:8090 

--replay

OR 

docker run --name steem-node --rm -it --volumes-from steem-blockchain -v ~/steem/node.config.ini:/witness_node_data_dir/config.ini -p 8090:8090 teego/steem-wallet
docker run --name steem-node --rm -it --volumes-from steem-blockchain -v ~/steem/witness.config.ini:/witness_node_data_dir/config.ini -p 8090:8090 teego/steem-wallet


run wallet:
docker exec -it steem-wallet /usr/local/bin/cli_wallet


## Install Piston
pip install git+git://github.com/xeroc/piston@master


pip install --upgrade --no-deps --force-reinstall  git+git://github.com/xeroc/piston@master
pip install --upgrade --no-deps --force-reinstall  git+git://github.com/xeroc/python-steemlib@master
pip install --upgrade --no-deps --force-reinstall  git+git://github.com/xeroc/python-graphenelib@master

pip install --upgrade --no-deps --force-reinstall  git+git://github.com/xeroc/piston@develop
pip install --upgrade --no-deps --force-reinstall  git+git://github.com/xeroc/python-steemlib@develop
pip install --upgrade --no-deps --force-reinstall  git+git://github.com/xeroc/python-graphenelib@develop