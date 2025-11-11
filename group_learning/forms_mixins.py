"""
Form mixins for Design Thinking / Quest CIQ forms.

Provides shared functionality for level-based forms that need access to
the quest session (DesignThinkingSession) without causing duplicate argument errors.
"""


class QuestSessionFormMixin:
    """
    Mixin to inject quest_session exactly once for Level forms.

    Prevents TypeError: __init__() got multiple values for argument 'quest_session'
    by accepting quest_session as keyword-only and removing it before passing to super().

    Usage:
        class MyLevelForm(QuestSessionFormMixin, forms.Form):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                # self.quest_session is available here
    """

    def __init__(self, *args, **kwargs):
        # Accept quest_session as kw-only; remove if present to avoid super clashes
        self.quest_session = kwargs.pop("quest_session", None)
        super().__init__(*args, **kwargs)
