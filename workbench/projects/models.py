from datetime import date

from django.contrib import messages
from django.db import models
from django.db.models import Sum
from django.db.models.expressions import RawSQL
from django.utils import timezone
from django.utils.functional import cached_property
from django.utils.html import format_html
from django.utils.translation import gettext, gettext_lazy as _

from workbench.accounts.models import User
from workbench.contacts.models import Organization, Person
from workbench.services.models import ServiceBase
from workbench.tools.formats import local_date_format
from workbench.tools.models import Model, SearchQuerySet, Z
from workbench.tools.urls import model_urls


class ProjectQuerySet(SearchQuerySet):
    def open(self):
        return self.filter(closed_on__isnull=True)


@model_urls
class Project(Model):
    ACQUISITION = "acquisition"
    MAINTENANCE = "maintenance"
    ORDER = "order"
    INTERNAL = "internal"

    TYPE_CHOICES = [
        (ACQUISITION, _("Acquisition")),
        (MAINTENANCE, _("Maintenance")),
        (ORDER, _("Order")),
        (INTERNAL, _("Internal")),
    ]

    customer = models.ForeignKey(
        Organization,
        on_delete=models.PROTECT,
        verbose_name=_("customer"),
        related_name="+",
    )
    contact = models.ForeignKey(
        Person,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        verbose_name=_("contact"),
        related_name="+",
    )

    title = models.CharField(_("title"), max_length=200)
    description = models.TextField(_("description"), blank=True)
    owned_by = models.ForeignKey(
        User, on_delete=models.PROTECT, verbose_name=_("owned by"), related_name="+"
    )

    type = models.CharField(_("type"), choices=TYPE_CHOICES, max_length=20)
    created_at = models.DateTimeField(_("created at"), default=timezone.now)
    closed_on = models.DateField(_("closed on"), blank=True, null=True)

    _code = models.IntegerField(_("code"))
    _fts = models.TextField(editable=False, blank=True)

    objects = ProjectQuerySet.as_manager()

    class Meta:
        ordering = ("-id",)
        verbose_name = _("project")
        verbose_name_plural = _("projects")

    def __str__(self):
        return "%s %s %s" % (self.code, self.title, self.owned_by.get_short_name())

    def __html__(self):
        return format_html(
            "<small>{}</small> {} - {}",
            self.code,
            self.title,
            self.owned_by.get_short_name(),
        )

    @property
    def code(self):
        return "%s-%04d" % (self.created_at.year, self._code)

    def save(self, *args, **kwargs):
        new = not self.pk
        if new:
            self._code = RawSQL(
                "SELECT COALESCE(MAX(_code), 0) + 1 FROM projects_project"
                " WHERE EXTRACT(year FROM created_at) = %s",
                (timezone.now().year,),
            )
            super().save(*args, **kwargs)
            self.refresh_from_db()

        self._fts = " ".join(
            str(part)
            for part in [
                self.code,
                self.customer.name,
                self.contact.full_name if self.contact else "",
            ]
        )
        if new:
            super().save()
        else:
            super().save(*args, **kwargs)

    save.alters_data = True

    @property
    def status_css(self):
        if self.closed_on:
            return "secondary"

        return {
            self.ACQUISITION: "info",
            self.MAINTENANCE: "light",
            self.ORDER: "success",
            self.INTERNAL: "warning",
        }[self.type]

    @property
    def pretty_status(self):
        parts = [str(self.get_type_display())]
        if self.closed_on:
            parts.append(
                gettext("closed on %s") % local_date_format(self.closed_on, "d.m.Y")
            )
        return ", ".join(parts)

    @cached_property
    def grouped_services(self):
        # Avoid circular imports
        from workbench.logbook.models import LoggedHours, LoggedCost

        service_hours = Z
        logged_hours = Z
        total_service_cost = Z
        total_logged_cost = Z
        total_service_hours_rate_undefined = Z
        total_logged_hours_rate_undefined = Z

        offers = {
            offer.pk: (offer, []) for offer in self.offers.select_related("owned_by")
        }
        offers[None] = (None, [])

        logged_hours_per_service = {
            row["service"]: row["hours__sum"]
            for row in LoggedHours.objects.order_by()
            .filter(service__project=self)
            .values("service")
            .annotate(Sum("hours"))
        }
        logged_cost_per_service = {
            row["service"]: row["cost__sum"]
            for row in LoggedCost.objects.order_by()
            .filter(project=self)
            .values("service")
            .annotate(Sum("cost"))
        }

        for service in self.services.all():
            service.logged_hours = logged_hours_per_service.get(service.id, 0)
            service.logged_cost = logged_cost_per_service.get(service.id, 0)
            offers[service.offer_id][1].append(service)

            service_hours += service.service_hours
            logged_hours += service.logged_hours

            total_service_cost += service.service_cost
            total_logged_cost += service.logged_cost
            if service.effort_rate:
                total_logged_cost += service.effort_rate * service.logged_hours
            else:
                total_service_hours_rate_undefined += service.service_hours
                total_logged_hours_rate_undefined += service.logged_hours

        if None in logged_cost_per_service:
            service = Service(
                title=gettext("Not bound to a particular service."), service_cost=Z
            )
            service.logged_hours = Z
            service.logged_cost = logged_cost_per_service[None]
            offers[None][1].append(service)

            total_logged_cost += service.logged_cost

        return {
            "offers": sorted(
                (
                    value
                    for value in offers.values()
                    if value[1] or value[0] is not None
                ),
                key=lambda item: (
                    item[0] and item[0].offered_on or date.max,
                    item[0] and item[0].pk or 1e100,
                ),
            ),
            "logged_hours": logged_hours,
            "service_hours": service_hours,
            "total_service_cost": total_service_cost,
            "total_logged_cost": total_logged_cost,
            "total_service_hours_rate_undefined": total_service_hours_rate_undefined,
            "total_logged_hours_rate_undefined": total_logged_hours_rate_undefined,
        }

    @cached_property
    def project_invoices(self):
        return self.invoices.select_related("contact__organization").reverse()

    @cached_property
    def project_invoices_subtotal(self):
        return sum((invoice.subtotal for invoice in self.project_invoices), Z)


@model_urls
class Service(ServiceBase):
    RELATED_MODEL_FIELD = "offer"

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="services",
        verbose_name=_("project"),
    )
    offer = models.ForeignKey(
        "offers.Offer",
        on_delete=models.SET_NULL,
        related_name="services",
        verbose_name=_("offer"),
        blank=True,
        null=True,
    )
    allow_logging = models.BooleanField(
        _("allow logging"),
        default=True,
        help_text=_(
            "Deactivate this for service entries which are only used for budgeting."
        ),
    )
    is_optional = models.BooleanField(
        _("is optional"),
        default=False,
        help_text=_("Optional services to not count towards the offer total."),
    )
    role = models.ForeignKey(
        "circles.Role",
        on_delete=models.SET_NULL,
        related_name="services",
        verbose_name=_("role"),
        blank=True,
        null=True,
    )

    def get_absolute_url(self):
        return self.project.get_absolute_url()

    @classmethod
    def allow_update(cls, instance, request):
        return True

    @classmethod
    def allow_delete(cls, instance, request):
        if instance.offer and instance.offer.status > instance.offer.IN_PREPARATION:
            messages.error(
                request,
                _(
                    "Cannot delete a service bound to an offer"
                    " which is not in preparation anymore."
                ),
            )
            return False
        return None

    @classmethod
    def get_redirect_url(cls, instance, request):
        if not request.is_ajax():
            return instance.get_absolute_url() if instance else "projects_project_list"
