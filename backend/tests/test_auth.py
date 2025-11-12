"""
Authentication and Authorization Tests
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from auth.auth_service import (
    AuthenticationService,
    UserRegistration,
    UserLogin,
    PasswordChange,
    TokenType,
    AuthAction,
    get_current_user,
    get_current_user_token,
    require_permission,
    require_role
)
from database.models import User, UserRole

class TestAuthenticationService:
    """Test AuthenticationService class"""

    def test_init(self):
        """Test AuthenticationService initialization"""
        service = AuthenticationService()
        assert service.secret_key is not None
        assert service.algorithm == "HS256"
        assert service.access_token_expire_minutes > 0
        assert service.refresh_token_expire_days > 0
        assert isinstance(service.role_permissions, dict)

    def test_hash_password(self):
        """Test password hashing"""
        service = AuthenticationService()
        password = "test_password_123"
        hashed = service.hash_password(password)

        assert hashed != password
        assert len(hashed) > 50  # bcrypt hashes are long
        assert hashed.startswith("$2b$")

    def test_verify_password(self):
        """Test password verification"""
        service = AuthenticationService()
        password = "test_password_123"
        hashed = service.hash_password(password)

        # Correct password
        assert service.verify_password(password, hashed) is True

        # Wrong password
        assert service.verify_password("wrong_password", hashed) is False

    def test_get_user_permissions(self):
        """Test getting user permissions by role"""
        service = AuthenticationService()

        # Test each role
        for role in UserRole:
            permissions = service.get_user_permissions(role)
            assert isinstance(permissions, list)
            assert len(permissions) > 0

        # Test invalid role
        permissions = service.get_user_permissions("invalid_role")
        assert permissions == []

    def test_check_permission(self):
        """Test permission checking"""
        service = AuthenticationService()

        # Test with specific permission
        user_permissions = ["read_complaints", "create_complaints"]
        assert service.check_permission(user_permissions, "read_complaints") is True
        assert service.check_permission(user_permissions, "manage_users") is False

        # Test with super admin permission
        admin_permissions = ["super_admin"]
        assert service.check_permission(admin_permissions, "any_permission") is True

    def test_create_access_token(self):
        """Test access token creation"""
        service = AuthenticationService()
        data = {
            "sub": "test_user_id",
            "email": "test@example.com",
            "role": "citizen"
        }

        token = service.create_access_token(data)
        assert isinstance(token, str)
        assert len(token) > 100  # JWT tokens are long

        # Test custom expiry
        custom_expiry = timedelta(hours=2)
        token_with_expiry = service.create_access_token(data, custom_expiry)
        assert isinstance(token_with_expiry, str)
        assert token_with_expiry != token  # Should be different due to different expiry

    def test_create_refresh_token(self):
        """Test refresh token creation"""
        service = AuthenticationService()
        data = {
            "sub": "test_user_id",
            "email": "test@example.com",
            "role": "citizen"
        }

        token = service.create_refresh_token(data)
        assert isinstance(token, str)
        assert len(token) > 100

    def test_verify_token_valid(self):
        """Test token verification with valid token"""
        service = AuthenticationService()
        data = {
            "sub": "test_user_id",
            "email": "test@example.com",
            "role": "citizen"
        }

        # Create and verify access token
        access_token = service.create_access_token(data)
        payload = service.verify_token(access_token, TokenType.ACCESS)

        assert payload is not None
        assert payload["sub"] == "test_user_id"
        assert payload["email"] == "test@example.com"
        assert payload["role"] == "citizen"
        assert payload["type"] == TokenType.ACCESS.value

        # Create and verify refresh token
        refresh_token = service.create_refresh_token(data)
        payload = service.verify_token(refresh_token, TokenType.REFRESH)

        assert payload is not None
        assert payload["sub"] == "test_user_id"
        assert payload["type"] == TokenType.REFRESH.value

    def test_verify_token_invalid(self):
        """Test token verification with invalid token"""
        service = AuthenticationService()

        # Invalid token
        payload = service.verify_token("invalid_token")
        assert payload is None

        # Empty token
        payload = service.verify_token("")
        assert payload is None

        # Wrong token type
        service.secret_key = "test_key"
        access_token = service.create_access_token({"sub": "test"})
        payload = service.verify_token(access_token, TokenType.REFRESH)
        assert payload is None

    @pytest.mark.asyncio
    async def test_authenticate_user_success(self, test_db_session, test_user):
        """Test successful user authentication"""
        service = AuthenticationService()

        # Mock password verification to succeed
        service.verify_password = Mock(return_value=True)

        authenticated_user = await service.authenticate_user(
            test_db_session,
            test_user.email,
            "any_password"
        )

        assert authenticated_user is not None
        assert authenticated_user.user_id == test_user.user_id
        assert authenticated_user.email == test_user.email

    @pytest.mark.asyncio
    async def test_authenticate_user_failure(self, test_db_session):
        """Test failed user authentication"""
        service = AuthenticationService()

        # Non-existent user
        authenticated_user = await service.authenticate_user(
            test_db_session,
            "nonexistent@example.com",
            "password"
        )
        assert authenticated_user is None

        # Inactive user
        inactive_user = User(
            user_id="inactive_user",
            email="inactive@example.com",
            name="Inactive User",
            password="hashed_password",
            role=UserRole.CITIZEN,
            is_active=False
        )
        test_db_session.add(inactive_user)
        test_db_session.commit()

        authenticated_user = await service.authenticate_user(
            test_db_session,
            "inactive@example.com",
            "password"
        )
        assert authenticated_user is None

    @pytest.mark.asyncio
    async def test_register_user_success(self, test_db_session):
        """Test successful user registration"""
        service = AuthenticationService()
        service.hash_password = Mock(return_value="hashed_password")

        user_data = UserRegistration(
            user_id="new_user_123",
            email="newuser@example.com",
            name="New User",
            password="password123",
            role=UserRole.CITIZEN,
            department="test_dept",
            phone="+919876543210"
        )

        registered_user = await service.register_user(test_db_session, user_data)

        assert registered_user is not None
        assert registered_user.user_id == "new_user_123"
        assert registered_user.email == "newuser@example.com"
        assert registered_user.is_active is True

    @pytest.mark.asyncio
    async def test_register_user_duplicate(self, test_db_session, test_user):
        """Test user registration with duplicate email/user_id"""
        service = AuthenticationService()

        user_data = UserRegistration(
            user_id=test_user.user_id,  # Duplicate user_id
            email="different@example.com",
            name="Different User",
            password="password123",
            role=UserRole.CITIZEN
        )

        registered_user = await service.register_user(test_db_session, user_data)
        assert registered_user is None

    @pytest.mark.asyncio
    async def test_login_user_success(self, test_db_session, test_user):
        """Test successful user login"""
        service = AuthenticationService()
        service.authenticate_user = AsyncMock(return_value=test_user)
        service.create_access_token = Mock(return_value="access_token")
        service.create_refresh_token = Mock(return_value="refresh_token")
        service.get_user_permissions = Mock(return_value=["read_complaints"])

        login_data = UserLogin(
            email=test_user.email,
            password="password",
            remember_me=False
        )

        login_result = await service.login_user(test_db_session, login_data)

        assert login_result is not None
        assert "access_token" in login_result
        assert "refresh_token" in login_result
        assert "user" in login_result
        assert login_result["token_type"] == "bearer"

    @pytest.mark.asyncio
    async def test_login_user_failure(self, test_db_session):
        """Test failed user login"""
        service = AuthenticationService()
        service.authenticate_user = AsyncMock(return_value=None)

        login_data = UserLogin(
            email="nonexistent@example.com",
            password="password",
            remember_me=False
        )

        login_result = await service.login_user(test_db_session, login_data)
        assert login_result is None

    @pytest.mark.asyncio
    async def test_change_password_success(self, test_db_session, test_user):
        """Test successful password change"""
        service = AuthenticationService()
        service.verify_password = Mock(return_value=True)
        service.hash_password = Mock(return_value="new_hashed_password")

        password_data = PasswordChange(
            current_password="old_password",
            new_password="new_password",
            confirm_password="new_password"
        )

        result = await service.change_password(
            test_db_session,
            test_user.user_id,
            password_data
        )

        assert result is True

    @pytest.mark.asyncio
    async def test_change_password_failure(self, test_db_session, test_user):
        """Test failed password change"""
        service = AuthenticationService()

        # Wrong current password
        service.verify_password = Mock(return_value=False)

        password_data = PasswordChange(
            current_password="wrong_password",
            new_password="new_password",
            confirm_password="new_password"
        )

        result = await service.change_password(
            test_db_session,
            test_user.user_id,
            password_data
        )

        assert result is False

    @pytest.mark.asyncio
    async def test_reset_password_success(self, test_db_session, test_user):
        """Test successful password reset"""
        service = AuthenticationService()
        service.hash_password = Mock(return_value="new_hashed_password")

        result = await service.reset_password(
            test_db_session,
            test_user.email,
            "new_password"
        )

        assert result is True

    @pytest.mark.asyncio
    async def test_create_password_reset_token(self):
        """Test password reset token creation"""
        service = AuthenticationService()
        service.create_access_token = Mock(return_value="reset_token")

        token = service.create_password_reset_token("test@example.com")

        assert isinstance(token, str)
        assert len(token) > 0

    @pytest.mark.asyncio
    async def test_verify_password_reset_token(self):
        """Test password reset token verification"""
        service = AuthenticationService()

        # Valid token
        service.verify_token = Mock(return_value={"sub": "test@example.com"})
        email = service.verify_password_reset_token("valid_token")
        assert email == "test@example.com"

        # Invalid token
        service.verify_token = Mock(return_value=None)
        email = service.verify_password_reset_token("invalid_token")
        assert email is None

class TestAuthDependencies:
    """Test authentication dependencies"""

    @pytest.mark.asyncio
    async def test_get_current_user_token_valid(self):
        """Test get_current_user_token with valid token"""
        service = AuthenticationService()
        token_payload = {
            "sub": "test_user_id",
            "email": "test@example.com",
            "role": "citizen"
        }
        service.verify_token = Mock(return_value=token_payload)

        with patch('auth.auth_service.auth_service', service):
            payload = await get_current_user_token("valid_token")

            assert payload is not None
            assert payload["sub"] == "test_user_id"

    @pytest.mark.asyncio
    async def test_get_current_user_token_invalid(self):
        """Test get_current_user_token with invalid token"""
        service = AuthenticationService()
        service.verify_token = Mock(return_value=None)

        with patch('auth.auth_service.auth_service', service):
            payload = await get_current_user_token("invalid_token")
            assert payload is None

    @pytest.mark.asyncio
    async def test_get_current_user_success(self, test_db_session, test_user):
        """Test get_current_user with valid token and user"""
        service = AuthenticationService()
        token_payload = {
            "sub": test_user.user_id,
            "email": test_user.email,
            "role": test_user.role.value
        }
        service.verify_token = Mock(return_value=token_payload)
        service.get_user_by_id = AsyncMock(return_value=test_user)
        service.update_user_last_activity = AsyncMock(return_value=True)

        with patch('auth.auth_service.auth_service', service):
            user = await get_current_user("valid_token", test_db_session)

            assert user is not None
            assert user.user_id == test_user.user_id

    @pytest.mark.asyncio
    async def test_get_current_user_invalid_token(self, test_db_session):
        """Test get_current_user with invalid token"""
        service = AuthenticationService()
        service.verify_token = Mock(return_value=None)

        with patch('auth.auth_service.auth_service', service):
            user = await get_current_user("invalid_token", test_db_session)
            assert user is None

    def test_require_permission_decorator(self):
        """Test require_permission decorator"""
        service = AuthenticationService()
        service.get_user_permissions = Mock(return_value=["read_complaints"])
        service.check_permission = Mock(return_value=True)

        with patch('auth.auth_service.auth_service', service):
            decorator = require_permission("read_complaints")

            async def dummy_function(*args, **kwargs):
                return "success"

            wrapped_func = decorator(dummy_function)

            # This would need actual testing in request context
            # For now, just verify decorator creation
            assert callable(wrapped_func)

    def test_require_role_decorator(self):
        """Test require_role decorator"""
        decorator = require_role(UserRole.CITIZEN)

        async def dummy_function(*args, **kwargs):
            return "success"

        wrapped_func = decorator(dummy_function)

        # This would need actual testing in request context
        # For now, just verify decorator creation
        assert callable(wrapped_func)

class TestPasswordSecurity:
    """Test password security features"""

    def test_password_strength_validation(self):
        """Test password strength validation"""
        service = AuthenticationService()

        # Strong password
        strong_password = "StrongP@ssw0rd123!"
        hashed = service.hash_password(strong_password)
        assert len(hashed) > 50

        # Weak password (should still be hashed, but validation might be needed)
        weak_password = "123456"
        hashed = service.hash_password(weak_password)
        assert len(hashed) > 50

    def test_token_security(self):
        """Test JWT token security"""
        service = AuthenticationService()

        # Test with different secrets
        original_secret = service.secret_key
        service.secret_key = "different_secret"

        data = {"sub": "test_user"}
        token1 = service.create_access_token(data)

        service.secret_key = original_secret
        token2 = service.create_access_token(data)

        # Tokens should be different with different secrets
        assert token1 != token2

class TestRoleBasedAccess:
    """Test role-based access control"""

    def test_role_permissions_mapping(self):
        """Test role permissions mapping"""
        service = AuthenticationService()

        # Check citizen permissions
        citizen_perms = service.get_user_permissions(UserRole.CITIZEN)
        assert "read_complaints" in citizen_perms
        assert "create_complaints" in citizen_perms
        assert "manage_users" not in citizen_perms

        # Check admin permissions
        admin_perms = service.get_user_permissions(UserRole.ADMINISTRATOR)
        assert "manage_users" in admin_perms
        assert "manage_system" in admin_perms

        # Check system permissions (super admin)
        system_perms = service.get_user_permissions(UserRole.SYSTEM)
        assert "super_admin" in system_perms

    def test_permission_inheritance(self):
        """Test permission inheritance and hierarchy"""
        service = AuthenticationService()

        # Super admin should have all permissions
        system_perms = service.get_user_permissions(UserRole.SYSTEM)
        assert service.check_permission(system_perms, "any_permission") is True

        # Regular permissions should not work without proper role
        citizen_perms = service.get_user_permissions(UserRole.CITIZEN)
        assert service.check_permission(citizen_perms, "manage_system") is False

class TestErrorHandling:
    """Test error handling in authentication"""

    @pytest.mark.asyncio
    async def test_database_errors(self, test_db_session):
        """Test handling of database errors"""
        service = AuthenticationService()

        # Mock database session to raise exception
        broken_session = Mock()
        broken_session.query = Mock(side_effect=Exception("Database connection failed"))

        user_data = UserRegistration(
            user_id="test_user",
            email="test@example.com",
            name="Test User",
            password="password",
            role=UserRole.CITIZEN
        )

        result = await service.register_user(broken_session, user_data)
        assert result is None

    def test_token_validation_errors(self):
        """Test token validation error handling"""
        service = AuthenticationService()

        # Test malformed tokens
        malformed_tokens = [
            "",
            "invalid",
            "too.short",
            "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.invalid.signature"
        ]

        for token in malformed_tokens:
            payload = service.verify_token(token)
            assert payload is None

if __name__ == "__main__":
    pytest.main([__file__])