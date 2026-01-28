from web3 import Web3
from datetime import datetime
import time
from database import Database
from email_service import EmailService, get_eth_price_usd

class WhaleMonitor:
    def __init__(self, rpc_url):
        self.w3 = Web3(Web3.HTTPProvider(rpc_url))
        self.db = Database()
        self.email_service = EmailService()
        self.last_block = None
        self.eth_price_usd = None
        
        if not self.w3.is_connected():
            raise Exception("Failed to connect to Ethereum node")
        
        print(f"✅ Connected to Ethereum")
        
        # Fetch initial ETH price
        self.update_eth_price()
    
    def update_eth_price(self):
        """Update ETH price in USD"""
        price = get_eth_price_usd()
        if price:
            self.eth_price_usd = price
            print(f"💰 ETH Price: ${price:,.2f}")
    
    def wei_to_eth(self, wei_value):
        """Convert Wei to ETH"""
        return self.w3.from_wei(wei_value, 'ether')
    
    def get_transaction_type(self, tx):
        """Determine transaction type"""
        if tx['to'] is None:
            return "Contract Creation"
        elif tx['input'] != '0x':
            return "Contract Call"
        else:
            return "Transfer"
    
    def check_and_send_alerts(self, tx_data, from_addr, to_addr):
        """Check if any users need to be alerted about this transaction"""
        
        # Check users tracking the from address
        users_from = self.db.get_users_tracking_wallet(from_addr)
        for user in users_from:
            if float(tx_data['value']) >= user['large_tx_threshold']:
                # Send alert
                self.send_transaction_alert(
                    user_email=user['email'],
                    wallet_name=user['wallet_name'],
                    wallet_address=from_addr,
                    tx_data=tx_data,
                    direction='outgoing'
                )
        
        # Check users tracking the to address
        if to_addr:
            users_to = self.db.get_users_tracking_wallet(to_addr)
            for user in users_to:
                if float(tx_data['value']) >= user['large_tx_threshold']:
                    # Send alert
                    self.send_transaction_alert(
                        user_email=user['email'],
                        wallet_name=user['wallet_name'],
                        wallet_address=to_addr,
                        tx_data=tx_data,
                        direction='incoming'
                    )
    
    def send_transaction_alert(self, user_email, wallet_name, wallet_address, tx_data, direction):
        """Send email alert to user"""
        try:
            value_eth = float(tx_data['value'])
            value_usd = value_eth * self.eth_price_usd if self.eth_price_usd else None
            
            self.email_service.send_alert_email(
                to_email=user_email,
                wallet_name=wallet_name,
                wallet_address=wallet_address,
                tx_hash=tx_data['hash'],
                value_eth=f"{value_eth:.4f}",
                value_usd=value_usd,
                tx_type=tx_data['type'],
                direction=direction
            )
            
            print(f"📧 Alert sent to {user_email} for {wallet_name}")
            
        except Exception as e:
            print(f"❌ Failed to send alert: {e}")
    
    def process_transaction(self, tx_hash):
        """Process a single transaction"""
        try:
            tx = self.w3.eth.get_transaction(tx_hash)
            
            from_addr = tx['from'].lower() if tx['from'] else None
            to_addr = tx['to'].lower() if tx['to'] else None
            
            # Get all tracked wallets
            tracked_wallets = self.db.get_all_tracked_wallets()
            
            # Check if transaction involves any tracked wallet
            if from_addr not in tracked_wallets and to_addr not in tracked_wallets:
                return None
            
            value_eth = self.wei_to_eth(tx['value'])
            gas_price_gwei = self.w3.from_wei(tx['gasPrice'], 'gwei')
            
            # Calculate USD value
            value_usd = float(value_eth) * self.eth_price_usd if self.eth_price_usd else None
            
            tx_data = {
                'hash': tx_hash.hex(),
                'from': tx['from'],
                'to': tx['to'],
                'value': str(value_eth),
                'value_usd': value_usd,
                'gasPrice': str(gas_price_gwei),
                'blockNumber': tx['blockNumber'],
                'timestamp': int(time.time()),
                'type': self.get_transaction_type(tx),
                'isLarge': False  # Will be determined per user
            }
            
            # Store in database
            tx_id = self.db.insert_transaction(tx_data)
            
            if tx_id:
                print(f"🐋 New transaction: {value_eth} ETH")
                
                # Check and send alerts to relevant users
                self.check_and_send_alerts(tx_data, from_addr, to_addr)
            
            return tx_data
            
        except Exception as e:
            print(f"❌ Error processing transaction: {e}")
            return None
    
    def monitor_block(self, block_number):
        """Monitor a single block for whale transactions"""
        try:
            block = self.w3.eth.get_block(block_number, full_transactions=True)
            
            # Record gas price
            if block['baseFeePerGas']:
                gas_price_gwei = self.w3.from_wei(block['baseFeePerGas'], 'gwei')
                self.db.insert_gas_price(int(gas_price_gwei), int(time.time()))
            
            # Process transactions
            whale_txs = []
            for tx in block['transactions']:
                tx_data = self.process_transaction(tx['hash'])
                if tx_data:
                    whale_txs.append(tx_data)
            
            return whale_txs
            
        except Exception as e:
            print(f"❌ Error monitoring block {block_number}: {e}")
            return []
    
    def start_monitoring(self):
        """Start monitoring blockchain in real-time"""
        print("🚀 Starting whale monitor...")
        
        # Get current block
        self.last_block = self.w3.eth.block_number
        print(f"📦 Starting from block: {self.last_block}")
        
        # Update ETH price every 5 minutes
        last_price_update = time.time()
        
        while True:
            try:
                current_block = self.w3.eth.block_number
                
                # Process new blocks
                if current_block > self.last_block:
                    for block_num in range(self.last_block + 1, current_block + 1):
                        print(f"🔍 Scanning block {block_num}...")
                        self.monitor_block(block_num)
                    
                    self.last_block = current_block
                
                # Update ETH price every 5 minutes
                if time.time() - last_price_update > 300:
                    self.update_eth_price()
                    last_price_update = time.time()
                
                # Wait before checking again
                time.sleep(12)  # Ethereum block time ~12 seconds
                
            except KeyboardInterrupt:
                print("\n⏹️  Stopping monitor...")
                break
            except Exception as e:
                print(f"❌ Error in monitoring loop: {e}")
                time.sleep(5)

if __name__ == "__main__":
    import config
    
    if not config.RPC_URL:
        print("❌ Error: RPC_URL not configured in .env file")
        exit(1)
    
    monitor = WhaleMonitor(config.RPC_URL)
    monitor.start_monitoring()