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

        self.log_info( device, solucao)

        else:
            self.log_info(f"A solução escolhida '{solucao}' não requer a criação de uma interface.")

        return f"Processo concluído para o dispositivo {device.name}."

