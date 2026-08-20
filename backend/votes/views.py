from rest_framework import generics, permissions, status
from rest_framework.response import Response
from .models import Vote
from .serializers import VoteSerializer, VoteCreateSerializer


class VoteCreateView(generics.CreateAPIView):
    """POST /api/votes/ — créer ou mettre à jour un vote."""
    serializer_class = VoteCreateSerializer
    permission_classes = [permissions.IsAuthenticated]

    def create(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        sig = serializer.validated_data["id_signalement"]
        vt = serializer.validated_data["type_vote"]

        vote, created = Vote.objects.update_or_create(
            id_utilisateur=request.user,
            id_signalement=sig,
            defaults={"type_vote": vt},
        )
        return Response(
            VoteSerializer(vote).data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )
