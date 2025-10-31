# deploy_contract.py
# WARNING: Use testnet and a throwaway key. Do NOT expose real keys.
from web3 import Web3
import json, os
w3 = Web3(Web3.HTTPProvider(os.environ.get("BLOCKCHAIN_RPC")))
acct = w3.eth.account.from_key(os.environ.get("DEPLOY_PRIVATE_KEY"))
with open("DeviceRegistry.json") as f:
    abi = json.load(f)["abi"]
bytecode = open("DeviceRegistry.bin","r").read().strip()
contract = w3.eth.contract(abi=abi, bytecode=bytecode)
tx = contract.constructor().buildTransaction({
    "from": acct.address,
    "nonce": w3.eth.getTransactionCount(acct.address),
    "gas": 4000000,
    "gasPrice": w3.eth.gas_price
})
signed = acct.sign_transaction(tx)
txh = w3.eth.send_raw_transaction(signed.rawTransaction)
print("txh:", txh.hex())
rcpt = w3.eth.wait_for_transaction_receipt(txh)
print("contract at:", rcpt.contractAddress)
