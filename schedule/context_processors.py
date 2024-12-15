from .models import Department

def department_links(request):
    """
    Returns all departments to make them available across all templates.
    """
    return {
        'departments': Department.objects.all()
    }