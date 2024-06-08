import json
from extras.scripts import Script, StringVar, ObjectVar
from dcim.choices import DeviceStatusChoices
from dcim.models import Device, DeviceRole, DeviceType, Site, Interface
from ipam.models import IPAddress
from extras.models import Tag, ConfigTemplate, ConfigContext

class NewSingleDeviceScript(Script):

    class Meta:
        name = "Cria novo device"
        description = "Create a single device in an existing site with local context data from a POP device"

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

    def run(self, data, commit):
        site = data['site']
        pop_device = data['pop_device']
        connected_to = data['connected_to']

        # Obter o dispositivo POP DEVICE
        try:
            pop_device_info = Device.objects.get(id=pop_device.id)
        except Device.DoesNotExist:
            self.log_failure(f"POP DEVICE '{pop_device.name}' not found in site '{pop_device.site.name}'")
            return

        # Obter todas as interfaces do POP DEVICE que possuem tags e seus endereços IP
        interfaces_with_tags = Interface.objects.filter(device=pop_device_info, tags__isnull=False)

        # Criar um dicionário para adicionar ao contexto local
        local_context_dict = {
            "pop_device_name": pop_device_info.name,
            "pop_device_role": pop_device_info.device_role.name,
            "interfaces": []
        }

        # Adicionar informações das interfaces e IPs ao dicionário
        if interfaces_with_tags.exists():
            for interface in interfaces_with_tags:
                tags = ', '.join([tag.name for tag in interface.tags.all()])
                # Obter todos os endereços IP associados a essa interface
                ip_addresses = IPAddress.objects.filter(interface=interface)
                ip_list = [str(ip) for ip in ip_addresses]

                # Adicionar as informações ao dicionário
                local_context_dict["interfaces"].append({
                    "interface_name": interface.name,
                    "tags": tags,
                    "ips": ip_list
                })
        else:
            self.log_info("No interfaces with tags found in POP DEVICE")

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

        # Se um template de configuração foi fornecido, atribuí-lo ao dispositivo
        config_template = data.get('config_template', None)
        if config_template and isinstance(config_template, ConfigTemplate):
            device.config_template = config_template

        if commit:
            try:
                device.save()  # Salvar o dispositivo para atribuir a chave primária

                tag = data.get('tags', None)
                if tag:
                    device.tags.add(tag)

                self.log_success(f"Created new device: {device.name} at site {site.name} with local context data from {pop_device.name}")
            except Exception as e:
                self.log_failure(f"Failed to create device: {str(e)}")
        else:
            self.log_info(f"Simulation: Would have created new device {device.name} at site {site.name}")

        return f"Device {device.name} has been {'created' if commit else 'simulated'} successfully at site {site.name}"
