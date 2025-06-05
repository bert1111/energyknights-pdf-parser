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

```alias: Energy Knights prijzen ophalen - 6x om de 2 uur zonder helpers
triggers:
  - at: "00:05:00"
    trigger: time
conditions:
  - condition: template
    value_template: "{{ now().day == 1 }}"
actions:
  - repeat:
      while:
        - condition: template
          value_template: "{{ repeat.index <= max_attempts }}"
        - condition: template
          value_template: "{{ states('sensor.energy_buy_price') == last_price }}"
      sequence:
        - data: {}
          action: pyscript.fetch_energyknights_prices
        - delay: "02:00:00"
  - choose:
      - conditions:
          - condition: template
            value_template: "{{ states('sensor.energy_buy_price') != last_price }}"
        sequence:
          - data:
              message: Prijs is gewijzigd, automatie stopt.
              title: Energy Knights
            action: persistent_notification.create
          - data:
              message: Prijs is gewijzigd, automatie stopt.
              title: Energy Knights
            action: notify.mobile_app_XXXX
      - conditions:
          - condition: template
            value_template: "{{ repeat.index > max_attempts }}"
        sequence:
          - data:
              message: Maximaal aantal pogingen (6) bereikt, automatie stopt.
              title: Energy Knights
            action: persistent_notification.create
          - data:
              message: Maximaal aantal pogingen (6) bereikt, automatie stopt.
              title: Energy Knights
            action: notify.mobile_app_XXXX
mode: restart
variables:
  max_attempts: 6
  last_price: "{{ states('sensor.energy_buy_price') }}"
```
