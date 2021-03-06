from MateriaPrima import MateriaPrima
from Estimativa import Estimativa
from Pessoa import Pessoa
from RateioOp import RateioOp
from RateioFixos import RateioFixos
from CustosFixos import CustosFixos
from PrecoVenda import PrecoVenda
from CustoVendas import CustoVendas
from Tributos import Tributos
from Frete import Frete
from Estoque import Estoque
from CapGiro import CapGiro
from InvestimentoInicial import InvestimentoInicial
from InvestimentoFixo import InvestimentoFixo
from decimal import Decimal, ROUND_HALF_UP
from Banco import Banco
from Reservas import Reservas
class Financeiro:
    def dec(self, var):
        return float(Decimal(var).quantize(Decimal('0.01'), ROUND_HALF_UP))

    def demonstrativo(self, mes, ret):
        fat = self.calculaFaturamento(mes)
        cv = self.custosVariaveis(mes)
        mc = fat - cv
        cf = self.calculaTotal(CustosFixos, 'total')

        lucro = mc - cf
        ipr = lucro * (self.calculaTotal(Tributos, 'irpj') / 100)
        reserv = self.calculaTotal(Reservas, 'reservas')
        rv = (lucro * reserv) / 100
        liquido = lucro - ipr - rv
        print(str(lucro) + " ---- " + str(reserv) + " ---- " + str(ipr) + " ->>>> " +str(liquido))
        if ret == 'liquido':
            return self.dec(liquido)
        if ret == 'imposto':
            return self.dec(ipr)
        if ret == 'reserva':
            return self.dec(rv)

    def calculaFaturamento(self, mes):
        produtos = MateriaPrima.relatorio(MateriaPrima, 'DISTINCT produto')
        fat = 0
        pv = 0
        for prod in produtos:
            if mes != ' ':
                est = self.calculaTotal(Estimativa, 'DISTINCT quant',
                                    ' WHERE mes = ' + str(mes) + ' AND descricao = "' + prod[0] + '"')
                pv = self.calculaPV(prod[0], mes, 'Preco')
            else:
                est = self.calculaTotal(Estimativa, 'DISTINCT quant',
                                        ' WHERE descricao = "' + prod[0] + '"')
                for m in range(1,13):
                    pv += self.calculaPV(prod[0], m, 'Preco')
            val = est * pv
            fat += val
        return float(Decimal(fat).quantize(Decimal('0.01'), ROUND_HALF_UP))

    def calculaPV(self, nome, mes, retorno):
        mat = self.calculaTotal(MateriaPrima, 'total', ' WHERE produto = "' + nome + '"')

        total = self.calculaTotal(Pessoa, 'total', ' WHERE categoria = "Producao"')
        rateio = self.calculaTotal(RateioOp, 'porc', ' WHERE produto = "' + nome + '"')
        op = total * (rateio / 100)
        quant = self.calculaTotal(Estimativa, 'quant', ' WHERE descricao = "' + nome + '" AND mes = ' + str(mes))
        if quant != 0:
            cprod = op / quant
        else:
            cprod = 0
        totalf = self.calculaTotal(CustosFixos, 'total')
        rateiof = self.calculaTotal(RateioFixos, 'porc', ' WHERE produto = "' + nome + '"')
        opf = totalf * (rateiof / 100)
        quantf = self.calculaTotal(Estimativa, 'quant', ' WHERE descricao = "' + nome + '" AND mes = ' + str(mes))
        if quantf != 0:
            cfixo = opf / quantf
        else:
            cfixo = 0
        outros = self.calculaTotal(PrecoVenda, 'outros',
                                       ' WHERE mes =' + str(mes) + ' AND produto = "' + nome + '"')
        cip = self.dec(mat) + self.dec(cprod) + self.dec(outros)

        if self.calculaTotal(Estimativa, 'quant', ' WHERE mes ="' + str(mes) + '"') != 0:
            cfgiro = (self.calculaTotalBD('custofinanceiro', 'custo') * (self.balancoIni('emprestimos') + self.balancoIni( 'capsocial'))) / self.calculaTotal(
                Estimativa, 'quant', ' WHERE mes ="' + str(mes) + '"')
        else:
            cfgiro = 0

        lucro = self.calculaTotal(Estimativa, 'lucrounitario', ' WHERE descricao = "' + nome + '" AND mes = ' + str(mes))

        trib = self.calculaTotal(Tributos, 'total') * 0.01
        cvenda = self.calculaTotal(CustoVendas, 'porcentagem') * 0.01
        preco = (self.dec(cip) + self.dec(cfixo) + self.dec(lucro) + self.dec(cfgiro)) * (1 / (1 - (trib + self.dec(cvenda))))

        ctrib = preco * trib
        cdirvendas = preco * cvenda

        ctotal = self.dec(cip + ctrib + cdirvendas + cfgiro)

        if retorno == 'Preco':
            return float(Decimal(preco).quantize(Decimal('0.01'), ROUND_HALF_UP))
        if retorno == 'CTotal':
            return ctotal

    def calculaTotal(self, table, col=None, cond=None):
        list = table.relatorio(table, col, cond)
        val = 0
        #print(list)
        if list is not None:
            for t in list:
                t = str(t).replace(",", "").replace(")", "").replace("(", "")
                val = val + float(t)
        return val

    def calculaTotalBD(self, table, col=None, cond = None):
        list = Banco.relatorio(Banco, table, col, cond)
        val = 0
        #print(list)
        if list is not None:
            for t in list:
                t = str(t).replace(",", "").replace(")", "").replace("(", "")
                val = val + float(t)
        return val

    def custosVariaveis(self, mes):

        pd = self.calculaTotal(Pessoa, 'total', ' WHERE categoria = "Producao"')

        trib = self.calculaTotal(Tributos, 'total')

        if mes == " ":
            ct = 0
            ct += self.calculaFaturamento(' ')
            imp = ct * (trib / 100)

            etq = self.calculaTotal(Estoque, 'custototal')

            frete = self.calculaTotal(Frete, 'frete')

            pj = Estimativa.relatorio(Estimativa, 'DISTINCT quant')

            opv = PrecoVenda.relatorio(PrecoVenda, 'outros')
        else:
            ct = self.calculaFaturamento(mes)
            imp = ct * (trib / 100)
            etq = self.calculaTotal(Estoque, 'custototal', ' WHERE mes = ' + str(mes))

            frete = self.calculaTotal(Frete, 'frete', ' WHERE mes = ' + str(mes))

            pj = Estimativa.relatorio(Estimativa, 'DISTINCT quant',
                                      ' WHERE mes = ' + str(mes))

            opv = PrecoVenda.relatorio(PrecoVenda, 'outros', ' WHERE mes = ' + str(mes))

        cv = self.calculaTotal(CustoVendas, 'porcentagem')
        cvendas = ct * (cv / 100)

        ter = 0
        for outros in opv:
            for proj in pj:
                ter += proj[0] * outros[0]

        inv = self.balancoIni('emprestimos') + self.balancoIni('capsocial')
        custo = self.calculaTotalBD('custofinanceiro', 'custo')
        amort = inv * custo

        cvar = pd + imp + cvendas + etq + frete + ter + amort

        return self.dec(cvar)

    def calculaPagRec(self, mes, var, ret):
        avista = self.calculaTotal(CapGiro, 'avista', ' WHERE categoria = "' + var + '"')
        tres = self.calculaTotal(CapGiro, 'tres', ' WHERE categoria = "' + var + '"')
        seis = self.calculaTotal(CapGiro, 'seis', ' WHERE categoria = "' + var + '"')
        nove = self.calculaTotal(CapGiro, 'nov', ' WHERE categoria = "' + var + '"')
        total = avista + tres + seis + nove

        if mes != ' ':
            if mes == 1:
                valt = 0
            if mes == 1 or mes == 2:
                vals = 0
            if mes == 1 or mes == 2 or mes == 3:
                valn = 0

            if var == 'Recebimentos':
                fat = self.calculaFaturamento(mes)
                valv = self.calculaTotal(CapGiro, 'avista', ' WHERE categoria = "' + var + '"') * (
                            self.calculaFaturamento(mes) / 100)
                if mes != 1:
                    valt = self.calculaTotal(CapGiro, 'tres', ' WHERE categoria = "' + var + '"') * (self.calculaFaturamento(mes) / 100)
                if mes != 1 or mes != 2:
                    vals = self.calculaTotal(CapGiro, 'seis', ' WHERE categoria = "' + var + '"') * (
                            self.calculaFaturamento(mes) / 100)
                if mes != 1 or mes != 2 or mes != 3:
                    valn = self.calculaTotal(CapGiro, 'nov', ' WHERE categoria = "' + var + '"') * (
                            self.calculaFaturamento(mes) / 100)

            else:
                fat = self.calculaTotal(Estoque, 'custototal', ' WHERE mes = ' + str(mes))
                valv = self.calculaTotal(CapGiro, 'avista', ' WHERE categoria = "' + var + '"') * (self.calculaTotal(Estoque, 'custototal', ' WHERE mes = ' + str(mes)) / 100)
                if mes != 1:
                    valt = self.calculaTotal(CapGiro, 'tres', ' WHERE categoria = "' + var + '"') * (self.calculaTotal(Estoque, 'custototal', ' WHERE mes = ' + str(mes - 1))  / 100)
                if mes != 1 or mes != 2:
                    vals = self.calculaTotal(CapGiro, 'seis', ' WHERE categoria = "' + var + '"') * (self.calculaTotal(Estoque, 'custototal', ' WHERE mes = ' + str(mes - 2))  / 100)
                if mes != 1 or mes != 2 or mes != 3:
                    valn = self.calculaTotal(CapGiro, 'nov', ' WHERE categoria = "' + var + '"') * (self.calculaTotal(Estoque, 'custototal', ' WHERE mes = ' + str(mes - 3))  / 100)
            valtotal = valv + valt + vals + valn
        else:
            valtotal = 0
            for m in range(13,16):

                if var == 'Recebimentos':
                    valv = self.calculaTotal(CapGiro, 'avista', ' WHERE categoria = "' + var + '"') * (
                            self.calculaFaturamento(m) / 100)
                    valt = self.calculaTotal(CapGiro, 'tres', ' WHERE categoria = "' + var + '"') * (self.calculaFaturamento(m-1) / 100)
                    vals = self.calculaTotal(CapGiro, 'seis', ' WHERE categoria = "' + var + '"') * (
                            self.calculaFaturamento(m-2) / 100)
                    valn = self.calculaTotal(CapGiro, 'nov', ' WHERE categoria = "' + var + '"') * (
                            self.calculaFaturamento(m-3)/ 100)
                else:
                    valv = self.calculaTotal(CapGiro, 'avista', ' WHERE categoria = "' + var + '"') * (
                            self.calculaTotal(Estoque, 'custototal', ' WHERE mes = ' + str(m)) / 100)
                    valt = self.calculaTotal(CapGiro, 'tres', ' WHERE categoria = "' + var + '"') * (
                            self.calculaTotal(Estoque, 'custototal', ' WHERE mes = ' + str(m - 1)) / 100)
                    vals = self.calculaTotal(CapGiro, 'seis', ' WHERE categoria = "' + var + '"') * (
                            self.calculaTotal(Estoque, 'custototal', ' WHERE mes = ' + str(m - 2)) / 100)
                    valn = self.calculaTotal(CapGiro, 'nov', ' WHERE categoria = "' + var + '"') * (
                            self.calculaTotal(Estoque, 'custototal', ' WHERE mes = ' + str(m - 3)) / 100)
                valtotal = valtotal + valv + valt + vals + valn
                valv = 0
                valt = 0
                vals = 0
                valn = 0


        if ret == 'total':
            return self.dec(valtotal)
        if ret == 'avista':
            return self.dec(valv)
        if ret == 'tres':
            return self.dec(valt)
        if ret == 'seis':
            return self.dec(vals)
        if ret == 'nove':
            return self.dec(valn)

    def calculaMin(self, ret):

        if ret == 'pmrv':
            receber = self.calculaPagRec(" ", 'Recebimentos', 'total')
            receita = 0
            for m in range(1, 13):
                receita += self.calculaFaturamento(m)

            if receita != 0:
                pmrv = (receber / receita) * 360
            else:
                pmrv = 0
            return self.dec(pmrv)
        if ret == 'pmpc':
            pagar = self.calculaPagRec(" ", 'Pagamentos', 'total')
            canual = self.calculaTotal(Estoque, 'custototal')

            if canual != 0:
                pmpc = (pagar / canual) * 360
            else:
                pmpc = 0

            return self.dec(pmpc)
        if ret == 'pmre':
            canual = self.calculaTotal(Estoque, 'custototal')
            pmre = self.calculaTotal(Estoque, 'custototal', ' WHERE mes = 12') / canual * 360
            return self.dec(pmre)

    def calculaInvPreOp(self):
        legal = self.calculaTotal(InvestimentoInicial, 'legalizacao')
        div = self.calculaTotal(InvestimentoInicial, 'divulgacao')
        out = self.calculaTotal(InvestimentoInicial, 'outros')
        return self.dec(legal+div+out)

    def necessidadeGiro(self, ret):
        receb = self.calculaMin('pmrv')
        est = self.calculaMin('pmre')
        sub = receb + est

        forn = self.calculaMin('pmpc')
        sub2 = forn
        liq = sub - sub2

        if ret == 'liq':
            return self.dec(liq)
        if ret == 'rec':
            return self.dec(receb)
        if ret == 'est':
            return self.dec(est)
        if ret == 'sub':
            return self.dec(sub)
        if ret == 'forn':
            return self.dec(forn)
        if ret == 'sub2':
            return self.dec(sub2)

    def caixaMin(self, ret):

        if ret == 'total':
            cf = self.calculaTotal(CustosFixos, 'total')
            cv = self.custosVariaveis(1)
            ct = cf + cv
            ctd = ct / 30
            need = self.necessidadeGiro('liq')
            total = need * ctd
            return self.dec(total)
        if ret == 'cf':
            cf = self.calculaTotal(CustosFixos, 'total')
            return self.dec(cf)
        if ret == 'cv':
            cv = self.custosVariaveis(1)
            return self.dec(cv)
        if ret == 'ct':
            cf = self.calculaTotal(CustosFixos, 'total')
            cv = self.custosVariaveis(1)
            ct = cf + cv
            return self.dec(ct)
        if ret == 'ctd':
            cf = self.calculaTotal(CustosFixos, 'total')
            cv = self.custosVariaveis(1)
            ct = cf + cv
            ctd = ct / 30
            return self.dec(ctd)
        if ret == 'need':
            need = self.necessidadeGiro('liq')
            return self.dec(need)

    def capGiro(self):
        est = self.calculaTotal(Estoque, 'custototal')
        caixa = self.caixaMin('total')

        return self.dec(est+caixa)

    def balancoIni(self, ret):
        est = self.calculaTotal(InvestimentoInicial, 'estoque')
        caixa = self.calculaTotal(InvestimentoInicial, 'caixa')
        desp = self.calculaTotal(InvestimentoInicial, 'totaldesp')
        terr = self.calculaTotal(InvestimentoFixo, 'total', ' WHERE categoria = "Imoveis Terrenos"')
        pred = self.calculaTotal(InvestimentoFixo, 'total', ' WHERE categoria = "Imoveis Predios"')
        veic = self.calculaTotal(InvestimentoFixo, 'total', ' WHERE categoria = "Fixos em Veiculos"')
        movs = self.calculaTotal(InvestimentoFixo, 'total', ' WHERE categoria = "Moveis e Utensilios"')
        maqs = self.calculaTotal(InvestimentoFixo, 'total', ' WHERE categoria = "Maquinas e Equipamentos"')
        comp = self.calculaTotal(InvestimentoFixo, 'total', ' WHERE categoria = "Computadores/Equipamentos de Informatica"')
        total = est + caixa + desp + terr + pred + veic + movs + maqs + comp
        forn = self.calculaPagRec(2, 'Pagamentos','tres')+self.calculaPagRec(3, 'Pagamentos', 'seis')+self.calculaPagRec(4, 'Pagamentos', 'nove')
        #print(str(self.calculaPagRec(2, 'Pagamentos','tres')) + " - " + str(self.calculaPagRec(3, 'Pagamentos', 'seis')) + " - " + str(self.calculaPagRec(4, 'Pagamentos', 'nove')))
        cap = self.calculaTotal(Reservas, 'capsocial')
        emp = total - forn - cap
        totalp = forn + emp + cap
        outrosg = self.calculaTotal(InvestimentoInicial, 'outrosg')
        if ret == 'estoques':
            return est
        if ret == 'caixa':
            return caixa
        if ret == 'despesas':
            return desp
        if ret == 'terrenos':
            return terr
        if ret == 'predios':
            return pred
        if ret == 'veiculos':
            return veic
        if ret == 'moveis':
            return movs
        if ret == 'computador':
            return comp
        if ret == 'maquinas':
            return maqs
        if ret == 'totalativo':
            return total
        if ret == 'fornecedores':
            return forn
        if ret == 'emprestimos':
            return emp
        if ret == 'capsocial':
            return cap
        if ret == 'totalpassivo':
            return totalp
        if ret == 'outrosest':
            return outrosg

    def balancoProj(self, ret):









        if ret == 'caixa':
            caixa = 0
            for i in range(1, 13):
                caixa += self.calculaFaturamento(i)
                caixa -= self.calculaTotal(CustosFixos, 'total')
                caixa -= self.custosVariaveis(i)

            caixa += self.calculaPagRec(" ", 'Pagamentos', 'total')
            caixa -= self.calculaPagRec(" ", 'Recebimentos', 'total')
            caixa += self.balancoIni('caixa')
            caixa -= self.balancoIni('fornecedores')

            desp = self.balancoIni('despesas')
            mdesp = desp / 10 * -1
            deprimoveis = (self.calculaTotal(InvestimentoFixo, 'total',
                                             ' WHERE categoria = "Imoveis Predios"') * 4) / 100 * (-1)
            mveic = (self.calculaTotal(InvestimentoFixo, 'total',
                                       ' WHERE categoria = "Fixos em Veiculos"') * 20) / 100 * (-1)
            mmovs = (self.calculaTotal(InvestimentoFixo, 'total',
                                       ' WHERE categoria = "Moveis e Utensilios"') * 10) / 100 * (-1)
            mcomp = (self.calculaTotal(InvestimentoFixo, 'total',
                                       ' WHERE categoria = "Computadores/Equipamentos de Informatica"') * 20) / 100 * (
                        -1)
            mmaqs = (self.calculaTotal(InvestimentoFixo, 'total',
                                       ' WHERE categoria = "Maquinas e Equipamentos"') * 10) / 100 * (-1)

            caixa -= mdesp
            caixa -= deprimoveis
            caixa -= mveic
            caixa -= mmovs
            caixa -= mcomp
            caixa -= mmaqs
            return self.dec(caixa)
        if ret == 'clientes':
            cli = 0
            cli += self.calculaPagRec(" ", 'Recebimentos', 'total')
            return self.dec(cli)
        if ret == 'estoques':
            est = self.balancoIni('estoques')
            return self.dec(est)
        if ret == 'despesas':
            desp = self.balancoIni('despesas')
            return self.dec(desp)
        if ret == '-despesas':
            desp = self.balancoIni('despesas')

            mdesp = desp / 10 * -1
            return self.dec(mdesp)
        if ret == 'terrenos':
            terr = self.balancoIni('terrenos')
            return self.dec(terr)
        if ret == 'predios':
            pred = self.balancoIni('predios')
            return self.dec(pred)
        if ret == '-imoveis':
            deprimoveis = (self.calculaTotal(InvestimentoFixo, 'total',
                                             ' WHERE categoria = "Imoveis Predios"') * 4) / 100 * (-1)
            return self.dec(deprimoveis)
        if ret == 'veiculos':
            veic = self.balancoIni('veiculos')
            return self.dec(veic)
        if ret == '-veiculos':
            mveic = (self.calculaTotal(InvestimentoFixo, 'total',
                                       ' WHERE categoria = "Fixos em Veiculos"') * 20) / 100 * (-1)

            return self.dec(mveic)
        if ret == 'moveis':
            movs = self.balancoIni('moveis')
            return self.dec(movs)
        if ret == '-moveis':
            mmovs = (self.calculaTotal(InvestimentoFixo, 'total',
                                       ' WHERE categoria = "Moveis e Utensilios"') * 10) / 100 * (-1)

            return self.dec(mmovs)
        if ret == 'computadores':
            comp = self.balancoIni('computadores')
            return self.dec(comp)
        if ret == '-computadores':
            mcomp = (self.calculaTotal(InvestimentoFixo, 'total',
                                       ' WHERE categoria = "Computadores/Equipamentos de Informatica"') * 20) / 100 * (
                        -1)
            return self.dec(mcomp)
        if ret == 'maquinas':
            maqs = self.balancoIni('maquinas')
            return self.dec(maqs)
        if ret == '-maquinas':
            mmaqs = (self.calculaTotal(InvestimentoFixo, 'total',
                                       ' WHERE categoria = "Maquinas e Equipamentos"') * 10) / 100 * (-1)

            return self.dec(mmaqs)
        if ret == 'fornecedores':
            forn = self.balancoIni('fornecedores')
            return self.dec(forn)
        if ret == 'irpj':
            irpj = 0
            for i in range(1, 13):
                irpj += self.demonstrativo(i, 'imposto')
            return self.dec(irpj)
        if ret == 'emprestimos':
            emp = self.balancoIni('emprestimos')
            return self.dec(emp)
        if ret == 'capsocial':
            cap = self.balancoIni('capsocial')
            return self.dec(cap)
        if ret == 'lucro':
            lucro = 0
            for i in range(1, 13):
                lucro += self.demonstrativo(i, 'liquido')

            return self.dec(lucro)
        if ret == 'reservas':
            res = 0
            for i in range(1, 13):
                res += self.demonstrativo(i, 'reserva')
            return self.dec(res)

    def calculaDeprec(self, ret):
        contas = ['Moveis e Utensilios', 'Maquinas e Equipamentos', 'Computadores/Equipamentos de Informatica',
                  'Fixos em Veiculos', 'Imoveis Predios', 'Imoveis Terrenos']
        total = 0
        totalmes = 0

        for t in contas:

            valor = self.calculaTotal(InvestimentoFixo, 'total', ' WHERE categoria = "' + t + '"')

            if t == 'Moveis e Utensilios' or t == 'Maquinas e Equipamentos':
                taxa = 10
            else:
                if t == 'Computadores/Equipamentos de Informatica' or t == 'Fixos em Veiculos':
                    taxa = 20
                else:
                    if t == 'Imoveis Predios':
                        taxa = 4
                    else:
                        taxa = 0

            mensal = float(Decimal(((valor * taxa) / 100) / 12).quantize(Decimal('0.01'), ROUND_HALF_UP))
            total = float(Decimal(total + valor).quantize(Decimal('0.01'), ROUND_HALF_UP))
            totalmes = float(Decimal(totalmes + mensal).quantize(Decimal('0.01'), ROUND_HALF_UP))

        if ret == 'total':
            return self.dec(total)
        if ret == 'totalmes':
            return self.dec(totalmes)