from rest_framework import serializers
from .models import QuestionAnswer


class QuestionAnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuestionAnswer
        fields = ["id", "question", "answer", "sources", "error", "created_at"]
        read_only_fields = fields


class AskSerializer(serializers.Serializer):
    question = serializers.CharField()
    k = serializers.IntegerField(required=False, default=4, min_value=1, max_value=10)
