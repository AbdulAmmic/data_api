from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.String(64), primary_key=True)
    full_name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    phone = db.Column(db.String(30), unique=True, nullable=True, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    wallet_balance_kobo = db.Column(db.BigInteger, default=0)  # store in kobo for accuracy

    def set_password(self, raw: str):
        self.password_hash = generate_password_hash(raw)

    def check_password(self, raw: str) -> bool:
        return check_password_hash(self.password_hash, raw)

class WalletTransaction(db.Model):
    __tablename__ = "wallet_transactions"
    id = db.Column(db.String(64), primary_key=True)
    user_id = db.Column(db.String(64), db.ForeignKey("users.id"), nullable=False, index=True)

    tx_type = db.Column(db.String(20), nullable=False)  # CREDIT / DEBIT
    amount_kobo = db.Column(db.BigInteger, nullable=False)
    status = db.Column(db.String(20), default="PENDING")  # PENDING / SUCCESS / FAILED
    narration = db.Column(db.String(255), nullable=True)

    # funding / external references
    provider = db.Column(db.String(30), nullable=True)  # PAYSTACK / DATASTATION
    reference = db.Column(db.String(120), unique=True, nullable=True, index=True)

    raw_response = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class ServicePurchase(db.Model):
    __tablename__ = "service_purchases"
    id = db.Column(db.String(64), primary_key=True)
    user_id = db.Column(db.String(64), db.ForeignKey("users.id"), nullable=False, index=True)

    service = db.Column(db.String(40), nullable=False)  # METER_VALIDATE / AIRTIME_PIN / EPIN
    amount_kobo = db.Column(db.BigInteger, nullable=False)
    status = db.Column(db.String(20), default="PENDING")  # PENDING / SUCCESS / FAILED
    provider = db.Column(db.String(30), default="DATASTATION")

    request_payload = db.Column(db.Text, nullable=True)
    response_payload = db.Column(db.Text, nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)



# ---- Roles ----
class Role(db.Model):
    __tablename__ = "roles"
    id = db.Column(db.String(32), primary_key=True)  # admin, user
    name = db.Column(db.String(50), unique=True, nullable=False)

class UserRole(db.Model):
    __tablename__ = "user_roles"
    user_id = db.Column(db.String(64), db.ForeignKey("users.id"), primary_key=True)
    role_id = db.Column(db.String(32), db.ForeignKey("roles.id"), primary_key=True)

# ---- Pricing ----
class PriceItem(db.Model):
    """
    Generic price table for all services.
    """
    __tablename__ = "price_items"
    id = db.Column(db.String(64), primary_key=True)

    service = db.Column(db.String(40), nullable=False)  
    # DATA, AIRTIME, ELECTRICITY, CABLE, AIRTIME_PIN, EPIN

    provider_code = db.Column(db.String(50), nullable=True)
    # Examples:
    # DATA: "mtn_1gb"
    # AIRTIME: "mtn"
    # ELECTRICITY: "ikeja-prepaid"
    # CABLE: "dstv-compact"
    # EPIN: "waec"

    provider_cost_kobo = db.Column(db.BigInteger, nullable=False)
    markup_type = db.Column(db.String(10), default="FLAT")  # FLAT | PERCENT
    markup_value = db.Column(db.Float, default=0.0)

    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def selling_price_kobo(self) -> int:
        if self.markup_type == "PERCENT":
            return int(self.provider_cost_kobo * (1 + self.markup_value / 100))
        return int(self.provider_cost_kobo + self.markup_value)
