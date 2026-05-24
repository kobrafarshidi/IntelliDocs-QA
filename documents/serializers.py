from rest_framework import serializers
from .models import Document, extract_docx_text


class DocumentSerializer(serializers.ModelSerializer):
    file = serializers.FileField(required=False, allow_null=True, write_only=True)

    class Meta:
        model = Document
        fields = ["id", "title", "file", "content", "chunk_count", "created_at", "updated_at"]
        read_only_fields = ["chunk_count", "created_at", "updated_at"]

    def _maybe_extract(self, validated_data):
        upload = validated_data.get("file")
        if upload and not validated_data.get("content"):
            try:
                validated_data["content"] = extract_docx_text(upload)
            except Exception as exc:
                raise serializers.ValidationError({"file": f"DOCX parse error: {exc}"})
        return validated_data

    def create(self, validated_data):
        validated_data = self._maybe_extract(validated_data)
        doc = super().create(validated_data)
        doc.reindex()
        return doc

    def update(self, instance, validated_data):
        validated_data = self._maybe_extract(validated_data)
        doc = super().update(instance, validated_data)
        doc.reindex()
        return doc
