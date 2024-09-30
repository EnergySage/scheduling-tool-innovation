import base64
import datetime
import json
import os
from typing import Annotated
from uuid import UUID

import sentry_sdk
from fastapi import Depends, Body, Request, HTTPException
from fastapi.security import OAuth2PasswordBearer
import jwt

from sqlalchemy.orm import Session

from ..database import repo, models
from ..dependencies.database import get_db
from ..exceptions import validation
from ..exceptions.validation import InvalidTokenException, InvalidPermissionLevelException

oauth2_scheme = OAuth2PasswordBearer(tokenUrl='token', auto_error=False)


def get_user_from_token(db, token: str, require_jti = False):
    try:
        payload = jwt.decode(token, os.getenv('JWT_SECRET'), algorithms=[os.getenv('JWT_ALGO')])
        sub = payload.get('sub')
        iat = payload.get('iat')
        jti = payload.get('jti')
        if sub is None:
            raise InvalidTokenException()
    except jwt.exceptions.InvalidTokenError:
        raise InvalidTokenException()

    sub_id = sub.replace('uid-', '')
    subscriber = repo.subscriber.get(db, int(sub_id))

    # Check this first as any doesn't short-circuit
    if subscriber is None:
        raise InvalidTokenException()

    # Token has been expired by us - temp measure to avoid spinning a refresh system, or a deny list for this issue
    if any(
        [
            subscriber.is_deleted,
            subscriber.minimum_valid_iat_time and not iat,
            # We only need second resolution
            subscriber.minimum_valid_iat_time and int(subscriber.minimum_valid_iat_time.timestamp()) > int(iat),
            # If we require this token to be a one time token, then require the claim
            require_jti and not jti
        ]
    ):
        raise InvalidTokenException()

    # If we're a one-time token, set the minimum valid iat time to now!
    # Beats having to store them multiple times, and it's only used in post-login.
    if jti:
        subscriber.minimum_valid_iat_time = datetime.datetime.now(datetime.UTC)
        db.add(subscriber)
        db.commit()

    return subscriber


def get_subscriber(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Session = Depends(get_db),
    require_jti=False
):
    """Automatically retrieve and return the subscriber"""
    if token is None:
        raise InvalidTokenException()

    user = get_user_from_token(db, token, require_jti)

    if user is None:
        raise InvalidTokenException()

    # Associate user id with users
    if os.getenv('SENTRY_DSN'):
        sentry_sdk.set_user(
            {
                'id': user.id,
            }
        )

    return user


async def get_subscriber_from_onetime_token(
    request: Request,
    db: Session = Depends(get_db),
):
    """Retrieve the subscriber via a one-time token only!"""
    token: str = await oauth2_scheme(request)
    return get_subscriber(token, db, require_jti=True)


async def get_subscriber_or_none(
    request: Request,
    db: Session = Depends(get_db),
):
    """Retrieve the subscriber or return None. This does not automatically error out like the other deps"""
    try:
        token: str = await oauth2_scheme(request)
        subscriber = get_subscriber(token, db)
    except InvalidTokenException:
        return None
    except HTTPException:
        return None
    except Exception as ex:
        # Catch any un-expected exceptions
        if os.getenv('SENTRY_DSN'):
            sentry_sdk.capture_exception(ex)
        return None

    return subscriber


def get_admin_subscriber(
    user: models.Subscriber = Depends(get_subscriber),
):
    """Retrieve the subscriber and check if they're an admin"""
    # check admin allow list
    admin_emails = os.getenv('APP_ADMIN_ALLOW_LIST')

    # Raise an error if we don't have any admin emails specified
    if not admin_emails or not user:
        raise InvalidPermissionLevelException()

    admin_emails = admin_emails.split(',')
    if not any([user.email.endswith(allowed_email) for allowed_email in admin_emails]):
        raise InvalidPermissionLevelException()

    return user


def get_subscriber_from_signed_url(
    url: str = Body(..., embed=True),
    db: Session = Depends(get_db),
):
    """Retrieve a subscriber based off a signed url from the body. Requires `url` param to be used in the request."""
    subscriber = repo.subscriber.verify_link(db, url)
    if not subscriber:
        raise validation.InvalidLinkException

    return subscriber


def get_subscriber_from_schedule_or_signed_url(
    url: str = Body(..., embed=True),
    db: Session = Depends(get_db),
):
    """Retrieve a subscriber based off a signed url or schedule slug namespaced by their username."""
    subscriber = repo.subscriber.verify_link(db, url)
    if not subscriber:
        subscriber = repo.schedule.verify_link(db, url)

    if not subscriber:
        raise validation.InvalidLinkException

    return subscriber

def get_flash_user_data_from_token(request):
    token = request.headers.get('Authorization', None)
    if not token:
        return "Missing Authorization Header"
    
    token = token.replace("Bearer ", "")

    _, payload, _ = token.split(".")

    # b64decode() requires the length of input to be a multiple of 4
    padded_payload = payload + "=" * (4 - len(payload) % 4)
    decoded_payload = base64.b64decode(padded_payload).decode("utf-8")

    payload_json = json.loads(decoded_payload)
    print("________________________________")
    print(payload_json)
    print("________________________________")
    flash_user_data = {
        "username": payload_json["preferred_username"] if "preffered_username" in payload_json else payload_json["given_name"] + "." + payload_json["family_name"],
        "email": payload_json["email"],
        "name": payload_json["given_name"] + " " + payload_json["family_name"]
    }

    return flash_user_data

