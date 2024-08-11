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



    def run(self, data, commit):
        device = data['device']
