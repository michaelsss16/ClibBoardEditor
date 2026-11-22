# ClipBoard Editor

Editor da área de transferência para o NVDA. Este complemento permite alterar o texto copiado, consultar os últimos conteúdos detectados e formatar dados JSON, XML ou SQL diretamente em uma janela acessível.

## Funcionalidades

- Editar o texto atual da área de transferência sem abrir outra aplicação.
- Consultar um histórico temporário com até **10 textos copiados**.
- Recuperar uma entrada do histórico para continuar a edição.
- Identificar e formatar automaticamente JSON, XML e SQL.
- Receber respostas por voz após salvar, cancelar ou formatar.
- Navegar pela interface usando o teclado.

## Compatibilidade

- Versão atual: **1.0.0**
- Versão mínima do NVDA: **2026.3**
- Versão do NVDA testada: **2026.3**

## Instalação

1. Baixe o arquivo `.nvda-addon` da seção [Releases](https://github.com/michaelsss16/ClipBoardEditor/releases) ou gere o pacote a partir dos arquivos-fonte.
2. Abra o arquivo baixado no NVDA.
3. Confirme a instalação solicitada pelo Gestor de Complementos.
4. Reinicie o NVDA, se solicitado.

Também é possível instalar o complemento manualmente no NVDA:

1. Abra o menu **NVDA**.
2. Escolha **Ferramentas > Gerenciar complementos**.
3. Selecione **Instalar**.
4. Localize o arquivo `.nvda-addon` e confirme.

## Uso

### Abrir o editor

Pressione **NVDA+Shift+C**.

O complemento abre uma janela com:

- uma área de texto para editar o conteúdo atual da área de transferência;
- uma lista com os últimos 10 textos detectados;
- um botão de formatação, exibido quando o conteúdo é JSON, XML ou SQL válido;
- os botões **Salvar** e **Cancelar**.

O foco começa na área de texto. O conteúdo atual da área de transferência é carregado automaticamente.

### Editar e salvar

Altere o texto na área de edição e escolha **Salvar**, ou pressione **Ctrl+Shift+S**. O conteúdo editado será copiado de volta para a área de transferência e o NVDA anunciará que a operação foi concluída.

Para fechar o editor sem alterar a área de transferência, escolha **Cancelar**, ou pressione **Esc**.

Se já houver outro editor aberto, o NVDA perguntará antes de descartar a edição atual.

## Histórico da área de transferência

O complemento monitora a área de transferência a cada segundo e mantém, somente na memória, até 10 textos diferentes, começando pelo mais recente.

Ao iniciar o NVDA, o complemento registra o texto que já estiver na área de transferência. Cada novo texto diferente é colocado no início da lista.

Para recuperar um item:

1. Use **Tab** até chegar à lista **Últimos 10 textos copiados**.
2. Use **Seta para cima** ou **Seta para baixo** para selecionar um texto.
3. Pressione **Enter**.

O texto selecionado será colocado na área de edição e o foco voltará para ela.

O histórico não é gravado em disco. Ele é apagado quando o NVDA é reiniciado ou encerrado.

## Formatação de conteúdo

A formatação é feita apenas após o complemento reconhecer o conteúdo como JSON, XML ou SQL. Nenhuma alteração é feita na área de transferência até que o texto seja salvo.

| Formato | Reconhecimento | Resultado |
|---|---|---|
| JSON | Objeto ou lista JSON válida | Reindenta o conteúdo com quatro espaços e preserva os caracteres acentuados |
| XML | Documento XML válido | Organiza os elementos com quatro espaços de indentação |
| SQL | Comando reconhecido no início do texto | Coloca palavras-chave comuns em linhas separadas e indenta `AND`, `OR` e `ON` |

Comandos SQL reconhecidos incluem `SELECT`, `INSERT`, `UPDATE`, `DELETE`, `WITH`, `CREATE`, `ALTER`, `DROP`, `TRUNCATE`, `EXEC`, `EXECUTE`, `MERGE`, `DECLARE` e `SET`.

Para formatar o conteúdo:

- escolha o botão exibido com o nome do formato; ou
- pressione **Ctrl+Shift+F**.

Caso o JSON seja inválido, o complemento informa a linha e a coluna do problema. Para XML ou outro erro de formatação, o NVDA informa que não foi possível concluir a operação e mantém o texto editável.

O formatador SQL é uma ferramenta simples voltada à legibilidade. Ele não substitui um analisador ou um validador completo de SQL.

## Atalhos

### Atalho global

| Atalho | Ação |
|---|---|
| NVDA+Shift+C | Abrir o editor da área de transferência |

O atalho pode ser alterado em **NVDA > Preferências > Definir comandos**, na categoria **ClipBoardEditor**.

### Atalhos dentro do editor

| Atalho | Ação |
|---|---|
| Ctrl+Shift+S | Salvar e fechar |
| Ctrl+Shift+F | Formatar JSON, XML ou SQL |
| Enter, com a lista do histórico em foco | Carregar o texto selecionado |
| Tab / Shift+Tab | Navegar pelos controles |
| Esc | Cancelar e fechar |

## Limitações e privacidade

- O complemento trabalha principalmente com texto simples.
- Imagens, arquivos ou outros conteúdos não textuais podem não aparecer como texto editável.
- Conteúdos com até aproximadamente 300 KB podem ser analisados para a formatação automática.
- O histórico existe somente na memória do NVDA.
- O complemento não envia o conteúdo da área de transferência pela internet.
- O complemento não grava o histórico em arquivo.

## Construir o complemento

Os arquivos-fonte exigem Python 3.13 e podem ser gerenciados com `uv`.

```powershell
uv sync
uv run scons
```

O comando gera o pacote `ClipBoardEditor-1.0.0.nvda-addon` na raiz do repositório.

Para converter os arquivos de documentação Markdown em HTML:

```powershell
uv run scons
```

Para formatar o código e executar as verificações configuradas:

```powershell
uv run ruff format .
uv run prek run --all-files
```

## Registro de alterações

Consulte o arquivo [changelog.md](./changelog.md) para ver as alterações das versões.

## Autor

Michael da Silva Soares dos Santos

- E-mail: michaelsss16@gmail.com
- Repositório: https://github.com/michaelsss16/ClipBoardEditor

## Licença

Este complemento é distribuído sob a **GNU General Public License, versão 2**. Consulte o arquivo [COPYING.txt](./COPYING.txt) para obter o texto completo da licença.
