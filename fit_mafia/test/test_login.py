import pytest
from unittest.mock import patch, MagicMock
from fit_mafia.app_controller import login
from fit_mafia.constants import INTERNAL_SERVER_ERROR

@patch('fit_mafia.app_controller.session', new_callable=dict)
@patch('fit_mafia.app_controller.create_db_session')
@patch('fit_mafia.app_controller.db.session')
def test_login_admin_success(mock_db_session, mock_create_db_session, mock_session):
    result = login('admin', 'admin')
    
    assert result == {'status': 'success', 'message': 'valid login credentials'}
    assert mock_session['role'] == 'admin'
    assert mock_session['display_name'] == 'Admin'
    assert mock_session['logged_in'] is True
    assert mock_session['username'] == 'admin'
    assert 'last_active' in mock_session
    mock_create_db_session.assert_called_once_with('admin')


@patch('fit_mafia.app_controller.session', new_callable=dict)
def test_login_admin_failure(mock_session):
    result = login('admin', 'wrong_password')
    
    assert result == {'status': 'failure', 'message': 'Invalid login credentials'}
    assert 'role' not in mock_session


@patch('fit_mafia.app_controller.session', new_callable=dict)
@patch('fit_mafia.app_controller.create_db_session')
@patch('fit_mafia.app_controller.db.session')
def test_login_member_success(mock_db_session, mock_create_db_session, mock_session):
    mock_member = MagicMock()
    mock_member.password = 'password123'
    mock_member.first_name = 'John'
    mock_member.last_name = 'Doe'
    
    mock_query = mock_db_session.query.return_value
    mock_filter = mock_query.filter_by.return_value
    mock_filter.first.return_value = mock_member
    
    result = login('9999999999', 'password123')
    
    assert result == {'status': 'success', 'message': 'valid login credentials'}
    assert mock_session['role'] == 'member'
    assert mock_session['display_name'] == 'John Doe'
    assert mock_session['logged_in'] is True
    assert mock_session['username'] == '9999999999'
    assert 'last_active' in mock_session
    mock_create_db_session.assert_called_once_with('9999999999')


@patch('fit_mafia.app_controller.session', new_callable=dict)
@patch('fit_mafia.app_controller.db.session')
def test_login_member_failure_wrong_password(mock_db_session, mock_session):
    mock_member = MagicMock()
    mock_member.password = 'password123'
    
    mock_query = mock_db_session.query.return_value
    mock_filter = mock_query.filter_by.return_value
    mock_filter.first.return_value = mock_member
    
    result = login('9999999999', 'wrong_password')
    
    assert result == {'status': 'failure', 'message': 'Invalid login credentials'}


@patch('fit_mafia.app_controller.session', new_callable=dict)
@patch('fit_mafia.app_controller.db.session')
def test_login_member_failure_not_found(mock_db_session, mock_session):
    mock_query = mock_db_session.query.return_value
    mock_filter = mock_query.filter_by.return_value
    mock_filter.first.return_value = None
    
    result = login('9999999999', 'password123')
    
    assert result == {'status': 'failure', 'message': 'Invalid login credentials'}


@patch('fit_mafia.app_controller.db.session')
def test_login_exception(mock_db_session):
    mock_db_session.query.side_effect = Exception("Database error")
    
    result = login('9999999999', 'password123')
    
    assert result == {'status': 'error', 'message': INTERNAL_SERVER_ERROR}
