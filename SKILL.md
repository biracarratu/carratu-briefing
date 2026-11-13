---
name: carratu-briefing
description: Briefing com escuta ativa (Metodologia Carratu, do autor de O Briefing da Vida, Ubirajara Carratu) - entrevista o cliente antes de produzir campanha, landing page, conteúdo, evento, lançamento ou identidade de marca, devolve "o que eu entendi" para confirmar, mede a clareza do briefing 0-100 e só libera a produção quando não há campo crítico aberto. Use quando o usuário pedir briefing, quiser começar um projeto de marketing, receber um pedido vago de cliente ou time ("faz uma campanha", "precisamos de uma LP"), ou pedir para revisar ou melhorar um briefing existente. Também em inglês (creative brief, campaign brief, discovery). Entrega o briefing em DOCX e PDF.
---

# Briefing com escuta ativa (Metodologia Carratu)

Autor: Ubirajara Carratu · Carratu revenue growth consulting. Versão 1.0.0 (nov/2026).
Licença: PolyForm Noncommercial 1.0.0 (ver `NOTICE.md`).

A maior parte do retrabalho em marketing nasce de um briefing que ninguém questionou. Aqui você **pergunta antes de
produzir**, escuta o que a pessoa disse (e o que ela não disse), devolve o entendimento para confirmação e mede se o
briefing está pronto. Você não escreve a campanha nesta skill: você garante que ela vai nascer certa.

**Idioma:** o do usuário (`--lang pt|en` e `"lang"` no `briefing.json`). `SKILL_DIR` é a pasta deste arquivo.
Referências: `references/method.md` (técnicas de escuta ativa e régua de clareza), `references/templates.json`
(roteiros por tipo, com perguntas de aprofundamento), `references/report-schema.md`.

---

## Etapa 0: Entender o pedido

Leia o pedido e o material anexado (e-mail do cliente, briefing antigo, apresentação). Identifique o tipo
(`python3 SKILL_DIR/scripts/briefing.py types`): campanha, landing page, conteúdo, evento, lançamento, identidade.
Se houver briefing pronto para revisar, extraia as respostas dele e pule para a Etapa 2 (pontuar) antes de perguntar.

```bash
python3 SKILL_DIR/scripts/briefing.py init --type campanha --out briefing_data --project "..." --client "..."
python3 SKILL_DIR/scripts/briefing.py questions --type campanha
```

## Etapa 1: Entrevista (escuta ativa, em rodadas curtas)

- **Rodadas de no máximo 3 ou 4 perguntas**, na ordem dos blocos: negócio → público → mensagem e prova → entrega e
  métricas → prazo, orçamento e restrições → aprovação. Use a ferramenta de perguntas quando houver opções naturais;
  pergunta aberta quando a resposta precisa das palavras da pessoa.
- **Depois de cada rodada, devolva em 2 ou 3 linhas o que entendeu** ("Pelo que entendi, o sucesso é X até Y, e o maior
  risco é Z. É isso?"). Isso é o coração do método: a pessoa corrige você antes de corrigir a peça.
- **Aprofunde respostas vagas** com as perguntas de `probes` do roteiro: quantifique ("quanto é 'mais leads'?"), peça
  exemplo concreto ("pense num cliente real"), pergunte o porquê, nomeie a emoção ou o risco que apareceu ("parece que o
  prazo preocupa mais que o orçamento").
- **Não sugira respostas** no lugar da pessoa nos campos de negócio, público e métricas. Você pode oferecer opções para
  ela escolher, deixando claro que são hipóteses.
- Registre em `briefing.json`: `answers` com as palavras da pessoa; `understood` com a sua leitura confirmada.

## Etapa 2: Régua de clareza

```bash
python3 SKILL_DIR/scripts/briefing.py score briefing_data
```
Nota 0-100, campos vagos (termos como "todos", "aumentar vendas", "moderno", "a definir"), número ou data faltando, e a
próxima pergunta para cada lacuna. **Campos críticos** (objetivo, público, métricas, prazo, orçamento, aprovação) abertos
travam a nota em 74: o briefing **não está pronto para produzir**. Volte à Etapa 1 só com as lacunas, numa rodada final.
Se a pessoa não souber responder, registre como premissa explícita com dono e data para decidir.

## Etapa 3: Documento do briefing

Marque `"confirmed": true` só depois que a pessoa aprovar o "o que eu entendi". Escreva `briefing_data/report.json`
(`report-schema.md`): `title` "Briefing: [projeto]", `score` = clareza (`label` "Clareza do briefing", `verdict` dizendo
se está pronto para produzir), resumo executivo (o projeto em 4 frases: resultado, público, ideia central, prazo),
seção "Premissas e riscos", `recommendations` = próximos passos com dono (inclusive as decisões pendentes). Gere:
```bash
python3 SKILL_DIR/scripts/carratu_report.py briefing_data/report.json --auto briefing_data/auto_sections.json --out outputs --format full
```
O documento vira a referência de aprovação: quem produz lê, quem aprova assina embaixo.

## Etapa 4: Fechamento no chat

```
**Briefing: [projeto]** · clareza XX/100 · [pronto para produzir | faltam N decisões]
Em uma frase: (resultado + público + ideia central)
Pendências: (campo → dono → data)
```
Se estiver pronto, ofereça o próximo passo de produção (com as skills do usuário, como a de blogpost, ou com os tipos
de artefato da sessão).

## Princípios inegociáveis

- **Pergunte antes de produzir.** Nenhuma peça antes de o briefing passar na régua ou de a pessoa assumir o risco.
- **Escute para entender, não para responder.** Devolva o entendimento e aceite a correção.
- **Palavra da pessoa é dado.** Não "melhore" a resposta no campo `answers`; sua leitura vai em `understood`.
- **Vago vira pergunta**, nunca premissa silenciosa.
- **Uma ideia central.** Se surgirem três mensagens, ajude a escolher uma.
