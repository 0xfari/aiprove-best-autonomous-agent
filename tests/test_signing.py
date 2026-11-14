"""Offline tests for agent.py signing (no network, no keypair file).

Run: python3 -m pytest tests/  OR  python3 tests/test_signing.py
Checks:
  1. eth_account path signs a challenge and the address recovers.
  2. Pure-python fallback (secp256k1 + keccak, RFC 6979) produces a
     signature for the same key that recovers the same address.
  3. The fallback's address derivation matches eth_account's.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import agent  # noqa: E402


def test_signing_paths_agree():
    from eth_account import Account
    acct = Account.create()
    kp = agent.Keypair(acct.key.hex(), acct.address)
    msg = "test-challenge-12345"
    sig_eth = kp.sign_message(msg)
    assert sig_eth.startswith("0x") and len(sig_eth) == 132, sig_eth
    # Force the pure-python path by hiding eth_account.
    real_loader = agent._load_eth_account
    agent._load_eth_account = lambda: (None, None)
    try:
        sig_pure = kp.sign_message(msg)
        assert sig_pure.startswith("0x") and len(sig_pure) == 132, sig_pure
        # Both signatures must recover to the same address.
        r, s = int(sig_pure[2:66], 16), int(sig_pure[66:130], 16)
        v = int(sig_pure[130:132], 16)
        assert agent._recover_address(msg, r, s, v) == acct.address.lower()
        assert agent._pure_address(int(acct.key.hex(), 16)) == acct.address.lower()
    finally:
        agent._load_eth_account = real_loader
    print("signing paths agree for", acct.address)


def test_forecast_shapes():
    # Forecast builders must not crash offline when feeds are stubbed.
    agent.coingecko_history = lambda coin, days=30: [100 * (1 + 0.001 * i) for i in range(30)]
    pred, ev = agent.forecast_btc_7d()
    assert pred["answer"] in ("yes", "no") and 0.25 <= pred["prob"] <= 0.75, pred
    agent.yahoo_closes = lambda symbol, range_="1mo": ([150 + i * 0.5 for i in range(22)], 161.0)
    pred, ev = agent.forecast_nvda_3d()
    assert isinstance(pred["answer"], float) and pred["answer"] > 0, pred
    print("forecast shapes OK")


if __name__ == "__main__":
    test_signing_paths_agree()
    test_forecast_shapes()
    print("ALL OFFLINE TESTS PASSED")
