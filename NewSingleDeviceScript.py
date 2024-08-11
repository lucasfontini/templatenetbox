from extras.scripts import Script, StringVar, ObjectVar
from dcim.models import Device, Interface, VLAN
from dcim.choices import InterfaceTypeChoices

class CreateDeviceInterfaceScript(Script):

    class Meta:
        name = "Cria Interface EoIP"
        description = "Cria uma interface EoIP para um dispositivo selecionado e a associa a uma VLAN"

    device = ObjectVar(
        description="Selecione o dispositivo",
        model=Device,
        required=True
    )

    vlan = ObjectVar(
        description="Selecione a VLAN para associar à interface",
        model=VLAN,
        required=True
    )

    solucao = StringVar(
        description="Selecione a solução",
        choices=[
            ('EOIP', 'EoIP'),
            ('OUTRA', 'Outra')  # Outras soluções podem ser adicionadas conforme necessário
        ],
        required=True
    )

    def run(self, data, commit):
        device = data['device']
        vlan = data['vlan']
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
                self.log_info(f"Simulação: A interface '{eoip_interface_name}' seria criada e associada à VLAN '{vlan.name}'")
        else:
            self.log_info(f"Solução '{solucao}' selecionada, nenhuma interface EoIP será criada.")

        return f"Script concluído com sucesso para o dispositivo {device.name}."
