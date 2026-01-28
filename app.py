from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from datetime import timedelta
from database import Database
from email_service import EmailService
import config
import traceback

app = Flask(__name__)
app.config['JWT_SECRET_KEY'] = config.JWT_SECRET
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(days=30)
CORS(app)

# Initialize JWT
jwt = JWTManager(app)

db = Database()
email_service = EmailService()

# Error handler
@app.errorhandler(Exception)
def handle_error(e):
    traceback.print_exc()
    return jsonify({'error': str(e)}), 500

# ==================== HEALTH CHECK ====================

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'ok', 'message': 'Whale monitor API is running'}), 200

# ==================== AUTH ROUTES ====================

@app.route('/api/auth/signup', methods=['POST'])
def signup():
    """User signup"""
    try:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        
        if not email or not password:
            return jsonify({'error': 'Email and password required'}), 400
        
        if '@' not in email:
            return jsonify({'error': 'Invalid email format'}), 400
        
        if len(password) < 6:
            return jsonify({'error': 'Password must be at least 6 characters'}), 400
        
        user = db.create_user(email, password)
        
        if not user:
            return jsonify({'error': 'User already exists'}), 409
        
        try:
            email_service.send_welcome_email(email)
        except Exception as e:
            print(f"Failed to send welcome email: {e}")
        
        # Create token with user ID as string
        access_token = create_access_token(identity=str(user['id']))
        
        return jsonify({
            'message': 'User created successfully',
            'access_token': access_token,
            'user': {
                'id': user['id'],
                'email': user['email']
            }
        }), 201
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/auth/login', methods=['POST'])
def login():
    """User login"""
    try:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        
        if not email or not password:
            return jsonify({'error': 'Email and password required'}), 400
        
        user = db.verify_user(email, password)
        
        if not user:
            return jsonify({'error': 'Invalid credentials'}), 401
        
        # Create token with user ID as string
        access_token = create_access_token(identity=str(user['id']))
        
        return jsonify({
            'access_token': access_token,
            'user': {
                'id': user['id'],
                'email': user['email']
            }
        }), 200
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/auth/me', methods=['GET'])
@jwt_required()
def get_current_user():
    """Get current user info"""
    try:
        user_id_str = get_jwt_identity()
        user_id = int(user_id_str)  # Convert string back to int
        user = db.get_user_by_id(user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        return jsonify({
            'id': user['id'],
            'email': user['email']
        }), 200
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

# ==================== PUBLIC ROUTES ====================

@app.route('/api/whales', methods=['GET'])
def get_public_whales():
    """Get default whale wallets (public demo)"""
    whales = []
    for address, label in config.WHALE_LABELS.items():
        whales.append({
            'address': address.lower(),
            'label': label,
            'shortAddress': f"{address[:6]}...{address[-4:]}"
        })
    
    return jsonify(whales), 200

@app.route('/api/transactions', methods=['GET'])
def get_public_transactions():
    """Get recent transactions (public)"""
    limit = request.args.get('limit', 50, type=int)
    transactions = db.get_recent_transactions(limit)
    
    # Add wallet labels
    for tx in transactions:
        tx['from_label'] = config.get_whale_label(tx['from_address'])
        tx['to_label'] = config.get_whale_label(tx['to_address']) if tx['to_address'] else None
    
    return jsonify(transactions), 200


@app.route('/api/stats', methods=['GET'])
def get_public_stats():
    """Get overall statistics (public)"""
    transactions = db.get_recent_transactions(100)
    
    total_volume = sum(float(tx['value']) for tx in transactions)
    large_txs = sum(1 for tx in transactions if tx['is_large'])
    
    gas_history = db.get_gas_history(10)
    avg_gas = sum(g['gas_price'] for g in gas_history) / len(gas_history) if gas_history else 0
    
    whale_count = len(config.WHALE_LABELS)
    
    return jsonify({
        'totalVolume': round(total_volume, 2),
        'avgGasPrice': int(avg_gas),
        'largeTransactions': large_txs,
        'activeWhales': whale_count
    }), 200

@app.route('/api/gas-history', methods=['GET'])
def get_gas_history():
    """Get gas price history (public)"""
    limit = request.args.get('limit', 100, type=int)
    gas_data = db.get_gas_history(limit)
    
    return jsonify(gas_data), 200

# ==================== USER ROUTES ====================

@app.route('/api/user/wallets', methods=['GET'])
@jwt_required()
def get_user_wallets():
    """Get user's wallets"""
    try:
        user_id_str = get_jwt_identity()
        user_id = int(user_id_str)
        wallets = db.get_user_wallets(user_id)
        
        formatted_wallets = []
        for wallet in wallets:
            formatted_wallets.append({
                'id': wallet['id'],
                'address': wallet['wallet_address'],
                'label': wallet['wallet_name'],
                'shortAddress': f"{wallet['wallet_address'][:6]}...{wallet['wallet_address'][-4:]}",
                'threshold': wallet['large_tx_threshold'],
                'email_alerts': wallet['email_alerts']
            })
        
        return jsonify(formatted_wallets), 200
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/user/wallets', methods=['POST'])
@jwt_required()
def add_user_wallet():
    """Add wallet"""
    try:
        user_id_str = get_jwt_identity()
        user_id = int(user_id_str)
        data = request.get_json()
        
        wallet_address = data.get('wallet_address')
        wallet_name = data.get('wallet_name')
        threshold = data.get('threshold', 100.0)
        
        if not wallet_address or not wallet_name:
            return jsonify({'error': 'Wallet address and name required'}), 400
        
        if not wallet_address.startswith('0x') or len(wallet_address) != 42:
            return jsonify({'error': 'Invalid Ethereum address'}), 400
        
        wallet_id = db.add_user_wallet(user_id, wallet_address, wallet_name, threshold)
        
        if not wallet_id:
            return jsonify({'error': 'Wallet already being tracked'}), 409
        
        return jsonify({
            'message': 'Wallet added successfully',
            'wallet_id': wallet_id
        }), 201
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/user/wallets/<int:wallet_id>', methods=['DELETE'])
@jwt_required()
def delete_user_wallet(wallet_id):
    """Remove wallet"""
    try:
        user_id_str = get_jwt_identity()
        user_id = int(user_id_str)
        
        deleted = db.delete_user_wallet(user_id, wallet_id)
        
        if not deleted:
            return jsonify({'error': 'Wallet not found'}), 404
        
        return jsonify({'message': 'Wallet removed successfully'}), 200
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/user/wallets/<int:wallet_id>/threshold', methods=['PUT'])
@jwt_required()
def update_wallet_threshold(wallet_id):
    """Update threshold"""
    try:
        user_id_str = get_jwt_identity()
        user_id = int(user_id_str)
        data = request.get_json()
        
        threshold = data.get('threshold')
        
        if threshold is None or threshold < 0:
            return jsonify({'error': 'Valid threshold required'}), 400
        
        updated = db.update_wallet_threshold(user_id, wallet_id, threshold)
        
        if not updated:
            return jsonify({'error': 'Wallet not found'}), 404
        
        return jsonify({'message': 'Threshold updated successfully'}), 200
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/user/transactions', methods=['GET'])
@jwt_required()
def get_user_transactions():
    """Get user's transactions"""
    try:
        user_id_str = get_jwt_identity()
        user_id = int(user_id_str)
        limit = request.args.get('limit', 50, type=int)
        
        transactions = db.get_recent_transactions(limit, user_id=user_id)
        
        # Get user's wallet names
        user_wallets = db.get_user_wallets(user_id)
        wallet_map = {w['wallet_address'].lower(): w['wallet_name'] for w in user_wallets}
        
        # Add wallet labels (prioritize user's custom names)
        for tx in transactions:
            from_addr = tx['from_address'].lower()
            to_addr = tx['to_address'].lower() if tx['to_address'] else None
            
            # Check user's wallets first, then fall back to default labels
            tx['from_label'] = wallet_map.get(from_addr) or config.get_whale_label(tx['from_address'])
            tx['to_label'] = wallet_map.get(to_addr) or config.get_whale_label(tx['to_address']) if tx['to_address'] else None
        
        return jsonify(transactions), 200
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/user/stats', methods=['GET'])
@jwt_required()
def get_user_stats():
    """Get user's stats"""
    try:
        user_id_str = get_jwt_identity()
        user_id = int(user_id_str)
        
        transactions = db.get_recent_transactions(100, user_id=user_id)
        wallets = db.get_user_wallets(user_id)
        
        total_volume = sum(float(tx['value']) for tx in transactions)
        large_txs = sum(1 for tx in transactions if tx['is_large'])
        
        gas_history = db.get_gas_history(10)
        avg_gas = sum(g['gas_price'] for g in gas_history) / len(gas_history) if gas_history else 0
        
        return jsonify({
            'totalVolume': round(total_volume, 2),
            'avgGasPrice': int(avg_gas),
            'largeTransactions': large_txs,
            'activeWhales': len(wallets)
        }), 200
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("🚀 Starting Whale Monitor API...")
    app.run(host=config.API_HOST, port=config.API_PORT, debug=True)