import json
import web3

from web3 import Web3, HTTPProvider, TestRPCProvider
from solc import compile_source, compile_files
from web3.contract import ConciseContract

import time
from datetime import datetime

import redis
import os
import bcrypt

pool = redis.ConnectionPool(host='localhost', port=6379, db=5)
redis_db = redis.Redis(connection_pool=pool)

from ast import literal_eval

w3 = Web3(HTTPProvider('http://localhost:8545'))


###
# Account Management
###

def create_account(passphrase=None):
    acct = w3.eth.account.create()
    encrypted = w3.eth.account.encrypt(acct.privateKey, passphrase)
    string_time = datetime.fromtimestamp(time.time()).strftime('UTC--%Y-%m-%dT%H-%M-%S.%fZ')
    key_name = '%s--%s' % (string_time, acct.address[2:])
    with open('chains/samy/chain_data/keystore/%s' % key_name, 'w') as f:
        f.write(json.dumps(encrypted))

    return acct.address


def decrypt_account(address=None, passphrase=None):
    print('Decrypting Address: %s' % address)
    for file_name in os.listdir("chains/samy/chain_data/keystore/"):
        data = file_name.split('--')
        file_address = data[-1]
        if address[2:] == file_address:
            data = open('chains/samy/chain_data/keystore/%s' % file_name)
            encrypted = json.load(data)
            return w3.eth.account.decrypt(encrypted, passphrase)


def unlock_account(address=None, passphrase=None):
    print('Unlocking Address: %s' % address)
    return w3.personal.unlockAccount(address, passphrase)


def lock_account(address=None):
    print('Locking Address: %s' % address)
    return w3.personal.lockAccount(address)


###
# Testing Samy Token Contract Deployment
###

# SAMY Token Contract
# TODO
# [START SAMY Token Contract]
samy_compiled_sol = compile_files(['contracts/SamyToken.sol'])  # Compiled source code
samy_contract_interface = samy_compiled_sol['contracts/SamyToken.sol:SamyToken']
samy_contract = w3.eth.contract(abi=samy_contract_interface['abi'], bytecode=samy_contract_interface['bin'])

_initialSupply = 100000000


# [END SAMY Token Contract]


###
# Testing Founder Contract Deployment
###

# Founder Token Contract
# TODO
# [START Founder Token Contract]
founder_compiled_sol = compile_files(['contracts/TokenVesting.sol'])  # Compiled source code
founder_contract_interface = founder_compiled_sol['contracts/TokenVesting.sol:TokenVesting']
founder_contract = w3.eth.contract(abi=founder_contract_interface['abi'], bytecode=founder_contract_interface['bin'])


# [END Founder Token Contract]

def create_founder_accounts():
    founder1passphrase = 'Founder1'
    founder1_address = create_account(founder1passphrase)
    print(founder1_address)

    founder2passphrase = 'Founder2'
    founder2_address = create_account(founder2passphrase)
    print(founder2_address)

    founder3passphrase = 'Founder3'
    founder3_address = create_account(founder3passphrase)
    print(founder3_address)


def deploy_founders(founders=None):
    r = redis_db.get('SAMYToken')
    r = r.decode('utf8')
    r = literal_eval(r)
    samy_token_address = r['address']

    i = 0
    for founder in founders:
        i += 1
        try:
            _beneficiary = founder
            _start = int(time.time())
            _cliff = int(60)
            _duration = int(120)
            _revocable = True

            tx_hash = founder_contract.deploy(args=(_beneficiary,
                                                    _start,
                                                    _cliff,
                                                    _duration,
                                                    _revocable),
                                              transaction={'from': w3.eth.coinbase, 'gas': 600000000})

            while w3.eth.getTransactionReceipt(tx_hash) == None:
                time.sleep(5)
                print('Waiting To Verify Transaction')

            tx_receipt = w3.eth.getTransactionReceipt(tx_hash)

            contract_address = tx_receipt['contractAddress']

            print('Founder Contract Address: {}'.format(contract_address))

            data = {
                'address': contract_address
            }
            redis_db.set('Founder%s' % i, data)

        except Exception as e:
            print(e)
            break


def fund_founders(founders=None):
    r = redis_db.get('SAMYToken')
    r = r.decode('utf8')
    r = literal_eval(r)
    samy_token_address = r['address']

    i = 0
    for founder in founders:
        try:
            i += 1
            r = redis_db.get('Founder%s' % i)
            r = r.decode('utf8')
            r = literal_eval(r)
            founder_address = r['address']

            _amount = int(_initialSupply * .10)
            _amount = Web3.toWei(_amount, 'ether')
            _amount = int(_amount / 3)

            samy_contract_instance = w3.eth.contract(samy_token_address, abi=samy_contract_interface['abi'])

            samy_contract_instance.functions.transfer(founder_address, _amount).transact(
                {'from': w3.eth.coinbase, 'gas': 60000000})

        except Exception as e:
            print(e)
            break


def test_founders(founders=None):
    r = redis_db.get('SAMYToken')
    r = r.decode('utf8')
    r = literal_eval(r)
    samy_token_address = r['address']

    i = 0
    for founder in founders:
        i += 1
        r = redis_db.get('Founder%s' % i)
        r = r.decode('utf8')
        r = literal_eval(r)
        founder_address = r['address']

        samy_contract_instance = w3.eth.contract(samy_token_address, abi=samy_contract_interface['abi'])

        founder_contract_instance = w3.eth.contract(founder_address, abi=founder_contract_interface['abi'])

        start = founder_contract_instance.functions.start().call()
        start_date = datetime.fromtimestamp(float(start)).strftime('UTC-%Y-%m-%dT%H-%M-%S.%fZ')
        cliff = founder_contract_instance.functions.cliff().call()
        cliff_date = datetime.fromtimestamp(float(cliff)).strftime('UTC-%Y-%m-%dT%H-%M-%S.%fZ')
        duration = founder_contract_instance.functions.duration().call() + start
        end_date = datetime.fromtimestamp(float(duration)).strftime('UTC-%Y-%m-%dT%H-%M-%S.%fZ')

        print('Current Datetime: %s' % datetime.fromtimestamp(float(time.time())).strftime('UTC-%Y-%m-%dT%H-%M-%S.%fZ'))

        print('Founder %s Contract Vesting Start Datetime: %s' % (i, start_date))
        print('Founder %s Contract Vesting Cliff Datetime: %s' % (i, cliff_date))
        print('Founder %s Contract Vesting End Datetime: %s' % (i, end_date))

        balance = samy_contract_instance.functions.balanceOf(founder_address).call()
        balance = Web3.fromWei(balance, 'ether')
        print('Founder %s Contract SAMY Token Balance: %s' % (i, balance))

        balance = founder_contract_instance.functions.releasableAmount(samy_token_address).call()
        balance = Web3.fromWei(balance, 'ether')
        print('Founder %s Contract Releaseable Amount: %s' % (i, balance))

        balance = w3.eth.getBalance(founder_address)
        balance = Web3.fromWei(balance, 'ether')
        print('Founder %s Contract Eth Balance: %s' % (i, balance))

        balance = samy_contract_instance.functions.balanceOf(founder).call()
        balance = Web3.fromWei(balance, 'ether')
        print('Founder %s Wallet SAMY Token Balance: %s' % (i, balance))

        balance = w3.eth.getBalance(founder)
        balance = Web3.fromWei(balance, 'ether')
        print('Founder %s Wallet Eth Balance: %s' % (i, balance))


def release_founders(founders=None):
    r = redis_db.get('SAMYToken')
    r = r.decode('utf8')
    r = literal_eval(r)
    samy_token_address = r['address']

    i = 0
    for founder in founders:
        try:
            i += 1
            r = redis_db.get('Founder%s' % i)
            r = r.decode('utf8')
            r = literal_eval(r)
            founder_address = r['address']

            founder_contract_instance = w3.eth.contract(founder_address, abi=founder_contract_interface['abi'])

            founder_contract_instance.functions.release(samy_token_address).transact(
                {'from': w3.eth.coinbase, 'gas': 6000000})
        except Exception as e:
            print(e)
            break


def revoke_founders(founders=None):
    r = redis_db.get('SAMYToken')
    r = r.decode('utf8')
    r = literal_eval(r)
    samy_token_address = r['address']

    i = 0
    for founder in founders:
        try:
            i += 1
            r = redis_db.get('Founder%s' % i)
            r = r.decode('utf8')
            r = literal_eval(r)
            founder_address = r['address']

            founder_contract_instance = w3.eth.contract(founder_address, abi=founder_contract_interface['abi'])

            founder_contract_instance.functions.revoke(samy_token_address).transact(
                {'from': w3.eth.coinbase, 'gas': 6000000})
        except Exception as e:
            print(e)
            break


###
# Testing Crowdfunding Contract Deployment
###

# Crowdsale Contract
# TODO
# [START Crowdsale Contract]

crowdsale_compiled_sol = compile_files(['contracts/Crowdsale.sol'])
crowdsale_contract_interface = crowdsale_compiled_sol['contracts/Crowdsale.sol:Crowdsale']
crowdsale_contract = w3.eth.contract(abi=crowdsale_contract_interface['abi'],
                                     bytecode=crowdsale_contract_interface['bin'])


# [END Crowdsale Contract]

def test_beneficiary(beneficiary=None):
    r = redis_db.get('SAMYToken')
    r = r.decode('utf8')
    r = literal_eval(r)
    samy_token_address = r['address']

    samy_token_contract_instance = w3.eth.contract(samy_token_address, abi=samy_contract_interface['abi'])

    balance = samy_token_contract_instance.functions.balanceOf(beneficiary).call()
    balance = Web3.fromWei(balance, 'ether')
    print('Beneficiary Account SAMY Token Balance: %s' % balance)

    balance = w3.eth.getBalance(beneficiary)
    balance = Web3.fromWei(balance, 'ether')
    print('Beneficiary Account Eth Balance: %s' % balance)


def deploy_crowdsale(beneficiary=None):
    r = redis_db.get('SAMYToken')
    r = r.decode('utf8')
    r = literal_eval(r)
    samy_token_address = r['address']

    _rate = 10000

    _fundingGoal = 20
    _fundingGoal = Web3.toWei(_fundingGoal, 'ether')

    _durationMinutes = 2
    # _durationMinutes = 20160

    _bonus_start = int(time.time())
    # _bonus_start = 1
    _bonus_end = int(time.time() + 60)
    # _bonus_end = 1
    _bonus = 10

    tx_hash = crowdsale_contract.deploy(args=(beneficiary,
                                              _fundingGoal,
                                              _durationMinutes,
                                              _rate,
                                              _bonus_start,
                                              _bonus_end,
                                              _bonus,
                                              samy_token_address),
                                        transaction={'from': w3.eth.coinbase, 'gas': 4000000})

    while w3.eth.getTransactionReceipt(tx_hash) == None:
        time.sleep(5)
        print('Waiting To Verify Transaction')

    tx_receipt = w3.eth.getTransactionReceipt(tx_hash)
    contract_address = tx_receipt['contractAddress']

    print('SAMY Crowdsale Contract Address: {}'.format(contract_address))

    data = {
        'address': contract_address
    }
    redis_db.set('Crowdsale', data)


def fund_crowdsale():
    r = redis_db.get('SAMYToken')
    r = r.decode('utf8')
    r = literal_eval(r)
    samy_token_address = r['address']

    r = redis_db.get('Crowdsale')
    r = r.decode('utf8')
    r = literal_eval(r)
    crowdsale_address = r['address']

    _amount = int(_initialSupply * .40)
    _amount = Web3.toWei(_amount, 'ether')

    try:

        crowdsale_contract_instance = w3.eth.contract(samy_token_address, abi=samy_contract_interface['abi'])

        crowdsale_contract_instance.functions.transfer(crowdsale_address, _amount).transact(
            {'from': w3.eth.coinbase, 'gas': 6000000})

    except Exception as e:
        print(e)


# Refund Vault Contract
# TODO
# [START Refund Vault Contract]
vault_compiled_sol = compile_files(['contracts/RefundVault.sol'])
vault_contract_interface = vault_compiled_sol['contracts/RefundVault.sol:RefundVault']
vault_contract = w3.eth.contract(abi=vault_contract_interface['abi'], bytecode=vault_contract_interface['bin'])


# [END Refund Vault Contract]

def test_crowdsale():
    r = redis_db.get('SAMYToken')
    r = r.decode('utf8')
    r = literal_eval(r)
    samy_token_address = r['address']

    r = redis_db.get('Crowdsale')
    r = r.decode('utf8')
    r = literal_eval(r)
    crowdsale_address = r['address']

    samy_token_contract_instance = w3.eth.contract(samy_token_address, abi=samy_contract_interface['abi'])
    crowdsale_contract_instance = w3.eth.contract(crowdsale_address, abi=crowdsale_contract_interface['abi'])

    refund_vault_address = crowdsale_contract_instance.functions.vault().call()

    print('Current Time %s' % int(time.time()))
    print('Crowdsale Ending Time %s' % crowdsale_contract_instance.functions.deadline().call())
    amountRaised = crowdsale_contract_instance.functions.weiAmountRaised().call()
    amountRaised = Web3.fromWei(amountRaised, 'ether')
    print('Crowdsale Amount Raised %s' % amountRaised)
    fundingGoal = crowdsale_contract_instance.functions.fundingGoal().call()
    fundingGoal = Web3.fromWei(fundingGoal, 'ether')
    print('Crowdsale Funding Goal %s' % fundingGoal)
    goal_reached = crowdsale_contract_instance.functions.goalReached().call()
    has_ended = crowdsale_contract_instance.functions.hasEnded().call()
    print('Crowdsale Has Ended: %s' % has_ended)
    print('Crowdsale Goal Reached: %s' % goal_reached)
    print('Crowdsale Beneficiary Address %s' % crowdsale_contract_instance.functions.beneficiary().call())

    rate = crowdsale_contract_instance.functions.rate().call()
    print('Crowdsale Tokens per 1 Ether: %s' % rate)

    balance = samy_token_contract_instance.functions.balanceOf(crowdsale_address).call()
    balance = Web3.fromWei(balance, 'ether')
    print('Crowdsale Contract Balance of SAMY Tokens: %s' % balance)
    balance = w3.eth.getBalance(refund_vault_address)
    balance = Web3.fromWei(balance, 'ether')
    print('Vault Contract Balance of Ether: %s' % balance)


def test_user(user=None):
    r = redis_db.get('SAMYToken')
    r = r.decode('utf8')
    r = literal_eval(r)
    samy_token_address = r['address']

    samy_token_contract_instance = w3.eth.contract(samy_token_address, abi=samy_contract_interface['abi'])

    balance = samy_token_contract_instance.functions.balanceOf(user).call()
    balance = Web3.fromWei(balance, 'ether')
    print('User Account SAMY Token Balance: %s' % balance)

    balance = w3.eth.getBalance(user)
    balance = Web3.fromWei(balance, 'ether')
    print('User Account Eth Balance: %s' % balance)

    latest_filter = samy_token_contract_instance.eventFilter('Buy', {'fromBlock': 0, 'toBlock': 'latest'})
    latest_transfers = latest_filter.get_all_entries()
    print(latest_transfers)


def crowdsale_trans(user=None):
    r = redis_db.get('Crowdsale')
    r = r.decode('utf8')
    r = literal_eval(r)
    crowdsale_address = r['address']

    _amount = 10
    _amount = Web3.toWei(_amount, 'ether')

    transaction = {
        'from': user,
        'to': crowdsale_address,
        'value': _amount,
        'gas': 7000000,
        'gasPrice': w3.eth.gasPrice,
    }

    result = unlock_account(user, 'User')

    if result == True:

        print('Unlocked Account: %s' % user)
        w3.eth.sendTransaction(transaction)
        result = lock_account(user)
        if result == True:
            print('Locked Account: %s' % user)
        else:
            print('Error Locking Account: %s' % user)
    else:
        print('Error Unlocking Account: %s' % user)


def finalize_crowdsale():
    r = redis_db.get('Crowdsale')
    r = r.decode('utf8')
    r = literal_eval(r)
    crowdsale_address = r['address']

    crowdsale_contract_instance = w3.eth.contract(crowdsale_address, abi=crowdsale_contract_interface['abi'])

    crowdsale_contract_instance.functions.finalization().transact({'from': w3.eth.coinbase, 'gas': 7000000})

    finalized = crowdsale_contract_instance.functions.isFinalized().call()
    print('Crowdsale is finalized: %s' % finalized)


def refund_crowdsale():
    r = redis_db.get('Crowdsale')
    r = r.decode('utf8')
    r = literal_eval(r)
    crowdsale_address = r['address']

    crowdsale_contract_instance = w3.eth.contract(crowdsale_address, abi=crowdsale_contract_interface['abi'])

    crowdsale_contract_instance.functions.sendRefunds().transact({'from': w3.eth.coinbase, 'gas': 7000000})


def set_prices():
    r = redis_db.get('SAMYToken')
    r = r.decode('utf8')
    r = literal_eval(r)
    samy_token_address = r['address']

    samy_token_contract_instance = w3.eth.contract(samy_token_address, abi=samy_contract_interface['abi'])

    samy_token_contract_instance.functions.setPrices(100000000000000, 100000000000000).transact(
        {'from': w3.eth.coinbase, 'gas': 7000000})


def test_sell(user=None):
    r = redis_db.get('SAMYToken')
    r = r.decode('utf8')
    r = literal_eval(r)
    samy_token_address = r['address']

    samy_token_contract_instance = w3.eth.contract(samy_token_address, abi=samy_contract_interface['abi'])

    sell_price = samy_token_contract_instance.functions.sellPrice().call()
    sell_price = Web3.fromWei(sell_price, 'ether')
    print('Sell Price: %s' % sell_price)

    _amount = 10
    _amount = Web3.toWei(_amount, 'ether')

    try:
        transaction = samy_token_contract_instance.functions.sell(_amount).buildTransaction(
            {'from': user, 'gas': 70000000})
        est_gas = w3.eth.estimateGas(transaction)
        print('Estimated Gas %s' % est_gas)
        result = unlock_account(user, 'User')
        if result == True:
            print('Unlocked Account: %s' % user)
            samy_token_contract_instance.functions.sell(_amount).transact({'from': user, 'gas': 700000})
            result = lock_account(user)
            if result == True:
                print('Locked Account: %s' % user)
            else:
                print('Error Locking Account: %s' % user)
        else:
            print('Error Unlocking Account: %s' % user)
    except Exception as e:
        print(e)


def test_buy(user=None):
    r = redis_db.get('SAMYToken')
    r = r.decode('utf8')
    r = literal_eval(r)
    samy_token_address = r['address']

    samy_token_contract_instance = w3.eth.contract(samy_token_address, abi=samy_contract_interface['abi'])

    _buy_price = samy_token_contract_instance.functions.buyPrice().call()
    buy_price = Web3.fromWei(_buy_price, 'ether')
    print('Buy Price: %s' % buy_price)

    try:

        _value = 230
        #_value = Web3.toWei(_value, 'ether')

        transaction = {
            'to': w3.eth.coinbase,
            'from': user,
            'gas': 700000000,
            'value': _value,
            'nonce': 5,
            'chainId': 10,
            'gasPrice': 18000000000
        }

        key = decrypt_account(address=user, passphrase='Brand')

        signed = w3.eth.account.signTransaction(transaction, key)

        tx_hash = w3.eth.sendRawTransaction(signed.rawTransaction)

        print(w3.eth.getTransaction(tx_hash))

    except Exception as e:
        print(e)

    '''try:
        _value = 1
        _value = Web3.toWei(_value, 'ether')
        transaction = samy_token_contract_instance.functions.buy().buildTransaction(
            {
                'from': user,
                'gas': 700000,
                'value': _value,
            }
        )
        est_gas = w3.eth.estimateGas(transaction)
        print('Estimated Gas %s' % est_gas)
        result = unlock_account(user, 'Brand')
        if result == True:
            print('Unlocked Account: %s' % user)
            samy_token_contract_instance.functions.buy().transact({'from': user, 'gas': 700000, 'value': _value})
            result = lock_account(user)
            if result == True:
                print('Locked Account: %s' % user)
            else:
                print('Error Locking Account: %s' % user)
        else:
            print('Error Unlocking Account: %s' % user)
    except Exception as e:
        print(e)'''


def test_xfer_from(user=None, _to=None):
    r = redis_db.get('SAMYToken')
    r = r.decode('utf8')
    r = literal_eval(r)
    samy_token_address = r['address']

    samy_token_contract_instance = w3.eth.contract(samy_token_address, abi=samy_contract_interface['abi'])

    _amount = 10
    _amount = Web3.toWei(_amount)

    def approve(user=None):
        samy_token_contract_instance.functions.approve(user, _amount).transact({'from': user, 'gas': 70000000})

    approve(user=user)
    allowance = samy_token_contract_instance.call().allowance(user, user)
    print('Address: %s Allowance: %s' % (user, allowance))

    samy_token_contract_instance.functions.transferFrom(user, samy_token_address, _amount).transact(
        {'from': user, 'gas': 70000000})

def send_signed(_to=None,
            _from=None,
            _value=None):

    _value = Web3.toWei(_value, 'ether')


    if _from == '0x489375ecF742af60653b0a29dD1d3CD660671358':

        transaction = {
            'to': _to,
            'from': _from,
            'gas': 700000000,
            'value': _value,
            'nonce': w3.eth.getTransactionCount(_from),
            'gasPrice': 18000000000
        }

        tx_hash = w3.eth.sendTransaction(transaction)

        while w3.eth.getTransactionReceipt(tx_hash) == None:
            time.sleep(5)
            print('Waiting To Verify Transaction')

        tx_receipt = w3.eth.getTransactionReceipt(tx_hash)

        print(tx_receipt)

    else:

        try:
            transaction = {
                'to': _to,
                'gas': 2000000,
                'value': _value,
                'nonce': 4,
                'chainId': 10,
                'gasPrice': 18000000000
            }

            print(transaction)

            key = decrypt_account(address=_from, passphrase='Brand')

            signed = w3.eth.account.signTransaction(transaction, key)

            tx_hash = w3.eth.sendRawTransaction(signed.rawTransaction)

            while w3.eth.getTransactionReceipt(tx_hash) == None:
                time.sleep(5)
                print('Waiting To Verify Transaction')

            tx_receipt = w3.eth.getTransactionReceipt(tx_hash)

            print(tx_receipt)

        except Exception as e:
            print(e)


# init_token()

# test_samy()

# fund_buy_sell()

# create_founder_accounts()

# founders = [w3.eth.accounts[1], w3.eth.accounts[2], w3.eth.accounts[3]]

# deploy_founders(founders=founders)

# fund_founders(founders=founders)

# test_founders(founders=founders)

# release_founders(founders=founders)

# revoke_founders(founders=founders)

# beneficiary = create_account(passphrase='Beneficiary')

# beneficiary = w3.eth.accounts[4]

# test_beneficiary(beneficiary=beneficiary)

# deploy_crowdsale(beneficiary=beneficiary)

# fund_crowdsale()

# test_crowdsale()

# user = create_account(passphrase='Ambassador')

user = w3.eth.accounts[1]

amount = 240

fund_user(amount=amount, user=w3.eth.accounts[1])

# test_user(user=user)

# crowdsale_trans(user=user)

# crowdsale_trans(user=user)

# finalize_crowdsale()

# refund_crowdsale()

set_prices()

# test_xfer_from()

# test_buy(user=user)

# test_sell(user=user)

# send_signed(_to=user, _from=w3.eth.coinbase, _value=240)

# send_signed(_to=w3.eth.coinbase, _from=user, _value=200)

# Vidulum Contract
# TODO
# [START Vidulum Contract]
vidulum_compiled_sol = compile_files(['contracts/Vidulum.sol'])
vidulum_contract_interface = vidulum_compiled_sol['contracts/Vidulum.sol:Vidulum']
vidulum_contract = w3.eth.contract(abi=vidulum_contract_interface['abi'], bytecode=vidulum_contract_interface['bin'])


# [END Vidulum Contract]
def deploy_vidulum():

    password = b'1234'

    _pinHash = bcrypt.hashpw(password, bcrypt.gensalt())

    _pinHash = _pinHash.decode('utf-8')

    state = b'MySecretKey'

    _state = bcrypt.hashpw(state, bcrypt.gensalt())

    _state = _state.decode('utf-8')

    _exp = (time.time() + 600)
    _cvv = '987'
    _zip = '32754'
    _addresses = [w3.eth.accounts[0], w3.eth.accounts[5]]
    _required = 2

    est_gas = w3.eth.estimateGas(transaction={'to': w3.eth.coinbase, 'data': vidulum_contract.bytecode})
    print('Estimated Gas %s' % est_gas)

    gas_price = w3.eth.gasPrice
    print('Current Gas Price %s' % gas_price)

    gas_to_deploy = gas_price * est_gas
    print('Gas to Deploy Contract %s' % gas_to_deploy)

    tx_hash = vidulum_contract.deploy(args=(_addresses,
                                            _required,
                                            _state,
                                            _pinHash), transaction={'from': w3.eth.coinbase, 'gas': 600000000})

    while w3.eth.getTransactionReceipt(tx_hash) == None:
        time.sleep(5)
        print('Waiting on Tranasaction')

    tx_receipt = w3.eth.getTransactionReceipt(tx_hash)

    contract_address = tx_receipt['contractAddress']

    print('Vidulum Token Contract Address: {}'.format(contract_address))

    data = {
        'address': contract_address
    }
    redis_db.set('Vidulum', data)


def test_accounts():
    r = redis_db.get('Vidulum')
    r = r.decode('utf8')
    r = literal_eval(r)
    vidulum_address = r['address']

    vidulum_contract_instance = w3.eth.contract(vidulum_address, abi=vidulum_contract_interface['abi'])

    print('Vidulum Address Master Owner: {}'.format(vidulum_contract_instance.functions.masterOwner().call()))
    print('Vidulum Address 0: {}'.format(vidulum_contract_instance.functions.owners(0).call()))
    print('Vidulum Address 1: {}'.format(vidulum_contract_instance.functions.owners(1).call()))
    print('Vidulum Confirmations Needed: {}'.format(vidulum_contract_instance.functions.required().call()))

    print('Vidulum Pin Hash: {}'.format(vidulum_contract_instance.functions.getPinHash().call()))
    print('Vidulum State: {}'.format(vidulum_contract_instance.functions.getState().call()))

    balance = w3.eth.getBalance(vidulum_address)
    balance = Web3.fromWei(balance, 'ether')
    print('Vidulum Eth Balance: %s' % balance)

    balance = w3.eth.getBalance(w3.eth.accounts[0])
    balance = Web3.fromWei(balance, 'ether')
    print('Account 0 Eth Balance: %s' % balance)

    balance = w3.eth.getBalance(w3.eth.accounts[5])
    balance = Web3.fromWei(balance, 'ether')
    print('Account 5 Eth Balance: %s' % balance)


def send_to_vidulum():
    r = redis_db.get('Vidulum')
    r = r.decode('utf8')
    r = literal_eval(r)
    vidulum_address = r['address']

    _amount = 1000
    _amount = Web3.toWei(_amount, 'ether')

    w3.eth.sendTransaction(
        transaction={'from': w3.eth.coinbase, 'to': vidulum_address, 'value': _amount, 'gas': 7000000})


def send_gas_to_user(_address=None, _gas=None):
    print(_address)
    print(_gas)

    return w3.eth.sendTransaction(transaction={'from': w3.eth.coinbase, 'to': _address, 'value': _gas, 'gas': 7000000})


def create_vidulum_transaction():
    r = redis_db.get('Vidulum')
    r = r.decode('utf8')
    r = literal_eval(r)
    vidulum_address = r['address']

    vidulum_contract_instance = w3.eth.contract(vidulum_address, abi=vidulum_contract_interface['abi'])

    _amount = 2540
    _amount = Web3.toWei(_amount, 'ether')

    state = b'MySecretKey'

    _state = bcrypt.hashpw(state, bcrypt.gensalt())

    _state = _state.decode('utf-8')

    _data = Web3.toBytes(text='%s' % _state)

    estimated_gas = vidulum_contract_instance.estimateGas().submitTransaction(
        w3.eth.accounts[5],
        _amount,
        _data
    )

    '''estimated_gas = vidulum_contract_instance.functions.submitTransaction(
        w3.eth.accounts[5],
        _amount,
        _data
    ).estimateGas'''

    print(estimated_gas)

    transaction = vidulum_contract_instance.functions.submitTransaction(
        w3.eth.accounts[5],
        _amount,
        _data
    ).buildTransaction(
        {
            'nonce': w3.eth.getTransactionCount(w3.eth.accounts[5]),
            'from': w3.eth.accounts[5],
            'gas': estimated_gas,
            'chainId': 10,
            'value': 0
        })

    print(transaction)

    estimated_wei = estimated_gas * transaction['gasPrice']

    print(Web3.fromWei(estimated_wei, 'ether'))

    def test():

        if w3.eth.getBalance(w3.eth.accounts[5]) <= estimated_wei:

            tx_hash = send_gas_to_user(w3.eth.accounts[5], estimated_wei)

            print(tx_hash)

            while w3.eth.getTransactionReceipt(tx_hash) == None:
                time.sleep(5)
                print('Waiting on Tranasaction')

            tx_receipt = w3.eth.getTransactionReceipt(tx_hash)

        key = decrypt_account(address=w3.eth.accounts[5], passphrase='User')

        print(key)

        signed = w3.eth.account.signTransaction(transaction, key)

        print(signed)

        w3.eth.sendRawTransaction(signed.rawTransaction)

        # test()


def confirm_from_vidulum():
    r = redis_db.get('Vidulum')
    r = r.decode('utf8')
    r = literal_eval(r)
    vidulum_address = r['address']

    vidulum_contract_instance = w3.eth.contract(vidulum_address, abi=vidulum_contract_interface['abi'])

    _trx = 0

    print('Get Pending Transaction Count: %s' % vidulum_contract_instance.functions.getTransactionCount(True,
                                                                                                        False).call())
    print('Confirmation Count: %s' % vidulum_contract_instance.functions.getConfirmationCount(_trx).call())
    print('Get Confirmations: %s' % vidulum_contract_instance.functions.getConfirmations(_trx).call())
    print('Transaction Confirmed: %s' % vidulum_contract_instance.functions.isConfirmed(_trx).call())
    print('Transaction: %s' % vidulum_contract_instance.functions.transactions(_trx).call())

    hashed_state = vidulum_contract_instance.functions.getState().call()

    hashed_state = hashed_state.encode('utf-8')

    _state = b'MySecretKey'

    if bcrypt.checkpw(_state, hashed_state):
        def test1():
            key = decrypt_account(address=w3.eth.accounts[0], passphrase='this-is-not-a-secure-password')
            print(key)
            transaction = vidulum_contract_instance.functions.confirmTransaction(_trx).buildTransaction(
                {'nonce': w3.eth.getTransactionCount(w3.eth.accounts[0]),
                 'from': w3.eth.accounts[0],
                 'gas': 7000000,
                 'chainId': 10})
            print(transaction)
            signed = w3.eth.account.signTransaction(transaction, key)
            print(signed)
            w3.eth.sendRawTransaction(signed.rawTransaction)
            # test1()


def vidulum_events():
    r = redis_db.get('Vidulum')
    r = r.decode('utf8')
    r = literal_eval(r)
    vidulum_address = r['address']

    vidulum_contract_instance = w3.eth.contract(address=vidulum_address, abi=vidulum_contract_interface['abi'])

    f = vidulum_contract_instance.eventFilter('Submission', {})
    logs = w3.eth.getFilterLogs(f.filter_id)
    print(logs)


# deploy_vidulum()

# test_accounts()

# send_to_vidulum()

# create_vidulum_transaction()

# confirm_from_vidulum()

# vidulum_events()

# address = create_account()

# address = '0x421AfB539e962C081d5b6AFda292abee508d0D0a'
# key = open_account(address=address)
# print(key)


'''
hashed_password = hashed_password.encode('utf-8')
    
    password = b'1234'

    if bcrypt.checkpw(password, hashed_password):
        print('Match')
'''


def transfer_agent(log_entry):
    print('SAMY Token Transfer Event: %s' % log_entry['event'])
    print('SAMY Token Transfer Address: %s' % log_entry['args']['to'])
    print('SAMY Token Transfer Block Number: %s' % log_entry['blockNumber'])


def update_transfer_agent():
    r = redis_db.get('SAMYToken')
    r = r.decode('utf8')
    r = literal_eval(r)
    samy_token_address = r['address']

    samy_token_contract_instance = w3.eth.contract(samy_token_address, abi=samy_contract_interface['abi'])

    samy_token_contract_instance.pastEvents('Transfer', {}, transfer_agent)

    event_signature_transfer = Web3.sha3(text='Transfer(address,address,uint256)')
    event_filter = w3.eth.filter({'topics': [event_signature_transfer]})
    transfer_events = w3.eth.getFilterChanges(event_filter.filter_id)

    # ... do something ...

    new_transfer_events = w3.eth.getFilterChanges(event_filter.filter_id)




