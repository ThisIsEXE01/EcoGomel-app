from django.http import JsonResponse

from .models import WasteItem


def waste_list(request):
    items = WasteItem.objects.all()

    data = []

    for item in items:
        data.append({
            "id": item.id,
            "name": item.name,
            "category": item.category,
            "code": item.code,
            "recyclable": item.recyclable,
            "hazard_class": item.hazard_class,
            "preparation_steps": item.preparation_steps,
            "what_happens_next": item.what_happens_next,
            "keywords": item.keywords,
            "map_filter_category": item.map_filter_category
        })

    return JsonResponse(data, safe=False)