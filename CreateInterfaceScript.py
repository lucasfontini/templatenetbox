from extras.scripts import Script, ChoiceVar, ObjectVar
from dcim.models import Device, Interface
from ipam.models import IPAddress, VLAN
from django.contrib.contenttypes.models import ContentType

class CreateInterfaceScript(Script):
    class Meta:
        name = "Criar Interface para Solução"
        description = "Cria uma interface no dispositivo com base na solução escolhida"

    device = ObjectVar(
        description="Selecione o dispositivo",
        model=Device,
        required=True
    )

    solucao = ChoiceVar(
        description="Escolha a solução (e.g., EoIP)",
        choices=[('EoIP', 'EoIP'), ('OutraSolucao', 'Outra Solução')],
        required=True
    )

    ip_manual = ObjectVar(
        description="Selecione o IP no formato 192.168.2.1/30",
        model=IPAddress,
        required=False
    )

    vlan = ObjectVar(
        description="Selecione a VLAN",
        model=VLAN,
        required=False
    )

    def run(self, data, commit):
        device = data['device']
        solucao = data['solucao']
        ip_manual = data.get('ip_manual')
        vlan = data.get('vlan')

        self.log_info(f"Device: {device}, Solução: {solucao}, IP: {ip_manual}, VLAN: {vlan}")

        if solucao == "EoIP":
            # Criar a interface EoIP
            interface_eoip_name = f"EoIP-{device.name.upper()}"
            existing_interface_eoip = Interface.objects.filter(device=device, name=interface_eoip_name).first()
            if existing_interface_eoip:
                self.log_failure(f"Interface '{interface_eoip_name}' já existe no dispositivo '{device.name}'.")
            else:
                interface_eoip = Interface(
                    device=device,
                    name=interface_eoip_name,
                    type='virtual',
                    enabled=True
                )
                if commit:
                    try:
                        interface_eoip.save()
                        self.log_success(f"Interface '{interface_eoip_name}' criada com sucesso no dispositivo '{device.name}'.")
                    except Exception as e:
                        self.log_failure(f"Falha ao criar a interface EoIP: {str(e)}")
                else:
                    self.log_info(f"Simulação: Interface '{interface_eoip_name}' seria criada no dispositivo '{device.name}'.")

            # Criar a interface GRE
            interface_gre_name = f"GRE-{device.name.upper()}"
            existing_interface_gre = Interface.objects.filter(device=device, name=interface_gre_name).first()
            if existing_interface_gre:
                self.log_failure(f"Interface '{interface_gre_name}' já existe no dispositivo '{device.name}'.")
            else:
                interface_gre = Interface(
                    device=device,
                    name=interface_gre_name,
                    type='virtual',
                    enabled=True
                )
                if commit:
                    try:
                        interface_gre.save()
                        self.log_success(f"Interface '{interface_gre_name}' criada com sucesso no dispositivo '{device.name}'.")
                    except Exception as e:
                        self.log_failure(f"Falha ao criar a interface GRE: {str(e)}")
                else:
                    self.log_info(f"Simulação: Interface '{interface_gre_name}' seria criada no dispositivo '{device.name}'.")

            # Cadastrar o IP se não estiver cadastrado
            if ip_manual:
                ip_address = IPAddress.objects.filter(address=ip_manual.address).first()
            else:
                # Cria o IP manualmente
                ip_address = IPAddress(
                    address="200.100.10.1/30",
                    assigned_object=interface_gre,
                    assigned_object_type=ContentType.objects.get_for_model(interface_gre)
                )
                if commit:
                    try:
                        ip_address.save()
                        self.log_success(f"IP '{ip_address.address}' criado com sucesso.")
                    except Exception as e:
                        self.log_failure(f"Falha ao criar IP: {str(e)}")
                else:
                    self.log_info(f"Simulação: IP '{ip_address.address}' seria criado.")

            # Associar o IP à interface GRE
            if ip_address:
                if commit:
                    try:
                        ip_address.assigned_object = interface_gre
                        ip_address.assigned_object_type = ContentType.objects.get_for_model(interface_gre)
                        ip_address.save()
                        self.log_success(f"IP '{ip_address.address}' configurado na interface GRE '{interface_gre_name}'.")
                    except Exception as e:
                        self.log_failure(f"Falha ao configurar IP na interface GRE: {str(e)}")
                else:
                    self.log_info(f"Simulação: IP '{ip_address.address}' seria configurado na interface GRE '{interface_gre_name}'.")

            # Associar VLAN à interface GRE
            if vlan:
                interface_gre.vlan = vlan
                if commit:
                    try:
                        interface_gre.save()
                        self.log_success(f"VLAN '{vlan.name}' associada à interface GRE '{interface_gre_name}'.")
                    except Exception as e:
                        self.log_failure(f"Falha ao associar VLAN na interface GRE: {str(e)}")
                else:
                    self.log_info(f"Simulação: VLAN '{vlan.name}' seria associada à interface GRE '{interface_gre_name}'.")

        else:
            self.log_info(f"A solução escolhida '{solucao}' não requer a criação de interfaces.")

        return f"Processo concluído para o dispositivo {device.name}."
