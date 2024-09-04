from django.core.mail import send_mail, EmailMessage
from celery import shared_task
import os
from datetime import datetime
from email.utils import formataddr
from django.urls import reverse
from subscriptions.views import create_subscribed_listing
import os
import logging
from subscriptions.models import Subscription
from listings.models import RoomProfile

logger = logging.getLogger('messaging')


HOME_URL = os.getenv('HOME_URL')


@shared_task
def send_initial_subscribed_listings(subscription_pk):
    """
    This task is called just once, when a client
    completes the subscription
    """
    try:
        subscription = Subscription.objects.get(pk=subscription_pk)
        from_email = formataddr((
            'Upperoom', 'upperoom.ng@gmail.com'
        ))
        relative_url = reverse('get_subscribed_listings',
                               args=[subscription.pk])
        url = f'{HOME_URL}{relative_url}'

        html_message = f'''
        <html>
        <head>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    color: #333333;
                    background-color: #f9f9f9;
                    margin: 0;
                    padding: 0;
                    width: 100%;
                    box-sizing: border-box;
                }}
                .container {{
                    width: 100%;
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                    background-color: #ffffff;
                    border-radius: 10px;
                    box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
                    box-sizing: border-box;
                }}
                .header {{
                    background-color: #013220; /* Oxford Blue */
                    padding: 10px;
                    text-align: center;
                    color: #ffffff;
                    border-radius: 10px 10px 0 0;
                }}
                .header h1 {{
                    margin: 0;
                    font-size: 24px;
                }}
                .content {{
                    padding: 20px;
                    color: #333333;
                    box-sizing: border-box;
                }}
                .content p {{
                    line-height: 1.6;
                    margin: 20px 0;
                }}
                .content a {{
                    display: inline-block;
                    padding: 10px 20px;
                    background-color: #2e8b57; /* Sea Green */
                    color: #ffffff;
                    text-decoration: none;
                    border-radius: 5px;
                    margin-top: 20px;
                }}
                .content a:hover {{
                    background-color: #276d47;
                }}
                .footer {{
                    text-align: center;
                    padding: 20px;
                    font-size: 12px;
                    color: #777777;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Listings Updated!</h1>
                </div>
                <div class="content">
                    <p>Hello,</p>
                    <p>Listings have now been updated!</p>
                    <p><a href="{url}">Click to see updates</a></p>
                    <p>Thank you,<br>The Upperoom Team</p>
                </div>
                <div class="footer">
                    <p>&copy; {datetime.now().year} Upperoom Accommodations. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        '''

        response = send_mail(
            'Listings updated for subscription!',
            '',
            from_email,
            [subscription.client.email],
            html_message=html_message,
            fail_silently=False
        )
        if response == 1:
            logger.info(
                f'Initial subscribed listings successfully sent [client_email: {subscription.client.email}]'
            )
            subscription.number_of_listings_sent = subscription.subscribed_rooms.count()
            subscription.save()
            subscribed_listings, creator_email_list = create_subscribed_listing(
                subscription)

            # send_creator_subscription_mail.delay(creator_email_list)
            send_creator_subscription_mail(creator_email_list)
        else:
            logger.error(
                f'Initial subscription listings not sent [client_email: {subscription.client.email}]'
            )

    except Exception as e:
        logger.error(
            f'Failed with exception: {e} \n[client_email: {subscription.client.email}]'
        )


@shared_task
def send_verification_mail(user_email, uuid):
    try:
        from_email = formataddr((
            'Upperoom Verification', 'upperoom.ng@gmail.com'
        ))
        home_url = os.getenv('HOME_URL', 'http://127.0.0.1:8000')
        url = f"{home_url}/auth/verify_email/{uuid}"

        # debug
        logger.info(f'{url}')

        html_message = f'''
        <html>
        <head>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    color: #333333;
                    background-color: #f9f9f9;
                    margin: 0;
                    padding: 0;
                    width: 100%;
                    box-sizing: border-box;
                }}
                .container {{
                    width: 100%;
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                    background-color: #ffffff;
                    border-radius: 10px;
                    box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
                    box-sizing: border-box;
                }}
                .header {{
                    background-color: #013220; /* Oxford Blue */
                    padding: 10px;
                    text-align: center;
                    color: #ffffff;
                    border-radius: 10px 10px 0 0;
                }}
                .header h1 {{
                    margin: 0;
                    font-size: 24px;
                }}
                .content {{
                    padding: 20px;
                    color: #333333;
                    box-sizing: border-box;
                }}
                .content p {{
                    line-height: 1.6;
                    margin: 20px 0;
                }}
                .content a {{
                    display: inline-block;
                    padding: 10px 20px;
                    background-color: #2e8b57; /* Sea Green */
                    color: #ffffff;
                    text-decoration: none;
                    border-radius: 5px;
                    margin-top: 20px;
                }}
                .content a:hover {{
                    background-color: #276d47;
                }}
                .footer {{
                    text-align: center;
                    padding: 20px;
                    font-size: 12px;
                    color: #777777;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Upperoom Account Verification</h1>
                </div>
                <div class="content">
                    <p>Hello,</p>
                    <p>Thank you for registering with Upperoom! To complete your registration, please verify your email address by clicking the link below:</p>
                    <p><a href="{url}">Verify Email</a></p>
                    <p>If you did not request this verification, you can safely ignore this email.</p>
                    <p>Thank you,<br>The Upperoom Team</p>
                </div>
                <div class="footer">
                    <p>&copy; {datetime.now().year} Upperoom Accommodations. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        '''
        response = send_mail(
            'Confirm your email address',
            '',
            from_email,
            [user_email],
            html_message=html_message,
            fail_silently=False
        )
        if response == 1:
            logger.info(
                f'Email verification link successfully sent [user_email: {user_email}]'
            )
        else:
            logger.error(
                f'Email verification link NOT successfuly sent [user_email: {user_email}]'
            )

    except Exception as e:
        logger.error(
            f'Failed with exception: {e} \n[user_email: {user_email}]'
        )


@shared_task
def send_creator_subscription_mail(creator_email_list):
    try:
        from_email = formataddr((
            'Upperoom - Client Subscription Notification', 'upperoom.ng@gmail.com'
        ))
        relative_url = reverse('get_creator')
        url = f'{HOME_URL}{relative_url}'
        html_message = f'''
        <html>
        <head>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    color: #333333;
                    background-color: #f9f9f9;
                    margin: 0;
                    padding: 0;
                    width: 100%;
                    box-sizing: border-box;
                }}
                .container {{
                    width: 100%;
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                    background-color: #ffffff;
                    border-radius: 10px;
                    box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
                    box-sizing: border-box;
                }}
                .header {{
                    background-color: #013220; /* Oxford Blue */
                    padding: 10px;
                    text-align: center;
                    color: #ffffff;
                    border-radius: 10px 10px 0 0;
                }}
                .header h1 {{
                    margin: 0;
                    font-size: 24px;
                }}
                .content {{
                    padding: 20px;
                    color: #333333;
                    box-sizing: border-box;
                }}
                .content p {{
                    line-height: 1.6;
                    margin: 20px 0;
                }}
                .content a {{
                    display: inline-block;
                    padding: 10px 20px;
                    background-color: #2e8b57; /* Sea Green */
                    color: #ffffff;
                    text-decoration: none;
                    border-radius: 5px;
                    margin-top: 20px;
                }}
                .content a:hover {{
                    background-color: #276d47;
                }}
                .footer {{
                    text-align: center;
                    padding: 20px;
                    font-size: 12px;
                    color: #777777;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Subscription Notification</h1>
                </div>
                <div class="content">
                    <p>Hello,</p>
                    <p>Some clients have subscribed to your listings</p>
                    <p><a href="{url}">Click to view in your account</a></p>
                    <p>Thank you,<br>The Upperoom Team</p>
                </div>
                <div class="footer">
                    <p>&copy; {datetime.now().year} Upperoom Accommodations. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        '''

        response = send_mail(
            'Your listings are getting noticed!',
            '',
            from_email,
            creator_email_list,
            html_message=html_message,
            fail_silently=False
        )

        # work on this later
        logger.info(
            f'client subscription email successfully sent'
        )

    except Exception as e:
        # improve
        logger.error(
            f'Could not send client subscription mail with Execption {e}\nCreator mail list {str(creator_email_list)}')


@shared_task
def send_vacancy_update_mail(pk):
    """
    Sends vacancy updates to all subscribed clients
    Args:
        pk: room_profile pk
            type(str, uuid)
    """

    room_profile = RoomProfile.objects.get(pk=pk)
    region = room_profile.lodge.region

    subscriptions = Subscription.objects.filter(
        is_expired=False,
        transaction__regions=region
    ).distinct()

    subscriptions_without_room = subscriptions.exclude(
        subscribed_rooms=room_profile
    )

    for subscription in subscriptions_without_room:
        subscription.subscribed_rooms.add(room_profile)

    client_emails_list = []
    for subscription in subscriptions:
        if subscription.client.email not in client_emails_list:
            client_emails_list.append(subscription.client.email)

    html_message = f'''
        <html>
        <head>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    color: #333333;
                    background-color: #f9f9f9;
                    margin: 0;
                    padding: 0;
                    width: 100%;
                    box-sizing: border-box;
                }}
                .container {{
                    width: 100%;
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                    background-color: #ffffff;
                    border-radius: 10px;
                    box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
                    box-sizing: border-box;
                }}
                .header {{
                    background-color: #013220; /* Oxford Blue */
                    padding: 10px;
                    text-align: center;
                    color: #ffffff;
                    border-radius: 10px 10px 0 0;
                }}
                .header h1 {{
                    margin: 0;
                    font-size: 24px;
                }}
                .content {{
                    padding: 20px;
                    color: #333333;
                    box-sizing: border-box;
                }}
                .content p {{
                    line-height: 1.6;
                    margin: 20px 0;
                }}
                .content a {{
                    display: inline-block;
                    padding: 10px 20px;
                    background-color: #2e8b57; /* Sea Green */
                    color: #ffffff;
                    text-decoration: none;
                    border-radius: 5px;
                    margin-top: 20px;
                }}
                .content a:hover {{
                    background-color: #276d47;
                }}
                .footer {{
                    text-align: center;
                    padding: 20px;
                    font-size: 12px;
                    color: #777777;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>New Vacancy Updates</h1>
                </div>
                <div class="content">
                    <p>Hello,</p>
                    <p>You have new vacancy updates for your subscription</p>
                    <p><a href="#">Click to view in your account</a></p>
                    <p>Thank you,<br>The Upperoom Team</p>
                </div>
                <div class="footer">
                    <p>&copy; {datetime.now().year} Upperoom Accommodations. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        '''

    from_email = formataddr((
        'Upperoom', 'upperoom.ng@gmail.com'
    ))
    response = send_mail(
        'Vacancy updates!',
        '',
        from_email,
        client_emails_list,
        html_message=html_message,
        fail_silently=False
    )
