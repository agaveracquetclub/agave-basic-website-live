from .services.carts import get_cart


def cart_summary(request):
    if request.path.startswith("/admin/"):
        return {"cart_item_count": 0}
    try:
        cart = get_cart(request, create=False)
        return {"cart_item_count": cart.item_count if cart else 0}
    except Exception:
        return {"cart_item_count": 0}

