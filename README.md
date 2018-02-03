Install Forked Web3 Repo

```
pip install -e git+git://github.com/harpangell7/web3.py.git@master#egg=web3.py
```

## Populus Test Env

```
sudo apt-get install libssl-dev
sudo apt-get install software-properties-common
sudo add-apt-repository -y ppa:ethereum/ethereum
sudo apt-get update
sudo apt-get install ethereum
```

### Local Samy Chain

Create Local Test Chain

```
populus chain new samynet
```

Init Local Test Chain

```
chains/samynet/./init_chain.sh
```

Run Local Test Chain

```
chains/samy/./run_chain.sh
```

Run Production Test Chain

```
chains/samy/./run_prod_chain.sh
```

Attach Geth to Local Test Chain

```
geth attach /home/harpangell/PycharmProjects/samy/samy_ethereum/chains/samy/chain_data/geth.ipc
```

Attach Geth to Production Test Chain

```
geth attach /home/dorian/samynet/chains/samy/chain_data/geth.ipc
```

On Server

```
admin.nodeInfo.enode
```