from django import forms

class ExpressionLookupForm(forms.Form):
    # e.g., "Then when he's in his happy place..."
    original_context = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 3}),
        label="原始句子"
    )
    # e.g., "in his happy place; strike like a cobra"
    # 我们用分号来分隔多个短语
    expressions_to_lookup = forms.CharField(
        max_length=500,
        label="想查询的短语（用 / 分隔）"
    )