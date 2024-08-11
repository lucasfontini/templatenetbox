from extras.scripts import Script, ChoiceVar, ObjectVar, StringVar, IntegerVar
from dcim.models import Device, Interface, Site
from ipam.models import IPAddress, VLAN
from django.contrib.contenttypes.models import ContentType

class CreateInterfaceScript(Script):
    class Meta:
        name = "Criar Interface para Solução"
        description = "Cria uma interface no dispositivo e no POP com base na solução escolhida"

    device = ObjectVar(
        description="Selecione o dispositivo",
        model=Device,
        required=True
    )

    pop_device = ObjectVar(
        description="Selecione o dispositivo POP",
        model=Device,
        required=True
    )

    solucao = ChoiceVar(
        description="Escolha a solução (e.g., EoIP)",
        choices=[('EoIP', 'EoIP'), ('OutraSolucao', 'Outra Solução')],
        required=True
    )

    ip_manual = StringVar(
        description="Insira o IP no formato 192.168.2.1/30",
        required=False
    )

    pop_ip_manual = StringVar(
        description="Insira o IP para o GRE no POP no formato 192.168.2.2/30",
        required=False
    )

    vlan_id = IntegerVar(
        description="Insira o ID da VLAN",
        required=False
    )

    serial_number = StringVar(
        description="Insira o número de série do dispositivo (opcional)",
        required=False
    )

    def run(self, data, commit):
        device = data['device']
        pop_device = data['pop_device']
        solucao = data['solucao']
        ip_manual = data.get('ip_manual')
        pop_ip_manual = data.get('pop_ip_manual')
        vlan_id = data.get('vlan_id')
        serial_number = data.get('serial_number')

        self.log_info(f"Device: {device}, POP: {pop_device}, Solução: {solucao}, IP: {ip_manual}, POP IP: {pop_ip_manual}, VLAN ID: {vlan_id}")

        if solucao == "EoIP":
            # Função para criar VLAN se ela não existir
            def get_or_create_vlan(vlan_id, site):
                vlan = VLAN.objects.filter(id=vlan_id).first()
                if not vlan:
                    vlan = VLAN(
                        id=vlan_id,
                        name=f"VLAN {vlan_id}",
                        site=site,
                        vid=vlan_id
                    )
                    if commit:
                        try:
                            vlan.save()
                            self.log_success(f"VLAN '{vlan.name}' criada e associada ao site '{site.name}'.")
                        except Exception as e:
                            self.log_failure(f"Falha ao criar VLAN: {str(e)}")
                    else:
                        self.log_info(f"Simulação: VLAN '{vlan.name}' seria criada e associada ao site '{site.name}'.")
                return vlan

            # Função para criar interfaces em um dispositivo específico
            def create_interface(device, interface_name, ip=None, vlan=None):
                existing_interface = Interface.objects.filter(device=device, name=interface_name).first()
                if existing_interface:
                    self.log_failure(f"Interface '{interface_name}' já existe no dispositivo '{device.name}'.")
                else:
                    interface = Interface(
                        device=device,
                        name=interface_name,
                        type='virtual',
                        enabled=True
                    )
                    if commit:
                        try:
                            interface.save()
                            self.log_success(f"Interface '{interface_name}' criada com sucesso no dispositivo '{device.name}'.")

                            # Associar IP à interface
                            if ip:
                                ip_address = IPAddress(
                                    address=ip,
                                    assigned_object=interface,
                                    assigned_object_type=ContentType.objects.get_for_model(interface)
                                )
                                ip_address.save()
                                self.log_success(f"IP '{ip_address.address}' criado com sucesso e associado à interface '{interface_name}'.")

                            # Definir o IP como primário, se necessário
                            if ip:
                                device.primary_ip4 = ip_address
                                device.save()
                                self.log_success(f"IP '{ip_address.address}' definido como primário para o dispositivo '{device.name}'.")

                            # Associar VLAN à interface
                            if vlan:
                                interface.vlan = vlan
                                interface.save()
                                self.log_success(f"VLAN '{vlan.name}' associada à interface '{interface_name}'.")

                        except Exception as e:
                            self.log_failure(f"Falha ao criar a interface '{interface_name}': {str(e)}")
                    else:
                        self.log_info(f"Simulação: Interface '{interface_name}' seria criada no dispositivo '{device.name}'.")

            # Obter o site do dispositivo principal
            site = device.site

            # Criar ou obter a VLAN
            vlan = get_or_create_vlan(vlan_id, site)

            # Criar as interfaces no dispositivo principal
            create_interface(device, f"EoIP-{device.name.upper()}")
            create_interface(device, f"GRE-{device.name.upper()}", ip_manual, vlan)

            # Criar as interfaces no dispositivo POP
            create_interface(pop_device, f"EoIP-{pop_device.name.upper()}")
            create_interface(pop_device, f"GRE-{pop_device.name.upper()}", pop_ip_manual, vlan)

            # Definir o número de série manualmente, se fornecido
            if serial_number:
                device.serial = serial_number
                device.save()
                self.log_success(f"Número de série '{serial_number}' definido para o dispositivo '{device.name}'.")

            # Verificar e registrar o número de série do dispositivo
            if not device.serial:
                self.log_info("Dispositivo não possui número de série cadastrado.")

        else:
            self.log_info(f"A solução escolhida '{solucao}' não requer a criação de interfaces.")

        return f"Processo concluído para os dispositivos {device.name} e {pop_device.name}."
