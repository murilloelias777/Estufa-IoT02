
class Medicao:

    def __init__(
        self,
        id_sensor,
        valor,
        id_medicao=None,
        numero_medicao=None,
        data_hora=None
    ):
        self.id_medicao = id_medicao
        self.id_sensor = id_sensor
        self.numero_medicao = numero_medicao
        self.data_hora = data_hora
        self.valor = valor

    def identificador(self):
        if self.numero_medicao is None:
            return str(self.id_sensor)

        return f"{self.id_sensor}-{self.numero_medicao}"

    def __str__(self):
        return (
            f"ID da medição: {self.identificador()}\n"
            f"ID interno: {self.id_medicao}\n"
            f"ID do sensor: {self.id_sensor}\n"
            f"Data e hora: {self.data_hora}\n"
            f"Valor: {self.valor}"
        )
