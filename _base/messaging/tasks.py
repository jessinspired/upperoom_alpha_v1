from django.core.mail import send_mail, EmailMessage
from celery import shared_task
import os
from datetime import datetime
from email.utils import formataddr
from django.urls import reverse
import os


HOME_URL = os.getenv('HOME_URL')


@shared_task
def send_initial_subscribed_listings(subscription):
    """
    This task is called just once, when a client
    completes the subscription
    """
    try:
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
        if response > 1:
            print('Email sent successfully')
            subscription.number_of_listings_sent = subscription.subscribed_rooms.count()
            subscription.save()
        else:
            print('Email not successfully sent')

    except Exception as e:
        print(f"Failed to send email: {e}")


@shared_task
def send_email_verification_mail(user_email, uuid):
    try:
        from_email = formataddr((
            'Upperoom Verification', 'upperoom.ng@gmail.com'
        ))
        home_url = os.getenv('HOME_URL', 'http://127.0.0.1:8000')
        url = f"{home_url}/auth/verify_email/{uuid}"
        print(url)
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
        send_mail(
            'Confirm your email address',
            '',
            from_email,
            [user_email],
            html_message=html_message,
            fail_silently=False
        )
        print('email sent')
    except Exception as e:
        print(f"Failed to send email: {e}")
