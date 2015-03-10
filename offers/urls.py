from django.conf.urls import url

from offers.forms import OfferForm
from offers.models import Offer
from offers.views import OfferListView, OfferRefreshView, OfferPDFView
from tools.views import (
    DetailView, CreateView, UpdateView, DeleteView)


urlpatterns = [
    url(
        r'^$',
        OfferListView.as_view(),
        name='offers_offer_list'),
    url(
        r'^(?P<pk>\d+)/$',
        DetailView.as_view(model=Offer),
        name='offers_offer_detail'),
    url(
        r'^create/$',
        CreateView.as_view(
            form_class=OfferForm,
            model=Offer,
        ),
        name='offers_offer_create'),
    url(
        r'^(?P<pk>\d+)/update/$',
        UpdateView.as_view(
            form_class=OfferForm,
            model=Offer,
        ),
        name='offers_offer_update'),
    url(
        r'^(?P<pk>\d+)/delete/$',
        DeleteView.as_view(model=Offer),
        name='offers_offer_delete'),

    url(
        r'^(?P<pk>\d+)/refresh/$',
        OfferRefreshView.as_view(),
        name='offers_offer_refresh'),
    url(
        r'^(?P<pk>\d+)/pdf/$',
        OfferPDFView.as_view(),
        name='offers_offer_pdf'),
]
