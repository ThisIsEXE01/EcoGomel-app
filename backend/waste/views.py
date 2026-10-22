from django.http import JsonResponse
from django.db.models import Q
from .models import WasteItem


def waste_to_dict(item):
    """Превращает объект отхода из базы данных в формат JSON."""
    return {
        "id": item.id,
        "name": item.name,
        "category": item.category,
        "code": item.code,
        "recyclable": item.recyclable,
        "hazard_class": item.hazard_class,
        "preparation_steps": item.preparation_steps,
        "what_happens_next": item.what_happens_next,
        "keywords": item.keywords,
        "map_filter_category": item.map_filter_category,
    }


def waste_list(request):
    """
    GET /api/waste/
    GET /api/waste/?search=PET&code=01&category=Пластик&recyclable=true

    Получение списка отходов с поиском и фильтрацией.
    """
    if request.method != "GET":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    queryset = WasteItem.objects.all()

    # 1. Общий поиск (по названию, категории, ключевым словам И коду)
    search_query = request.GET.get("search", "").strip()
    if search_query:
        queryset = queryset.filter(
            Q(name__icontains=search_query) |
            Q(category__icontains=search_query) |
            Q(keywords__icontains=search_query) |
            Q(code__icontains=search_query)
        )

    # 2. Фильтрация по конкретному коду (например, ?code=01 или ?code=PET)
    code_query = request.GET.get("code", "").strip()
    if code_query:
        queryset = queryset.filter(code__icontains=code_query)

    # 3. Фильтрация по категории
    category = request.GET.get("category", "").strip()
    if category:
        queryset = queryset.filter(category__iexact=category)

    # 4. Фильтрация по перерабатываемости (true / false)
    recyclable = request.GET.get("recyclable", "").strip()
    if recyclable.lower() in ["true", "1"]:
        queryset = queryset.filter(recyclable=True)
    elif recyclable.lower() in ["false", "0"]:
        queryset = queryset.filter(recyclable=False)

    data = [waste_to_dict(item) for item in queryset]
    return JsonResponse(data, safe=False, json_dumps_params={'ensure_ascii': False})


def waste_detail(request, pk):
    """
    GET /api/waste/<pk>/

    Получение одного отхода по ID.
    """
    if request.method != "GET":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    try:
        item = WasteItem.objects.get(pk=pk)
    except WasteItem.DoesNotExist:
        return JsonResponse({"error": "Waste item not found"}, status=404)

    return JsonResponse(waste_to_dict(item), json_dumps_params={'ensure_ascii': False})