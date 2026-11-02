# ClipBoard Editor

Complemento global do NVDA para editar o texto da área de transferência, consultar os últimos textos copiados e formatar conteúdo JSON, XML ou SQL. O editor pode ser usado pelo teclado e informa por voz o resultado das operações.

## Abrir o editor

Pressione **NVDA+Shift+C** para abrir o editor da área de transferência. O atalho pode ser alterado em **NVDA > Preferências > Definir comandos**, na categoria do complemento.

A janela contém:

* **Texto para edição**: área de texto com o conteúdo atual da área de transferência. O foco começa nela.
* **Últimos 10 textos copiados**: lista dos textos detectados desde que o NVDA foi iniciado, incluindo o texto que já estava na área de transferência ao iniciar. As entradas mais recentes aparecem primeiro.
* **Formatar JSON/XML/SQL**: botão exibido quando o conteúdo é reconhecido como um desses formatos.
* **Salvar** e **Cancelar**: atualiza a área de transferência com o texto editado ou descarta a edição.

## Editar e salvar

Altere o texto e pressione **Esc** ou escolha **Salvar** para copiar o conteúdo editado para a área de transferência. O NVDA informa quando a atualização é concluída.

Para descartar as alterações, escolha **Cancelar**. Se o texto estiver vazio, o complemento não altera a área de transferência e mantém o editor aberto.

O complemento verifica periodicamente se o texto da área de transferência mudou. Quando isso acontece, ele atualiza o histórico enquanto o NVDA está em execução. Se o editor estiver aberto, a lista de histórico também é atualizada.

## Histórico

Use **Seta para cima** e **Seta para baixo** para percorrer a lista. Pressione **Enter** sobre uma entrada para carregá-la no editor; o foco retorna à área de texto.

O histórico guarda no máximo os **10 textos mais recentes** e existe apenas na memória durante a execução do NVDA. Ele não é salvo em arquivo e é apagado quando o NVDA é encerrado.

## Formatar conteúdo

O complemento identifica automaticamente conteúdos JSON e XML válidos e textos SQL que começam com comandos reconhecidos, como `SELECT`, `INSERT`, `UPDATE` ou `CREATE`. Quando um formato é identificado, o botão correspondente aparece:

| Formato | O que faz |
|---|---|
| JSON | Reindenta o conteúdo com quatro espaços e mantém os caracteres acentuados. |
| XML | Organiza os elementos com quatro espaços de indentação. |
| SQL | Quebra linhas em palavras-chave comuns e indenta condições `AND`, `OR` e `ON`. |

A formatação substitui o texto no editor, mas não atualiza a área de transferência até você salvar. JSON inválido apresenta a linha e a coluna do erro. XML inválido ou outro problema de formatação é informado pelo NVDA; o conteúdo permanece disponível para edição.

## Acessibilidade e limites

O editor e o histórico são controles de teclado padrão. Use **Tab** e **Shift+Tab** para percorrer os controles. Na lista do histórico, **Enter** carrega o item selecionado. **Esc** salva e fecha o editor.

O complemento trabalha com texto. Conteúdos que não podem ser lidos como texto, como imagens e arquivos copiados, não são exibidos como conteúdo editável. A formatação SQL é simples e não substitui um formatador ou validador completo de SQL.

## Privacidade

O histórico é mantido somente na memória do NVDA e não é persistido pelo complemento. O complemento não envia o conteúdo da área de transferência pela internet.
