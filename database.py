import sqlite3
from datetime import datetime
import json
import hashlib
import secrets

class Database:
    def __init__(self, db_name='whale_monitor.db'):
        self.db_name = db_name
        self.init_db()
    
    def init_db(self):
        """Initialize database tables"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        # Users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                api_key TEXT UNIQUE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_verified BOOLEAN DEFAULT 0
            )
        ''')
        
        # User wallets to track
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_wallets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                wallet_address TEXT NOT NULL,
                wallet_name TEXT NOT NULL,
                large_tx_threshold REAL DEFAULT 100.0,
                email_alerts BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id),
                UNIQUE(user_id, wallet_address)
            )
        ''')
        
        # Transactions table (updated)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tx_hash TEXT UNIQUE NOT NULL,
                from_address TEXT NOT NULL,
                to_address TEXT,
                value TEXT NOT NULL,
                value_usd REAL,
                gas_price TEXT NOT NULL,
                block_number INTEGER,
                timestamp INTEGER,
                tx_type TEXT,
                is_large BOOLEAN,
                alert_sent BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Email alerts log
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS email_alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                transaction_id INTEGER NOT NULL,
                email_sent BOOLEAN DEFAULT 0,
                sent_at TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (transaction_id) REFERENCES transactions (id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS gas_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                gas_price INTEGER NOT NULL,
                timestamp INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    # User management methods
    def create_user(self, email, password):
        """Create a new user"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        api_key = secrets.token_urlsafe(32)
        
        try:
            cursor.execute('''
                INSERT INTO users (email, password_hash, api_key)
                VALUES (?, ?, ?)
            ''', (email, password_hash, api_key))
            conn.commit()
            user_id = cursor.lastrowid
            conn.close()
            return {'id': user_id, 'email': email, 'api_key': api_key}
        except sqlite3.IntegrityError:
            conn.close()
            return None
    
    def get_user_by_id(self, user_id):
        """Get user by ID"""
        conn = sqlite3.connect(self.db_name)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
        user = cursor.fetchone()
        conn.close()
        
        return dict(user) if user else None
    
    def verify_user(self, email, password):
        """Verify user credentials"""
        conn = sqlite3.connect(self.db_name)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        cursor.execute('''
            SELECT * FROM users 
            WHERE email = ? AND password_hash = ?
        ''', (email, password_hash))
        
        user = cursor.fetchone()
        conn.close()
        
        return dict(user) if user else None
    
    def get_user_by_api_key(self, api_key):
        """Get user by API key"""
        conn = sqlite3.connect(self.db_name)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM users WHERE api_key = ?', (api_key,))
        user = cursor.fetchone()
        conn.close()
        
        return dict(user) if user else None
    
    # Wallet management
    def add_user_wallet(self, user_id, wallet_address, wallet_name, threshold=100.0):
        """Add wallet to user's tracking list"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO user_wallets 
                (user_id, wallet_address, wallet_name, large_tx_threshold)
                VALUES (?, ?, ?, ?)
            ''', (user_id, wallet_address.lower(), wallet_name, threshold))
            conn.commit()
            wallet_id = cursor.lastrowid
            conn.close()
            return wallet_id
        except sqlite3.IntegrityError:
            conn.close()
            return None
    
    def get_user_wallets(self, user_id):
        """Get all wallets for a user"""
        conn = sqlite3.connect(self.db_name)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM user_wallets 
            WHERE user_id = ?
            ORDER BY created_at DESC
        ''', (user_id,))
        
        wallets = cursor.fetchall()
        conn.close()
        
        return [dict(w) for w in wallets]
    
    def delete_user_wallet(self, user_id, wallet_id):
        """Remove wallet from tracking"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('''
            DELETE FROM user_wallets 
            WHERE id = ? AND user_id = ?
        ''', (wallet_id, user_id))
        
        deleted = cursor.rowcount > 0
        conn.commit()
        conn.close()
        return deleted
    
    def update_wallet_threshold(self, user_id, wallet_id, threshold):
        """Update alert threshold for wallet"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE user_wallets 
            SET large_tx_threshold = ?
            WHERE id = ? AND user_id = ?
        ''', (threshold, wallet_id, user_id))
        
        updated = cursor.rowcount > 0
        conn.commit()
        conn.close()
        return updated
    
    def get_all_tracked_wallets(self):
        """Get all wallets being tracked by any user"""
        conn = sqlite3.connect(self.db_name)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('SELECT DISTINCT wallet_address FROM user_wallets')
        wallets = cursor.fetchall()
        conn.close()
        
        return [w['wallet_address'] for w in wallets]
    
    def get_users_tracking_wallet(self, wallet_address):
        """Get all users tracking a specific wallet"""
        conn = sqlite3.connect(self.db_name)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT u.id, u.email, uw.wallet_name, uw.large_tx_threshold
            FROM users u
            JOIN user_wallets uw ON u.id = uw.user_id
            WHERE uw.wallet_address = ? AND uw.email_alerts = 1
        ''', (wallet_address.lower(),))
        
        users = cursor.fetchall()
        conn.close()
        
        return [dict(u) for u in users]
    
    # Transaction methods (updated)
    def insert_transaction(self, tx_data):
        """Insert a new transaction"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO transactions 
                (tx_hash, from_address, to_address, value, value_usd, gas_price, 
                 block_number, timestamp, tx_type, is_large)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                tx_data['hash'],
                tx_data['from'],
                tx_data['to'],
                tx_data['value'],
                tx_data.get('value_usd'),
                tx_data['gasPrice'],
                tx_data['blockNumber'],
                tx_data['timestamp'],
                tx_data.get('type', 'Transfer'),
                tx_data.get('isLarge', False)
            ))
            conn.commit()
            tx_id = cursor.lastrowid
            conn.close()
            return tx_id
        except sqlite3.IntegrityError:
            conn.close()
            return None
    
    def log_email_alert(self, user_id, transaction_id):
        """Log that an email alert was sent"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO email_alerts (user_id, transaction_id, email_sent, sent_at)
            VALUES (?, ?, 1, ?)
        ''', (user_id, transaction_id, datetime.now()))
        
        conn.commit()
        conn.close()
    
    def get_recent_transactions(self, limit=20, user_id=None):
        """Get recent transactions, optionally filtered by user's wallets"""
        conn = sqlite3.connect(self.db_name)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        if user_id:
            cursor.execute('''
                SELECT DISTINCT t.* FROM transactions t
                JOIN user_wallets uw ON 
                    (t.from_address = uw.wallet_address OR t.to_address = uw.wallet_address)
                WHERE uw.user_id = ?
                ORDER BY t.timestamp DESC 
                LIMIT ?
            ''', (user_id, limit))
        else:
            cursor.execute('''
                SELECT * FROM transactions 
                ORDER BY timestamp DESC 
                LIMIT ?
            ''', (limit,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    def insert_gas_price(self, gas_price, timestamp):
        """Insert gas price data"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO gas_history (gas_price, timestamp)
            VALUES (?, ?)
        ''', (gas_price, timestamp))
        
        conn.commit()
        conn.close()
    
    def get_gas_history(self, limit=100):
        """Get gas price history"""
        conn = sqlite3.connect(self.db_name)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM gas_history 
            ORDER BY timestamp DESC 
            LIMIT ?
        ''', (limit,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    


    def get_user_by_id(self, user_id):
        """Get user by ID"""
        conn = sqlite3.connect(self.db_name)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
        user = cursor.fetchone()
        conn.close()
        
        return dict(user) if user else None