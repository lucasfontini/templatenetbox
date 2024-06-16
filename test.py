
import json
from extras.scripts import Script, StringVar, ObjectVar
from dcim.choices import DeviceStatusChoices
from dcim.models import Device, DeviceRole, DeviceType, Site, Interface
from ipam.models import IPAddress
from extras.models import Tag, ConfigTemplate, ConfigContext
 
    def run(self, data, commit):
       self.log_info(data)


        return f"terminou"
