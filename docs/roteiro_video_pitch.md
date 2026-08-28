# PULSO — Roteiro do vídeo pitch

**Equipe Vital Analytics · 1TSCOA · Challenge Oracle + FIAP 2026 · Sprint 2**

Duração alvo: **4min50s** (o limite é 5min — nunca entregar em cima da linha).
Formato: gravação de tela com narração, no estilo *hands on*.

---

## Antes de gravar

**Prepare a tela.** Abra em abas separadas, nesta ordem, e deixe tudo já carregado:

1. O dashboard (`dashboard/index.html`), na aba **Visão geral**
2. O dashboard, em outra janela, na aba **Pergunte ao PULSO**
3. O Database Actions do Oracle, com o SQL Worksheet aberto *(se estiver provisionado)*
4. O repositório no GitHub

**Configure a gravação.** Resolução 1920×1080. Feche notificações. Se possível, use
o OBS Studio (gratuito) — ele grava tela e microfone separados, o que facilita
regravar só o áudio se errar a fala.

**Ensaie duas vezes com cronômetro antes de gravar valendo.** O bloco de
demonstração é o que sempre estoura o tempo.

**Divisão de fala sugerida:** cada integrante narra um bloco. Isso mostra que o
time todo domina o projeto — critério que a banca observa.

---

## Bloco 1 · Abertura e contextualização — 30s

**Quem fala:** Nélson
**Tela:** slide de capa do PPT

> "Uma Secretaria de Saúde tem todos os dados de que precisa. O que ela não tem
> é o caminho entre a pergunta e a resposta.
>
> Hoje esse caminho passa por um analista que escreve SQL, extrai uma planilha e
> devolve dias depois — quando a pergunta já mudou. Na prática, a decisão de abrir
> um leito ou redirecionar uma ambulância é tomada com o dado do mês passado.
>
> Somos a equipe Vital Analytics e este é o PULSO."

⏱ **00:00 – 00:30**

---

## Bloco 2 · Objetivo do projeto — 30s

**Quem fala:** Nélson
**Tela:** slide 3 do PPT (o que mudou da Sprint 1 para a Sprint 2)

> "O objetivo do PULSO é encurtar esse caminho para uma pergunta em linguagem
> natural. O gestor pergunta em português, e o banco de dados gera e executa o
> SQL sozinho.
>
> Na Sprint 1 apresentamos a ideia. Nesta Sprint 2 o MVP está rodando — e com
> dado real: dois milhões novecentos e treze mil internações do SUS, extraídas
> das fontes públicas nos últimos doze meses."

⏱ **00:30 – 01:00**

---

## Bloco 3 · Proposta de solução — 1min

**Quem fala:** Giovanny
**Tela:** slide 9 (arquitetura) e slide 10 (as três fontes)

> "A arquitetura tem cinco camadas.
>
> Na origem, três fontes públicas — e cada uma entra no formato que a natureza
> dela pede. O SIH do SUS é um fato transacional com grão definido, então vira
> **tabela relacional**. O CNES é um cadastro com atributos opcionais — um hospital
> de ensino tem centro cirúrgico e neonatal, um pronto-atendimento não tem nenhum —
> então entra como **JSON**, que o Oracle 23ai consulta nativamente. E o IBGE é
> dado de referência anual, que fica como **External Table**: o Oracle lê o arquivo
> no Object Storage sem precisar carregar nada.
>
> Um detalhe que quase nos custou o projeto: as três fontes **não compartilham
> chave primária**. O SUS usa o código IBGE de seis dígitos, o IBGE usa sete com
> dígito verificador. Integramos sempre por código, nunca por nome de município —
> integrar por nome falha em silêncio, a linha simplesmente some.
>
> Do outro lado, o Oracle Autonomous Database com o Select AI: a camada que traduz
> a pergunta em SQL."

⏱ **01:00 – 02:00**

---

## Bloco 4 · Demonstração da solução funcionando — 2min ⭐

**Quem fala:** Pedro
**Tela:** o dashboard ao vivo — este é o bloco mais importante do vídeo

**[0:00–0:35] Visão geral do painel**

> "Este é o PULSO rodando. No topo, o estado da rede paulista em seis indicadores:
> dois vírgula nove milhões de internações, cinco vírgula sete bilhões de reais
> executados, cinquenta e cinco mil leitos SUS — e o número que motiva a ação:
> **quinze municípios operando acima de cem por cento da capacidade**.
>
> Abaixo, a série mensal com a linha de tendência. Essa queda entre novembro e
> fevereiro é sazonal, se repete todo ano — por isso o painel compara trimestres
> equivalentes, não meses isolados."

*(role até os gráficos de ranking e perfil CID)*

**[0:35–1:05] Drill-down por município**

*(clique na aba **Municípios**, busque "Jundiaí", clique na linha)*

> "A tabela filtra por região e por situação de capacidade. Escolhendo um
> município — Jundiaí — o painel abre a série mensal, os dez indicadores
> calculados e o perfil assistencial dominante.
>
> Jundiaí opera a **cento e cinco por cento** de ocupação estimada sobre
> quatrocentos e quarenta e três leitos SUS, com tendência de alta de quase
> dezesseis por cento. É um caso concreto para a Secretaria agir."

**[1:05–2:00] Pergunte ao PULSO — o diferencial**

*(clique na aba **Pergunte ao PULSO**)*

> "E aqui está o diferencial. O gestor não precisa de analista.
>
> *(clique na pergunta 'Quais municípios estão com a capacidade hospitalar
> ultrapassada?')*
>
> A pergunta vai em português. O banco gera o SQL — este aqui — executa e devolve
> o resultado com a leitura de negócio.
>
> Mostramos os três de propósito: a resposta, a consulta gerada e a tabela.
> Auditar o SQL faz parte da confiança na resposta.
>
> *(clique na pergunta 'Onde as internações estão crescendo mais rápido?')*
>
> Outra pergunta, outro SQL. Repare no filtro `r2 >= 0.4` — ele descarta oscilação
> sem tendência. Sem isso, o ranking premiaria a série mais instável, não a que
> realmente cresce."

> **Se o Oracle estiver provisionado**, troque este último trecho por: alterne para
> o SQL Worksheet e execute ao vivo
> `SELECT AI showsql 'quais municipios estao com a capacidade hospitalar ultrapassada';`
> Deixe a pergunta e o SQL gerado visíveis na mesma tela. É a evidência mais forte
> que o vídeo pode ter.

⏱ **02:00 – 04:00**

---

## Bloco 5 · Benefícios gerados — 30s

**Quem fala:** Marco
**Tela:** slide 22 do PPT (resultados alcançados)

> "O que o MVP entregou, com dado real e verificável:
>
> Quinze municípios com capacidade ultrapassada e trinta e um em faixa de atenção —
> quarenta e seis pontos concretos onde a decisão de leito precisa ser revista.
>
> Três capítulos da CID-10 concentrando trinta e cinco por cento da demanda, com
> gravidez e parto na liderança — o que aponta para fora do hospital, para a
> atenção primária.
>
> E vinte municípios com crescimento estatisticamente consistente, separados do
> ruído sazonal pelo R quadrado.
>
> Nenhum desses números é ilustrativo. Todos saem de fonte pública verificável."

⏱ **04:00 – 04:30**

---

## Bloco 6 · Conclusão e próximos passos — 30s

**Quem fala:** Nélson
**Tela:** slide 23 (conclusão) e depois o repositório no GitHub

> "O MVP provou três coisas. Que o dado público do SUS é utilizável — o obstáculo
> é de acesso, não de disponibilidade. Que a pergunta em linguagem natural elimina
> a dependência do analista. E que o tratamento de dados é o que separa um ranking
> útil de um ranking enganoso.
>
> Os próximos passos: ingestão agendada, expansão para as vinte e sete unidades da
> federação — que é troca de parâmetro, não mudança de arquitetura — e modelo
> preditivo com o Oracle AutoML.
>
> Todo o código está no repositório público, com a documentação da arquitetura e
> o guia de reprodução.
>
> **Transformar dado público em decisão de saúde na velocidade de uma pergunta.**
> Obrigado."

⏱ **04:30 – 05:00**

---

## Checklist antes de publicar

- [ ] Duração total **abaixo de 5min00s**
- [ ] Áudio audível, sem eco e sem ruído de fundo
- [ ] A demonstração ao vivo aparece — não só slides
- [ ] O SQL gerado pelo Select AI fica legível na tela
- [ ] Todos os quatro integrantes falam ao menos um bloco
- [ ] Vídeo subido no YouTube como **público** ou **não listado**
- [ ] Link colado no slide 21 do PPT
- [ ] Link colado no arquivo `link_video_pitch.txt`

---

## Erros comuns que custam nota

| Erro | Consequência |
|---|---|
| Ler o slide em voz alta | A banca desliga; o slide é apoio, não teleprompter |
| Estourar os 5 minutos | Penalidade direta na avaliação |
| Demonstração só com slides | O critério é "MVP em funcionamento", exige tela real |
| Um só integrante falando | O critério de condução avalia o grupo |
| Gravar sem ensaiar | Dá para ouvir, e a gestão de tempo escorrega |
