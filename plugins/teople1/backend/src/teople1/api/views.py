from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny


class StartingView(APIView):
    permission_classes = (AllowAny,)

    def get(self, request):
        return Response({"title": "Starting title", "content": "Starting text"})


class LoginView(APIView):
    permission_classes = (AllowAny,)

    def post(self, request):
        if request.data.get("username") == "admin" and request.data.get("password") == "admin123":
            return Response({"status": "success", "message": "Login successful"})
        return Response({"status": "error", "message": "Invalid credentials"})
