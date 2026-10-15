from django import forms

from .models import MenuItem, DiscoveryTag


class MenuItemAdminForm(forms.ModelForm):

    # ============================================================
    # DISCOVERY TAGS
    # ============================================================

    mood_tags = forms.ModelMultipleChoiceField(
        queryset=DiscoveryTag.objects.filter(type="mood"),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label="Mood",
    )

    craving_tags = forms.ModelMultipleChoiceField(
        queryset=DiscoveryTag.objects.filter(type="craving"),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label="Craving",
    )

    looks_tags = forms.ModelMultipleChoiceField(
        queryset=DiscoveryTag.objects.filter(type="looks"),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label="Looks",
    )

    hunger_tags = forms.ModelMultipleChoiceField(
        queryset=DiscoveryTag.objects.filter(type="hunger"),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label="Hunger",
    )

    experience_tags = forms.ModelMultipleChoiceField(
        queryset=DiscoveryTag.objects.filter(type="experience"),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label="Experience",
    )

    class Meta:
        model = MenuItem
        exclude = ["discovery_tags"]

    # ============================================================
    # LOAD EXISTING DISCOVERY TAGS
    # ============================================================

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        if self.instance and self.instance.pk:

            tags = self.instance.discovery_tags.all()

            self.fields["mood_tags"].initial = tags.filter(
                type="mood"
            )

            self.fields["craving_tags"].initial = tags.filter(
                type="craving"
            )

            self.fields["looks_tags"].initial = tags.filter(
                type="looks"
            )

            self.fields["hunger_tags"].initial = tags.filter(
                type="hunger"
            )

            self.fields["experience_tags"].initial = tags.filter(
                type="experience"
            )

    # ============================================================
    # SAVE MENU ITEM
    # ============================================================

    # def save(self, commit=True):

    #     instance = super().save(commit=commit)

    #     if commit:
    #         self._save_discovery_tags()

    #     return instance

    # ============================================================
    # SAVE MANY-TO-MANY DATA
    # ============================================================

    # def save_m2m(self):

    #     self._save_discovery_tags()

    # ============================================================
    # SAVE DISCOVERY TAGS
    # ============================================================

    def _save_discovery_tags(self):

        if not self.instance.pk:
            return

        tags = []

        tags.extend(
            self.cleaned_data.get("mood_tags", [])
        )

        tags.extend(
            self.cleaned_data.get("craving_tags", [])
        )

        tags.extend(
            self.cleaned_data.get("looks_tags", [])
        )

        tags.extend(
            self.cleaned_data.get("hunger_tags", [])
        )

        tags.extend(
            self.cleaned_data.get("experience_tags", [])
        )

        self.instance.discovery_tags.set(tags)