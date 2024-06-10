import re

from dcim.choices import DeviceStatusChoices
from dcim.models import Device
from extras.reports import Report

class DeviceHostnameReport(Report):
    description = "Verify each device conforms to naming convention Example: ABC.5555.A555.PE05"

    def test_device_naming(self):
        # Regex pattern to match the naming convention
        pattern = r"[A-Za-z0-9]{3,4}\.[0-9]{3,6}\.[A-Z][0-9]{3}\.PE[0-9]{1,2}"
        
        for device in Device.objects.filter(status=DeviceStatusChoices.STATUS_ACTIVE):
            # Check if the device name matches the pattern
            self.info("Cheking", device.name)
            if re.match(pattern, device.name):
                self.log_success(device.name)
            else:
                self.log_failure(device, "Hostname does not conform to standard!")
