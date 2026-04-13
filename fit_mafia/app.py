import datetime
from dateutil.relativedelta import relativedelta
import os
import uuid
import base64
from flask import render_template, Blueprint, request, Response, session, redirect, url_for, jsonify
from fit_mafia.models import db, Session, Member, Transaction
from sqlalchemy.orm import class_mapper

template_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), 'templates'))
app = Blueprint('fit_mafia', __name__, template_folder=template_dir)

AUTH_REALM = 'Basic realm="Login Required"'

def handle_session_timeout(now):
    last_active = datetime.datetime.fromisoformat(session['last_active'])
    if now - last_active > datetime.timedelta(minutes=30):
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
    """Check authentication before every request in this Blueprint."""
    if request.endpoint == 'fit_mafia.logout':
        return None

    auth = request.authorization
    if not auth or auth.password != "prashanth" or auth.username != "prashanth":
        return Response(
            'Could not verify your access level for that URL.\n'
            'You have to login with proper credentials', 401,
            {'WWW-Authenticate': AUTH_REALM})
            
    now = datetime.datetime.now()

    if 'session_id' in session and 'last_active' in session:
        if handle_session_timeout(now):
            return Response('Session expired due to inactivity. Please login again.', 401,
                            {'WWW-Authenticate': AUTH_REALM})

    session.permanent = True
    if 'session_id' not in session:
        try:
            new_session_id = str(uuid.uuid4())
            new_record = Session(session_id=new_session_id,
                                 start_time=str(now),
                                 user_name=str(auth.username))
            db.session.add(new_record)
            db.session.commit()
            session['session_id'] = new_session_id
            print(f"New session created and recorded: {new_session_id}")
        except Exception as e:
            db.session.rollback()
            print(e)
    else:
        print(f"Continuing session: {session['session_id']}")
        
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

    # Pass current_user dict (we use auth username from request.authorization)
    current_user = {"username": request.authorization.username if request.authorization else "Admin"}
    
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
    
    if not joining_date:
        joining_date = datetime.date.today().isoformat()

    # Determine status if it's a new registration vs update, but don't strictly require plan here yet 
    # since we removed subscription fields from registration
    
    photo = None
    if 'photo' in request.files:
        photo_file = request.files['photo']
        if photo_file.filename != '':
            # To simplify for the example, we read the photo as base64 and store the string.
            # In a real app, you'd save it to a cloud bucket or local filesystem and save the path.
            photo_bytes = photo_file.read()
            photo = "data:" + photo_file.content_type + ";base64," + base64.b64encode(photo_bytes).decode('utf-8')

    if mobile_number:
        try:
            # Check if member exists to retain old photo if new one isn't uploaded during edit
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
                status='active' # Set as active by default
            )
            # If the columns height, weight, bmi still exist in the database, 
            # they will just receive None as we don't pass them in the constructor,
            # which is fine since they have nullable=True.
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
                
                # Check status based on new end date
                today = datetime.date.today()
                try:
                    end_date = datetime.date.fromisoformat(subscription_end_date)
                    if end_date < today:
                        member.status = 'expired'
                    else:
                        member.status = 'active'
                except Exception:
                    member.status = 'active' # fallback

                db.session.commit()
                
                # Register a transaction for this renewal if amount and payment method are provided
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
            # check and update status just in case it's fetched directly without hitting /fitmafia first
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

            # Serialize the SQLAlchemy model to a dict
            columns = [c.key for c in class_mapper(member.__class__).columns]
            member_dict = {c: getattr(member, c) for c in columns}
            return jsonify(member_dict)
        return jsonify({"error": "Member not found"}), 404
    except Exception as e:
        print(e)
        return jsonify({"error": "An error occurred"}), 500

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
    return Response(
        'Logged out successfully.', 401,
        {'WWW-Authenticate': AUTH_REALM})