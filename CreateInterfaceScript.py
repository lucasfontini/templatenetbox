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
        required=False
    )

    solucao = ChoiceVar(
        description="Escolha a solução (e.g., EoIP, L2TP)",
        choices=[('EoIP', 'EoIP'), ('L2TP', 'L2TP'), ('OutraSolucao', 'Outra Solução')],
        required=True
    )

    ip_manual = StringVar(
        description="Insira o IP no formato 192.168.2.1/30",
        required=False
    )

    pop_ip_manual = StringVar(
        description="Insira o IP para o L2TP no POP no formato 192.168.2.2/30",
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
        pop_device = data.get('pop_device')
        solucao = data['solucao']
        ip_manual = data.get('ip_manual')
        pop_ip_manual = data.get('pop_ip_manual')
        vlan_id = data.get('vlan_id')
        serial_number = data.get('serial_number')

        site = device.site
        pop_site = pop_device.site if pop_device else None

        self.log_info(f"Device: {device}, POP: {pop_device}, Site: {site.name}, POP Site: {pop_site.name if pop_site else 'N/A'}, Solução: {solucao}, IP: {ip_manual}, POP IP: {pop_ip_manual}, VLAN ID: {vlan_id}")

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

        # Criar ou obter a VLAN
        vlan = get_or_create_vlan(vlan_id, site)

        if solucao == "EoIP":
            # Criar as interfaces EoIP e GRE no dispositivo principal
            create_interface(device, f"EoIP-{site.name}")
            create_interface(device, f"GRE-{site.name}", ip_manual, vlan)

            # Criar as interfaces EoIP e GRE no dispositivo POP, se fornecido
            if pop_device:
                create_interface(pop_device, f"EoIP-{site.name}")
                create_interface(pop_device, f"GRE-{site.name}", pop_ip_manual, vlan)

        elif solucao == "L2TP":
            # Criar a interface L2TP no dispositivo principal
            create_interface(device, f"L2TP-{site.name}.A001", ip_manual, vlan)

            # Criar a interface L2TP no dispositivo POP, se fornecido
            if pop_device:
                create_interface(pop_device, f"L2TP-{site.name}.A001", pop_ip_manual, vlan)

        # Definir o número de série manualmente, se fornecido
        if serial_number:
            device.serial = serial_number
            device.save()
            self.log_success(f"Número de série '{serial_number}' definido para o dispositivo '{device.name}'.")

        # Verificar e registrar o número de série do dispositivo
        if not device.serial:
            self.log_info("Dispositivo não possui número de série cadastrado.")

        return f"Processo concluído para os dispositivos {device.name} e {pop_device.name if pop_device else ''}."
