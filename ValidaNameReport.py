import re

from dcim.choices import DeviceStatusChoices
from dcim.models import Device
from extras.reports import Report

# A modified John Anderson's NetBox Day 2020 Presentation by adding a check for all sites, not just LAX
# All credit goes to @lampwins

class DeviceHostnameReport(Report):
   description = "Verify each device conforms to naming convention Example: ABC.5555.A555.PE05"

   def test_device_naming(self):
       for device in Device.objects.filter(status=DeviceStatusChoices.STATUS_ACTIVE):
           # Change the naming standard based on the re.match
           pattern = r"[A-Za-z0-9]{3,4}\.[0-9]{3,6}\.A[0-9]{3}.PE[0-9]{1,2}"
           if re.match(pattern, str(device.name), re.IGNORECASE):
               self.log_success(device)
           else:
               self.log_failure(device, "Hostname does not conform to standard!")
