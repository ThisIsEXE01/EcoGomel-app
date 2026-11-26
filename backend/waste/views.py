from decimal import Decimal, InvalidOperation
import json

from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.db.models import Q
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.http import require_POST
import pymorphy3

from .models import DropoffPoint, PointSuggestion, WasteItem

morph = pymorphy3.MorphAnalyzer()


def get_word_lemmas(text: str) -> list[set[str]]:
  """Разбивает текст на слова и возвращает варианты (исходное, лемму и их капитализированные версии для обхода ограничений SQLite с кириллицей)."""
  words = text.strip().split()
  term_groups = []

  for word in words:
    clean_word = word.strip(',.!?:;()[]{}""\'')

    if not clean_word:
      continue

    clean_lower = clean_word.lower()
    variants = {clean_lower, clean_word, clean_lower.capitalize()}
    parsed = morph.parse(clean_word)

    if parsed:
      p = parsed[0]
      nf = p.normal_form.lower()
      variants.add(nf)

      for form in p.lexeme:
        fw = form.word.lower()
        variants.add(fw)
        variants.add(fw.capitalize())

    term_groups.append(variants)

  return term_groups


def waste_to_dict(item):
  """Превращает объект отхода из базы данных в формат JSON."""
  return {
      'id': item.id,
      'name': item.name,
      'category': item.category,
      'code': item.code,
      'recyclable': item.recyclable,
      'hazard_class': item.hazard_class,
      'preparation_steps': item.preparation_steps,
      'what_happens_next': item.what_happens_next,
      'keywords': item.keywords,
      'map_filter_category': item.map_filter_category,
  }


def waste_list(request):
  """GET /api/waste/

  GET /api/waste/?search=PET&code=01&category=Пластик&recyclable=true

  Получение списка отходов с морфологическим поиском и фильтрацией.
  """
  if request.method != 'GET':
    return JsonResponse({'error': 'Method not allowed'}, status=405)

  queryset = WasteItem.objects.all()

  # 1. Общий поиск с морфологией: AND между разными словами, OR внутри вариантов слова
  search_query = request.GET.get('search', '').strip()
  if search_query:
    word_groups = get_word_lemmas(search_query)

    for variants in word_groups:
      word_query = Q()
      for term in variants:
        if len(term) >= 2:
          word_query |= (
              Q(name__icontains=term)
              | Q(category__icontains=term)
              | Q(keywords__icontains=term)
              | Q(code__icontains=term)
          )
      if word_query:
        queryset = queryset.filter(word_query)

    queryset = queryset.distinct()

  # 2. Фильтрация по конкретному коду
  code_query = request.GET.get('code', '').strip()
  if code_query:
    queryset = queryset.filter(code__icontains=code_query)

  # 3. Фильтрация по категории
  category = request.GET.get('category', '').strip()
  if category:
    queryset = queryset.filter(category__iexact=category)

  # 4. Фильтрация по перерабатываемости
  recyclable = request.GET.get('recyclable', '').strip()
  if recyclable.lower() in ['true', '1']:
    queryset = queryset.filter(recyclable=True)
  elif recyclable.lower() in ['false', '0']:
    queryset = queryset.filter(recyclable=False)

  data = [waste_to_dict(item) for item in queryset]
  return JsonResponse(
      data, safe=False, json_dumps_params={'ensure_ascii': False}
  )


def waste_detail(request, pk):
  """GET /api/waste/<pk>/

  Получение одного отхода по ID.
  """
  if request.method != 'GET':
    return JsonResponse({'error': 'Method not allowed'}, status=405)

  try:
    item = WasteItem.objects.get(pk=pk)
  except WasteItem.DoesNotExist:
    return JsonResponse({'error': 'Waste item not found'}, status=404)

  return JsonResponse(
      waste_to_dict(item), json_dumps_params={'ensure_ascii': False}
  )


def point_to_dict(point):
  """Превращает пункт приёма в формат JSON для карты Leaflet."""
  accepted_types = sorted({
      waste.map_filter_category or waste.category
      for waste in point.accepted_types.all()
  })

  return {
      'id': point.id,
      'name': point.name,
      'address': point.address,
      'latitude': float(point.latitude),
      'longitude': float(point.longitude),
      'working_hours': point.working_hours,
      'description': point.description,
      'accepted_types': accepted_types,
  }


def points_list(request):
  """GET /api/points/

  GET /api/points/?waste_id=1

  Список пунктов приёма для карты.
  """
  if request.method != 'GET':
    return JsonResponse({'error': 'Method not allowed'}, status=405)

  queryset = DropoffPoint.objects.prefetch_related('accepted_types').order_by(
      'id'
  )

  waste_id = request.GET.get('waste_id', '').strip()
  if waste_id:
    try:
      waste_id = int(waste_id)
    except ValueError:
      return JsonResponse(
          {'error': 'waste_id должен быть целым числом'},
          status=400,
          json_dumps_params={'ensure_ascii': False},
      )
    queryset = queryset.filter(accepted_types__id=waste_id)

  data = [point_to_dict(point) for point in queryset]
  return JsonResponse(
      data, safe=False, json_dumps_params={'ensure_ascii': False}
  )


def _get_client_ip(request) -> str:
  forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
  if forwarded_for:
    return forwarded_for.split(',')[0].strip()
  return request.META.get('REMOTE_ADDR', '0.0.0.0')


def _parse_coordinate(raw_value, field_name: str, min_val: int, max_val: int):
  if raw_value is None or raw_value == '':
    return None
  try:
    value = Decimal(str(raw_value))
  except (InvalidOperation, TypeError, ValueError):
    raise ValueError(f'Поле «{field_name}» должно быть числом.')
  if not (min_val <= value <= max_val):
    raise ValueError(
        f'Поле «{field_name}» должно быть в диапазоне от {min_val} до {max_val}.'
    )
  return value


def _validate_suggestion_payload(data: dict) -> tuple[dict, dict]:
  errors = {}

  # Скрытое поле-ловушка (honeypot) для защиты от ботов
  honeypot = str(data.get('website', '') or '').strip()
  if honeypot:
    errors['spam'] = 'Обнаружен спам.'
    return {}, errors

  name = str(data.get('name', '') or '').strip()
  address = str(data.get('address', '') or '').strip()
  working_hours = str(data.get('working_hours', '') or '').strip()
  description = str(data.get('description', '') or '').strip()
  contact_email = str(data.get('contact_email', '') or '').strip()

  if len(name) < 2:
    errors['name'] = 'Название точки должно содержать минимум 2 символа.'
  elif len(name) > 300:
    errors['name'] = 'Название точки не должно превышать 300 символов.'

  if len(address) < 5:
    errors['address'] = 'Укажите более подробный адрес (минимум 5 символов).'
  elif len(address) > 300:
    errors['address'] = 'Адрес не должен превышать 300 символов.'

  if len(working_hours) > 300:
    errors['working_hours'] = 'Время работы не должно превышать 300 символов.'

  if len(description) > 1000:
    errors['description'] = 'Описание не должно превышать 1000 символов.'

  if contact_email:
    try:
      validate_email(contact_email)
    except ValidationError:
      errors['contact_email'] = 'Некорректный формат email.'

  lat = None
  lon = None
  try:
    lat = _parse_coordinate(data.get('latitude'), 'latitude', -90, 90)
  except ValueError as exc:
    errors['latitude'] = str(exc)

  try:
    lon = _parse_coordinate(data.get('longitude'), 'longitude', -180, 180)
  except ValueError as exc:
    errors['longitude'] = str(exc)

  if ('latitude' not in errors and 'longitude' not in errors) and (
      (lat is None) ^ (lon is None)
  ):
    errors['coordinates'] = (
        'Укажите обе координаты (широту и долготу) или оставьте оба поля'
        ' пустыми.'
    )

  accepted_type_ids = []
  raw_types = data.get('accepted_types')
  if raw_types is not None:
    if not isinstance(raw_types, list):
      errors['accepted_types'] = 'Поле accepted_types должно быть списком ID.'
    else:
      for item_id in raw_types:
        if (
            isinstance(item_id, bool)
            or not isinstance(item_id, int)
            or item_id <= 0
        ):
          errors['accepted_types'] = (
              'Каждый элемент accepted_types должен быть положительным целым'
              ' числом.'
          )
          break
        accepted_type_ids.append(item_id)

      if 'accepted_types' not in errors and accepted_type_ids:
        existing_ids = set(
            WasteItem.objects.filter(id__in=accepted_type_ids).values_list(
                'id', flat=True
            )
        )
        missing_ids = [
            item_id for item_id in accepted_type_ids if item_id not in existing_ids
        ]
        if missing_ids:
          errors['accepted_types'] = (
              f'Несуществующие ID видов отходов: {missing_ids}.'
          )

  if errors:
    return {}, errors

  cleaned = {
      'name': name,
      'address': address,
      'latitude': lat,
      'longitude': lon,
      'working_hours': working_hours,
      'description': description,
      'contact_email': contact_email,
      'accepted_type_ids': accepted_type_ids,
  }
  return cleaned, {}


@require_POST
def points_suggest(request):
  """POST /api/points/suggest/

  Приём предложения новой точки приёма с валидацией, защитой от спама и статусом модерации.
  """
  ip = _get_client_ip(request)

  # Ограничение частоты запросов: максимум 5 отправок за 10 минут с одного IP
  rate_key = f'points_suggest_rate:{ip}'
  attempts = cache.get(rate_key, 0)
  if attempts >= 5:
    return JsonResponse(
        {'error': 'Слишком много запросов. Попробуйте позже.'},
        status=429,
        json_dumps_params={'ensure_ascii': False},
    )

  if request.content_type and 'application/json' in request.content_type:
    try:
      payload = json.loads(request.body.decode('utf-8') or '{}')
    except (UnicodeDecodeError, json.JSONDecodeError):
      return JsonResponse(
          {'error': 'Некорректный JSON.'},
          status=400,
          json_dumps_params={'ensure_ascii': False},
      )
    if not isinstance(payload, dict):
      return JsonResponse(
          {'error': 'Ожидается JSON-объект.'},
          status=400,
          json_dumps_params={'ensure_ascii': False},
      )
  else:
    payload = request.POST.dict()

  cleaned_data, errors = _validate_suggestion_payload(payload)
  if errors:
    return JsonResponse(
        {'errors': errors},
        status=400,
        json_dumps_params={'ensure_ascii': False},
    )

  # Защита от дубликата с тем же адресом и IP за последние 10 минут
  ten_minutes_ago = timezone.now() - timezone.timedelta(minutes=10)
  is_duplicate = PointSuggestion.objects.filter(
      ip_address=ip,
      address__iexact=cleaned_data['address'],
      created_at__gte=ten_minutes_ago,
  ).exists()
  if is_duplicate:
    return JsonResponse(
        {'error': 'Предложение с таким адресом уже отправлено недавно.'},
        status=409,
        json_dumps_params={'ensure_ascii': False},
    )

  accepted_type_ids = cleaned_data.pop('accepted_type_ids')
  suggestion = PointSuggestion.objects.create(
      **cleaned_data,
      status=PointSuggestion.Status.PENDING,
      ip_address=ip,
  )
  if accepted_type_ids:
    suggestion.accepted_types.set(accepted_type_ids)

  cache.set(rate_key, attempts + 1, timeout=600)

  return JsonResponse(
      {
          'id': suggestion.id,
          'status': suggestion.status,
          'message': 'Предложение отправлено на модерацию.',
      },
      status=201,
      json_dumps_params={'ensure_ascii': False},
  )