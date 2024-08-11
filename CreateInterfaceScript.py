from extras.scripts import Script, ChoiceVar, ObjectVar, StringVar
from dcim.models import Device, Interface
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

    vlan = ObjectVar(
        description="Selecione a VLAN",
        model=VLAN,
        required=False
    )

    def run(self, data, commit):
        device = data['device']
        pop_device = data['pop_device']
        solucao = data['solucao']
        ip_manual = data.get('ip_manual')
        pop_ip_manual = data.get('pop_ip_manual')
        vlan = data.get('vlan')

        self.log_info(f"Device: {device}, POP: {pop_device}, Solução: {solucao}, IP: {ip_manual}, POP IP: {pop_ip_manual}, VLAN: {vlan}")

        if solucao == "EoIP":
            # Função para criar interfaces em um dispositivo específico
            def create_interface(device, interface_name, ip=None):
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

                        except Exception as e:
                            self.log_failure(f"Falha ao criar a interface '{interface_name}': {str(e)}")
                    else:
                        self.log_info(f"Simulação: Interface '{interface_name}' seria criada no dispositivo '{device.name}'.")

                    # Associar VLAN à interface
                    if vlan:
                        interface.vlan = vlan
                        if commit:
                            try:
                                interface.save()
                                self.log_success(f"VLAN '{vlan.name}' associada à interface '{interface_name}'.")
                            except Exception as e:
                                self.log_failure(f"Falha ao associar VLAN na interface '{interface_name}': {str(e)}")
                        else:
                            self.log_info(f"Simulação: VLAN '{vlan.name}' seria associada à interface '{interface_name}'.")

            # Criar as interfaces no dispositivo principal
            create_interface(device, f"EoIP-{device.name.upper()}")
            create_interface(device, f"GRE-{device.name.upper()}", ip_manual)

            # Criar as interfaces no dispositivo POP
            create_interface(pop_device, f"EoIP-{pop_device.name.upper()}")
            create_interface(pop_device, f"GRE-{pop_device.name.upper()}", pop_ip_manual)

            # Adicionar o número de série se disponível
            serial_number = device.serial
            if serial_number:
                self.log_info(f"Número de série do dispositivo: {serial_number}")
            else:
                self.log_info("Dispositivo não possui número de série cadastrado.")

        else:
            self.log_info(f"A solução escolhida '{solucao}' não requer a criação de interfaces.")

        return f"Processo concluído para os dispositivos {device.name} e {pop_device.name}."
