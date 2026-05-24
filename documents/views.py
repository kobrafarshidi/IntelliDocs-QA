from rest_framework import viewsets, parsers
from .models import Document
from .serializers import DocumentSerializer
from qa.rag import remove_document


class DocumentViewSet(viewsets.ModelViewSet):
    queryset = Document.objects.all()
    serializer_class = DocumentSerializer
    parser_classes = [parsers.MultiPartParser, parsers.FormParser, parsers.JSONParser]

    def perform_destroy(self, instance):
        remove_document(instance.id)
        instance.delete()
