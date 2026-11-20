from django.core.management.base import BaseCommand
from store.services.inventory import release_expired_holds


class Command(BaseCommand):
    help = "Libera el stock de pedidos cuyo pago venció. Ejecutar cada minuto en producción."

    def handle(self, *args, **options):
        count = release_expired_holds(limit=10000)
        self.stdout.write(self.style.SUCCESS(f"{count} pedidos vencidos liberados."))

