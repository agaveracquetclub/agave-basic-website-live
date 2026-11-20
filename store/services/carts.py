from django.db import transaction

from store.models import Cart


def _ensure_session(request):
    if not request.session.session_key:
        request.session.create()
    return request.session.session_key


@transaction.atomic
def get_cart(request, *, create=True):
    if request.user.is_authenticated:
        cart = Cart.objects.filter(user=request.user, status=Cart.Status.ACTIVE).first()
        session_key = request.session.session_key
        guest = None
        if session_key:
            guest = Cart.objects.filter(session_key=session_key, status=Cart.Status.ACTIVE, user__isnull=True).first()
        if cart and guest and cart.pk != guest.pk:
            for guest_item in guest.items.select_related("variant"):
                item, made = cart.items.get_or_create(variant=guest_item.variant, defaults={"quantity": guest_item.quantity})
                if not made:
                    item.quantity += guest_item.quantity
                    item.save(update_fields=["quantity", "updated_at"])
            guest.status = Cart.Status.ABANDONED
            guest.save(update_fields=["status", "updated_at"])
        if cart:
            return cart
        if guest:
            guest.user = request.user
            guest.save(update_fields=["user", "updated_at"])
            return guest
        return Cart.objects.create(user=request.user) if create else None
    session_key = _ensure_session(request) if create else request.session.session_key
    if not session_key:
        return None
    lookup = {"session_key": session_key, "status": Cart.Status.ACTIVE, "user__isnull": True}
    return Cart.objects.get_or_create(**lookup)[0] if create else Cart.objects.filter(**lookup).first()

