from django.contrib import admin
from .models import Vote

@admin.register(Vote)
class VoteAdmin(admin.ModelAdmin):
    list_display = ["id_vote", "id_signalement", "id_utilisateur", "type_vote", "date_vote"]
    list_filter = ["type_vote"]
    ordering = ["-date_vote"]
