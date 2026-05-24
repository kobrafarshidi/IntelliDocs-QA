from rest_framework import viewsets, mixins, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema

from .models import QuestionAnswer
from .serializers import QuestionAnswerSerializer, AskSerializer
from .rag import answer_question


class HistoryViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    queryset = QuestionAnswer.objects.all()
    serializer_class = QuestionAnswerSerializer


@extend_schema(request=AskSerializer, responses=QuestionAnswerSerializer)
@api_view(["POST"])
@permission_classes([AllowAny])
def ask(request):
    serializer = AskSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    q = serializer.validated_data["question"]
    k = serializer.validated_data["k"]
    qa = QuestionAnswer(question=q)
    try:
        answer, sources = answer_question(q, k=k)
        qa.answer = answer
        qa.sources = sources
    except Exception as exc:
        qa.error = str(exc)
        qa.save()
        return Response(QuestionAnswerSerializer(qa).data, status=status.HTTP_502_BAD_GATEWAY)
    qa.save()
    return Response(QuestionAnswerSerializer(qa).data)
