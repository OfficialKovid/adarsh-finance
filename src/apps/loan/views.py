from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from .models import LoanScheme, Benefit, EligibilityCriteria, RequiredDocument, CoveredSector, KeyPoint, LoanApplication

def list_loans(request):
    loans = LoanScheme.objects.filter(is_active=True).prefetch_related(
        'key_points',
        'covered_sectors'
    )
    return render(request, 'loan/list_loans.html', {'loans': loans})

def is_staff_user(user):
    return user.is_staff

@login_required
@user_passes_test(is_staff_user)
def add_new_loan(request):
    if request.method == 'POST':
        # Create new loan scheme
        scheme = LoanScheme.objects.create(
            title=request.POST['title'],
            full_name=request.POST['full_name'],  # changed from short_name
            description=request.POST['description'],
            start_year=request.POST.get('start_year') or None,  # handle optional field
            end_year=request.POST.get('end_year') or None,      # handle optional field
            contact_info=request.POST['contact_info'],
            image=request.FILES.get('image')
        )

        # Add sectors
        sectors = request.POST.get('sectors[]', '').split(',')
        for sector in sectors:
            if sector:
                CoveredSector.objects.create(
                    scheme=scheme,
                    sector_name=sector
                )

        # Add benefits
        benefits = request.POST.getlist('benefits[]')
        for benefit in benefits:
            if benefit:
                Benefit.objects.create(scheme=scheme, description=benefit)

        # Add eligibility criteria
        criteria_list = request.POST.getlist('criteria[]')
        for criteria in criteria_list:
            if criteria:
                EligibilityCriteria.objects.create(scheme=scheme, criteria=criteria)

        # Add required documents
        documents = request.POST.getlist('documents[]')
        for doc in documents:
            if doc:
                RequiredDocument.objects.create(scheme=scheme, document_name=doc)

        # Add key points
        key_points = request.POST.getlist('key_points[]')
        for i, point in enumerate(key_points[:3]):  # Limit to 3 points
            if point:
                KeyPoint.objects.create(
                    scheme=scheme,
                    point=point,
                    display_order=i
                )

        return redirect('list_loans')

    # Fetch all existing items
    context = {
        'existing_sectors': CoveredSector.objects.values_list('sector_name', flat=True).distinct().order_by('sector_name'),
        'existing_benefits': Benefit.objects.values_list('description', flat=True).distinct().order_by('description'),
        'existing_criteria': EligibilityCriteria.objects.values_list('criteria', flat=True).distinct().order_by('criteria'),
        'existing_documents': RequiredDocument.objects.values_list('document_name', flat=True).distinct().order_by('document_name'),
        'existing_key_points': KeyPoint.objects.values_list('point', flat=True).distinct().order_by('point'),
    }
    return render(request, 'loan/add_new_loan.html', context)

def loan_details(request, slug):
    loan = get_object_or_404(LoanScheme, slug=slug, is_active=True)
    context = {
        'loan': loan,
        'benefits': loan.benefits.all(),
        'criteria': loan.eligibility_criteria.all(),
        'documents': loan.required_documents.all(),
        'sectors': loan.covered_sectors.all(),
        'key_points': loan.key_points.all()[:3]
    }
    return render(request, 'loan/loan_details.html', context)

@require_POST
def apply_loan(request, slug):
    try:
        loan = get_object_or_404(LoanScheme, slug=slug)
        application = LoanApplication.objects.create(
            name=request.POST['name'],
            phone_number=request.POST['phone_number'],
            scheme=loan
        )
        return JsonResponse({'status': 'success'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})

@login_required
@user_passes_test(is_staff_user)
def applications_list(request):
    applications = LoanApplication.objects.select_related('scheme').all()
    
    # Apply filters
    status = request.GET.get('status')
    scheme = request.GET.get('scheme')
    
    if status:
        applications = applications.filter(status=status)
    if scheme:
        applications = applications.filter(scheme_id=scheme)
        
    context = {
        'applications': applications,
        'schemes': LoanScheme.objects.all()
    }
    return render(request, 'loan/applications_list.html', context)

@login_required
@user_passes_test(is_staff_user)
@require_POST
def update_application_status(request, application_id):
    try:
        application = LoanApplication.objects.get(id=application_id)
        application.status = request.POST.get('status')
        application.save()
        return JsonResponse({'status': 'success'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})
