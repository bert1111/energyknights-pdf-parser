# energyknights-pdf-parser
Load Energy knights variable prices into HA

Een script dat de maandelijkse tariefkaart van Energy Knights downloadt, de prijs per kWh uitleest en beschikbaar maakt voor Home Assistant.

pyscript to automatic import the new variable tariff of "Energy Knights"

prices are fetched from the online pdf file that Energy Knights updates every month or quarter

https://www.energyknights.be/website/getCurrentTariffchart/variable/nl

First install pyscript through hacs

I manually updated the configuration.yaml file

```
pyscript:
  allow_all_imports: true
  hass_is_global: true
```

dowload both files (requirements.txt and energyknights.py) and place them in the "pyscript" folder under home assistant

create an automation to get the data periodically

```
action: Pyscript Python scripting: fetch_energyknights_prices
```

Automation example, untested, so probably contains an error somewhere.

```
alias: Energy Knights prijzen ophalen - met datum validatie
description: >-
  Haalt Energy Knights prijzen op en blijft proberen tot de juiste maand
  beschikbaar is
triggers:
  - at: "00:05:00"
    trigger: time
conditions:
  - condition: template
    value_template: "{{ now().day == 1 }}"
actions:
  - variables:
      initial_price: "{{ states('sensor.energy_buy_price') }}"
      max_attempts: 20
      current_month: "{{ now().strftime('%Y-%m') }}"
  - data:
      message: >
        🔄 Start Energy Knights prijzen ophalen voor {{ current_month }} Huidige
        prijs: {{ initial_price }} EUR/kWh
      title: Energy Knights - Start
    action: persistent_notification.create
  - repeat:
      count: "{{ max_attempts }}"
      sequence:
        - data:
            message: >
              Poging {{ repeat.index }}/{{ max_attempts }}  Zoeken naar
              tariefkaart voor {{ current_month }} Huidige prijs: {{
              states('sensor.energy_buy_price') }}
            title: Energy Knights - Poging {{ repeat.index }}
          action: persistent_notification.create
        - data: {}
          action: pyscript.fetch_energyknights_prices
        - delay: "00:01:00"
        - if:
            - condition: template
              value_template: "{{ states('sensor.energy_buy_price') != initial_price }}"
          then:
            - data:
                message: >
                  ✅ Prijzen succesvol bijgewerkt voor {{ current_month }}! {{
                  initial_price }} → {{ states('sensor.energy_buy_price') }}
                  EUR/kWh  Na {{ repeat.index }} poging(en).
                title: Energy Knights - Succes
              action: persistent_notification.create
            - data:
                message: >
                  Energy Knights prijzen bijgewerkt voor {{ current_month }}! 
                  Nieuwe prijs: {{ states('sensor.energy_buy_price') }} EUR/kWh
                title: Energy Knights - Nieuwe tariefkaart
              action: notify.mobile_app_moto_g72
            - stop: Prijzen succesvol bijgewerkt
        - condition: template
          value_template: "{{ repeat.index < max_attempts }}"
        - choose:
            - conditions:
                - condition: template
                  value_template: "{{ repeat.index <= 5 }}"
              sequence:
                - delay: "00:29:00"
            - conditions:
                - condition: template
                  value_template: "{{ repeat.index <= 10 }}"
              sequence:
                - delay: "00:59:00"
          default:
            - delay: "02:59:00"
  - data:
      message: >
        ❌ Alle {{ max_attempts }} pogingen gefaald voor {{ current_month }}.
        Prijs blijft: {{ states('sensor.energy_buy_price') }} EUR/kWh

        Mogelijke oorzaken: - Energy Knights heeft nog geen tariefkaart voor {{
        current_month }} gepubliceerd - PDF formaat is gewijzigd   -
        Netwerkproblemen - Datum patroon in PDF is gewijzigd

        Het script zal morgen opnieuw proberen.
      title: Energy Knights - Alle pogingen gefaald
    action: persistent_notification.create
  - data:
      message: >
        Energy Knights tariefkaart voor {{ current_month }} nog niet beschikbaar
        na {{ max_attempts }} pogingen.  Controleer https://www.energyknights.be
        voor updates.
      title: Energy Knights - Tariefkaart niet gevonden
    action: notify.mobile_app_moto_g72
mode: restart
```
