import sys
from fitparse import FitFile, FitParseError

try:
	fitfile = FitFile('2016-06-07-16-05-17.fit')
	fitfile.parse()
except FitParseError as e:
	print("Error while parsing .FIT file: %s" % e)
	sys.exit(1)

records = list(fitfile.get_messages(name='device_info'))    #show only device_info
#records = list(fitfile.get_messages(name='record'))        #show only record (these records have the important lat/lon info)
#records = list(fitfile.get_messages())                     #show all available records
print('Amount of records = ' + str(len(records)))
print()

for record in records:
	print(record)
	for field in record:
		if field.value == None:                         #don't show empty values
			continue
		if field.units == 'semicircles':
			pos = field.value * (180.0 / 2147483648)
			print(field.name, "%.7f" % pos, 'degree')   #degrees instead of semicircles
		elif field.units == 'm/s':
			speed = field.value * 3.6
			print(field.name, "%.1f" % speed, 'km/h')   #km/h instead of m/s
		elif field.units == 'm':
			print(field.name, "%.1f" % field.value, field.units)
		else:
			if field.units == None:
				print(field.name, field.value)
			else:
				print(field.name, field.value, field.units)
	print('   - - -   ')