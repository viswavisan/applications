import pytest
from unittest.mock import patch, MagicMock
from fit_mafia.app_controller import (
    home, logout, register_transaction, print_receipt,
    register_member, update_vitals, renew_subscription, get_member
)
from fit_mafia.constants import INTERNAL_SERVER_ERROR, MEMBER_NOT_FOUND
from fit_mafia.test.app import app

@patch('fit_mafia.app_controller.db.session')
def test_home_admin(mock_db_session):
    with app.test_request_context():
        from flask import session
        session['role'] = 'admin'
        session['username'] = 'admin'
        
        mock_member = MagicMock()
        mock_member.status = 'active'
        
        mock_query = mock_db_session.query.return_value
        mock_query.all.return_value = [mock_member]
        
        result = home()
        assert result['status'] == 'success'
        assert result['template_data']['total_members'] == 1
        assert result['template_data']['active_members'] == 1

@patch('fit_mafia.app_controller.db.session')
def test_home_member_success(mock_db_session):
    with app.test_request_context():
        from flask import session
        session['role'] = 'member'
        session['username'] = '9999999999'
        
        mock_member = MagicMock()
        mock_member.status = 'active'
        mock_member.to_dict.return_value = {'name': 'Test'}
        
        mock_query = mock_db_session.query.return_value
        mock_filter = mock_query.filter_by.return_value
        mock_filter.first.return_value = mock_member
        mock_filter.all.return_value = []
        
        result = home()
        assert result['status'] == 'success'
        assert result['template_data']['current_member']['name'] == 'Test'

@patch('fit_mafia.app_controller.db.session')
def test_logout(mock_db_session):
    with app.test_request_context():
        from flask import session
        session['session_id'] = 'session123'
        
        mock_record = MagicMock()
        mock_query = mock_db_session.query.return_value
        mock_filter = mock_query.filter_by.return_value
        mock_filter.first.return_value = mock_record
        
        logout()
        assert 'session_id' not in session
        assert mock_record.end_time is not None
        mock_db_session.commit.assert_called_once()

@patch('fit_mafia.app_controller.request')
@patch('fit_mafia.app_controller.db.session')
def test_register_transaction_admin(mock_db_session, mock_request):
    with app.test_request_context():
        from flask import session
        session['role'] = 'admin'
        
        mock_request.form.get.return_value = 'test_data'
        
        result = register_transaction()
        assert result['status'] == 'success'
        mock_db_session.merge.assert_called_once()
        mock_db_session.commit.assert_called_once()

@patch('fit_mafia.app_controller.db.session')
def test_register_transaction_unauthorized(mock_db_session):
    with app.test_request_context():
        from flask import session
        session['role'] = 'member'
        
        result = register_transaction()
        assert result['status'] == 'error'
        mock_db_session.merge.assert_not_called()

@patch('fit_mafia.app_controller.db.session')
def test_print_receipt_success(mock_db_session):
    with app.test_request_context():
        from flask import session
        session['role'] = 'admin'
        
        mock_txn = MagicMock()
        mock_txn.mobile_number = '9999999999'
        
        mock_query = mock_db_session.query.return_value
        mock_filter = mock_query.filter_by.return_value
        mock_filter.first.return_value = mock_txn
        
        result = print_receipt('TXN123')
        assert result['status'] == 'success'

@patch('fit_mafia.app_controller.request')
@patch('fit_mafia.app_controller.db.session')
def test_register_member_success(mock_db_session, mock_request):
    with app.test_request_context():
        from flask import session
        session['role'] = 'admin'
        
        mock_request.form.get.return_value = 'test_data'
        mock_request.files = {}
        
        mock_query = mock_db_session.query.return_value
        mock_filter = mock_query.filter_by.return_value
        mock_filter.first.return_value = None # Member doesn't exist
        
        result = register_member()
        assert result['status'] == 'success'
        mock_db_session.add.assert_called_once()
        mock_db_session.commit.assert_called_once()

@patch('fit_mafia.app_controller.request')
@patch('fit_mafia.app_controller.db.session')
def test_update_vitals_success(mock_db_session, mock_request):
    with app.test_request_context():
        from flask import session
        session['role'] = 'admin'
        
        mock_request.form.get.return_value = '9999999999'
        
        mock_member = MagicMock()
        mock_query = mock_db_session.query.return_value
        mock_filter = mock_query.filter_by.return_value
        mock_filter.first.return_value = mock_member
        
        result = update_vitals()
        assert result['status'] == 'success'
        mock_db_session.commit.assert_called_once()

@patch('fit_mafia.app_controller.request')
@patch('fit_mafia.app_controller.db.session')
def test_renew_subscription_success(mock_db_session, mock_request):
    with app.test_request_context():
        from flask import session
        session['role'] = 'admin'
        
        def mock_form_get(key):
            return {
                'mobile_number': '9999999999',
                'subscription': '1 Month',
                'subscription_start_date': '2023-01-01',
                'amount': '1000',
                'payment_method': 'Cash'
            }.get(key)
        
        mock_request.form.get.side_effect = mock_form_get
        
        mock_member = MagicMock()
        mock_query = mock_db_session.query.return_value
        mock_filter = mock_query.filter_by.return_value
        mock_filter.first.return_value = mock_member
        
        result = renew_subscription()
        assert result['status'] == 'success'
        mock_db_session.commit.assert_called_once()

@patch('fit_mafia.app_controller.db.session')
def test_get_member_success(mock_db_session):
    with app.test_request_context():
        from flask import session
        session['role'] = 'admin'
        
        mock_member = MagicMock()
        mock_query = mock_db_session.query.return_value
        mock_filter = mock_query.filter_by.return_value
        mock_filter.first.return_value = mock_member
        
        result = get_member('9999999999')
        assert result['status'] == 'success'
        assert result['message'] == mock_member
