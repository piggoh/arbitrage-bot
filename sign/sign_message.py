import os
from dotenv import load_dotenv
from web3 import Web3

# Load environment variables
load_dotenv()

private_key = os.getenv("PRIVATE_KEY")
alchemy_rpc = os.getenv("RPC_URL")

# Setup provider
w3 = Web3(Web3.HTTPProvider(alchemy_rpc))

# Get account from private key
account = w3.eth.account.from_key(private_key)

# Prepare transaction (send to yourself with GitHub handle in data field)
txn = {
    "nonce": w3.eth.get_transaction_count(account.address),
    "to": account.address,
    "value": 0,
    "gas": 100000,
    "gasPrice": w3.eth.gas_price,
    "data": w3.to_bytes(text="piggoh"),
    "chainId": 11155111,  # Sepolia
}

signed = w3.eth.account.sign_transaction(txn, private_key)
tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)

print("✅ Transaction hash:", w3.to_hex(tx_hash))
print(f"🔗 View on Etherscan: https://sepolia.etherscan.io/tx/{w3.to_hex(tx_hash)}")

