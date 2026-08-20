from django.contrib.auth import login, authenticate
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import User
from .serializers import LoginSerializer, RegisterSerializer, UserSerializer, UserPublicSerializer


@method_decorator(csrf_exempt, name='dispatch')
class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({"error": str(serializer.errors)}, status=400)
        user = authenticate(
            request=request,
            email=serializer.validated_data["email"],
            password=serializer.validated_data["password"],
        )
        if user is None:
            return Response({"error": "Email ou mot de passe incorrect."}, status=401)
        if not user.est_actif:
            return Response({"error": "Compte desactive."}, status=403)
        login(request, user)
        return Response(UserSerializer(user).data)


@method_decorator(csrf_exempt, name='dispatch')
class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]


class UserProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer
    def get_object(self):
        return self.request.user


class LogoutView(APIView):
    def post(self, request):
        from django.contrib.auth import logout
        logout(request)
        return Response({"detail": "Deconnecte."})


class UserPublicView(generics.RetrieveAPIView):
    queryset = User.objects.filter(est_actif=True)
    serializer_class = UserPublicSerializer
    permission_classes = [permissions.AllowAny]
    lookup_field = "id_utilisateur"


from django.middleware.csrf import get_token
from django.http import JsonResponse

class CsrfView(APIView):
    """GET /api/auth/csrf/ — renvoie un cookie CSRF pour le frontend."""
    permission_classes = [permissions.AllowAny]
    def get(self, request):
        return JsonResponse({"csrfToken": get_token(request)})
