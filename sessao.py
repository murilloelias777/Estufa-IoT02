
class Sessao:

    usuario = None

    @classmethod
    def iniciar(cls, dados_usuario):
        cls.usuario = dados_usuario

    @classmethod
    def encerrar(cls):
        cls.usuario = None

    @classmethod
    def autenticada(cls):
        return cls.usuario is not None

    @classmethod
    def usuario_atual(cls):
        if cls.autenticada():
            return cls.usuario

        return None

    @classmethod
    def obter_id_usuario(cls):
        if cls.autenticada():
            return cls.usuario["idusuario"]

        return None
