from extras.scripts import Script, StringVar, ObjectVar
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

    solucao = StringVar(
        description="Escolha a solução (e.g., EoIP)",
        choices=[('EoIP', 'EoIP'), ('OutraSolucao', 'Outra Solução')],
        required=True
    )

    def run(self, data, commit):
        device = data['device']
        solucao = data['solucao']

        # Verificar se a solução é "EoIP"
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
                type='virtual',  # Defina o tipo de interface conforme necessário
                enabled=True
            )

            if commit:
                interface.save()
                self.log_success(f"Interface '{interface_name}' criada com sucesso no dispositivo '{device.name}'.")
            else:
                self.log_info(f"Simulação: Interface '{interface_name}' seria criada no dispositivo '{device.name}'.")

        else:
            self.log_info(f"A solução escolhida '{solucao}' não requer a criação de uma interface.")

        return f"Processo concluído para o dispositivo {device.name}."

