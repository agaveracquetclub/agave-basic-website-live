const form = document.querySelector('#checkout-form');
if (form) {
  const fulfillment = [...form.querySelectorAll('input[name="fulfillment"]')];
  const shipping = document.querySelector('#shipping-fields');
  const pickup = document.querySelector('#pickup-fields');
  const quoteButton = document.querySelector('#quote-button');
  const options = document.querySelector('#shipping-options');
  const packingSummary = document.querySelector('#packing-summary');

  function updateDelivery() {
    const value = fulfillment.find((x) => x.checked)?.value;
    shipping.hidden = value !== 'shipping';
    pickup.hidden = value !== 'pickup';
    fulfillment.forEach((radio) => radio.closest('label')?.classList.toggle('selected', radio.checked));
  }
  fulfillment.forEach((x) => x.addEventListener('change', updateDelivery));
  updateDelivery();

  quoteButton?.addEventListener('click', async () => {
    const address = form.querySelector('[name="address"]').value;
    if (!address) { options.textContent = 'Selecciona una dirección.'; return; }
    options.textContent = 'Consultando tarifas…';
    packingSummary.textContent = '';
    const data = new FormData();
    data.append('address_id', address);
    data.append('csrfmiddlewaretoken', form.querySelector('[name="csrfmiddlewaretoken"]').value);
    try {
      const response = await fetch(quoteButton.dataset.url, {method: 'POST', body: data, credentials: 'same-origin'});
      const payload = await response.json();
      if (!response.ok) throw new Error(payload.error || 'No fue posible cotizar.');
      options.replaceChildren();
      if (payload.packing) {
        const boxes = payload.packing.boxes === 1 ? '1 caja' : `${payload.packing.boxes} cajas`;
        packingSummary.textContent = `Empaque optimizado: ${boxes} para ${payload.packing.units} unidad(es). Peso real ${payload.packing.actual_weight_kg} kg; peso volumétrico/cobrable estimado ${payload.packing.billable_weight_kg} kg.`;
      }
      payload.quotes.forEach((quote, index) => {
        const label = document.createElement('label');
        label.className = 'shipping-option';
        const input = document.createElement('input');
        input.type = 'radio'; input.name = 'shipping-option'; input.required = true;
        input.addEventListener('change', () => {
          form.querySelector('[name="shipping_rate_id"]').value = quote.rate_id;
          form.querySelector('[name="carrier"]').value = quote.carrier;
          form.querySelector('[name="shipping_service"]').value = quote.service;
          form.querySelector('[name="shipping_amount"]').value = quote.amount;
        });
        if (index === 0) { input.checked = true; input.dispatchEvent(new Event('change')); }
        const delivery = quote.delivery_days ? ` · ${quote.delivery_days}` : '';
        label.append(input, document.createTextNode(` ${quote.carrier} · ${quote.service_label || quote.service}${delivery} — $${quote.amount} MXN`));
        options.append(label);
      });
      if (!payload.quotes.length) options.textContent = 'Envia.com no devolvió tarifas para esta dirección.';
    } catch (error) { options.textContent = error.message; }
  });
}

