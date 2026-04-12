import datetime
import os
import uuid
import base64
from flask import render_template, Blueprint, request, Response, session, redirect, url_for, jsonify
from fit_mafia.models import db, Session, Member
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


@app.route('/fitmafia', methods=['GET'])
def fitmafia():
    try:
        members = db.session.query(Member).all()
    except Exception as e:
        db.session.rollback()
        members = []
        print(f"Error fetching members: {e}")
    # Pass current_user dict (we use auth username from request.authorization)
    current_user = {"username": request.authorization.username if request.authorization else "Admin"}
    return render_template('test.html', members=members, current_user=current_user)

@app.route('/register_member', methods=['POST'])
def register_member():
    mobile_number = request.form.get('mobile_number')
    first_name = request.form.get('first_name')
    last_name = request.form.get('last_name')
    dob = request.form.get('dob')
    height = request.form.get('height')
    weight = request.form.get('weight')
    bmi = request.form.get('bmi')
    subscription = request.form.get('subscription')
    joining_date = request.form.get('joining_date')
    
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
                height=height,
                weight=weight,
                bmi=bmi,
                subscription=subscription,
                joining_date=joining_date,
                photo=photo
            )
            db.session.merge(new_member)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            print(f"Error registering/updating member: {e}")

    return redirect(url_for('fit_mafia.fitmafia'))

@app.route('/api/member/<mobile_number>', methods=['GET'])
def get_member(mobile_number):
    try:
        member = db.session.query(Member).filter_by(mobile_number=mobile_number).first()
        if member:
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
            
    session.pop('session_id', None)
    return Response(
        'Logged out successfully.', 401,
        {'WWW-Authenticate': AUTH_REALM})