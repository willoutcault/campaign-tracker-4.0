from datetime import datetime
from .extensions import db

class Pharma(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), unique=True, nullable=False)

class Brand(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    pharma_id = db.Column(db.Integer, db.ForeignKey('pharma.id'), nullable=False)
    pharma = db.relationship('Pharma', backref=db.backref('brands', lazy=True))

# Contracts can be linked to many brands
contract_brand = db.Table(
    'contract_brand',
    db.Column('contract_id', db.Integer, db.ForeignKey('contract.id'), primary_key=True),
    db.Column('brand_id', db.Integer, db.ForeignKey('brand.id'), primary_key=True),
)

class Contract(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    pharma_id = db.Column(db.Integer, db.ForeignKey('pharma.id'), nullable=False)
    start_date = db.Column(db.Date, nullable=True)
    end_date = db.Column(db.Date, nullable=True)
    pharma = db.relationship('Pharma', backref=db.backref('contracts', lazy=True))
    brands = db.relationship('Brand', secondary=contract_brand, backref='contracts')

class Client(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class TargetList(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    label = db.Column(db.String(200), nullable=False)
    s3_key = db.Column(db.String(300), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    size_bytes = db.Column(db.Integer, nullable=True)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)

class Campaign(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    contract_id = db.Column(db.Integer, db.ForeignKey('contract.id'), nullable=False)
    description = db.Column(db.Text, nullable=True)
    contract = db.relationship('Contract', backref=db.backref('campaigns', lazy=True))

class Program(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    campaign_id = db.Column(db.Integer, db.ForeignKey('campaign.id'), nullable=False)
    target_list_id = db.Column(db.Integer, db.ForeignKey('target_list.id'), nullable=True)
    campaign = db.relationship('Campaign', backref=db.backref('programs', lazy=True))
    target_list = db.relationship('TargetList', backref=db.backref('programs', lazy=True))

class Placement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    program_id = db.Column(db.Integer, db.ForeignKey('program.id'), nullable=False)
    channel = db.Column(db.String(100), nullable=True)  # e.g., email, app, web
    status = db.Column(db.String(50), nullable=True)    # planned, live, paused, complete
    start_date = db.Column(db.Date, nullable=True)
    end_date = db.Column(db.Date, nullable=True)
    program = db.relationship('Program', backref=db.backref('placements', lazy=True))
