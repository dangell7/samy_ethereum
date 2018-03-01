
import deploy_team, deploy_smy, utils, deploy_founders, deploy_crowdsale
import json
import time

from utils import Web3, w3

def main():

    owner_address = '0x90b0Bd4c7AbB7FCC6BE4E9354Ff7996ec5c5192a'
    owner_key = '0xa1884a65c860e2b835077034992a03fa88a24e63c5ace6170ecec65a9e88f729'

    if not owner_address:
        print('No Owner Wallet, Creating Owner')
        address = deploy_team.create_owner(utils.randompassword())
        print('Owner Address: %s' % address)
        return

    check = deploy_team.check(owner_address, 'Owner')
    if check == 0:
        print('Error, No Eth!!')
        return

    #return
    smy_token_address = '0x21C64552eC487bC3117562C96f306Bb9F77A9dD3'

    if not smy_token_address:
        print('No SMY Token Contract, Deploying Contract')
        address = deploy_smy.deploy_samy(owner_address, owner_key)
        print('SMY Token Contract Address: %s' % address)
        return

    isActive = deploy_smy.check_status(smy_token_address, owner_address, owner_key)
    print('SMY Token Active: %s' % isActive)
    #return

    if isActive == False:
        deploy_smy.change_status(smy_token_address, owner_address, owner_key)
        return

    #return

    deploy_smy.check_samy(smy_token_address, owner_address, 'Owner')

    Denis = {
        'address': '0x8aF423a19837d36Da044A4D8D7a43B011eCa44a3',
        'name': 'Denis'
    }

    William = {
        'address': '0x82FF3aEeB00f118D9352BA08718C89BA31724433',
        'name': 'William'
    }

    Matt = {
        'address': '0xB5398D902FA543Ddc7c9b14ca7Ddef442aF59DDD',
        'name': 'Matt'
    }

    founders_list = [Denis, William, Matt]

    if not founders_list:
        print('No Denis Wallet, Creating Denis')
        address = deploy_team.create_denis(utils.randompassword())
        print('Denis Address: %s' % address)

        print('No William Wallet, Creating William')
        address = deploy_team.create_william(utils.randompassword())
        print('William Address: %s' % address)

        print('No Matt Wallet, Creating Matt')
        address = deploy_team.create_matt(utils.randompassword())
        print('Matt Address: %s' % address)
        return

    deploy_smy.check_samy(smy_token_address, founders_list[0]['address'], 'Denis')
    deploy_smy.check_samy(smy_token_address, founders_list[1]['address'], 'William')
    deploy_smy.check_samy(smy_token_address, founders_list[2]['address'], 'Matt')

    Denis_Contract = {
        'address': '0x3A83758a742FD6a7E7068109d935D02d6FD4D05a',
        'name': 'Denis'
    }

    William_Contract = {
        'address': '0x37CD59c87c037D95A50aECD46B5ce265eA6385A4',
        'name': 'William'
    }

    Matt_Contract = {
        'address': '0x72d04A0893Bd22ac1153C543bc18D62eb043E7e1',
        'name': 'Matt'
    }

    founders_contract_list = [Denis_Contract, William_Contract, Matt_Contract]
    #founders_contract_list = []

    if not founders_contract_list:
        print('No Founders Contracts, Deploying Contracts')
        deploy_founders.deploy_founders(owner_address, owner_key, founders_list)
        return

    founders_funded = deploy_founders.check_founders(smy_token_address, founders_contract_list)
    print('Funders Founded: %s' % founders_funded)
    #return

    if founders_funded == False:
        print('Funding Founder Contracts')
        deploy_founders.fund_founders(smy_token_address, owner_address, owner_key, founders_contract_list)
        return

    deploy_founders.check_founders(smy_token_address, founders_contract_list)

    beneficiary_address = '0x89dBDeEEACBFBCba996c1e4cF31BCd224c016019'

    if not beneficiary_address:
        print('No Beneficiary Wallet, Creating Beneficiary')
        address = deploy_team.create_beneficiary(utils.randompassword())
        print('Beneficiary Address: %s' % address)
        return

    deploy_smy.check_samy(smy_token_address, beneficiary_address, 'Beneficiary')

    crowdsale_address = '0xc814f6AEc6769cB4DE212600Ed6C6F33cA8C85D4'

    if not crowdsale_address:
        print('No Crowdsale Contract, Deploying Crowdsale')
        address = deploy_crowdsale.deploy_crowdsale(smy_token_address,
                                                    owner_address,
                                                    owner_key,
                                                    beneficiary_address)
        print('Crowdsale Contract Address: %s' % address)
        return


    crowdsale_funded = deploy_crowdsale.check_crowdsale(smy_token_address=smy_token_address, crowdsale_address=crowdsale_address)
    print('Crowdsale Funded: %s' % crowdsale_funded)
    #return

    if crowdsale_funded == False:
        deploy_crowdsale.fund_crowdsale(
            smy_token_address,
            owner_address,
            owner_key,
            crowdsale_address
        )
        return

    user_address = '0xF37c0E6e4D436490F5ABc162D5B632f348A0764E'

    user_key = '0x6e7e1b0ad493e1bfdcd6ba1d33ad7aa919acff523e26c85e3f5fd72346bce160'

    if not user_address:
        print('No User Wallet, Creating User')
        address = deploy_team.create_user(utils.randompassword())
        print('User Address: %s' % address)
        return

    #return

    if w3.eth.getBalance(user_address) == 0:
        deploy_team.send(user_address, owner_address, owner_key)
        return

    deploy_smy.check_samy(smy_token_address, user_address, 'User')

    ended, goal = deploy_crowdsale.check_crowdsale(smy_token_address, crowdsale_address)

    #deploy_crowdsale.transaction_crowdsale(crowdsale_address, user_address, user_key)

    #return
    #ended = False
    #goal = False
    finalized = True

    if finalized == False:

        if ended == True:
            deploy_crowdsale.finalize_crowdsale(crowdsale_address, owner_address, owner_key)

            if not goal:
                deploy_crowdsale.refund_crowdsale(crowdsale_address, owner_address, owner_key)
                return

    #deploy_crowdsale.get_test(crowdsale_address)

    #deploy_founders.release_founders(smy_token_address, user_address, user_key, founders_contract_list)
    #deploy_founders.release_founders(smy_token_address, owner_address, owner_key)

main()
#print(Web3.toHex(b'\xb1g|\x8f\xfd\x05}\x8a%\xe5\x8e\xafO\xa6>\\\xe3\xc4 ]\x8f\x0b\xd2\x82\x15\x99!\xdb\x9f\xb43U'))
