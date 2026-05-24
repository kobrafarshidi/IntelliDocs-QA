from django import forms
from django.contrib import admin, messages
from django.shortcuts import render, redirect
from django.urls import path

from .models import QuestionAnswer
from .rag import answer_question


class AskForm(forms.Form):
    question = forms.CharField(widget=forms.Textarea(attrs={"rows": 3, "cols": 80}))
    k = forms.IntegerField(initial=4, min_value=1, max_value=10, label="Top-K chunks")


@admin.register(QuestionAnswer)
class QuestionAnswerAdmin(admin.ModelAdmin):
    list_display = ("id", "short_question", "short_answer", "created_at")
    readonly_fields = ("question", "answer", "sources", "error", "created_at")
    search_fields = ("question", "answer")
    change_list_template = "admin/qa/questionanswer/change_list.html"

    @admin.display(description="Question")
    def short_question(self, obj):
        return (obj.question or "")[:80]

    @admin.display(description="Answer")
    def short_answer(self, obj):
        return (obj.answer or obj.error or "")[:120]

    def get_urls(self):
        urls = super().get_urls()
        custom = [path("ask/", self.admin_site.admin_view(self.ask_view), name="qa_ask")]
        return custom + urls

    def ask_view(self, request):
        result = None
        if request.method == "POST":
            form = AskForm(request.POST)
            if form.is_valid():
                q = form.cleaned_data["question"]
                k = form.cleaned_data["k"]
                qa = QuestionAnswer(question=q)
                try:
                    answer, sources = answer_question(q, k=k)
                    qa.answer = answer
                    qa.sources = sources
                except Exception as exc:
                    qa.error = str(exc)
                    messages.error(request, f"LLM error: {exc}")
                qa.save()
                return redirect("admin:qa_questionanswer_change", qa.id)
        else:
            form = AskForm()
        return render(request, "admin/qa/ask.html", {
            "form": form,
            "result": result,
            "title": "Ask a question",
        })
