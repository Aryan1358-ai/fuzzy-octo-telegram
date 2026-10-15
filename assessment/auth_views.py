"""
Authentication API views using Django's built-in User model.

Endpoints:
  POST /api/auth/register/  — create account + auto-login
  POST /api/auth/login/     — email + password → session cookie
  POST /api/auth/logout/    — clear session
  GET  /api/auth/me/        — return current user info (or 401)
"""

import logging

from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.db import IntegrityError

from google.oauth2 import id_token as google_id_token
from google.auth.transport import requests as google_requests

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

logger = logging.getLogger(__name__)


@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    """Create a new user account and auto-login."""
    name = request.data.get('name', '').strip()
    email = request.data.get('email', '').strip().lower()
    password = request.data.get('password', '')

    # Validation
    if not email or not password:
        return Response(
            {'error': 'Email and password are required.'},
            status=status.HTTP_400_BAD_REQUEST,
        )
    if len(password) < 6:
        return Response(
            {'error': 'Password must be at least 6 characters.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Use email as the username (Django requires unique username)
    try:
        user = User.objects.create_user(
            username=email,
            email=email,
            password=password,
            first_name=name,
        )
    except IntegrityError:
        return Response(
            {'error': 'An account with this email already exists.'},
            status=status.HTTP_409_CONFLICT,
        )

    # Auto-login after registration
    login(request, user)

    return Response({
        'message': 'Account created successfully.',
        'user': _user_to_dict(user),
    }, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    """Authenticate with email + password."""
    email = request.data.get('email', '').strip().lower()
    password = request.data.get('password', '')

    if not email or not password:
        return Response(
            {'error': 'Email and password are required.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Django authenticate uses username — we store email as username
    user = authenticate(request, username=email, password=password)

    if user is None:
        return Response(
            {'error': 'Invalid email or password.'},
            status=status.HTTP_401_UNAUTHORIZED,
        )

    login(request, user)

    return Response({
        'message': 'Login successful.',
        'user': _user_to_dict(user),
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_view(request):
    """Clear the session."""
    logout(request)
    return Response({'message': 'Logged out successfully.'})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def me(request):
    """Return the currently authenticated user's info."""
    return Response({
        'user': _user_to_dict(request.user),
    })


@api_view(['POST'])
@permission_classes([AllowAny])
def google_login(request):
    """Authenticate via Google OAuth.

    Expects: { "credential": "<Google ID token>" }
    The token is verified server-side against Google's certificates.
    A Django user is created (or matched) by email, then logged in.
    """
    credential = request.data.get('credential', '')
    if not credential:
        return Response(
            {'error': 'Google credential token is required.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    client_id = getattr(settings, 'GOOGLE_OAUTH_CLIENT_ID', '')
    if not client_id:
        logger.error('GOOGLE_OAUTH_CLIENT_ID not configured in settings.')
        return Response(
            {'error': 'Google OAuth is not configured on this server.'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    # Verify the token with Google
    try:
        idinfo = google_id_token.verify_oauth2_token(
            credential,
            google_requests.Request(),
            client_id,
        )
    except ValueError as e:
        logger.warning(f'Google token verification failed: {e}')
        return Response(
            {'error': 'Invalid Google credential. Please try again.'},
            status=status.HTTP_401_UNAUTHORIZED,
        )

    # Extract user info from verified token
    google_email = idinfo.get('email', '').lower()
    google_name = idinfo.get('name', '')
    email_verified = idinfo.get('email_verified', False)

    if not google_email or not email_verified:
        return Response(
            {'error': 'Google account email is not verified.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Find or create user by email
    try:
        user = User.objects.get(email=google_email)
        # Update name if it was blank (user originally registered with email/password)
        if not user.first_name and google_name:
            user.first_name = google_name
            user.save(update_fields=['first_name'])
    except User.DoesNotExist:
        # Auto-create account for Google users (no password needed)
        user = User.objects.create_user(
            username=google_email,
            email=google_email,
            first_name=google_name,
        )
        # Set unusable password — they'll always sign in via Google
        user.set_unusable_password()
        user.save()

    login(request, user)

    return Response({
        'message': 'Google login successful.',
        'user': _user_to_dict(user),
    })


def _user_to_dict(user):
    """Serialize a User object to a simple dict."""
    return {
        'id': user.id,
        'name': user.first_name or user.username,
        'email': user.email,
        'is_staff': user.is_staff,
        'date_joined': user.date_joined.isoformat(),
    }
