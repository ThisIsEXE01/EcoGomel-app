from django.http import JsonResponse
from django.db.models import Q
from .models import DropoffPoint, WasteItem


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


def point_to_dict(point):
    """Превращает пункт приёма в формат JSON для карты Leaflet.

    Координаты отдаются числами (float), а не строками, чтобы их можно
    было сразу передать в L.marker([latitude, longitude]).
    accepted_types — уникальные категории принимаемых отходов
    (map_filter_category, а если она пустая — category); они совпадают
    со значениями фильтров на странице карты.
    """
    accepted_types = sorted({
        waste.map_filter_category or waste.category
        for waste in point.accepted_types.all()
    })

    return {
        "id": point.id,
        "name": point.name,
        "address": point.address,
        "latitude": float(point.latitude),
        "longitude": float(point.longitude),
        "working_hours": point.working_hours,
        "description": point.description,
        "accepted_types": accepted_types,
    }


def points_list(request):
    """
    GET /api/points/
    GET /api/points/?waste_id=1

    Список пунктов приёма для карты. Параметр waste_id оставляет только
    пункты, которые принимают отход с этим id (нечисловое значение -> 400).
    """
    if request.method != "GET":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    queryset = DropoffPoint.objects.prefetch_related("accepted_types").order_by("id")

    waste_id = request.GET.get("waste_id", "").strip()
    if waste_id:
        try:
            waste_id = int(waste_id)
        except ValueError:
            return JsonResponse(
                {"error": "waste_id должен быть целым числом"},
                status=400,
                json_dumps_params={'ensure_ascii': False},
            )
        queryset = queryset.filter(accepted_types__id=waste_id)

    data = [point_to_dict(point) for point in queryset]
    return JsonResponse(data, safe=False, json_dumps_params={'ensure_ascii': False})
