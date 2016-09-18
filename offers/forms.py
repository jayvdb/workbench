from collections import OrderedDict

from django import forms
from django.forms.models import inlineformset_factory
from django.template.defaultfilters import linebreaksbr
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

from contacts.models import PostalAddress
from offers.models import Offer, Service, Effort, Cost
from tools.formats import local_date_format
from tools.forms import ModelForm, Textarea, WarningsForm


class OfferSearchForm(forms.Form):
    s = forms.ChoiceField(
        choices=(('', _('All states')),) + Offer.STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'}),
    )

    def filter(self, queryset):
        if not self.is_valid():
            return queryset

        data = self.cleaned_data
        if data.get('s'):
            queryset = queryset.filter(status=data.get('s'))

        return queryset


class CreateOfferForm(ModelForm):
    user_fields = default_to_current_user = ('owned_by',)

    class Meta:
        model = Offer
        fields = (
            'title', 'description', 'owned_by',
        )

    def __init__(self, *args, **kwargs):
        self.project = kwargs.pop('project')
        kwargs['initial'] = {
            'title': self.project.title,
            'description': self.project.description,
        }

        super().__init__(*args, **kwargs)

        postal_addresses = []

        if self.project.contact:
            postal_addresses.extend(
                (pa.id, linebreaksbr(pa.postal_address))
                for pa in PostalAddress.objects.filter(
                    person=self.project.contact,
                )
            )

        postal_addresses.extend(
            (pa.id, linebreaksbr(pa.postal_address))
            for pa in PostalAddress.objects.filter(
                person__organization=self.project.customer,
            ).exclude(person=self.project.contact)
        )

        if postal_addresses:
            self.fields['pa'] = forms.ModelChoiceField(
                PostalAddress.objects.all(),
                label=_('postal address'),
                help_text=_('The exact address can be edited later.'),
                widget=forms.RadioSelect,
            )
            self.fields['pa'].choices = postal_addresses

    def save(self):
        instance = super().save(commit=False)
        if self.cleaned_data.get('pa'):
            instance.postal_address = self.cleaned_data['pa'].postal_address
        instance.project = self.project
        instance.save()
        return instance


class OfferForm(WarningsForm, ModelForm):
    user_fields = default_to_current_user = ('owned_by',)

    class Meta:
        model = Offer
        fields = (
            'offered_on', 'title', 'description', 'owned_by', 'status',
            'postal_address')
        widgets = {
            'status': forms.RadioSelect,
        }

    def clean(self):
        data = super().clean()
        s_dict = dict(Offer.STATUS_CHOICES)

        if data.get('status', 0) >= Offer.ACCEPTED:
            if not self.instance.closed_at:
                self.instance.closed_at = timezone.now()

        if self.instance.closed_at and data.get('status', 99) < Offer.ACCEPTED:
            if self.request.POST.get('ignore_warnings'):
                self.instance.closed_at = None
            else:
                self.add_warning(_(
                    "You are attempting to set status to '%(to)s',"
                    " but the offer has already been closed on %(closed)s."
                    " Are you sure?"
                ) % {
                    'to': s_dict[data['status']],
                    'closed': local_date_format(
                        self.instance.closed_at, 'd.m.Y'),
                })

        return data


class ServiceForm(ModelForm):
    class Meta:
        model = Service
        fields = ('title', 'description')
        widgets = {
            'description': Textarea(),
        }

    def __init__(self, *args, **kwargs):
        self.offer = kwargs.pop('offer', None)
        super().__init__(*args, **kwargs)
        kwargs.pop('request')
        self.formsets = OrderedDict((
            ('efforts', EffortFormset(*args, **kwargs)),
            ('costs', CostFormset(*args, **kwargs)),
        )) if self.instance.pk else OrderedDict()

    def is_valid(self):
        return all(
            [super().is_valid()] +
            [formset.is_valid() for formset in self.formsets.values()])

    def save(self):
        instance = super().save(commit=False)
        if self.offer:
            instance.offer = self.offer
        for formset in self.formsets.values():
            formset.save()
        instance.save()
        return instance


EffortFormset = inlineformset_factory(
    Service,
    Effort,
    fields=('service_type', 'hours'),
    extra=0,
)

CostFormset = inlineformset_factory(
    Service,
    Cost,
    fields=('title', 'cost'),
    extra=0,
)
