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
### Pull Git

```
mkdir samynet
cd samynet
git init
git add .
git remote add origin https://github.com/dangell7/samy_ethereum.git
git fetch --all
git status
git checkout master
git add .
git merge origin/denis-fb-dev
virtualenv env
source env/bin/activate
pip install -U -r requirements.txt
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
chains/samynet/./run_chain.sh
```


Attach Geth to Server Test Chain

```
admin.addPeer("enode://6262793720579d5093b58aeb41ddbd88715c4dea0d5b935a6b2f13707d04c8cf7dd5cdf29a135b8d02ec7d320541b6e977b7e3c5db132e887eeecf1b2f662542@159.89.80.176:30302?discport=0")
admin.addPeer("enode://d7665c0591f816f2076bb05d219b31d6a756876b80fb9cab59e4a38b72725b5c8fd007bf953328b15a0479e07bc54c99bc4f875d5d5e5d55f5b524f51e39f5f7@159.89.80.176:30302?discport=0")
```


On Server

```
admin.nodeInfo.enode
```