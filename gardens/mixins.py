"""
Reusable mixins for gardens app views.
"""

from django.http import JsonResponse


class JSONResponseMixin:
    """Mixin providing standardized JSON response methods for API views."""

    def json_success(self, data=None, message=None, status=200):
        """
        Return a success JSON response.

        Args:
            data: Optional dict of data to include in response
            message: Optional success message
            status: HTTP status code (default: 200)

        Returns:
            JsonResponse with success=True
        """
        response_data = {'success': True}
        if message:
            response_data['message'] = message
        if data:
            response_data.update(data)
        return JsonResponse(response_data, status=status)

    def json_error(self, error, status=400):
        """
        Return an error JSON response.

        Args:
            error: Error message string or Exception
            status: HTTP status code (default: 400)

        Returns:
            JsonResponse with success=False
        """
        return JsonResponse(
            {'success': False, 'error': str(error)},
            status=status
        )
