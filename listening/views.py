from django.http import JsonResponse


def get_info(request):
    info = {
    }
    return JsonResponse(info)
