from Banco import Banco
from decimal import Decimal, ROUND_HALF_UP
class MateriaPrima:

    def __init__(self, nome, materia, medida, preco, quant):
        self.nome = nome
        self.materia = materia
        self.medida = medida
        self.preco = preco
        self.quant = quant
        self.custoMateria = float(Decimal(preco * quant).quantize(Decimal('0.01'),ROUND_HALF_UP))
        self.insereBanco()

    def insereBanco(self):
        list = [self.nome, self.materia, self.medida, self.preco, self.quant, self.custoMateria]
        str = 'materiaprima (produto, descricao, unmedida, precounitario, quant, total)'

        Banco.insert(Banco, str, list)

    def relatorio(self, col = None, cond = None):
        ret = Banco.relatorio(Banco, 'materiaprima', col, cond)
        return ret