import json
from extras.scripts import Script, StringVar, ObjectVar
from dcim.choices import DeviceStatusChoices, InterfaceTypeChoices
from dcim.models import Device, DeviceRole, DeviceType, Site, Interface, VLAN
from ipam.models import IPAddress
from extras.models import Tag, ConfigTemplate

class NewDeviceWithInterfacesScript(Script):

    class Meta:
        name = "Create Device with Interfaces"
        description = "Create a single device in an existing site with interfaces based on the solution type"

    site = ObjectVar(
        description="Select an existing site",
        model=Site,
    )

    device_name = StringVar(
        description="Name of the new device",
        required=True
    )

    device_model = ObjectVar(
        description="Select o modelo do dispositivo",
        model=DeviceType,
    )

    device_role = ObjectVar(
        description="Select o papel do dispositivo",
        model=DeviceRole,
    )

    tags = ObjectVar(
        description="Select a tag para o dispositivo",
        model=Tag,
        required=False
    )

    config_template = ObjectVar(
        description="Optional config template para o novo dispositivo",
        model=ConfigTemplate,
        required=False
    )

    pop_device = ObjectVar(
        description="POP DEVICE",
        model=Device,
        required=True
    )

    connected_to = ObjectVar(
        description="Connected to",
        model=Device,
        required=True
    )

    solucao = StringVar(
        description="Solução a ser utilizada",
        required=True
    )

    vlan_id = ObjectVar(
        description="VLAN para associar à interface",
        model=VLAN,
        required=True
    )

    def run(self, data, commit):
        site = data['site']
        pop_device = data['pop_device']
        connected_to = data['connected_to']
        solucao = data['solucao']
        vlan = data['vlan_id']

        # Obter o dispositivo POP DEVICE
        try:
            pop_device_info = Device.objects.get(id=pop_device.id)
        except Device.DoesNotExist:
            self.log_failure(f"POP DEVICE '{pop_device.name}' not found in site '{pop_device.site.name}'")
            return

        # Criar um dicionário para adicionar ao contexto local
        local_context_dict = {
            "pop_device_name": pop_device_info.name,
            "pop_device_role": pop_device_info.device_role.name,
            "interfaces": []
        }

        # Criar o novo dispositivo com o contexto local
        existing_device = Device.objects.filter(name=data['device_name'], site=site).first()
        if existing_device:
            self.log_failure(f"A device with the name '{data['device_name']}' already exists in site '{site.name}'")
            return

        device_role = data['device_role']
        self.log_info(f"Using device role: {device_role.name}")

        device = Device(
            name=data['device_name'],
            device_type=data['device_model'],
            site=site,
            status=DeviceStatusChoices.STATUS_ACTIVE,
            device_role=device_role,
            local_context_data=local_context_dict,  # Adiciona o dicionário ao contexto local
            custom_field_data={"Connectedto": connected_to.id}  # Adiciona o ID do dispositivo ao campo customizado
        )

        if commit:
            try:
                device.save()  # Salvar o dispositivo para atribuir a chave primária

                tag = data.get('tags', None)
                if tag:
                    device.tags.add(tag)

                self.log_success(f"Created new device: {device.name} at site {site.name} with local context data from {pop_device.name}")

                # Criar interfaces dependendo da solução
                if solucao.lower() == "eoip":
                    # Criar a interface EoIP
                    eoip_interface_name = f"EOIP-{device.name}-A001"
                    eoip_interface = Interface(
                        device=device,
                        name=eoip_interface_name,
                        type=InterfaceTypeChoices.TYPE_VLAN,
                        mode="access"
                    )
                    eoip_interface.save()
                    eoip_interface.untagged_vlan = vlan
                    eoip_interface.save()
                    self.log_success(f"Interface '{eoip_interface_name}' criada e associada à VLAN '{vlan.name}'")

                    # Criar a interface GRE
                    gre_interface_name = f"GRE-{device.name}"
                    gre_interface = Interface(
                        device=device,
                        name=gre_interface_name,
                        type=InterfaceTypeChoices.TYPE_VLAN,
                        mode="access"
                    )
                    gre_interface.save()
                    gre_interface.untagged_vlan = vlan
                    gre_interface.save()
                    self.log_success(f"Interface '{gre_interface_name}' criada e associada à VLAN '{vlan.name}'")

            except Exception as e:
                self.log_failure(f"Failed to create device: {str(e)}")
        else:
            self.log_info(f"Simulation: Would have created new device {device.name} at site {site.name}")

        return f"Device {device.name} has been {'created' if commit else 'simulated'} successfully at site {site.name}"
