from collections import defaultdict
from decimal import Decimal

import requests
from django.conf import settings
from django.core.exceptions import ValidationError

from store.models import StoreLocation


VOLUMETRIC_DIVISOR = Decimal("5000")

MEXICO_STATE_CODES = {
    "aguascalientes": "AG", "baja california": "BC", "baja california sur": "BS",
    "campeche": "CM", "chiapas": "CS", "chihuahua": "CH", "ciudad de mexico": "CX",
    "cdmx": "CX", "coahuila": "CO", "colima": "CL", "durango": "DG",
    "guanajuato": "GT", "guerrero": "GR", "hidalgo": "HG", "jalisco": "JC",
    "estado de mexico": "EM", "mexico": "EM", "michoacan": "MI", "morelos": "MO",
    "nayarit": "NA", "nuevo leon": "NL", "oaxaca": "OA", "puebla": "PU",
    "queretaro": "QT", "quintana roo": "QR", "san luis potosi": "SP",
    "sinaloa": "SI", "sonora": "SO", "tabasco": "TB", "tamaulipas": "TM",
    "tlaxcala": "TL", "veracruz": "VE", "yucatan": "YU", "zacatecas": "ZA",
}


class ShippingConfigurationError(ValidationError):
    pass


def _plain(value):
    return Decimal(str(value))


def _state_code(value):
    normalized = str(value or "").strip().lower()
    return MEXICO_STATE_CODES.get(normalized, str(value or "").strip())


def _shipping_profile(variant):
    product = variant.product
    if product.has_shipping_dimensions:
        return {
            "weight": _plain(product.package_weight_kg),
            "length": _plain(product.package_length_cm),
            "width": _plain(product.package_width_cm),
            "height": _plain(product.package_height_cm),
            "capacity": int(product.units_per_package),
        }
    if all([variant.weight_kg, variant.length_cm, variant.width_cm, variant.height_cm]):
        return {
            "weight": _plain(variant.weight_kg),
            "length": _plain(variant.length_cm),
            "width": _plain(variant.width_cm),
            "height": _plain(variant.height_cm),
            "capacity": 1,
        }
    raise ShippingConfigurationError(
        f"Faltan peso o medidas de empaque para {variant.product.name} ({variant.sku})."
    )


def build_packages(cart):
    """Agrupa unidades compatibles para usar el menor número seguro de cajas."""
    groups = defaultdict(list)
    for item in cart.items.select_related("variant", "variant__product"):
        profile = _shipping_profile(item.variant)
        key = (
            profile["length"], profile["width"], profile["height"], profile["capacity"],
        )
        for _ in range(item.quantity):
            groups[key].append({
                "name": item.variant.product.name,
                "weight": profile["weight"],
                "value": _plain(item.variant.current_price),
            })

    packages = []
    for (length, width, height, capacity), units in groups.items():
        for start in range(0, len(units), capacity):
            box_units = units[start:start + capacity]
            real_weight = sum((unit["weight"] for unit in box_units), Decimal("0"))
            declared_value = sum((unit["value"] for unit in box_units), Decimal("0"))
            volumetric_weight = (length * width * height / VOLUMETRIC_DIVISOR).quantize(Decimal("0.001"))
            packages.append({
                "content": ", ".join(dict.fromkeys(unit["name"] for unit in box_units)),
                "amount": 1,
                "type": "box",
                "weight": float(real_weight),
                "insurance": 0,
                "declaredValue": float(declared_value),
                "weightUnit": "KG",
                "lengthUnit": "CM",
                "dimensions": {
                    "length": float(length),
                    "width": float(width),
                    "height": float(height),
                },
                "_units": len(box_units),
                "_volumetric_weight": volumetric_weight,
                "_billable_weight": max(real_weight, volumetric_weight),
            })
    return packages


def package_summary(packages):
    return {
        "boxes": len(packages),
        "actual_weight_kg": str(sum((_plain(p["weight"]) for p in packages), Decimal("0"))),
        "billable_weight_kg": str(sum((p["_billable_weight"] for p in packages), Decimal("0"))),
        "units": sum(p["_units"] for p in packages),
    }


def _api_packages(packages):
    return [
        {key: value for key, value in package.items() if not key.startswith("_")}
        for package in packages
    ]


def quote_shipping(*, cart, address):
    if not settings.ENVIA_API_TOKEN:
        raise ShippingConfigurationError(
            "Envia.com todavía no está habilitado. El administrador debe configurar ENVIA_API_TOKEN."
        )
    origin = StoreLocation.objects.filter(active=True, is_shipping_origin=True).first()
    if not origin:
        raise ShippingConfigurationError("Configura una sucursal como origen de envíos.")
    if not origin.postal_code or not origin.phone:
        raise ShippingConfigurationError(
            "El origen de envíos necesita código postal y teléfono antes de cotizar."
        )

    packages = build_packages(cart)
    origin_data = origin.envia_address()
    origin_data["state"] = _state_code(origin.state)
    payload = {
        "origin": origin_data,
        "destination": {
            "name": address.recipient_name,
            "street": f"{address.street} {address.exterior_number}",
            "district": address.neighborhood,
            "city": address.city,
            "state": _state_code(address.state),
            "postalCode": address.postal_code,
            "country": "MX",
            "phone": address.phone,
        },
        "packages": _api_packages(packages),
        "shipment": {"type": 1},
        "settings": {"currency": "MXN"},
    }
    response = requests.post(
        settings.ENVIA_RATE_URL,
        json=payload,
        headers={
            "Authorization": f"Bearer {settings.ENVIA_API_TOKEN}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        },
        timeout=25,
    )
    try:
        response.raise_for_status()
    except requests.HTTPError as exc:
        detail = ""
        try:
            error_body = response.json()
            detail = error_body.get("message") or error_body.get("error") or ""
        except (ValueError, AttributeError):
            pass
        raise ShippingConfigurationError(
            f"Envia.com rechazó la cotización ({response.status_code}). {detail}".strip()
        ) from exc

    data = response.json()
    if isinstance(data, dict) and data.get("meta") == "error":
        error = data.get("error") or {}
        detail = error.get("message") or error.get("description") or "Error no especificado."
        raise ShippingConfigurationError(f"Envia.com rechazó la cotización: {detail}")
    options = data.get("data", []) if isinstance(data, dict) else data
    if isinstance(options, dict):
        options = options.get("rates", options.get("services", []))
    normalized = []
    for option in options or []:
        total = option.get("totalPrice", option.get("cost", option.get("price")))
        if total is None:
            continue
        amount = Decimal(str(total)).quantize(Decimal("0.01"))
        carrier = str(option.get("carrier", option.get("carrierDescription", "")))
        service_code = str(option.get("service", option.get("serviceCode", "")))
        service_label = str(option.get("serviceDescription") or service_code)
        stable_id = str(option.get("rateId") or option.get("id") or f"{carrier}|{service_code}|{amount}")
        normalized.append({
            "rate_id": stable_id,
            "carrier": carrier,
            "service": service_code,
            "service_label": service_label,
            "amount": str(amount),
            "currency": option.get("currency", "MXN"),
            "delivery_days": option.get("deliveryEstimate", option.get("deliveryDays", "")),
        })
    return sorted(normalized, key=lambda item: Decimal(item["amount"])), package_summary(packages)
