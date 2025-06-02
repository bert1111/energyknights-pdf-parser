# energyknights-pdf-parser
Load Energy knights variable prices into HA

Een script dat de maandelijkse tariefkaart van Energy Knights downloadt, de prijs per kWh uitleest en beschikbaar maakt voor Home Assistant.

pyscript to automatic import the new variable tariff of "Energy Knights"

prices are fetched from the online pdf file that Energy Knights updates every month or quarter

https://www.energyknights.be/website/getCurrentTariffchart/variable/nl

First install pyscript through hacs

I manually updated the configuration.yaml file

'''
pyscript:
  allow_all_imports: true
  hass_is_global: true
'''

dowload both files (requirements.txt and energyknights.py) and place them in the "pyscript" folder under home assistant

create an automation to get the data periodically

'''
service: pyscript.get_bolt_data
'''
