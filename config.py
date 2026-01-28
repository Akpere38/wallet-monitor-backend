import os
from dotenv import load_dotenv

load_dotenv()

# Web3 Configuration
INFURA_URL = os.getenv('INFURA_URL')
ALCHEMY_URL = os.getenv('ALCHEMY_URL')
RPC_URL = INFURA_URL or ALCHEMY_URL

# Email Configuration (SMTP)
SMTP_SERVER = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
SMTP_PORT = int(os.getenv('SMTP_PORT', 587))
SMTP_USER = os.getenv('SMTP_USER')  # Your email
SMTP_PASSWORD = os.getenv('SMTP_PASSWORD')  # App password
FROM_EMAIL = os.getenv('FROM_EMAIL', SMTP_USER)

# JWT Secret for authentication
JWT_SECRET = os.getenv('JWT_SECRET', 'your-secret-key-change-this')

# Alert thresholds (defaults)
DEFAULT_LARGE_TRANSACTION_THRESHOLD = 100  # ETH
HIGH_GAS_THRESHOLD = 100  # Gwei

# API Configuration
API_HOST = '0.0.0.0'
API_PORT = 5000

# Whale labels - map addresses to names
WHALE_LABELS = {
    '0x00000000219ab540356cBB839Cbe05303d7705Fa': 'Ethereum Foundation',
    '0x220866B1A2219f40e72f5c628B65D54268cA3A9D': 'Vitalik Buterin',
    '0xd2DD7b597Fd2435b6dB61ddf48544fd931e6869F': 'Kraken 246',
    '0xf30ba13e4b04Ce5dC4D254Ae5FA95477800F0EB0': 'Kraken 251',
    '0x17E5545B11b468072283Cee1F066a059Fb0dbF24': 'Bithumb Hot Wallet',
    '0xA023f08c70A23aBc7EdFc5B6b5E171d78dFc947e': 'Crypto.com 22 Hot Wallet',
    '0xCFFAd3200574698b78f32232aa9D63eABD290703': 'Crypto.com 8 Hot Wallet',
    '0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb': 'Binance Hot Wallet',
    '0x47ac0Fb4F2D84898e4D9E7b4DaB3C24507a6D503': 'Binance Cold Wallet',
    '0xBE0eB53F46cd790Cd13851d5EFf43D12404d33E8': 'Bitfinex Wallet',
    '0x28C6c06298d514Db089934071355E5743bf21d60': 'Binance 14',
    '0x21a31Ee1afC51d94C2eFcCAa2092aD1028285549': 'Binance 15',
    '0xDFd5293D8e347dFe59E90eFd55b2956a1343963d': 'Binance 16',
    '0x0D0707963952f2fBA59dD06f2b425ace40b492Fe': 'Gate.io Hot Wallet',
    '0xD551234Ae421e3BCBA99A0Da6d736074f22192FF': 'Binance 8',

    # Add more whale addresses and their labels here
}



def get_whale_label(address):
    """Get label for a whale address"""
    if not address:
        return 'Unknown'
    
    # Check case-insensitive
    for whale_addr, label in WHALE_LABELS.items():
        if whale_addr.lower() == address.lower():
            return label
    
    return f"{address[:6]}...{address[-4:]}"