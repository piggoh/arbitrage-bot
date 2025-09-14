#!/usr/bin/env python3
"""
Smart Contract Interaction - How Python interacts with Solidity
"""

from web3 import Web3
import json
from typing import Dict, List, Optional
from config import RPC_URL, CONTRACT_ADDRESS, PRIVATE_KEY, TOKENS, ROUTERS
from eth_account import Account
from eth_account.signers.local import LocalAccount

class SmartContractInterface:
    """Interface for interacting with the ArbExecutor smart contract"""
    
    def __init__(self, rpc_url: str, contract_address: str, private_key: str):
        self.w3 = Web3(Web3.HTTPProvider(rpc_url))
        
        # For Sepolia and other PoA networks
        from web3.middleware.signing import construct_sign_and_send_raw_middleware
        account: LocalAccount = Account.from_key(private_key)
        self.w3.middleware_onion.add(construct_sign_and_send_raw_middleware(account))
        
        self.contract_address = contract_address
        self.private_key = private_key
        self.account = self.w3.eth.account.from_key(private_key)
        
        # Load contract ABI (Application Binary Interface)
        self.contract_abi = self._load_contract_abi()
        self.contract = self.w3.eth.contract(
            address=contract_address,
            abi=self.contract_abi
        )
        
        print(f"✅ Connected to contract at {contract_address}")
        print(f"✅ Account: {self.account.address}")
    
    def _load_contract_abi(self) -> List[Dict]:
        """Load the contract ABI from the compiled contract"""
        # This would typically be loaded from the compiled contract JSON
        # For now, I'll provide the essential ABI functions
        return [
            {
                "inputs": [
                    {"internalType": "address", "name": "tokenA", "type": "address"},
                    {"internalType": "address", "name": "tokenB", "type": "address"},
                    {"internalType": "uint256", "name": "amountIn", "type": "uint256"},
                    {"internalType": "address", "name": "router1", "type": "address"},
                    {"internalType": "address", "name": "router2", "type": "address"},
                    {"internalType": "bool", "name": "reverseOrder", "type": "bool"}
                ],
                "name": "executeArbitrage",
                "outputs": [],
                "stateMutability": "nonpayable",
                "type": "function"
            },
            {
                "inputs": [
                    {"internalType": "address", "name": "tokenA", "type": "address"},
                    {"internalType": "address", "name": "tokenB", "type": "address"},
                    {"internalType": "uint256", "name": "amountIn", "type": "uint256"},
                    {"internalType": "address", "name": "router1", "type": "address"},
                    {"internalType": "address", "name": "router2", "type": "address"},
                    {"internalType": "bool", "name": "reverseOrder", "type": "bool"}
                ],
                "name": "checkArbitrageOpportunity",
                "outputs": [{"internalType": "uint256", "name": "profit", "type": "uint256"}],
                "stateMutability": "view",
                "type": "function"
            },
            {
                "inputs": [
                    {"internalType": "address", "name": "token", "type": "address"},
                    {"internalType": "uint256", "name": "amount", "type": "uint256"}
                ],
                "name": "depositToken",
                "outputs": [],
                "stateMutability": "nonpayable",
                "type": "function"
            },
            {
                "inputs": [
                    {"internalType": "address", "name": "token", "type": "address"},
                    {"internalType": "uint256", "name": "amount", "type": "uint256"}
                ],
                "name": "withdrawProfit",
                "outputs": [],
                "stateMutability": "nonpayable",
                "type": "function"
            },
            {
                "inputs": [{"internalType": "address", "name": "token", "type": "address"}],
                "name": "getTokenBalance",
                "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
                "stateMutability": "view",
                "type": "function"
            },
            {
                "inputs": [{"internalType": "address", "name": "token", "type": "address"}],
                "name": "authorizeToken",
                "outputs": [],
                "stateMutability": "nonpayable",
                "type": "function"
            },
            {
                "inputs": [{"internalType": "address", "name": "router", "type": "address"}],
                "name": "authorizeRouter",
                "outputs": [],
                "stateMutability": "nonpayable",
                "type": "function"
            }
        ]
    
    def check_arbitrage_opportunity(self, token_a: str, token_b: str, amount_in: int, 
                                   router1: str, router2: str, reverse_order: bool) -> int:
        """Check arbitrage opportunity using the smart contract"""
        try:
            # Call the view function (no gas cost)
            profit = self.contract.functions.checkArbitrageOpportunity(
                token_a, token_b, amount_in, router1, router2, reverse_order
            ).call()
            
            return profit
            
        except Exception as e:
            print(f"❌ Error checking arbitrage opportunity: {e}")
            return 0
    
    def execute_arbitrage(self, token_a: str, token_b: str, amount_in: int,
                         router1: str, router2: str, reverse_order: bool) -> bool:
        """Execute arbitrage using the smart contract"""
        try:
            # Build transaction
            transaction = self.contract.functions.executeArbitrage(
                token_a, token_b, amount_in, router1, router2, reverse_order
            ).build_transaction({
                'from': self.account.address,
                'gas': 500000,  # Gas limit
                'gasPrice': self.w3.eth.gas_price,
                'nonce': self.w3.eth.get_transaction_count(self.account.address),
            })
            
            # Sign transaction
            signed_txn = self.w3.eth.account.sign_transaction(transaction, self.private_key)
            
            # Send transaction
            tx_hash = self.w3.eth.send_raw_transaction(signed_txn.rawTransaction)
            
            print(f"✅ Arbitrage transaction sent: {tx_hash.hex()}")
            
            # Wait for transaction receipt
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
            
            if receipt.status == 1:
                print(f"✅ Arbitrage executed successfully!")
                print(f"   Gas used: {receipt.gasUsed}")
                print(f"   Block: {receipt.blockNumber}")
                return True
            else:
                print(f"❌ Arbitrage transaction failed")
                return False
                
        except Exception as e:
            print(f"❌ Error executing arbitrage: {e}")
            return False
    
    def deposit_tokens(self, token_address: str, amount: int) -> bool:
        """Deposit tokens to the contract"""
        try:
            # First, we need to approve the contract to spend our tokens
            # This requires interacting with the ERC20 token contract
            token_abi = [
                {
                    "inputs": [
                        {"internalType": "address", "name": "spender", "type": "address"},
                        {"internalType": "uint256", "name": "amount", "type": "uint256"}
                    ],
                    "name": "approve",
                    "outputs": [{"internalType": "bool", "name": "", "type": "bool"}],
                    "stateMutability": "nonpayable",
                    "type": "function"
                }
            ]
            
            token_contract = self.w3.eth.contract(
                address=token_address,
                abi=token_abi
            )
            
            # Approve contract to spend tokens
            approve_tx = token_contract.functions.approve(
                self.contract_address, amount
            ).build_transaction({
                'from': self.account.address,
                'gas': 100000,
                'gasPrice': self.w3.eth.gas_price,
                'nonce': self.w3.eth.get_transaction_count(self.account.address),
            })
            
            signed_approve = self.w3.eth.account.sign_transaction(approve_tx, self.private_key)
            approve_hash = self.w3.eth.send_raw_transaction(signed_approve.rawTransaction)
            self.w3.eth.wait_for_transaction_receipt(approve_hash)
            
            # Now deposit tokens
            deposit_tx = self.contract.functions.depositToken(
                token_address, amount
            ).build_transaction({
                'from': self.account.address,
                'gas': 200000,
                'gasPrice': self.w3.eth.gas_price,
                'nonce': self.w3.eth.get_transaction_count(self.account.address),
            })
            
            signed_deposit = self.w3.eth.account.sign_transaction(deposit_tx, self.private_key)
            deposit_hash = self.w3.eth.send_raw_transaction(signed_deposit.rawTransaction)
            receipt = self.w3.eth.wait_for_transaction_receipt(deposit_hash)
            
            if receipt.status == 1:
                print(f"✅ Deposited {amount / 1e18:.6f} tokens successfully")
                return True
            else:
                print(f"❌ Deposit failed")
                return False
                
        except Exception as e:
            print(f"❌ Error depositing tokens: {e}")
            return False
    
    def get_token_balance(self, token_address: str) -> int:
        """Get token balance in the contract"""
        try:
            balance = self.contract.functions.getTokenBalance(token_address).call()
            return balance
        except Exception as e:
            print(f"❌ Error getting token balance: {e}")
            return 0
    
    def withdraw_profits(self, token_address: str, amount: int) -> bool:
        """Withdraw profits from the contract"""
        try:
            withdraw_tx = self.contract.functions.withdrawProfit(
                token_address, amount
            ).build_transaction({
                'from': self.account.address,
                'gas': 150000,
                'gasPrice': self.w3.eth.gas_price,
                'nonce': self.w3.eth.get_transaction_count(self.account.address),
            })
            
            signed_withdraw = self.w3.eth.account.sign_transaction(withdraw_tx, self.private_key)
            withdraw_hash = self.w3.eth.send_raw_transaction(signed_withdraw.rawTransaction)
            receipt = self.w3.eth.wait_for_transaction_receipt(withdraw_hash)
            
            if receipt.status == 1:
                print(f"✅ Withdrew {amount / 1e18:.6f} tokens successfully")
                return True
            else:
                print(f"❌ Withdrawal failed")
                return False
                
        except Exception as e:
            print(f"❌ Error withdrawing profits: {e}")
            return False

def demonstrate_interaction():
    """Demonstrate how Python interacts with the Solidity contract"""
    print("🔗 Python ↔ Solidity Interaction Demo")
    print("=" * 50)
    
    # Initialize the interface
    interface = SmartContractInterface(
        rpc_url=RPC_URL,
        contract_address=CONTRACT_ADDRESS,
        private_key=PRIVATE_KEY
    )
    
    # Example token addresses (Sepolia)
    weth_address = TOKENS["WETH"]
    usdc_address = TOKENS["USDC"]
    
    # Example router addresses
    uniswap_router = ROUTERS["UNISWAP_V2"]
    sushiswap_router = ROUTERS["SUSHISWAP"]
    
    print("\n1️⃣ Checking Arbitrage Opportunity...")
    profit = interface.check_arbitrage_opportunity(
        token_a=weth_address,
        token_b=usdc_address,
        amount_in=1000000000000000000,  # 1 ETH
        router1=uniswap_router,
        router2=sushiswap_router,
        reverse_order=True
    )
    
    print(f"   Expected profit: {profit / 1e18:.6f} ETH")
    
    print("\n2️⃣ Checking Token Balance...")
    balance = interface.get_token_balance(weth_address)
    print(f"   WETH balance in contract: {balance / 1e18:.6f} ETH")
    
    print("\n3️⃣ Example Arbitrage Execution...")
    if profit > 1000000000000000:  # If profit > 0.001 ETH
        print("   Profit threshold met, executing arbitrage...")
        success = interface.execute_arbitrage(
            token_a=weth_address,
            token_b=usdc_address,
            amount_in=1000000000000000000,  # 1 ETH
            router1=uniswap_router,
            router2=sushiswap_router,
            reverse_order=True
        )
        
        if success:
            print("   ✅ Arbitrage executed successfully!")
        else:
            print("   ❌ Arbitrage execution failed")
    else:
        print("   Profit too low, skipping execution")

if __name__ == "__main__":
    demonstrate_interaction()
