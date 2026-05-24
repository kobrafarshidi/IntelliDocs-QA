from django.contrib import admin, messages
from django.db.models.signals import post_delete
from django.dispatch import receiver
from .models import Document, extract_docx_text


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "chunk_count", "created_at")
    search_fields = ("title", "content")
    readonly_fields = ("chunk_count", "created_at", "updated_at")
    fields = ("title", "file", "content", "chunk_count", "created_at", "updated_at")
    actions = ["reindex_selected"]

    def save_model(self, request, obj, form, change):
        # If a new DOCX was uploaded, extract its text.
        if obj.file and (not change or "file" in form.changed_data):
            try:
                obj.content = extract_docx_text(obj.file)
            except Exception as exc:
                self.message_user(
                    request, f"Could not parse DOCX: {exc}", level=messages.ERROR
                )
        super().save_model(request, obj, form, change)
        try:
            count = obj.reindex()
            self.message_user(
                request, f"Indexed {count} chunks for '{obj.title}'.", level=messages.SUCCESS
            )
        except Exception as exc:
            self.message_user(
                request, f"Indexing failed: {exc}", level=messages.WARNING
            )

    @admin.action(description="Re-index selected documents")
    def reindex_selected(self, request, queryset):
        total = 0
        for doc in queryset:
            try:
                total += doc.reindex()
            except Exception as exc:
                self.message_user(request, f"{doc.title}: {exc}", level=messages.ERROR)
        self.message_user(request, f"Re-indexed {total} chunks.", level=messages.SUCCESS)


@receiver(post_delete, sender=Document)
def _remove_from_vectorstore(sender, instance, **kwargs):
    from qa.rag import remove_document
    try:
        remove_document(instance.id)
    except Exception:
        pass
