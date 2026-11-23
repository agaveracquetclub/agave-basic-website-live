from django.urls import path

from . import views
from . import owner_views


app_name = "store"

urlpatterns = [
    path("", views.home, name="home"),
    path("catalogo/", views.catalog, name="catalog"),
    path("producto/<slug:slug>/", views.product_detail, name="product_detail"),
    path("producto/<slug:slug>/agregar/", views.add_to_cart, name="add_to_cart"),
    path("carrito/", views.cart_view, name="cart"),
    path("carrito/item/<int:item_id>/", views.update_cart, name="update_cart"),
    path("registro/", views.register, name="register"),
    path("direcciones/nueva/", views.address_create, name="address_create"),
    path("checkout/", views.checkout, name="checkout"),
    path("checkout/cotizar/", views.shipping_quotes, name="shipping_quotes"),
    path("checkout/crear-pedido/", views.place_order, name="place_order"),
    path("webhooks/mercadopago/", views.mercadopago_webhook, name="mercadopago_webhook"),
    path("pago/exito/", views.payment_result, {"result": "success"}, name="payment_success"),
    path("pago/pendiente/", views.payment_result, {"result": "pending"}, name="payment_pending"),
    path("pago/error/", views.payment_result, {"result": "failure"}, name="payment_failure"),
    path("mis-pedidos/", views.my_orders, name="my_orders"),
    path("panel/venta-externa/", views.external_sale, name="external_sale"),
    path("dueno/", owner_views.dashboard, name="owner_dashboard"),
    path("dueno/productos/", owner_views.products, name="owner_products"),
    path("dueno/productos/nuevo/", owner_views.product_create, name="owner_product_create"),
    path("dueno/productos/<int:pk>/editar/", owner_views.product_edit, name="owner_product_edit"),
    path("dueno/productos/<int:pk>/archivar/", owner_views.product_archive, name="owner_product_archive"),
    path("dueno/productos/<int:pk>/restaurar/", owner_views.product_restore, name="owner_product_restore"),
    path("dueno/productos/<int:product_pk>/variantes/", owner_views.variants, name="owner_variants"),
    path("dueno/productos/<int:product_pk>/variantes/nueva/", owner_views.variant_create, name="owner_variant_create"),
    path("dueno/variantes/<int:pk>/editar/", owner_views.variant_edit, name="owner_variant_edit"),
    path("dueno/variantes/<int:pk>/alternar/", owner_views.variant_toggle, name="owner_variant_toggle"),
    path("dueno/inventario/", owner_views.stock, name="owner_stock"),
    path("dueno/inventario/ajustar/", owner_views.stock_adjust, name="owner_stock_adjust"),
    path("dueno/inventario/ajustar/<int:variant_pk>/", owner_views.stock_adjust, name="owner_stock_adjust_variant"),
    path("dueno/pedidos/", owner_views.orders, name="owner_orders"),
    path("dueno/ubicaciones/", owner_views.locations, name="owner_locations"),
    path("dueno/ubicaciones/nueva/", owner_views.location_create, name="owner_location_create"),
    path("dueno/ubicaciones/<int:pk>/editar/", owner_views.location_edit, name="owner_location_edit"),
    path("dueno/promociones/", owner_views.promotions, name="owner_promotions"),
]

