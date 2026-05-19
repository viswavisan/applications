import pytest
from unittest.mock import patch, MagicMock
from fit_mafia.app_controller import login
from fit_mafia.constants import INTERNAL_SERVER_ERROR
from fit_mafia.test.app import app

@patch('fit_mafia.app_controller.create_db_session')
@patch('fit_mafia.app_controller.db.session')
def test_login_admin_success(mock_db_session, mock_create_db_session):
    with app.test_request_context():
        result = login('admin', 'admin')
        
        from flask import session
        assert result == {'status': 'success', 'message': 'valid login credentials'}
        assert session['role'] == 'admin'
        assert session['display_name'] == 'Admin'
        assert session['logged_in'] is True
        assert session['username'] == 'admin'
        assert 'last_active' in session
        mock_create_db_session.assert_called_once_with('admin')


def test_login_admin_failure():
    with app.test_request_context():
        result = login('admin', 'wrong_password')
        
        from flask import session
        assert result == {'status': 'failure', 'message': 'Invalid login credentials'}
        assert 'role' not in session


@patch('fit_mafia.app_controller.create_db_session')
@patch('fit_mafia.app_controller.db.session')
def test_login_member_success(mock_db_session, mock_create_db_session):
    with app.test_request_context():
        mock_member = MagicMock()
        mock_member.password = 'password123'
        mock_member.first_name = 'John'
        mock_member.last_name = 'Doe'
        
        mock_query = mock_db_session.query.return_value
        mock_filter = mock_query.filter_by.return_value
        mock_filter.first.return_value = mock_member
        
        result = login('9999999999', 'password123')
        
        from flask import session
        assert result == {'status': 'success', 'message': 'valid login credentials'}
        assert session['role'] == 'member'
        assert session['display_name'] == 'John Doe'
        assert session['logged_in'] is True
        assert session['username'] == '9999999999'
        assert 'last_active' in session
        mock_create_db_session.assert_called_once_with('9999999999')


@patch('fit_mafia.app_controller.db.session')
def test_login_member_failure_wrong_password(mock_db_session):
    with app.test_request_context():
        mock_member = MagicMock()
        mock_member.password = 'password123'
        
        mock_query = mock_db_session.query.return_value
        mock_filter = mock_query.filter_by.return_value
        mock_filter.first.return_value = mock_member
        
        result = login('9999999999', 'wrong_password')
        
        assert result == {'status': 'failure', 'message': 'Invalid login credentials'}


@patch('fit_mafia.app_controller.db.session')
def test_login_member_failure_not_found(mock_db_session):
    with app.test_request_context():
        mock_query = mock_db_session.query.return_value
        mock_filter = mock_query.filter_by.return_value
        mock_filter.first.return_value = None
        
        result = login('9999999999', 'password123')
        
        assert result == {'status': 'failure', 'message': 'Invalid login credentials'}


@patch('fit_mafia.app_controller.db.session')
def test_login_exception(mock_db_session):
    with app.test_request_context():
        mock_db_session.query.side_effect = Exception("Database error")
        
        result = login('9999999999', 'password123')
        
        assert result == {'status': 'error', 'message': INTERNAL_SERVER_ERROR}
