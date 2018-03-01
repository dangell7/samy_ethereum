# utils.py

import web3
import json
from datetime import datetime
import time
import os
import random
import string
from web3 import Web3, HTTPProvider, TestRPCProvider, IPCProvider
from solc import compile_source, compile_files
from web3.contract import ConciseContract

try:
    #w3 = Web3(HTTPProvider('http://159.89.80.176:8102'))
    w3 = Web3(HTTPProvider('https://infura.io/hEkZ5mQIZbPJfygOuNgZ'))
    #w3 = Web3(IPCProvider('chains/samynet/chain_data/geth.ipc'))
except Exception as e:
    print('Error Getting Web3; Error: %s' % e)

def create_account(passphrase=None):
    try:
        acct = w3.eth.account.create()
        encrypted = w3.eth.account.encrypt(acct.privateKey, passphrase)
        string_time = datetime.fromtimestamp(time.time()).strftime('UTC--%Y-%m-%dT%H-%M-%S.%fZ')
        key_name = '%s--%s' % (string_time, acct.address[2:])
        with open('chains/samynet/chain_data/keystore/%s' % key_name, 'w') as f:
            f.write(json.dumps(encrypted))

        return acct.address, Web3.toHex(acct.privateKey)
    except Exception as e:
        print('Error Creating User; Error: %s' % e)


def decrypt_account(address=None, passphrase=None):
    try:
        for file_name in os.listdir("chains/samynet/chain_data/keystore/"):
            data = file_name.split('--')
            file_address = data[-1]
            if address[2:] == file_address:
                data = open('chains/samynet/chain_data/keystore/%s' % file_name)
                encrypted = json.load(data)
                return w3.eth.account.decrypt(encrypted, passphrase)
    except Exception as e:
        print('Error Decrypting User; Error: %s', e)

def randompassword():
    return ''.join([random.choice(string.ascii_letters + string.digits) for n in range(24)])
