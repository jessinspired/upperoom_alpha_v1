from django.contrib import messages
from django.shortcuts import render
from django.views.decorators.http import require_http_methods
from listings.models import RoomType, School
from django.http import HttpResponse


@require_http_methods('GET')
def get_home(request):

    schools = School.objects.all()
    room_types = RoomType.objects.all()

    context = {
        'schools': schools,
        'room_types': room_types
    }

    return render(
        request,
        'home.html',
        context
    )


def handle_http_errors(request, status):
    """
    request: request object
    status: status code
    """

    # Dictionary to map status codes to custom messages or actions
    error_messages = {
        400: "Bad Request: The server could not understand the request.",
        401: "Unauthorized: Access is denied due to invalid credentials.",
        403: "Forbidden: You do not have permission to access this resource.",
        404: "Not Found: The requested resource could not be found.",
        500: "Internal Server Error: The server encountered an error.",
        502: "Bad Gateway: The server received an invalid response from an upstream server.",
        503: "Service Unavailable: The server is currently unable to handle the request."
    }

    if status in error_messages:
        message = error_messages[status]
        # logging.error(f"HTTP Error {status}: {message}")
        if request.htmx:
            return HttpResponse(f'<div id="response-message">{message}</div>')

        page = f'{status}.html'
        return render(request, page, {'message': message})

    # logging.error(f"Unhandled HTTP Error {status}: An unexpected error occurred.")
    if request.htmx:
        return HttpResponse(f'<div id="response-message">{message}</div>')

    page = f'{status}.html'
    message = "An unexpected error occurred. Please try again later."
    return render(request, page, {'message': message})
