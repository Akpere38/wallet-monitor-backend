import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import requests
import config

class EmailService:
    def __init__(self):
        self.smtp_server = config.SMTP_SERVER
        self.smtp_port = config.SMTP_PORT
        self.smtp_user = config.SMTP_USER
        self.smtp_password = config.SMTP_PASSWORD
        self.from_email = config.FROM_EMAIL
    
    def send_alert_email(self, to_email, wallet_name, wallet_address, tx_hash, value_eth, value_usd, tx_type, direction):
        """Send email alert for large transaction"""
        
        subject = f"🚨 Large Transaction Alert: {wallet_name}"
        
        # Create beautiful HTML email
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ 
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
                    line-height: 1.6; 
                    color: #1f2937;
                    margin: 0;
                    padding: 0;
                    background-color: #f3f4f6;
                }}
                .container {{ 
                    max-width: 600px; 
                    margin: 40px auto; 
                    background: white;
                    border-radius: 16px;
                    overflow: hidden;
                    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                }}
                .header {{ 
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                    color: white; 
                    padding: 40px 30px; 
                    text-align: center;
                }}
                .header h1 {{
                    margin: 0;
                    font-size: 28px;
                    font-weight: 700;
                }}
                .content {{ 
                    padding: 40px 30px;
                }}
                .alert-box {{ 
                    background: #fef2f2;
                    border-left: 4px solid #ef4444; 
                    padding: 24px; 
                    margin: 24px 0; 
                    border-radius: 8px;
                }}
                .alert-box h2 {{
                    margin-top: 0;
                    color: #991b1b;
                    font-size: 20px;
                }}
                .detail-row {{ 
                    display: flex; 
                    justify-content: space-between; 
                    padding: 12px 0; 
                    border-bottom: 1px solid #e5e7eb;
                }}
                .detail-row:last-child {{
                    border-bottom: none;
                }}
                .label {{ 
                    font-weight: 600; 
                    color: #6b7280;
                    font-size: 14px;
                }}
                .value {{ 
                    color: #111827;
                    font-weight: 500;
                    text-align: right;
                }}
                .amount {{ 
                    font-size: 32px; 
                    font-weight: 700;
                    color: {"#ef4444" if direction == "outgoing" else "#10b981"};
                    margin: 20px 0;
                    text-align: center;
                }}
                .usd-amount {{
                    font-size: 18px;
                    color: #6b7280;
                    text-align: center;
                    margin-top: -10px;
                }}
                .button {{ 
                    display: inline-block; 
                    background: #667eea; 
                    color: white; 
                    padding: 14px 32px; 
                    text-decoration: none; 
                    border-radius: 8px; 
                    margin-top: 24px;
                    font-weight: 600;
                    text-align: center;
                }}
                .direction-badge {{
                    display: inline-block;
                    padding: 6px 12px;
                    border-radius: 20px;
                    font-size: 12px;
                    font-weight: 600;
                    background: {"#fee2e2" if direction == "outgoing" else "#d1fae5"};
                    color: {"#991b1b" if direction == "outgoing" else "#065f46"};
                }}
                .footer {{ 
                    text-align: center; 
                    color: #9ca3af; 
                    font-size: 13px; 
                    padding: 24px 30px;
                    background: #f9fafb;
                    border-top: 1px solid #e5e7eb;
                }}
                .footer a {{
                    color: #667eea;
                    text-decoration: none;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🐋 Whale Transaction Alert</h1>
                </div>
                <div class="content">
                    <div class="alert-box">
                        <h2>Large Transaction Detected!</h2>
                        <p style="color: #4b5563; margin-bottom: 20px;">
                            A significant transaction has been detected on your monitored wallet.
                        </p>
                        
                        <div class="detail-row">
                            <span class="label">Wallet Name</span>
                            <span class="value">{wallet_name}</span>
                        </div>
                        
                        <div class="detail-row">
                            <span class="label">Address</span>
                            <span class="value" style="font-family: monospace; font-size: 12px;">
                                {wallet_address[:10]}...{wallet_address[-8:]}
                            </span>
                        </div>
                        
                        <div class="detail-row">
                            <span class="label">Type</span>
                            <span class="value">{tx_type}</span>
                        </div>
                        
                        <div class="detail-row">
                            <span class="label">Direction</span>
                            <span class="value">
                                <span class="direction-badge">
                                    {"Outgoing ➡️" if direction == "outgoing" else "Incoming ⬅️"}
                                </span>
                            </span>
                        </div>
                    </div>
                    
                    <div class="amount">
                        {value_eth} ETH
                    </div>
                    {f'<div class="usd-amount">≈ ${value_usd:,.2f} USD</div>' if value_usd else ''}
                    
                    <div style="text-align: center;">
                        <a href="https://etherscan.io/tx/{tx_hash}" class="button">
                            View on Etherscan →
                        </a>
                    </div>
                    
                    <p style="margin-top: 30px; color: #6b7280; font-size: 14px; text-align: center;">
                        This alert was triggered because the transaction exceeded your configured threshold.
                    </p>
                </div>
                
                <div class="footer">
                    <p style="margin: 5px 0;">
                        <strong>Whale Wallet Monitor</strong> - Real-time Ethereum Transaction Tracking
                    </p>
                    <p style="margin: 5px 0;">
                        Manage your alerts in your <a href="#">dashboard</a>
                    </p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Plain text version for email clients that don't support HTML
        text_body = f"""
WHALE TRANSACTION ALERT

A large transaction has been detected on your monitored wallet:

Wallet Name: {wallet_name}
Wallet Address: {wallet_address}
Transaction Type: {tx_type}
Direction: {"Outgoing ➡️" if direction == "outgoing" else "Incoming ⬅️"}
Amount: {value_eth} ETH {f"(≈ ${value_usd:,.2f} USD)" if value_usd else ""}

View transaction: https://etherscan.io/tx/{tx_hash}

---
Whale Wallet Monitor
Real-time Ethereum Transaction Tracking
        """
        
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.from_email
            msg['To'] = to_email
            
            # Attach both plain text and HTML versions
            part1 = MIMEText(text_body, 'plain')
            part2 = MIMEText(html_body, 'html')
            msg.attach(part1)
            msg.attach(part2)
            
            # Send email via Gmail SMTP
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()  # Upgrade to secure connection
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)
            
            print(f"✅ Alert email sent to {to_email}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to send email to {to_email}: {e}")
            return False
    
    def send_welcome_email(self, to_email, user_name=None):
        """Send welcome email to new users"""
        
        subject = "Welcome to Whale Wallet Monitor! 🐋"
        
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ 
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    line-height: 1.6; 
                    color: #1f2937;
                    margin: 0;
                    padding: 0;
                    background-color: #f3f4f6;
                }}
                .container {{ 
                    max-width: 600px; 
                    margin: 40px auto; 
                    background: white;
                    border-radius: 16px;
                    overflow: hidden;
                    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                }}
                .header {{ 
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                    color: white; 
                    padding: 50px 30px; 
                    text-align: center;
                }}
                .header h1 {{
                    margin: 0;
                    font-size: 32px;
                    font-weight: 700;
                }}
                .content {{ 
                    padding: 40px 30px;
                }}
                .feature {{
                    display: flex;
                    align-items: start;
                    margin: 20px 0;
                }}
                .feature-icon {{
                    font-size: 24px;
                    margin-right: 15px;
                }}
                .feature-text {{
                    flex: 1;
                }}
                .feature-text h3 {{
                    margin: 0 0 5px 0;
                    color: #111827;
                    font-size: 16px;
                }}
                .feature-text p {{
                    margin: 0;
                    color: #6b7280;
                    font-size: 14px;
                }}
                .button {{ 
                    display: inline-block; 
                    background: #667eea; 
                    color: white; 
                    padding: 14px 32px; 
                    text-decoration: none; 
                    border-radius: 8px; 
                    font-weight: 600;
                    margin-top: 20px;
                }}
                .footer {{ 
                    text-align: center; 
                    color: #9ca3af; 
                    font-size: 13px; 
                    padding: 24px 30px;
                    background: #f9fafb;
                    border-top: 1px solid #e5e7eb;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🐋 Welcome Aboard!</h1>
                    <p style="font-size: 18px; margin: 10px 0 0 0; opacity: 0.9;">
                        Start tracking Ethereum whales today
                    </p>
                </div>
                <div class="content">
                    <h2 style="color: #111827; margin-top: 0;">
                        {"Hi " + user_name + "!" if user_name else "Welcome!"}
                    </h2>
                    <p style="color: #4b5563; font-size: 16px;">
                        Thank you for joining Whale Wallet Monitor. You now have access to powerful
                        real-time Ethereum transaction tracking.
                    </p>
                    
                    <div style="margin: 30px 0;">
                        <div class="feature">
                            <div class="feature-icon">🎯</div>
                            <div class="feature-text">
                                <h3>Track Any Wallet</h3>
                                <p>Monitor any Ethereum address in real-time</p>
                            </div>
                        </div>
                        
                        <div class="feature">
                            <div class="feature-icon">🔔</div>
                            <div class="feature-text">
                                <h3>Custom Alerts</h3>
                                <p>Set unique thresholds for each wallet you track</p>
                            </div>
                        </div>
                        
                        <div class="feature">
                            <div class="feature-icon">📧</div>
                            <div class="feature-text">
                                <h3>Instant Notifications</h3>
                                <p>Get email alerts for large transactions immediately</p>
                            </div>
                        </div>
                        
                        <div class="feature">
                            <div class="feature-icon">⛽</div>
                            <div class="feature-text">
                                <h3>Gas Analytics</h3>
                                <p>Track gas prices and transaction patterns</p>
                            </div>
                        </div>
                    </div>
                    
                    <p style="margin-top: 30px; color: #6b7280; font-size: 14px; text-align: center;">
                        Login to your dashboard to add your first wallet!
                    </p>
                </div>
                
                <div class="footer">
                    <p style="margin: 5px 0;">
                        <strong>Whale Wallet Monitor</strong>
                    </p>
                    <p style="margin: 5px 0;">
                        Real-time Ethereum Transaction Tracking
                    </p>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_body = f"""
Welcome to Whale Wallet Monitor!

{"Hi " + user_name + "!" if user_name else "Welcome!"}

Thank you for joining Whale Wallet Monitor. You now have access to:

🎯 Track Any Wallet - Monitor any Ethereum address in real-time
🔔 Custom Alerts - Set unique thresholds for each wallet
📧 Instant Notifications - Get email alerts for large transactions
⛽ Gas Analytics - Track gas prices and transaction patterns

Login to your dashboard to get started!

---
Whale Wallet Monitor
Real-time Ethereum Transaction Tracking
        """
        
        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.from_email
            msg['To'] = to_email
            
            part1 = MIMEText(text_body, 'plain')
            part2 = MIMEText(html_body, 'html')
            msg.attach(part1)
            msg.attach(part2)
            
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)
            
            print(f"✅ Welcome email sent to {to_email}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to send welcome email to {to_email}: {e}")
            return False


# Helper function to get ETH price in USD
def get_eth_price_usd():
    """Get current ETH price from CoinGecko API (free, no API key needed)"""
    try:
        response = requests.get(
            'https://api.coingecko.com/api/v3/simple/price?ids=ethereum&vs_currencies=usd',
            timeout=5
        )
        data = response.json()
        return data['ethereum']['usd']
    except Exception as e:
        print(f"❌ Failed to fetch ETH price: {e}")
        return None