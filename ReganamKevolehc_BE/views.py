from django.http import JsonResponse


def get_consts(request):
    consts = {
        # TODO: here insert choiches / consts relevant for FE
    }
    return JsonResponse(consts)
