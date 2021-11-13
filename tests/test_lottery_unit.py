#pomembno, brownie test je ocitno nekaj vezan tudi na ime datoteke, ni delovalo ko
#sem uporabil ime tests_lottery.py 

#za unit test-e je bojda fino poskrbeti, da se res testira celotno pogodbo, every line of code, the man said

from scripts.helpful_scripts import (
    LOCAL_BLOCKCHAIN_ENVIRONMENTS,
    get_account,
    fund_with_link,
    get_contract,
)
from brownie import Lottery, accounts, config, network, exceptions
from scripts.deploy_lottery import deploy_lottery
from web3 import Web3
import pytest

#prvotni, n00b test
#def test_get_entrance_fee():
#    account = accounts[0]
#    lottery = Lottery.deploy(config["networks"][network.show_active()]["eth_usd_price_feed"],
#        {"from": account},)
#    assert lottery.getEntranceFee() > Web3.toWei(0.0001, "ether")
#    assert lottery.getEntranceFee() < Web3.toWei(1, "ether")

def test_get_entrance_fee():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip()
    else:
        #Arrange
        lottery = deploy_lottery()
        #Act
        expected_entrance_fee = Web3.toWei(0.025, "ether")
        entrance_fee = lottery.getEntranceFee()
        #Assert
        assert expected_entrance_fee == entrance_fee

def test_cant_enter_unless_started():
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip()
    lottery = deploy_lottery()
    # Act / Assert
    with pytest.raises(exceptions.VirtualMachineError):
        lottery.enter({"from": get_account(), "value": lottery.getEntranceFee()})

def test_can_start_and_enter_lottery():
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip()
    lottery = deploy_lottery()
    account = get_account()
    lottery.startLottery({"from": account})
    # Act
    lottery.enter({"from": account, "value": lottery.getEntranceFee()})
    # Assert
    assert lottery.players(0) == account

def test_can_end_lottery():
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip()
    lottery = deploy_lottery()
    account = get_account()
    lottery.startLottery({"from": account})
    lottery.enter({"from": account, "value": lottery.getEntranceFee()})
    fund_with_link(lottery)
    lottery.endLottery({"from": account})
    assert lottery.lottery_state() == 2 #vezano na cifre v loteriji, tj. na stanje procesa (start, ongoing, end)


def test_can_pick_winner_correctly():
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip()
    lottery = deploy_lottery()
    account = get_account()
    lottery.startLottery({"from": account})
    #dodajas vec igralcev, lahko bi loopnil (to je btw bojda ze skoraj bolj integration test)
    lottery.enter({"from": account, "value": lottery.getEntranceFee()})
    lottery.enter({"from": get_account(index=1), "value": lottery.getEntranceFee()})
    lottery.enter({"from": get_account(index=2), "value": lottery.getEntranceFee()})
    fund_with_link(lottery)
    starting_balance_of_account = account.balance()
    balance_of_lottery = lottery.balance()
    transaction = lottery.endLottery({"from": account})
    request_id = transaction.events["RequestedRandomness"]["requestId"] #tu gres not v objekt
    STATIC_RNG = 777
    get_contract("vrf_coordinator").callBackWithRandomness(
        request_id, STATIC_RNG, lottery.address, {"from": account}
    )
    # 777 % 3 = 0
    assert lottery.recentWinner() == account
    assert lottery.balance() == 0
    assert account.balance() == starting_balance_of_account + balance_of_lottery