from steem.utils import assets_from_string
from steem.utils import resolve_authorperm

def test_assets_from_string():
    assert assets_from_string('USD:BTS') == ['USD', 'BTS']
    assert assets_from_string('BTSBOTS.S1:BTS') == ['BTSBOTS.S1', 'BTS']

def test_authorperm_resolve():
    assert resolve_authorperm('theaussiegame/cryptokittie-giveaway-number-2') == ('theaussiegame', 'cryptokittie-giveaway-number-2')
    assert resolve_authorperm('holger80/virtuelle-cloud-mining-ponzi-schemen-auch-bekannt-als-hypt') == ('holger80', 'virtuelle-cloud-mining-ponzi-schemen-auch-bekannt-als-hypt')
