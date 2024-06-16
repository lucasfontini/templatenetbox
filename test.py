from extras.scripts import Script, StringVar, ObjectVar
from dcim.choices import DeviceStatusChoices
from dcim.models import Device, DeviceRole, DeviceType, Site, Interface
from ipam.models import IPAddress
from extras.models import Tag, ConfigTemplate, ConfigContext

class ShowDataScript(Script):

    class Meta:
        name = "Exibir Dados Recebidos"
        description = "Script para exibir os dados recebidos ao ser executado"

    def run(self, data, commit):
        self.log_info(f"Dados recebidos: {json.dumps(data, indent=4)}")

        return "terminou"
