from extras.scripts import Script, StringVar, ObjectVar
from dcim.choices import InterfaceTypeChoices
from dcim.models import Device, Interface, VLAN

class CreateEoIPInterfaceScript(Script):

    class Meta:
        name = "Create EoIP Interface"
        description = "Create an EoIP interface for a selected device and associate it with a VLAN"

    device = ObjectVar(
        description="Select the device",
        model=Device,
        required=True
    )

    vlan_id = ObjectVar(
        description="Select the VLAN to associate with the interface",
        model=VLAN,
        required=True
    )

    solucao = StringVar(
        description="Select the solution",
        choices=[
            ('EOIP', 'EoIP'),
            ('OUTRA', 'Outra')  # Adicione mais opções conforme necessário
        ],
        required=True
    )

    def run(self, data, commit):
        device = data['device']
        vlan = data['vlan_id']
        solucao = data['solucao']

        if solucao == 'EOIP':
            # Criar a interface EoIP
            eoip_interface_name = f"EOIP-{device.name}"
            eoip_interface = Interface(
                device=device,
                name=eoip_interface_name,
                type=InterfaceTypeChoices.TYPE_VLAN,
                mode="access"
            )

            if commit:
                eoip_interface.save()
                eoip_interface.untagged_vlan = vlan
                eoip_interface.save()
                self.log_success(f"Interface '{eoip_interface_name}' criada e associada à VLAN '{vlan.name}'")
            else:
                self.log_info(f"Simulation: Would have created interface '{eoip_interface_name}' and associated it with VLAN '{vlan.name}'")
        else:
            self.log_info(f"Solução '{solucao}' selecionada, nenhuma interface EoIP será criada.")

        return f"Script completed successfully for device {device.name}."

