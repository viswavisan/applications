import datetime
from dateutil.relativedelta import relativedelta
import os
import uuid
import base64
from flask import render_template, Blueprint, request, session, redirect, url_for, jsonify
from fit_mafia.models import db, Session, Member, Transaction
from sqlalchemy.orm import class_mapper

template_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), 'templates'))
app = Blueprint('fit_mafia', __name__, template_folder=template_dir)

# Instead of using HTTP Basic Auth globally, we'll handle login via a form and session.

def handle_session_timeout(now):
    if 'last_active' not in session:
        return False
    last_active = datetime.datetime.fromisoformat(session['last_active'])
    if now - last_active > datetime.timedelta(minutes=30): # increased to 30 mins
        session_id = session.get('session_id')
        try:
            record = db.session.query(Session).filter_by(session_id=session_id).first()
            if record:
                record.end_time = str(now)
                db.session.commit()
        except Exception as e:
            db.session.rollback()
            print(f"Error updating session end_time on timeout: {e}")
        
        session.clear()
        return True
    return False


@app.before_request
def require_auth():
    """Check authentication before every request in this Blueprint except public endpoints."""
    public_endpoints = ['fit_mafia.public_page', 'fit_mafia.login']
    
    # Allow static files if any
    if request.endpoint and request.endpoint.startswith('static'):
        return None

    if request.endpoint in public_endpoints:
        return None

    # Check if user is logged in
    if 'logged_in' not in session or not session['logged_in']:
        return redirect(url_for('fit_mafia.public_page'))
            
    now = datetime.datetime.now()

    if handle_session_timeout(now):
        # Redirect to public page with an optional message or just basic redirect
        return redirect(url_for('fit_mafia.public_page'))

    session.permanent = True
    if 'session_id' not in session:
        try:
            new_session_id = str(uuid.uuid4())
            new_record = Session(session_id=new_session_id,
                                 start_time=str(now),
                                 user_name=session.get('username', 'Admin'))
            db.session.add(new_record)
            db.session.commit()
            session['session_id'] = new_session_id
            print(f"New session created and recorded: {new_session_id}")
        except Exception as e:
            db.session.rollback()
            print(e)
        
    session['last_active'] = now.isoformat()
    return None

def update_member_statuses(members):
    today = datetime.date.today()
    updated = False
    for member in members:
        if member.subscription_end_date:
            try:
                end_date = datetime.date.fromisoformat(member.subscription_end_date)
                if end_date < today and member.status == 'active':
                    member.status = 'expired'
                    updated = True
                elif end_date >= today and member.status == 'expired':
                    member.status = 'active'
                    updated = True
            except Exception:
                pass
    if updated:
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            print(f"Error updating member statuses: {e}")

@app.route('/', methods=['GET'])
def public_page():
    # If already logged in, redirect to dashboard
    if session.get('logged_in'):
        return redirect(url_for('fit_mafia.fitmafia'))
    return render_template('index.html')

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')
    
    # Hardcoded credentials as before
    if username == "prashanth" and password == "prashanth":
        session['logged_in'] = True
        session['username'] = username
        session['last_active'] = datetime.datetime.now().isoformat()
        
        # Create DB session record
        try:
            new_session_id = str(uuid.uuid4())
            new_record = Session(session_id=new_session_id,
                                 start_time=str(datetime.datetime.now()),
                                 user_name=username)
            db.session.add(new_record)
            db.session.commit()
            session['session_id'] = new_session_id
        except Exception as e:
            db.session.rollback()
            print(f"Error recording login session: {e}")
            
        return redirect(url_for('fit_mafia.fitmafia'))
    else:
        # Invalid credentials
        return render_template('index.html', error="Invalid username or password")

@app.route('/fitmafia', methods=['GET'])
def fitmafia():
    total_members = 0
    active_members = 0
    inactive_members = 0
    transactions = []
    
    try:
        members = db.session.query(Member).all()
        update_member_statuses(members) # Update status before counting and rendering
        
        total_members = len(members)
        active_members = len([m for m in members if m.status == 'active'])
        inactive_members = total_members - active_members
        
        transactions = db.session.query(Transaction).all()
                
    except Exception as e:
        db.session.rollback()
        members = []
        print(f"Error fetching data: {e}")

    current_user = {"username": session.get('username', 'Admin')}
    
    return render_template('test.html', 
                           members=members, 
                           current_user=current_user, 
                           total_members=total_members, 
                           active_members=active_members,
                           inactive_members=inactive_members,
                           transactions=transactions)

def calculate_end_date(start_date_str, plan):
    if not start_date_str or not plan:
        return None
    try:
        start_date = datetime.date.fromisoformat(start_date_str)
        months = int(plan.split(' ')[0])
        end_date = start_date + relativedelta(months=months)
        return end_date.isoformat()
    except Exception:
        return None

@app.route('/register_member', methods=['POST'])
def register_member():
    mobile_number = request.form.get('mobile_number')
    first_name = request.form.get('first_name')
    last_name = request.form.get('last_name')
    dob = request.form.get('dob')
    gender = request.form.get('gender')
    email = request.form.get('email')
    address = request.form.get('address')
    joining_date = request.form.get('joining_date')
    captured_photo = request.form.get('captured_photo')
    
    if not joining_date:
        joining_date = datetime.date.today().isoformat()

    photo = None
    if 'photo' in request.files and request.files['photo'].filename != '':
        photo_file = request.files['photo']
        photo_bytes = photo_file.read()
        photo = "data:" + photo_file.content_type + ";base64," + base64.b64encode(photo_bytes).decode('utf-8')
    elif captured_photo:
        photo = captured_photo

    if mobile_number:
        try:
            existing_member = db.session.query(Member).filter_by(mobile_number=mobile_number).first()
            if existing_member and not photo:
                photo = existing_member.photo
                
            new_member = Member(
                mobile_number=mobile_number,
                first_name=first_name,
                last_name=last_name,
                dob=dob,
                gender=gender,
                email=email,
                address=address,
                joining_date=joining_date,
                photo=photo,
                status='active'
            )
            if existing_member:
                new_member.height = existing_member.height
                new_member.weight = existing_member.weight
                new_member.bmi = existing_member.bmi
                new_member.status = existing_member.status
                new_member.subscription = existing_member.subscription
                new_member.subscription_start_date = existing_member.subscription_start_date
                new_member.subscription_end_date = existing_member.subscription_end_date

            db.session.merge(new_member)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            print(f"Error registering/updating member: {e}")

    return redirect(url_for('fit_mafia.fitmafia'))

@app.route('/update_vitals', methods=['POST'])
def update_vitals():
    mobile_number = request.form.get('mobile_number')
    height = request.form.get('height')
    weight = request.form.get('weight')
    bmi = request.form.get('bmi')

    if mobile_number:
        try:
            member = db.session.query(Member).filter_by(mobile_number=mobile_number).first()
            if member:
                member.height = height
                member.weight = weight
                member.bmi = bmi
                db.session.commit()
                return jsonify({"success": True})
            return jsonify({"error": "Member not found"}), 404
        except Exception as e:
            db.session.rollback()
            print(f"Error updating vitals: {e}")
            return jsonify({"error": "Database error"}), 500
    return jsonify({"error": "Mobile number required"}), 400

@app.route('/renew_subscription', methods=['POST'])
def renew_subscription():
    mobile_number = request.form.get('mobile_number')
    subscription = request.form.get('subscription')
    subscription_start_date = request.form.get('subscription_start_date')
    subscription_end_date = request.form.get('subscription_end_date')
    amount = request.form.get('amount')
    discount = request.form.get('discount')
    payment_method = request.form.get('payment_method')

    if mobile_number and subscription and subscription_start_date:
        if not subscription_end_date:
            subscription_end_date = calculate_end_date(subscription_start_date, subscription)

        try:
            member = db.session.query(Member).filter_by(mobile_number=mobile_number).first()
            if member:
                member.subscription = subscription
                member.subscription_start_date = subscription_start_date
                member.subscription_end_date = subscription_end_date
                
                today = datetime.date.today()
                try:
                    end_date = datetime.date.fromisoformat(subscription_end_date)
                    if end_date < today:
                        member.status = 'expired'
                    else:
                        member.status = 'active'
                except Exception:
                    member.status = 'active'

                db.session.commit()
                
                if amount and payment_method:
                    transaction_id = f"TXN{str(uuid.uuid4())[:8].upper()}"
                    member_name = f"{member.first_name or ''} {member.last_name or ''}".strip()
                    if not member_name:
                        member_name = member.mobile_number
                        
                    new_txn = Transaction(
                        transaction_id=transaction_id,
                        member_name=member_name,
                        mobile_number=member.mobile_number,
                        date=today.isoformat(),
                        amount=amount,
                        discount=discount,
                        payment_method=payment_method,
                        status="Completed"
                    )
                    db.session.add(new_txn)
                    db.session.commit()

                return jsonify({"success": True})
            return jsonify({"error": "Member not found"}), 404
        except Exception as e:
            db.session.rollback()
            print(f"Error renewing subscription: {e}")
            return jsonify({"error": "Database error"}), 500
    return jsonify({"error": "Missing parameters"}), 400

@app.route('/register_transaction', methods=['POST'])
def register_transaction():
    transaction_id = request.form.get('transaction_id')
    member_name = request.form.get('member_name')
    mobile_number = request.form.get('mobile_number')
    date = request.form.get('date')
    amount = request.form.get('amount')
    payment_method = request.form.get('payment_method')
    status = request.form.get('status')
    
    if not transaction_id:
        transaction_id = f"TXN{str(uuid.uuid4())[:8].upper()}"

    try:
        new_txn = Transaction(
            transaction_id=transaction_id,
            member_name=member_name,
            mobile_number=mobile_number,
            date=date,
            amount=amount,
            payment_method=payment_method,
            status=status
        )
        db.session.merge(new_txn)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"Error registering transaction: {e}")

    return redirect(url_for('fit_mafia.fitmafia'))

@app.route('/api/member/<mobile_number>', methods=['GET'])
def get_member(mobile_number):
    try:
        member = db.session.query(Member).filter_by(mobile_number=mobile_number).first()
        if member:
            today = datetime.date.today()
            if member.subscription_end_date:
                try:
                    end_date = datetime.date.fromisoformat(member.subscription_end_date)
                    if end_date < today and member.status == 'active':
                        member.status = 'expired'
                        db.session.commit()
                    elif end_date >= today and member.status == 'expired':
                        member.status = 'active'
                        db.session.commit()
                except Exception:
                    pass

            columns = [c.key for c in class_mapper(member.__class__).columns]
            member_dict = {c: getattr(member, c) for c in columns}
            return jsonify(member_dict)
        return jsonify({"error": "Member not found"}), 404
    except Exception as e:
        print(e)
        return jsonify({"error": "An error occurred"}), 500

@app.route('/print_receipt/<transaction_id>', methods=['GET'])
def print_receipt(transaction_id):
    try:
        txn = db.session.query(Transaction).filter_by(transaction_id=transaction_id).first()
        if not txn:
            return "Transaction not found", 404
            
        member = db.session.query(Member).filter_by(mobile_number=txn.mobile_number).first()
        
        return render_template('receipt.html', txn=txn, member=member)
    except Exception as e:
        print(e)
        return "An error occurred", 500

@app.route('/logout', methods=['GET'])
def logout():
    session_id = session.get('session_id')
    if session_id:
        try:
            record = db.session.query(Session).filter_by(session_id=session_id).first()
            if record:
                record.end_time = str(datetime.datetime.now())
                db.session.commit()
        except Exception as e:
            db.session.rollback()
            print(f"Error updating session end_time: {e}")
            
    session.clear()
    return redirect(url_for('fit_mafia.public_page'))