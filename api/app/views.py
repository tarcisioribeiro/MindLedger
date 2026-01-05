from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.utils import timezone


@api_view(['GET'])
def current_date(request):
    """
    Returns the current date in the server's timezone (America/Sao_Paulo).
    This ensures frontend and backend use the same date reference.
    No authentication required - this is a public utility endpoint.
    """
    today = timezone.now().date()
    return Response({
        'date': today.isoformat()
    })
