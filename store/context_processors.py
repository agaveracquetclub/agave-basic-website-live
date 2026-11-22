from django.conf import settings

from .services.carts import get_cart


def cart_summary(request):
    if request.path.startswith("/admin/"):
        return {"cart_item_count": 0}
    try:
        cart = get_cart(request, create=False)
        return {"cart_item_count": cart.item_count if cart else 0}
    except Exception:
        return {"cart_item_count": 0}


def public_contact(request):
    return {
        "contact_email": settings.AGAVE_CONTACT_EMAIL,
        "whatsapp_url": settings.AGAVE_WHATSAPP_URL,
        "facebook_url": settings.AGAVE_FACEBOOK_URL,
        "instagram_url": settings.AGAVE_INSTAGRAM_URL,
        "google_business_url": settings.AGAVE_GOOGLE_BUSINESS_URL,
    }

