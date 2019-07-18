from django.shortcuts import redirect, render

from workbench.projects.forms import ProjectAutocompleteForm


def createhours(request):
    form = ProjectAutocompleteForm(request.POST if request.method == "POST" else None)
    if form.is_valid():
        return redirect(form.cleaned_data["project"].urls["createhours"])
    return render(request, "projects/select_project.html", {"form": form})
