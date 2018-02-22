import json
import web3

from web3 import Web3, HTTPProvider, TestRPCProvider, IPCProvider
from solc import compile_source, compile_files
from web3.contract import ConciseContract

import time
from datetime import datetime

#import redis
import os
#import bcrypt
import uuid
#import rlp
#from ethereum.transactions import Transaction

#from samy_firebase import admin_db
#from samy_firebase import admin_auth

#pool = redis.ConnectionPool(host='localhost', port=6379, db=5)
#redis_db = redis.Redis(connection_pool=pool)

from ast import literal_eval

w3 = Web3(HTTPProvider('http://159.89.80.176:8102'))
#w3 = Web3(IPCProvider('chains/samy/chain_data/geth.ipc'))

#print('Current BlockNumber: %s' % w3.eth.blockNumber)

# Vidulum Contract
# TODO
# [START Vidulum Contract]
vidulum_compiled_sol = compile_files(['contracts/Vidulum.sol'])
vidulum_contract_interface = vidulum_compiled_sol['contracts/Vidulum.sol:Vidulum']
vidulum_contract = w3.eth.contract(abi=vidulum_contract_interface['abi'], bytecode=vidulum_contract_interface['bin'])

# [END Vidulum Contract]

# SAMY Token Contract
# TODO
# [START SAMY Token Contract]
samy_compiled_sol = compile_files(['contracts/SamyToken.sol'])
samy_contract_interface = samy_compiled_sol['contracts/SamyToken.sol:SamyToken']
samy_contract = w3.eth.contract(abi=samy_contract_interface['abi'], bytecode=samy_contract_interface['bin'])

_initialSupply = 100000000
# [END SAMY Token Contract]


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


# Deploy Samy Contract
# TODO
# [START Deploy Samy Contract]
def deploy_samy():

    gas_price = w3.eth.gasPrice
    gas_limit = 7000000

    nonce = w3.eth.getTransactionCount(w3.eth.coinbase)

    built_transaction = {
        'nonce': nonce,
        'gasPrice': gas_price,
        'gas': gas_limit,
        'chainId': None
    }

    transaction = samy_contract.constructor().buildTransaction(built_transaction)

    print(transaction)

    #key = decrypt_account(w3.eth.coinbase, 'Coinbase-Master')

    #signed = w3.eth.account.signTransaction(transaction, key)

    raw_tx_hex = Web3.toHex(signed.rawTransaction)

    '''tx_hash = w3.eth.sendRawTransaction(raw_tx_hex)

    while w3.eth.getTransactionReceipt(tx_hash) == None:
        time.sleep(5)
        print('Waiting on Tranasaction')

    tx_receipt = w3.eth.getTransactionReceipt(tx_hash)

    contract_address = tx_receipt['contractAddress']

    print('SAMY Token Contract Address: {}'.format(contract_address))

    data = {
        'address': contract_address
    }
    redis_db.set('SAMYToken', data)'''

# [END Deploy Samy Contract]

# Fund Buy Sell Contract
# TODO
# [START Fund Buy Sell Contract]
def fund_buy_sell():
    r = redis_db.get('SAMYToken')
    r = r.decode('utf8')
    r = literal_eval(r)
    samy_token_address = r['address']

    _amount = int(_initialSupply * .74)
    _amount = Web3.toWei(_amount, 'ether')

    try:

        gas_price = w3.eth.gasPrice
        gas_limit = 7000000

        nonce = w3.eth.getTransactionCount(w3.eth.coinbase)

        samy_token_contract_instance = w3.eth.contract(samy_token_address, abi=samy_contract_interface['abi'])

        if samy_token_contract_instance.functions.isActive().call() == False:
            print('Samy Token Contract is not Active')
            return

        transaction = samy_token_contract_instance.functions.transfer(
            samy_token_address,
            _amount
        ).buildTransaction(
            {
                'from': w3.eth.coinbase,
                'nonce': nonce,
                'gasPrice': gas_price,
                'gas': gas_limit,
                'value': 0,
                'chainId': None
            }
        )

        key = decrypt_account(w3.eth.coinbase, 'Coinbase-Master')
        signed = w3.eth.account.signTransaction(transaction, key)
        raw_tx_hex = Web3.toHex(signed.rawTransaction)
        tx_hash = w3.eth.sendRawTransaction(raw_tx_hex)
        while w3.eth.getTransactionReceipt(tx_hash) == None:
            time.sleep(5)
            print('Waiting on Tranasaction')

        tx_receipt = w3.eth.getTransactionReceipt(tx_hash)

        print(tx_receipt)

    except Exception as e:
        print(e)

# [END Fund Buy Sell Contract]


# Create User Private Key & Wallet
# TODO
# [START Create User Private Key & Wallet]
def create_user_vidulum_wallet(passphrase=None, userUUID=None):
    try:

        user_address = admin_db.child('users').child(userUUID).child('address').get()

        if user_address:
            address = user_address
        else:
            address = create_account(passphrase=passphrase)

        address = Web3.toChecksumAddress(address)

        pin = b'1234'

        _pinHash = bcrypt.hashpw(pin, bcrypt.gensalt())

        _pinHash = _pinHash.decode('utf-8')

        state = userUUID.encode('utf-8')

        _state = bcrypt.hashpw(state, bcrypt.gensalt())

        _state = _state.decode('utf-8')

        _exp = (time.time() + 600)
        _cvv = '987'
        _zip = '32754'
        _addresses = [w3.eth.coinbase, address]
        _required = 2

        contract_data = vidulum_contract.deploy_data(
            args=(
                _addresses,
                _required,
                _state,
                _pinHash
            )
        )

        key = decrypt_account(w3.eth.coinbase, 'Coinbase-Master')

        gas_price = w3.eth.gasPrice
        gas_limit = 7000000

        nonce = w3.eth.getTransactionCount(w3.eth.coinbase)

        transaction = {
            'nonce': nonce,
            'gasPrice': gas_price,
            'gas': gas_limit,
            'to': '',
            'value': 0,
            'data': contract_data,
            'chainId': None
        }

        signed = w3.eth.account.signTransaction(transaction, key)

        raw_tx_hex = Web3.toHex(signed.rawTransaction)

        tx_hash = w3.eth.sendRawTransaction(raw_tx_hex)

        while w3.eth.getTransactionReceipt(tx_hash) == None:
            time.sleep(5)
            print('Waiting on Tranasaction')

        tx_receipt = w3.eth.getTransactionReceipt(tx_hash)

        contract_address = tx_receipt['contractAddress']

        print('Vidulum Contract Address: {}'.format(contract_address))

        return contract_address

    except Exception as e:
        print(e)


# [END Create User Private Key & Wallet]

# Create Brand User
# TODO
# [START Create Brand User]
def create_brand():
    try:

        userUUID = 'lb693WDuQ9NtcY59o35uCr62a392'

        passphrase = 'Chris12345()'

        vidulum_address = create_user_vidulum_wallet(passphrase=passphrase, userUUID=userUUID)

        admin_db.child('users').child(userUUID).update({'vidulum': vidulum_address})

    except Exception as e:
        print(e)


# [END Create Brand User]

# Fund Brand User
# TODO
# [START Fund Brand User]
def fund_brand(address=None, value=None):

    _value = Web3.toWei(value, 'ether')

    gas_price = w3.eth.gasPrice
    gas_limit = 7000000
    nonce = w3.eth.getTransactionCount(w3.eth.coinbase)
    transaction = {
        'nonce': nonce,
        'gasPrice': gas_price,
        'gas': gas_limit,
        'to': address,
        'value': _value,
        'data': b'',
        'chainId': None
    }

    key = decrypt_account(w3.eth.coinbase, 'Coinbase-Master')
    signed = w3.eth.account.signTransaction(transaction, key)
    raw_tx_hex = Web3.toHex(signed.rawTransaction)
    tx_hash = w3.eth.sendRawTransaction(raw_tx_hex)
    while w3.eth.getTransactionReceipt(tx_hash) == None:
        time.sleep(5)
        print('Waiting on Tranasaction')

    tx_receipt = w3.eth.getTransactionReceipt(tx_hash)
    print(tx_receipt)

# [END Fund Brand User]

# Set Buy Sell Prices
# TODO
# [START Set Buy Sell Prices]
def set_prices(buy_price=None, sell_price=None):
    r = redis_db.get('SAMYToken')
    r = r.decode('utf8')
    r = literal_eval(r)
    samy_token_address = r['address']

    _buy_price = Web3.toWei(buy_price, 'ether')
    _sell_price = Web3.toWei(sell_price, 'ether')

    samy_token_contract_instance = w3.eth.contract(samy_token_address, abi=samy_contract_interface['abi'])

    gas_price = w3.eth.gasPrice
    gas_limit = 7000000
    nonce = w3.eth.getTransactionCount(w3.eth.coinbase)

    transaction = samy_token_contract_instance.functions.setPrices(
        _buy_price,
        _sell_price
    ).buildTransaction(
        {
            'from': w3.eth.coinbase,
            'nonce': nonce,
            'gasPrice': gas_price,
            'gas': gas_limit,
            'value': 0,
            'chainId': None
        }
    )

    key = decrypt_account(w3.eth.coinbase, 'Coinbase-Master')
    signed = w3.eth.account.signTransaction(transaction, key)
    raw_tx_hex = Web3.toHex(signed.rawTransaction)
    tx_hash = w3.eth.sendRawTransaction(raw_tx_hex)
    while w3.eth.getTransactionReceipt(tx_hash) == None:
        time.sleep(5)
        print('Waiting on Tranasaction')

    tx_receipt = w3.eth.getTransactionReceipt(tx_hash)

    print(tx_receipt)

# [END Set BUy Sell Prices]

#create_brand()

#value = 240
#address = '0xb2651cBc22A69a7d10886AE3d8Ebc6A1608242BC'
#fund_brand(address=address, value=value)

#deploy_samy()

#fund_buy_sell()

#buy_price = .0001
#sell_price = .0001

#set_prices(buy_price=buy_price, sell_price=sell_price)




