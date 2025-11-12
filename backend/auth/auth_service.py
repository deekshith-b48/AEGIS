"""
Authentication and Authorization Service for Project AEGIS
Comprehensive security system with JWT, role-based access control, and audit logging
"""

import os
import secrets
import hashlib
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass
from enum import Enum

import jwt
import bcrypt
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from database.database import get_db
from database.models import User, AuditLog, UserRole

logger = logging.getLogger(__name__)

# JWT Configuration
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", secrets.token_urlsafe(32))
JWT_ALGORITHM = "HS256"
JWT_ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
JWT_REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("JWT_REFRESH_TOKEN_EXPIRE_DAYS", "7"))

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class TokenType(str, Enum):
    ACCESS = "access"
    REFRESH = "refresh"
    RESET = "reset"
    VERIFICATION = "verification"

class AuthAction(str, Enum):
    LOGIN = "login"
    LOGOUT = "logout"
    REGISTER = "register"
    CHANGE_PASSWORD = "change_password"
    RESET_PASSWORD = "reset_password"
    VERIFY_EMAIL = "verify_email"

class Permission(str, Enum):
    # Read permissions
    READ_COMPLAINTS = "read_complaints"
    READ_PREDICTIONS = "read_predictions"
    READ_ALERTS = "read_alerts"
    READ_ANALYTICS = "read_analytics"
    READ_USERS = "read_users"

    # Write permissions
    CREATE_COMPLAINTS = "create_complaints"
    UPDATE_COMPLAINTS = "update_complaints"
    CREATE_PREDICTIONS = "create_predictions"
    CREATE_ALERTS = "create_alerts"
    UPDATE_ANALYTICS = "update_analytics"

    # Management permissions
    MANAGE_USERS = "manage_users"
    MANAGE_SYSTEM = "manage_system"
    MANAGE_CORDONS = "manage_cordons"
    MANAGE_INTEGRATIONS = "manage_integrations"

    # Super admin permissions
    SUPER_ADMIN = "super_admin"

@dataclass
class TokenData:
    """JWT token data structure"""
    user_id: str
    email: str
    role: UserRole
    permissions: List[str]
    token_type: TokenType
    issued_at: datetime
    expires_at: datetime
    jti: str  # JWT ID

@dataclass
class AuthUser:
    """Authenticated user structure"""
    user_id: str
    email: str
    name: Optional[str]
    role: UserRole
    permissions: List[str]
    is_active: bool
    last_login: Optional[datetime]
    metadata: Dict[str, Any]

class UserRegistration(BaseModel):
    """User registration request"""
    user_id: str
    email: EmailStr
    name: str
    password: str
    role: UserRole
    department: Optional[str] = None
    phone: Optional[str] = None
    badge_number: Optional[str] = None
    designation: Optional[str] = None

class UserLogin(BaseModel):
    """User login request"""
    email: EmailStr
    password: str
    remember_me: bool = False

class PasswordChange(BaseModel):
    """Password change request"""
    current_password: str
    new_password: str
    confirm_password: str

class PasswordReset(BaseModel):
    """Password reset request"""
    email: EmailStr

class AuthenticationService:
    """
    Comprehensive authentication and authorization service
    Handles user authentication, JWT tokens, role-based access control, and audit logging
    """

    def __init__(self):
        self.secret_key = JWT_SECRET_KEY
        self.algorithm = JWT_ALGORITHM
        self.access_token_expire_minutes = JWT_ACCESS_TOKEN_EXPIRE_MINUTES
        self.refresh_token_expire_days = JWT_REFRESH_TOKEN_EXPIRE_DAYS

        # Role permissions mapping
        self.role_permissions = {
            UserRole.CITIZEN: [
                Permission.READ_COMPLAINTS,
                Permission.CREATE_COMPLAINTS
            ],
            UserRole.LAW_ENFORCEMENT: [
                Permission.READ_COMPLAINTS,
                Permission.READ_PREDICTIONS,
                Permission.READ_ALERTS,
                Permission.READ_ANALYTICS,
                Permission.CREATE_COMPLAINTS,
                Permission.UPDATE_COMPLAINTS,
                Permission.CREATE_PREDICTIONS,
                Permission.CREATE_ALERTS,
                Permission.MANAGE_CORDONS
            ],
            UserRole.ANALYST: [
                Permission.READ_COMPLAINTS,
                Permission.READ_PREDICTIONS,
                Permission.READ_ALERTS,
                Permission.READ_ANALYTICS,
                Permission.CREATE_PREDICTIONS,
                Permission.CREATE_ALERTS,
                Permission.UPDATE_ANALYTICS
            ],
            UserRole.ADMINISTRATOR: [
                Permission.READ_COMPLAINTS,
                Permission.READ_PREDICTIONS,
                Permission.READ_ALERTS,
                Permission.READ_ANALYTICS,
                Permission.READ_USERS,
                Permission.CREATE_COMPLAINTS,
                Permission.UPDATE_COMPLAINTS,
                Permission.CREATE_PREDICTIONS,
                Permission.CREATE_ALERTS,
                Permission.UPDATE_ANALYTICS,
                Permission.MANAGE_USERS,
                Permission.MANAGE_SYSTEM,
                Permission.MANAGE_CORDONS,
                Permission.MANAGE_INTEGRATIONS
            ],
            UserRole.SYSTEM: [
                Permission.SUPER_ADMIN
            ]
        }

    def hash_password(self, password: str) -> str:
        """Hash a password using bcrypt"""
        return pwd_context.hash(password)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        return pwd_context.verify(plain_password, hashed_password)

    def get_user_permissions(self, role: UserRole) -> List[str]:
        """Get permissions for a specific role"""
        return self.role_permissions.get(role, [])

    def check_permission(self, user_permissions: List[str], required_permission: str) -> bool:
        """Check if user has a specific permission"""
        return required_permission in user_permissions or Permission.SUPER_ADMIN in user_permissions

    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """Create a JWT access token"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)

        to_encode.update({
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": TokenType.ACCESS.value
        })

        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt

    def create_refresh_token(self, data: dict) -> str:
        """Create a JWT refresh token"""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=self.refresh_token_expire_days)

        to_encode.update({
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": TokenType.REFRESH.value
        })

        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt

    def verify_token(self, token: str, token_type: TokenType = TokenType.ACCESS) -> Optional[Dict[str, Any]]:
        """Verify and decode a JWT token"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])

            # Check token type
            if payload.get("type") != token_type.value:
                return None

            # Check expiration
            exp = payload.get("exp")
            if exp is None or datetime.fromtimestamp(exp) < datetime.utcnow():
                return None

            return payload

        except jwt.ExpiredSignatureError:
            logger.warning("JWT token has expired")
            return None
        except jwt.JWTError:
            logger.warning("Invalid JWT token")
            return None

    async def authenticate_user(self, db: Session, email: str, password: str) -> Optional[User]:
        """Authenticate a user with email and password"""
        try:
            user = db.query(User).filter(User.email == email).first()
            if not user:
                return None

            if not self.verify_password(password, user.password):
                return None

            if not user.is_active:
                return None

            # Update last login
            user.last_login = datetime.utcnow()
            db.commit()

            # Log authentication action
            await self._log_auth_action(
                db=db,
                action=AuthAction.LOGIN,
                user_id=user.user_id,
                email=email,
                status="success"
            )

            return user

        except Exception as e:
            logger.error(f"❌ Error authenticating user: {str(e)}")
            return None

    async def register_user(self, db: Session, user_data: UserRegistration) -> Optional[User]:
        """Register a new user"""
        try:
            # Check if user already exists
            existing_user = db.query(User).filter(
                (User.email == user_data.email) | (User.user_id == user_data.user_id)
            ).first()

            if existing_user:
                return None

            # Hash password
            hashed_password = self.hash_password(user_data.password)

            # Create user
            user = User(
                user_id=user_data.user_id,
                email=user_data.email,
                name=user_data.name,
                password=hashed_password,
                role=user_data.role,
                department=user_data.department,
                phone=user_data.phone,
                badge_number=user_data.badge_number,
                designation=user_data.designation,
                is_active=True,
                permissions=self.get_user_permissions(user_data.role)
            )

            db.add(user)
            db.commit()
            db.refresh(user)

            # Log registration action
            await self._log_auth_action(
                db=db,
                action=AuthAction.REGISTER,
                user_id=user.user_id,
                email=user_data.email,
                status="success"
            )

            logger.info(f"✅ User registered successfully: {user_data.email}")
            return user

        except Exception as e:
            logger.error(f"❌ Error registering user: {str(e)}")
            db.rollback()
            return None

    async def login_user(self, db: Session, login_data: UserLogin) -> Optional[Dict[str, Any]]:
        """Login a user and return tokens"""
        try:
            # Authenticate user
            user = await self.authenticate_user(db, login_data.email, login_data.password)
            if not user:
                return None

            # Get user permissions
            permissions = self.get_user_permissions(user.role)

            # Create tokens
            token_data = {
                "sub": user.user_id,
                "email": user.email,
                "role": user.role.value,
                "permissions": permissions,
                "jti": secrets.token_urlsafe(16)
            }

            access_token = self.create_access_token(token_data)
            refresh_token = self.create_refresh_token(token_data)

            # Create auth user object
            auth_user = AuthUser(
                user_id=user.user_id,
                email=user.email,
                name=user.name,
                role=user.role,
                permissions=permissions,
                is_active=user.is_active,
                last_login=user.last_login,
                metadata={
                    "department": user.department,
                    "phone": user.phone,
                    "badge_number": user.badge_number,
                    "designation": user.designation
                }
            )

            return {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": "bearer",
                "expires_in": self.access_token_expire_minutes * 60,
                "user": auth_user
            }

        except Exception as e:
            logger.error(f"❌ Error logging in user: {str(e)}")
            return None

    async def refresh_access_token(self, db: Session, refresh_token: str) -> Optional[Dict[str, Any]]:
        """Refresh an access token using a refresh token"""
        try:
            # Verify refresh token
            payload = self.verify_token(refresh_token, TokenType.REFRESH)
            if not payload:
                return None

            # Get user
            user = db.query(User).filter(User.user_id == payload["sub"]).first()
            if not user or not user.is_active:
                return None

            # Get updated permissions
            permissions = self.get_user_permissions(user.role)

            # Create new access token
            token_data = {
                "sub": user.user_id,
                "email": user.email,
                "role": user.role.value,
                "permissions": permissions,
                "jti": secrets.token_urlsafe(16)
            }

            new_access_token = self.create_access_token(token_data)

            return {
                "access_token": new_access_token,
                "token_type": "bearer",
                "expires_in": self.access_token_expire_minutes * 60
            }

        except Exception as e:
            logger.error(f"❌ Error refreshing token: {str(e)}")
            return None

    async def change_password(self, db: Session, user_id: str, password_data: PasswordChange) -> bool:
        """Change user password"""
        try:
            # Get user
            user = db.query(User).filter(User.user_id == user_id).first()
            if not user:
                return False

            # Verify current password
            if not self.verify_password(password_data.current_password, user.password):
                return False

            # Verify new passwords match
            if password_data.new_password != password_data.confirm_password:
                return False

            # Update password
            user.password = self.hash_password(password_data.new_password)
            db.commit()

            # Log password change action
            await self._log_auth_action(
                db=db,
                action=AuthAction.CHANGE_PASSWORD,
                user_id=user_id,
                email=user.email,
                status="success"
            )

            logger.info(f"✅ Password changed successfully for user: {user.email}")
            return True

        except Exception as e:
            logger.error(f"❌ Error changing password: {str(e)}")
            db.rollback()
            return False

    async def reset_password(self, db: Session, email: str, new_password: str) -> bool:
        """Reset user password (for forgotten password flow)"""
        try:
            # Get user
            user = db.query(User).filter(User.email == email).first()
            if not user:
                return False

            # Update password
            user.password = self.hash_password(new_password)
            db.commit()

            # Log password reset action
            await self._log_auth_action(
                db=db,
                action=AuthAction.RESET_PASSWORD,
                user_id=user.user_id,
                email=email,
                status="success"
            )

            logger.info(f"✅ Password reset successfully for user: {email}")
            return True

        except Exception as e:
            logger.error(f"❌ Error resetting password: {str(e)}")
            db.rollback()
            return False

    async def logout_user(self, db: Session, user_id: str, email: str) -> bool:
        """Logout a user"""
        try:
            # Log logout action
            await self._log_auth_action(
                db=db,
                action=AuthAction.LOGOUT,
                user_id=user_id,
                email=email,
                status="success"
            )

            logger.info(f"✅ User logged out: {email}")
            return True

        except Exception as e:
            logger.error(f"❌ Error logging out user: {str(e)}")
            return False

    async def get_user_by_id(self, db: Session, user_id: str) -> Optional[User]:
        """Get user by ID"""
        return db.query(User).filter(User.user_id == user_id).first()

    async def update_user_last_activity(self, db: Session, user_id: str) -> bool:
        """Update user's last activity timestamp"""
        try:
            user = db.query(User).filter(User.user_id == user_id).first()
            if user:
                user.last_login = datetime.utcnow()
                db.commit()
                return True
            return False
        except Exception as e:
            logger.error(f"❌ Error updating user activity: {str(e)}")
            return False

    async def get_users_by_role(self, db: Session, role: UserRole) -> List[User]:
        """Get all users by role"""
        return db.query(User).filter(User.role == role, User.is_active == True).all()

    async def deactivate_user(self, db: Session, user_id: str) -> bool:
        """Deactivate a user account"""
        try:
            user = db.query(User).filter(User.user_id == user_id).first()
            if not user:
                return False

            user.is_active = False
            db.commit()

            logger.info(f"✅ User deactivated: {user.email}")
            return True

        except Exception as e:
            logger.error(f"❌ Error deactivating user: {str(e)}")
            db.rollback()
            return False

    async def _log_auth_action(self, db: Session, action: AuthAction, user_id: str,
                              email: str, status: str, metadata: Dict[str, Any] = None) -> None:
        """Log authentication-related actions"""
        try:
            audit_log = AuditLog(
                action=action.value,
                resource_type="user",
                resource_id=user_id,
                user_id=user_id,
                user_role="user",  # Would get from session
                timestamp=datetime.utcnow(),
                status=status,
                metadata=metadata or {}
            )

            db.add(audit_log)
            db.commit()

        except Exception as e:
            logger.error(f"❌ Error logging auth action: {str(e)}")

    def create_password_reset_token(self, email: str) -> str:
        """Create a password reset token"""
        token_data = {
            "sub": email,
            "type": TokenType.RESET.value,
            "jti": secrets.token_urlsafe(32)
        }

        # Create token with 1 hour expiry
        token = self.create_access_token(
            token_data,
            expires_delta=timedelta(hours=1)
        )

        return token

    def verify_password_reset_token(self, token: str) -> Optional[str]:
        """Verify password reset token and return email"""
        try:
            payload = self.verify_token(token, TokenType.RESET)
            if payload:
                return payload.get("sub")
            return None
        except Exception as e:
            logger.error(f"❌ Error verifying reset token: {str(e)}")
            return None

    async def get_system_users(self, db: Session) -> List[User]:
        """Get all system users for management"""
        return db.query(User).filter(
            User.is_active == True,
            User.role.in_([UserRole.ADMINISTRATOR, UserRole.SYSTEM])
        ).all()

    def get_user_statistics(self, db: Session) -> Dict[str, Any]:
        """Get user statistics for dashboard"""
        try:
            total_users = db.query(User).count()
            active_users = db.query(User).filter(User.is_active == True).count()

            users_by_role = {}
            for role in UserRole:
                count = db.query(User).filter(
                    User.role == role,
                    User.is_active == True
                ).count()
                users_by_role[role.value] = count

            recent_logins = db.query(User).filter(
                User.last_login >= datetime.utcnow() - timedelta(days=7)
            ).count()

            return {
                "total_users": total_users,
                "active_users": active_users,
                "inactive_users": total_users - active_users,
                "users_by_role": users_by_role,
                "recent_logins_7d": recent_logins,
                "user_growth_rate": 0.0  # Would calculate from historical data
            }

        except Exception as e:
            logger.error(f"❌ Error getting user statistics: {str(e)}")
            return {}

# Global authentication service instance
auth_service = AuthenticationService()

# FastAPI dependencies
async def get_current_user_token(token: str = None, db: Session = None) -> Optional[Dict[str, Any]]:
    """Get current user from JWT token"""
    if not token:
        return None

    payload = auth_service.verify_token(token)
    if not payload:
        return None

    return payload

async def get_current_user(token: str = None, db: Session = None) -> Optional[User]:
    """Get current user from database"""
    if not token or not db:
        return None

    payload = await get_current_user_token(token, db)
    if not payload:
        return None

    user = await auth_service.get_user_by_id(db, payload["sub"])
    if not user or not user.is_active:
        return None

    # Update last activity
    await auth_service.update_user_last_activity(db, user.user_id)

    return user

def require_permission(permission: str):
    """Decorator to require specific permission"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Get current user
            current_user = kwargs.get('current_user')
            if not current_user:
                raise HTTPException(
                    status_code=401,
                    detail="Authentication required"
                )

            # Check permission
            user_permissions = auth_service.get_user_permissions(current_user.role)
            if not auth_service.check_permission(user_permissions, permission):
                raise HTTPException(
                    status_code=403,
                    detail=f"Insufficient permissions. Required: {permission}"
                )

            return await func(*args, **kwargs)
        return wrapper
    return decorator

def require_role(role: UserRole):
    """Decorator to require specific role"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Get current user
            current_user = kwargs.get('current_user')
            if not current_user:
                raise HTTPException(
                    status_code=401,
                    detail="Authentication required"
                )

            if current_user.role != role:
                raise HTTPException(
                    status_code=403,
                    detail=f"Insufficient role. Required: {role.value}"
                )

            return await func(*args, **kwargs)
        return wrapper
    return decorator