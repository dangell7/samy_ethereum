

def test_voting(chain):
    voter, _ = chain.provider.get_or_deploy_contract('Voting')
    voting = voter.call().totalVotesFor.call('Rama')
    assert voting == 1



