from django.shortcuts import render, redirect
from .forms import ExpressionLookupForm
from .services import get_structured_explanations
from .types import LookupRequestData
from .models import PhraseLog

# Create your views here.
def lookup_view(request):
    if request.method == 'POST':
        # 验证表单
        form = ExpressionLookupForm(request.POST)
        if form.is_valid():
            # #    form.cleaned_data 是一个包含安全数据的字典
            print(form.cleaned_data)
            original_context = form.cleaned_data["original_context"]
            expressions_str = form.cleaned_data["expressions_to_lookup"]
            results = get_structured_explanations({"expressions_to_lookup": expressions_str, "original_context": original_context})
            if results:
                new_pks = []
                for item in results:
                    log_entry = PhraseLog.objects.create(
                        original_context=item.get("original_context"),
                        expression_text=item.get("expression_text"),
                        chinese_meaning=item.get("chinese_meaning"),
                        example_sentence=item.get("example_sentence")
                    )
                    new_pks.append(log_entry.pk)
                # 把 pk 存入 Session
                request.session['latest_result_pks'] = new_pks    
            else:
                request.session['latest_result_pks'] = []
            return redirect("results-page")
    else:
        form = ExpressionLookupForm()
    return render(request, "lookup_form.html", {"form": form})

def result_view(request):
    # .pop() 会获取值并立刻从 session 中删除它，繁殖刷新页面时重新显示
    result_pks = request.session.pop("latest_result_pks", [])
    if result_pks:
        from django.db.models import Case, When
        preserved_order = Case(*[When(pk=pk, then=pos) for pos, pk in enumerate(result_pks)])
        results_from_db = PhraseLog.objects.filter(pk__in=result_pks).order_by(preserved_order)
    else:
        results_from_db = []
    return render(request, "results.html", {"results": results_from_db})
