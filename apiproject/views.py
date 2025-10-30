from django.http import HttpResponse,JsonResponse

def home_page(request):
    print("home page requested")
    friends=[
        'satyam','megha','krina'
    ]
    return JsonResponse(friends,safe=False)