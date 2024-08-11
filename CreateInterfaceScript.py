from extras.scripts import Script, ChoiceVar, ObjectVar
from dcim.models import Device, Interface

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

    ip_manual = ChoiceVar(
        description="Insira o IP manual no formato 192.168.2.1/30",
        required=True
    )

    def run(self, data, commit):
        device = data['device']
        solucao = data['solucao']

        ip_manual = data['ip_manual']

        self.log_info(f"Device: {device}, Solução: {solucao}, IP: {ip_manual}")

        if solucao == "EoIP":
            interface_name = f"EoIP-{device.name}"

            # Verificar se a interface já existe no dispositivo
            existing_interface = Interface.objects.filter(device=device, name=interface_name).first()
            if existing_interface:
                self.log_failure(f"Interface '{interface_name}' já existe no dispositivo '{device.name}'.")
                return

            # Criar a interface
            interface = Interface(
                device=device,
                name=interface_name,
                type='virtual',  # Ajuste conforme necessário
                enabled=True
            )

            if commit:
                try:
                    interface.save()
                    self.log_success(f"Interface '{interface_name}' criada com sucesso no dispositivo '{device.name}'.")
                except Exception as e:
                    self.log_failure(f"Falha ao criar a interface: {str(e)}")
            else:
                self.log_info(f"Simulação: Interface '{interface_name}' seria criada no dispositivo '{device.name}'.")

        else:
            self.log_info(f"A solução escolhida '{solucao}' não requer a criação de uma interface.")

        return f"Processo concluído para o dispositivo {device.name}."
