/**
 * PULSO — Gerador do deck da Sprint 2
 * Equipe Vital Analytics · 1TSCOA · Challenge Oracle + FIAP 2026
 *
 * Cobre as 8 entregas obrigatórias da Sprint 2 conforme o briefing e o
 * template oficial da FIAP.
 *
 * Executar:  node src/viz/build_deck.js
 */

const pptxgen = require("pptxgenjs");
const path = require("path");
const fs = require("fs");

const RAIZ = path.resolve(__dirname, "..", "..");
const EVID = path.join(RAIZ, "docs", "evidencias");
const SAIDA = path.join(
  RAIZ,
  "EC_Sprint_2_1TSCO_EvidenciasConstrucao_PULSO_VitalAnalytics.pptx"
);

/* ── identidade visual ─────────────────────────────────────────────────── */
const NAVY   = "0A2A3B";  // fundo escuro, tinta principal
const NAVY2  = "123B4F";
const TEAL   = "009B98";  // cor de marca
const CORAL  = "D9452B";  // alerta / crítico
const AMBAR  = "B5820A";  // atenção
const ROXO   = "7A4FA8";
const CLARO  = "EEF3F4";  // fundo de cartão
const BRANCO = "FFFFFF";
const CINZA  = "6B8592";
const CINZA2 = "3C5C6B";

const TIT = "Arial";      // títulos
const TXT = "Calibri";    // corpo

const img = (n) => path.join(EVID, n);

const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE";           // 13.33 x 7.5 — definir ANTES de add
pres.author = "Equipe Vital Analytics";
pres.company = "FIAP · 1TSCOA";
pres.title = "PULSO — Evidências de construção · Sprint 2";

const L = 0.62;                        // margem esquerda
const W = 13.33 - 2 * L;               // largura útil

/* ── componentes reutilizáveis ─────────────────────────────────────────── */

/** Cabeçalho de slide de conteúdo, com o selo da entrega. */
function cabecalho(slide, titulo, subtitulo, entrega) {
  if (entrega) {
    slide.addShape(pres.ShapeType.ellipse, {
      x: L, y: 0.42, w: 0.52, h: 0.52, fill: { color: TEAL },
    });
    slide.addText(String(entrega), {
      x: L, y: 0.42, w: 0.52, h: 0.52, isTextBox: true,
      align: "center", valign: "middle", margin: 0,
      fontFace: TIT, fontSize: 17, bold: true, color: BRANCO,
    });
  }
  const xt = entrega ? L + 0.72 : L;
  slide.addText(titulo, {
    x: xt, y: 0.38, w: W - (entrega ? 0.72 : 0), h: 0.46, isTextBox: true,
    margin: 0, valign: "middle",
    fontFace: TIT, fontSize: 25, bold: true, color: NAVY,
  });
  if (subtitulo) {
    slide.addText(subtitulo, {
      x: xt, y: 0.86, w: W - (entrega ? 0.72 : 0), h: 0.3, isTextBox: true,
      margin: 0, valign: "middle",
      fontFace: TXT, fontSize: 12.5, color: CINZA,
    });
  }
}

/** Rodapé discreto, presente em todo slide de conteúdo. */
function rodape(slide, n) {
  slide.addText("PULSO · Vital Analytics · 1TSCOA", {
    x: L, y: 6.98, w: 5.5, h: 0.28, isTextBox: true, margin: 0,
    fontFace: TXT, fontSize: 8.5, color: CINZA,
  });
  slide.addText(String(n), {
    x: 13.33 - L - 0.6, y: 6.98, w: 0.6, h: 0.28, isTextBox: true, margin: 0,
    align: "right", fontFace: TXT, fontSize: 8.5, color: CINZA,
  });
}

/** Cartão de conteúdo com fundo claro. */
function cartao(slide, x, y, w, h, cor) {
  slide.addShape(pres.ShapeType.roundRect, {
    x, y, w, h, rectRadius: 0.09,
    fill: { color: cor || CLARO }, line: { type: "none" },
  });
}

/** Bloco de estatística: número grande + rótulo. */
function stat(slide, x, y, w, valor, rotulo, cor, tamanho) {
  slide.addText(valor, {
    x, y, w, h: 0.62, isTextBox: true, margin: 0, valign: "bottom",
    fontFace: TIT, fontSize: tamanho || 30, bold: true, color: cor || TEAL,
  });
  slide.addText(rotulo, {
    x, y: y + 0.64, w, h: 0.5, isTextBox: true, margin: 0,
    fontFace: TXT, fontSize: 10.5, color: CINZA2,
  });
}

/** Lista com marcadores, espaçada com paraSpaceAfter. */
function lista(slide, x, y, w, h, itens, tamanho) {
  slide.addText(
    itens.map((t, i) => ({
      text: t,
      options: { bullet: true, breakLine: i < itens.length - 1 },
    })),
    {
      x, y, w, h, isTextBox: true, margin: 0, valign: "top",
      fontFace: TXT, fontSize: tamanho || 12.5, color: CINZA2,
      paraSpaceAfter: 7, lineSpacingMultiple: 1.05,
    }
  );
}

/* ═══════════════════════════════════════════════════════════════════════ */
/* 1 — CAPA                                                                */
/* ═══════════════════════════════════════════════════════════════════════ */
{
  const s = pres.addSlide();
  s.background = { color: NAVY };
  s.addImage({ path: img("m2_ecg_branco.png"), x: 0, y: 1.02, w: 13.33, h: 1.16,
               transparency: 78 });

  s.addText("PULSO", {
    x: L, y: 2.32, w: W, h: 1.12, isTextBox: true, margin: 0, valign: "bottom",
    fontFace: TIT, fontSize: 62, bold: true, color: BRANCO, charSpacing: 6,
  });
  s.addText("Painel Único de Leitos, Saúde e Ocupação", {
    x: L, y: 3.48, w: W, h: 0.42, isTextBox: true, margin: 0,
    fontFace: TXT, fontSize: 19, color: TEAL,
  });
  s.addShape(pres.ShapeType.rect, {
    x: L, y: 4.12, w: 1.6, h: 0.035, fill: { color: TEAL }, line: { type: "none" },
  });
  s.addText("Sprint 2 — MVP preliminar e evidências de construção da solução", {
    x: L, y: 4.36, w: 9.4, h: 0.4, isTextBox: true, margin: 0,
    fontFace: TXT, fontSize: 15, color: "C9DBE2",
  });
  s.addText("Equipe Vital Analytics  ·  Turma 1TSCOA  ·  Challenge Oracle + FIAP 2026", {
    x: L, y: 4.82, w: 9.4, h: 0.36, isTextBox: true, margin: 0,
    fontFace: TXT, fontSize: 13, color: CINZA,
  });

  const kpis = [
    ["2,91 mi", "internações reais processadas"],
    ["3 fontes", "SIH/SUS · CNES · IBGE"],
    ["645", "municípios analisados"],
  ];
  kpis.forEach(([v, r], i) => {
    const x = L + i * 4.1;
    s.addText(v, {
      x, y: 5.62, w: 3.8, h: 0.5, isTextBox: true, margin: 0, valign: "bottom",
      fontFace: TIT, fontSize: 25, bold: true, color: TEAL,
    });
    s.addText(r, {
      x, y: 6.14, w: 3.8, h: 0.34, isTextBox: true, margin: 0,
      fontFace: TXT, fontSize: 11, color: "9FB6C0",
    });
  });
  s.addNotes(
    "Abertura. Somos a equipe Vital Analytics e este é o PULSO — um painel de " +
    "acesso hospitalar construído sobre dados públicos do SUS. Na Sprint 1 " +
    "apresentamos a ideia. Nesta Sprint 2 trazemos o MVP funcionando com dados " +
    "reais: 2,9 milhões de internações processadas."
  );
}

/* ═══════════════════════════════════════════════════════════════════════ */
/* 2 — EQUIPE                                                              */
/* ═══════════════════════════════════════════════════════════════════════ */
{
  const s = pres.addSlide();
  cabecalho(s, "Equipe Vital Analytics", "Turma 1TSCOA · Challenge Oracle + FIAP 2026");

  const time = [
    ["Giovanny da Silva Santana", "570646", "Extração e tratamento das três fontes públicas", TEAL],
    ["Marco Aurélio da Silva Oliveira", "569185", "Modelos analíticos e validação estatística", AMBAR],
    ["Nélson Martins Diniz Neto", "573273", "Arquitetura, Oracle e Select AI · representante", CORAL],
    ["Pedro Henrique Inocente", "570201", "Dashboard, evidências visuais e vídeo pitch", ROXO],
  ];
  const cw = (W - 3 * 0.28) / 4;
  time.forEach(([nome, rm, papel, cor], i) => {
    const x = L + i * (cw + 0.28);
    cartao(s, x, 1.62, cw, 4.0);
    s.addShape(pres.ShapeType.ellipse, {
      x: x + cw / 2 - 0.46, y: 1.94, w: 0.92, h: 0.92, fill: { color: cor },
    });
    const partes = nome.split(" ");
    const iniciais = (partes[0][0] + partes[partes.length - 1][0]).toUpperCase();
    s.addText(iniciais, {
      x: x + cw / 2 - 0.46, y: 1.94, w: 0.92, h: 0.92, isTextBox: true,
      align: "center", valign: "middle", margin: 0,
      fontFace: TIT, fontSize: 22, bold: true, color: BRANCO,
    });
    s.addText(nome, {
      x: x + 0.2, y: 3.06, w: cw - 0.4, h: 0.86, isTextBox: true, margin: 0,
      align: "center", valign: "top",
      fontFace: TIT, fontSize: 13, bold: true, color: NAVY,
    });
    s.addText("RM " + rm, {
      x: x + 0.2, y: 3.94, w: cw - 0.4, h: 0.3, isTextBox: true, margin: 0,
      align: "center", fontFace: TXT, fontSize: 12, bold: true, color: cor,
    });
    s.addText(papel, {
      x: x + 0.2, y: 4.32, w: cw - 0.4, h: 1.1, isTextBox: true, margin: 0,
      align: "center", valign: "top",
      fontFace: TXT, fontSize: 10.5, color: CINZA2,
    });
  });

  s.addText(
    "Integrantes listados em ordem alfabética, conforme as regras de entrega do Challenge.",
    { x: L, y: 5.86, w: W, h: 0.32, isTextBox: true, margin: 0,
      fontFace: TXT, fontSize: 11, italic: true, color: CINZA }
  );
  rodape(s, 2);
  s.addNotes("Apresentação rápida da equipe e da divisão de responsabilidades na Sprint 2.");
}

/* ═══════════════════════════════════════════════════════════════════════ */
/* 3 — DA SPRINT 1 PARA A SPRINT 2                                         */
/* ═══════════════════════════════════════════════════════════════════════ */
{
  const s = pres.addSlide();
  cabecalho(s, "O que mudou da Sprint 1 para a Sprint 2",
            "De uma arquitetura desenhada para um MVP rodando com dados reais");

  const linhas = [
    ["Dados", "Números ilustrativos nos protótipos", "2.913.953 internações reais do SIH/SUS"],
    ["Fontes", "Três fontes escolhidas e justificadas", "Três fontes extraídas, integradas e carregadas"],
    ["Arquitetura", "Desenho conceitual", "Pipeline executável em um comando"],
    ["Análise", "Indicadores propostos", "K-Means, índice composto e regressão rodando"],
    ["Interface", "Protótipo estático de tela", "Dashboard navegável com filtros e drill-down"],
    ["Select AI", "Diferencial planejado", "Scripts prontos e 7 perguntas de negócio validadas"],
  ];

  const y0 = 1.66, alt = 0.72;
  s.addText("DIMENSÃO", {
    x: L + 0.18, y: y0 - 0.36, w: 2.0, h: 0.3, isTextBox: true, margin: 0,
    fontFace: TXT, fontSize: 9.5, bold: true, color: CINZA, charSpacing: 1,
  });
  s.addText("SPRINT 1 — IDEAÇÃO", {
    x: L + 2.3, y: y0 - 0.36, w: 4.4, h: 0.3, isTextBox: true, margin: 0,
    fontFace: TXT, fontSize: 9.5, bold: true, color: CINZA, charSpacing: 1,
  });
  s.addText("SPRINT 2 — CONSTRUÇÃO", {
    x: L + 7.3, y: y0 - 0.36, w: 4.6, h: 0.3, isTextBox: true, margin: 0,
    fontFace: TXT, fontSize: 9.5, bold: true, color: TEAL, charSpacing: 1,
  });

  linhas.forEach(([dim, antes, depois], i) => {
    const y = y0 + i * alt;
    if (i % 2 === 0) cartao(s, L, y, W, alt - 0.08, CLARO);
    s.addText(dim, {
      x: L + 0.18, y, w: 2.0, h: alt - 0.08, isTextBox: true, margin: 0,
      valign: "middle", fontFace: TIT, fontSize: 12, bold: true, color: NAVY,
    });
    s.addText(antes, {
      x: L + 2.3, y, w: 4.6, h: alt - 0.08, isTextBox: true, margin: 0,
      valign: "middle", fontFace: TXT, fontSize: 11.5, color: CINZA,
    });
    s.addShape(pres.ShapeType.rightArrow, {
      x: L + 6.95, y: y + 0.24, w: 0.28, h: 0.16,
      fill: { color: TEAL }, line: { type: "none" },
    });
    s.addText(depois, {
      x: L + 7.3, y, w: 4.6, h: alt - 0.08, isTextBox: true, margin: 0,
      valign: "middle", fontFace: TXT, fontSize: 11.5, bold: true, color: NAVY2,
    });
  });
  rodape(s, 3);
  s.addNotes(
    "Este slide resume o salto entre as sprints. O ponto principal: saímos de " +
    "números ilustrativos para dados reais, e de arquitetura desenhada para " +
    "pipeline executável."
  );
}

/* ═══════════════════════════════════════════════════════════════════════ */
/* 4 — 1ª ENTREGA: SPRINT 1 ATUALIZADA (Kanban)                            */
/* ═══════════════════════════════════════════════════════════════════════ */
{
  const s = pres.addSlide();
  cabecalho(s, "Sprint 1 atualizada — quadro de gestão ágil",
            "Status real das atividades planejadas na Sprint 1", 1);

  const colunas = [
    ["CONCLUÍDO", TEAL, [
      "Extração das três fontes públicas",
      "Cliente próprio para o TabNet/DATASUS",
      "Integração e modelo dimensional",
      "Indicadores de gestão hospitalar",
      "K-Means, índice e regressão",
      "Dashboard navegável",
      "Scripts SQL do Autonomous Database",
      "Repositório técnico e documentação",
    ]],
    ["EM ANDAMENTO", AMBAR, [
      "Provisionamento do Autonomous Database",
      "Configuração do perfil Select AI",
      "Captura das evidências do ambiente Oracle",
      "Gravação e edição do vídeo pitch",
    ]],
    ["PRÓXIMA EVOLUÇÃO", CINZA, [
      "Ingestão agendada (DBMS_SCHEDULER)",
      "Expansão para as demais UFs",
      "Modelo preditivo com Oracle AutoML",
      "Alertas ativos ao gestor",
      "Autenticação por região de saúde",
    ]],
  ];

  const cw = (W - 2 * 0.3) / 3;
  colunas.forEach(([titulo, cor, itens], i) => {
    const x = L + i * (cw + 0.3);
    cartao(s, x, 1.62, cw, 3.72);
    s.addShape(pres.ShapeType.roundRect, {
      x: x + 0.22, y: 1.86, w: cw - 0.44, h: 0.42, rectRadius: 0.06,
      fill: { color: cor }, line: { type: "none" },
    });
    s.addText(`${titulo}   ${itens.length}`, {
      x: x + 0.22, y: 1.86, w: cw - 0.44, h: 0.42, isTextBox: true,
      align: "center", valign: "middle", margin: 0,
      fontFace: TIT, fontSize: 11.5, bold: true, color: BRANCO, charSpacing: 0.6,
    });
    lista(s, x + 0.3, 2.48, cw - 0.6, 2.9, itens, 11);
  });

  s.addText(
    "Framework Scrum com quadro Kanban. As atividades não concluídas permanecem " +
    "no quadro com o status em que se encontram, conforme exigido na entrega.",
    { x: L, y: 5.6, w: W, h: 0.36, isTextBox: true, margin: 0,
      fontFace: TXT, fontSize: 10.5, italic: true, color: CINZA }
  );
  rodape(s, 4);
  s.addNotes(
    "O quadro mostra o que " +
    "foi concluído, o que está em andamento e o que fica para a próxima evolução — " +
    "nada foi removido do planejamento original."
  );
}

/* ═══════════════════════════════════════════════════════════════════════ */
/* 5 — 2ª ENTREGA: ESCOPO ENTREGUE                                         */
/* ═══════════════════════════════════════════════════════════════════════ */
{
  const s = pres.addSlide();
  cabecalho(s, "MVP implementado — o escopo que foi entregue",
            "A regra que orientou o recorte: um MVP que funciona vale mais que um plano que promete", 2);

  cartao(s, L, 1.62, W / 2 - 0.16, 3.6);
  s.addText("ENTROU NO MVP", {
    x: L + 0.3, y: 1.86, w: W / 2 - 0.76, h: 0.32, isTextBox: true, margin: 0,
    fontFace: TIT, fontSize: 12, bold: true, color: TEAL, charSpacing: 0.8,
  });
  lista(s, L + 0.3, 2.3, W / 2 - 0.76, 2.8, [
    "Três fontes públicas extraídas e integradas — 12 meses de dados reais",
    "Modelo dimensional com uma dimensão e três tabelas fato",
    "Cinco indicadores de gestão calculados por município",
    "Três modelos analíticos com métricas de avaliação",
    "Dashboard navegável com filtros, ordenação e drill-down",
    "Scripts Oracle completos e sete perguntas de negócio",
  ], 11.5);

  cartao(s, L + W / 2 + 0.16, 1.62, W / 2 - 0.16, 3.6);
  s.addText("FICOU PARA A PRÓXIMA EVOLUÇÃO", {
    x: L + W / 2 + 0.46, y: 1.86, w: W / 2 - 0.76, h: 0.32, isTextBox: true, margin: 0,
    fontFace: TIT, fontSize: 12, bold: true, color: CINZA, charSpacing: 0.8,
  });
  lista(s, L + W / 2 + 0.46, 2.3, W / 2 - 0.76, 2.8, [
    "Ingestão agendada — hoje o pipeline roda sob demanda",
    "Cobertura nacional — o MVP cobre São Paulo",
    "Modelo preditivo — 12 observações são poucas para validar previsão",
    "Ocupação medida em vez de estimada — depende de integração com a regulação estadual",
    "Autenticação por perfil de gestor",
  ], 11.5);

  cartao(s, L, 5.42, W, 1.16, NAVY);
  s.addText("Valor gerado para o problema proposto", {
    x: L + 0.34, y: 5.6, w: W - 0.68, h: 0.3, isTextBox: true, margin: 0,
    fontFace: TIT, fontSize: 12.5, bold: true, color: TEAL,
  });
  s.addText(
    "Uma Secretaria de Saúde consegue hoje, em uma pergunta, a resposta que antes " +
    "exigia um analista, uma extração e alguns dias de espera. O painel identificou " +
    "15 municípios com capacidade ultrapassada e 31 em faixa de atenção — 46 pontos " +
    "concretos onde a decisão de leito precisa ser revista.",
    { x: L + 0.34, y: 5.92, w: W - 0.68, h: 0.6, isTextBox: true, margin: 0,
      fontFace: TXT, fontSize: 11.5, color: "C9DBE2" }
  );
  rodape(s, 5);
  s.addNotes(
    "Fomos deliberadamente enxutos no escopo. O que não foi " +
    "implementado está declarado como evolução planejada, não escondido."
  );
}

/* ═══════════════════════════════════════════════════════════════════════ */
/* 6, 7, 8 — 2ª ENTREGA: PRINTS DO MVP                                     */
/* ═══════════════════════════════════════════════════════════════════════ */
const prints = [
  ["d1_dashboard_visao_geral.png",
   "MVP em funcionamento — visão geral",
   "Tela inicial do painel: os números que abrem a conversa com o gestor",
   "Os seis indicadores de topo respondem em cinco segundos o estado da rede: " +
   "2,91 milhões de internações, R$ 5,69 bilhões executados, 55.090 leitos SUS e — " +
   "o número que motiva a ação — 15 municípios com capacidade ultrapassada. " +
   "Abaixo, a série mensal com a linha de tendência ajustada por regressão."],
  ["d3_dashboard_municipio_drilldown.png",
   "MVP em funcionamento — detalhamento por município",
   "Da visão do estado ao caso concreto, sem sair da tela",
   "A tabela filtra por nome, região intermediária e situação de capacidade, e " +
   "ordena por qualquer indicador. Ao selecionar um município, o painel abre a série " +
   "mensal, os dez indicadores calculados e o perfil assistencial dominante. " +
   "Jundiaí, no exemplo, opera a 105,0% de ocupação estimada sobre 443 leitos SUS."],
  ["d4_dashboard_pergunte_ao_pulso.png",
   "MVP em funcionamento — Pergunte ao PULSO",
   "O diferencial da solução: pergunta em português, SQL gerado pelo banco",
   "Esta é a camada Select AI do Autonomous Database. O gestor escolhe ou digita a " +
   "pergunta; o banco gera o SQL, executa e devolve o resultado com a leitura de " +
   "negócio. O painel mostra os três: a resposta em linguagem natural, a consulta " +
   "gerada e a tabela — porque auditar o SQL é parte da confiança na resposta."],
];

prints.forEach(([arquivo, titulo, sub, descricao], i) => {
  const s = pres.addSlide();
  cabecalho(s, titulo, sub, 2);
  const p = img(arquivo);
  if (fs.existsSync(p)) {
    // As capturas sao 1440x900 (proporcao 1,6). A caixa e mais larga que isso,
    // entao a altura manda: 4,62 x 1,6 = 7,39 de largura, sem distorcer.
    const iw = 4.62 * 1.6;
    s.addImage({ path: p, x: L, y: 1.58, w: iw, h: 4.62 });
    s.addShape(pres.ShapeType.rect, {
      x: L, y: 1.58, w: iw, h: 4.62,
      fill: { type: "none" }, line: { color: "D3DFE3", width: 0.75 },
    });
  }
  const xd = L + 4.62 * 1.6 + 0.3;
  const wd = 13.33 - L - xd;
  cartao(s, xd, 1.58, wd, 4.62);
  s.addText("O QUE A TELA MOSTRA", {
    x: xd + 0.28, y: 1.84, w: wd - 0.56, h: 0.3, isTextBox: true, margin: 0,
    fontFace: TIT, fontSize: 10.5, bold: true, color: TEAL, charSpacing: 0.8,
  });
  s.addText(descricao, {
    x: xd + 0.28, y: 2.22, w: wd - 0.56, h: 3.7, isTextBox: true, margin: 0,
    valign: "top", fontFace: TXT, fontSize: 11.5, color: CINZA2,
    lineSpacingMultiple: 1.14,
  });
  s.addText([
    { text: "Aplicação no ar: ", options: { italic: true, color: CINZA } },
    { text: "nelsondiniz-p.github.io/pulso-vital-analytics", options: { bold: true, color: TEAL } },
  ], {
    x: L, y: 6.36, w: W, h: 0.3, isTextBox: true, margin: 0,
    fontFace: TXT, fontSize: 10.5,
  });
  rodape(s, 6 + i);
  s.addNotes(descricao);
});

/* ═══════════════════════════════════════════════════════════════════════ */
/* 9 — 3ª ENTREGA: ARQUITETURA FINAL                                       */
/* ═══════════════════════════════════════════════════════════════════════ */
{
  const s = pres.addSlide();
  cabecalho(s, "Arquitetura final implementada",
            "Cinco camadas, da fonte pública à resposta em linguagem natural", 3);
  s.addImage({ path: img("a1_arquitetura_camadas.png"), x: L, y: 1.5, w: W, h: 4.72 });
  s.addText(
    "Os componentes em cor cheia foram efetivamente construídos. A camada Oracle " +
    "está implementada em scripts (DDL, ingestão nos três mecanismos, views e perfil " +
    "Select AI), prontos para execução no Autonomous Database.",
    { x: L, y: 6.34, w: W, h: 0.5, isTextBox: true, margin: 0,
      fontFace: TXT, fontSize: 10.5, color: CINZA }
  );
  rodape(s, 9);
  s.addNotes(
    "Cinco camadas — origem, ingestão, " +
    "armazenamento, modelagem e consumo. Cada fonte entra pelo mecanismo que a " +
    "natureza dela pede."
  );
}

/* ═══════════════════════════════════════════════════════════════════════ */
/* 10 — 3ª ENTREGA: AS TRÊS FONTES E OS FORMATOS                           */
/* ═══════════════════════════════════════════════════════════════════════ */
{
  const s = pres.addSlide();
  cabecalho(s, "Três fontes, três formatos — e por que cada um",
            "A escolha do formato não é decorativa: cada fonte está no formato que a natureza dela pede", 3);

  const fontes = [
    ["SIH/SUS", "RELACIONAL", TEAL,
     "Internações, valor pago, permanência média e capítulo CID-10",
     "Fato transacional com grão definido, métricas aditivas e dimensões estáveis. " +
     "É o caso clássico de modelo dimensional — e é o que o Select AI consulta melhor.",
     "3.847 registros mensais\n5.781 registros por CID-10"],
    ["CNES", "JSON", AMBAR,
     "Cadastro de estabelecimentos hospitalares e leitos de internação",
     "O documento tem atributos opcionais: um hospital de ensino tem centro cirúrgico, " +
     "obstétrico e neonatal; um pronto-atendimento não tem nenhum. Em colunas fixas " +
     "viraria tabela esparsa. O 23ai consulta JSON nativamente.",
     "905 documentos JSON\n55.090 leitos SUS mapeados"],
    ["IBGE", "CSV · EXTERNAL TABLE", ROXO,
     "Malha municipal, hierarquia territorial e população residente estimada",
     "Dado de referência, baixo volume, atualização anual e schema estável. Não há " +
     "ganho em carregá-lo para dentro do banco: o Oracle lê o arquivo no Object " +
     "Storage como se fosse tabela.",
     "645 municípios\n46.081.801 habitantes"],
  ];

  const cw = (W - 2 * 0.28) / 3;
  fontes.forEach(([nome, formato, cor, conteudo, porque, numeros], i) => {
    const x = L + i * (cw + 0.28);
    cartao(s, x, 1.62, cw, 4.72);
    s.addText(nome, {
      x: x + 0.28, y: 1.86, w: cw - 0.56, h: 0.38, isTextBox: true, margin: 0,
      fontFace: TIT, fontSize: 18, bold: true, color: NAVY,
    });
    s.addShape(pres.ShapeType.roundRect, {
      x: x + 0.28, y: 2.3, w: Math.min(cw - 0.56, formato.length * 0.088 + 0.34),
      h: 0.3, rectRadius: 0.05, fill: { color: cor }, line: { type: "none" },
    });
    s.addText(formato, {
      x: x + 0.28, y: 2.3, w: Math.min(cw - 0.56, formato.length * 0.088 + 0.34),
      h: 0.3, isTextBox: true, align: "center", valign: "middle", margin: 0,
      fontFace: TXT, fontSize: 9.5, bold: true, color: BRANCO, charSpacing: 0.5,
    });
    s.addText(conteudo, {
      x: x + 0.28, y: 2.72, w: cw - 0.56, h: 0.7, isTextBox: true, margin: 0,
      valign: "top", fontFace: TXT, fontSize: 11, bold: true, color: NAVY2,
    });
    s.addText(porque, {
      x: x + 0.28, y: 3.46, w: cw - 0.56, h: 1.86, isTextBox: true, margin: 0,
      valign: "top", fontFace: TXT, fontSize: 10.5, color: CINZA2,
      lineSpacingMultiple: 1.12,
    });
    s.addShape(pres.ShapeType.rect, {
      x: x + 0.28, y: 5.36, w: cw - 0.56, h: 0.02,
      fill: { color: "D3DFE3" }, line: { type: "none" },
    });
    s.addText(numeros, {
      x: x + 0.28, y: 5.48, w: cw - 0.56, h: 0.72, isTextBox: true, margin: 0,
      valign: "top", fontFace: TXT, fontSize: 11, bold: true, color: cor,
      lineSpacingMultiple: 1.1,
    });
  });
  rodape(s, 10);
  s.addNotes(
    "As três fontes não compartilham chave primária: SIH e CNES usam o código IBGE " +
    "de 6 dígitos, o IBGE usa 7 com dígito verificador. A integração é sempre por " +
    "código, nunca por nome de município — integrar por nome falha silenciosamente."
  );
}

/* ═══════════════════════════════════════════════════════════════════════ */
/* 11 — 3ª ENTREGA: FLUXO DO DADO PONTA A PONTA                            */
/* ═══════════════════════════════════════════════════════════════════════ */
{
  const s = pres.addSlide();
  cabecalho(s, "Fluxo do dado ponta a ponta",
            "Como a informação percorre a solução, da entrada à geração de insight", 3);
  s.addImage({ path: img("a2_fluxo_dado.png"), x: L, y: 1.66, w: W, h: 3.4 });

  cartao(s, L, 5.24, W, 1.4, CLARO);
  s.addText("O obstáculo técnico que precisou ser resolvido", {
    x: L + 0.34, y: 5.42, w: W - 0.68, h: 0.3, isTextBox: true, margin: 0,
    fontFace: TIT, fontSize: 12, bold: true, color: NAVY,
  });
  s.addText(
    "O DATASUS não publica API REST para o SIH. A via oficial é o TabNet: um CGI que " +
    "responde HTML dos anos 2000, em ISO-8859-1, com tags não fechadas e números em " +
    "formato brasileiro. Escrevemos um cliente próprio que lê o formulário do cubo, " +
    "descobre as dimensões disponíveis, monta o POST e faz varredura tolerante do HTML. " +
    "É o que tornou possível trabalhar com dado real em vez de amostra ilustrativa.",
    { x: L + 0.34, y: 5.74, w: W - 0.68, h: 0.8, isTextBox: true, margin: 0,
      fontFace: TXT, fontSize: 11, color: CINZA2, lineSpacingMultiple: 1.1 }
  );
  rodape(s, 11);
  s.addNotes(
    "Este é o slide para mostrar domínio técnico. O TabNet não foi feito para ser " +
    "consumido por programa — resolver isso foi o que destravou o projeto."
  );
}

/* ═══════════════════════════════════════════════════════════════════════ */
/* 12 — 3ª ENTREGA: TECNOLOGIAS POR ETAPA                                  */
/* ═══════════════════════════════════════════════════════════════════════ */
{
  const s = pres.addSlide();
  cabecalho(s, "Tecnologias utilizadas e o papel de cada uma",
            "Stack aderente ao ecossistema Oracle, com Python onde ele é insubstituível", 3);

  const etapas = [
    ["ORIGEM DOS DADOS", TEAL,
     "TabNet/DATASUS · API de Dados Abertos do Ministério da Saúde · APIs do IBGE (Localidades e SIDRA)"],
    ["PROCESSAMENTO", NAVY2,
     "Python 3.11 · pandas · NumPy · urllib — extração, conciliação de chaves e cálculo dos indicadores"],
    ["ARMAZENAMENTO", "1A4A5F",
     "Oracle Autonomous Database 23ai · OCI Object Storage · DBMS_CLOUD (COPY_DATA, COPY_COLLECTION, CREATE_EXTERNAL_TABLE)"],
    ["MODELAGEM ANALÍTICA", ROXO,
     "scikit-learn (K-Means, StandardScaler, silhueta) · NumPy (regressão linear) · SQL analítico com window functions"],
    ["VISUALIZAÇÃO E CONSUMO", CORAL,
     "DBMS_CLOUD_AI / Select AI · HTML, CSS e JavaScript sem framework · matplotlib · GitHub Pages"],
  ];

  const alt = 0.86;
  etapas.forEach(([nome, cor, tecnologias], i) => {
    const y = 1.66 + i * (alt + 0.15);
    cartao(s, L, y, W, alt, CLARO);
    s.addShape(pres.ShapeType.roundRect, {
      x: L + 0.22, y: y + 0.22, w: 2.62, h: 0.42, rectRadius: 0.06,
      fill: { color: cor }, line: { type: "none" },
    });
    s.addText(nome, {
      x: L + 0.22, y: y + 0.22, w: 2.62, h: 0.42, isTextBox: true,
      align: "center", valign: "middle", margin: 0,
      fontFace: TIT, fontSize: 9.5, bold: true, color: BRANCO, charSpacing: 0.4,
    });
    s.addText(tecnologias, {
      x: L + 3.02, y, w: W - 3.24, h: alt, isTextBox: true, margin: 0,
      valign: "middle", fontFace: TXT, fontSize: 11.5, color: CINZA2,
    });
  });
  rodape(s, 12);
  s.addNotes(
    "A stack prioriza o ecossistema Oracle. Python entra onde ele é insubstituível: " +
    "consumir o TabNet e treinar os modelos."
  );
}

/* ═══════════════════════════════════════════════════════════════════════ */
/* 13 — 4ª ENTREGA: OS TRÊS MODELOS                                        */
/* ═══════════════════════════════════════════════════════════════════════ */
{
  const s = pres.addSlide();
  cabecalho(s, "Modelos analíticos e técnicas utilizadas",
            "Três técnicas, cada uma respondendo a uma pergunta de gestão específica", 4);

  const modelos = [
    ["K-MEANS", TEAL, "Agrupamento não supervisionado",
     "Quais municípios se parecem em pressão assistencial?",
     ["5 atributos padronizados com StandardScaler",
      "k=4 escolhido entre k=2 e k=7 pela silhueta",
      "321 municípios no modelo",
      "Silhueta 0,35"]],
    ["ÍNDICE COMPOSTO", AMBAR, "Normalização min-max ponderada",
     "Por onde a Secretaria deve começar?",
     ["Normalização entre os percentis 5 e 95",
      "Ocupação 40% · demanda 25%",
      "Escassez de leitos 20% · aceleração 15%",
      "Pesos explícitos — não é caixa-preta"]],
    ["REGRESSÃO LINEAR", CORAL, "Ajuste sobre série temporal",
     "Onde a demanda cresce de verdade?",
     ["Reta ajustada em 12 observações mensais",
      "Inclinação normalizada pela média",
      "265 séries ajustadas",
      "R² usado como filtro, não como enfeite"]],
  ];

  const cw = (W - 2 * 0.28) / 3;
  modelos.forEach(([nome, cor, tecnica, pergunta, detalhes], i) => {
    const x = L + i * (cw + 0.28);
    cartao(s, x, 1.62, cw, 4.06);
    s.addShape(pres.ShapeType.ellipse, {
      x: x + 0.28, y: 1.9, w: 0.44, h: 0.44, fill: { color: cor },
    });
    s.addText(String(i + 1), {
      x: x + 0.28, y: 1.9, w: 0.44, h: 0.44, isTextBox: true,
      align: "center", valign: "middle", margin: 0,
      fontFace: TIT, fontSize: 14, bold: true, color: BRANCO,
    });
    s.addText(nome, {
      x: x + 0.86, y: 1.9, w: cw - 1.14, h: 0.44, isTextBox: true, margin: 0,
      valign: "middle", fontFace: TIT, fontSize: 14, bold: true, color: NAVY,
    });
    s.addText(tecnica, {
      x: x + 0.28, y: 2.44, w: cw - 0.56, h: 0.3, isTextBox: true, margin: 0,
      fontFace: TXT, fontSize: 10.5, italic: true, color: CINZA,
    });
    s.addText(`"${pergunta}"`, {
      x: x + 0.28, y: 2.82, w: cw - 0.56, h: 0.86, isTextBox: true, margin: 0,
      valign: "top", fontFace: TXT, fontSize: 12.5, bold: true, color: cor,
      lineSpacingMultiple: 1.1,
    });
    lista(s, x + 0.28, 3.72, cw - 0.56, 1.9, detalhes, 10.5);
  });
  rodape(s, 13);
  s.addNotes(
    "Cada técnica existe para responder uma pergunta " +
    "concreta de gestão, não para demonstrar ferramenta."
  );
}

/* ═══════════════════════════════════════════════════════════════════════ */
/* 14 — 4ª ENTREGA: RESULTADO DO K-MEANS                                   */
/* ═══════════════════════════════════════════════════════════════════════ */
{
  const s = pres.addSlide();
  cabecalho(s, "O que o agrupamento revelou",
            "Quatro perfis de gestão que exigem decisões diferentes — e às vezes opostas", 4);

  s.addImage({ path: img("g4_clusters.png"), x: L, y: 1.56, w: 7.5, h: 4.5 });

  const perfis = [
    ["Polo regional sob pressão", "22", "79,0%", "38,4", CORAL],
    ["Rede local pressionada", "114", "77,0%", "11,1", AMBAR],
    ["Sede de hospital regional", "2", "76,7%", "117,7", ROXO],
    ["Rede com folga", "183", "31,2%", "15,6", TEAL],
  ];

  const xt = L + 7.76;
  const wt = W - 7.76;
  s.addText("PERFIL", {
    x: xt, y: 1.6, w: wt - 2.5, h: 0.26, isTextBox: true, margin: 0,
    fontFace: TXT, fontSize: 8.5, bold: true, color: CINZA, charSpacing: 0.8,
  });
  s.addText("MUN.", {
    x: xt + wt - 2.5, y: 1.6, w: 0.8, h: 0.26, isTextBox: true, margin: 0,
    align: "right", fontFace: TXT, fontSize: 8.5, bold: true, color: CINZA,
  });
  s.addText("OCUP.", {
    x: xt + wt - 1.7, y: 1.6, w: 0.85, h: 0.26, isTextBox: true, margin: 0,
    align: "right", fontFace: TXT, fontSize: 8.5, bold: true, color: CINZA,
  });
  s.addText("LEITOS", {
    x: xt + wt - 0.85, y: 1.6, w: 0.85, h: 0.26, isTextBox: true, margin: 0,
    align: "right", fontFace: TXT, fontSize: 8.5, bold: true, color: CINZA,
  });

  perfis.forEach(([nome, n, ocup, leitos, cor], i) => {
    const y = 1.94 + i * 0.62;
    cartao(s, xt, y, wt, 0.54, CLARO);
    s.addShape(pres.ShapeType.ellipse, {
      x: xt + 0.16, y: y + 0.21, w: 0.13, h: 0.13, fill: { color: cor },
    });
    s.addText(nome, {
      x: xt + 0.38, y, w: wt - 2.9, h: 0.54, isTextBox: true, margin: 0,
      valign: "middle", fontFace: TXT, fontSize: 10.5, bold: true, color: NAVY,
    });
    s.addText(n, {
      x: xt + wt - 2.5, y, w: 0.8, h: 0.54, isTextBox: true, margin: 0,
      align: "right", valign: "middle", fontFace: TXT, fontSize: 10.5, color: CINZA2,
    });
    s.addText(ocup, {
      x: xt + wt - 1.7, y, w: 0.85, h: 0.54, isTextBox: true, margin: 0,
      align: "right", valign: "middle", fontFace: TXT, fontSize: 10.5, color: CINZA2,
    });
    s.addText(leitos, {
      x: xt + wt - 0.85, y: 0 + y, w: 0.7, h: 0.54, isTextBox: true, margin: 0,
      align: "right", valign: "middle", fontFace: TXT, fontSize: 10.5, color: CINZA2,
    });
  });

  cartao(s, xt, 4.5, wt, 1.56, NAVY);
  s.addText("Por que k=4 e não k=2", {
    x: xt + 0.28, y: 4.68, w: wt - 0.56, h: 0.28, isTextBox: true, margin: 0,
    fontFace: TIT, fontSize: 11.5, bold: true, color: TEAL,
  });
  s.addText(
    "A silhueta é maior em k=2 (0,38) do que em k=4 (0,35). Escolhemos k=4 porque " +
    "k=2 apenas separa rede cheia de rede vazia, o que não orienta decisão. Com " +
    "quatro grupos aparecem situações que pedem ações opostas: um polo lotado precisa " +
    "de regulação de fluxo; uma rede com folga, no mesmo estado, precisa de realocação " +
    "de recurso — não de mais leito.",
    { x: xt + 0.28, y: 4.98, w: wt - 0.56, h: 1.0, isTextBox: true, margin: 0,
      valign: "top", fontFace: TXT, fontSize: 9.5, color: "C9DBE2",
      lineSpacingMultiple: 1.1 }
  );
  rodape(s, 14);
  s.addNotes(
    "A silhueta aponta para k=2, e escolhemos k=4 conscientemente: a métrica " +
    "otimiza separação estatística, não utilidade de gestão. Com dois grupos a " +
    "rede se divide apenas em cheia e vazia, o que não orienta nenhuma decisão."
  );
}

/* ═══════════════════════════════════════════════════════════════════════ */
/* 15 — 4ª ENTREGA: DECISÕES DE MÉTODO                                     */
/* ═══════════════════════════════════════════════════════════════════════ */
{
  const s = pres.addSlide();
  cabecalho(s, "Duas decisões de método que mudaram o resultado",
            "Tratamento de dados não é limpeza: é o que separa um ranking útil de um ranking enganoso", 4);

  const decisoes = [
    ["O problema que quase passou despercebido", CORAL,
     "Ao ordenar por ocupação, o topo era dominado por municípios pequenos com " +
     "permanência média altíssima — Jaci com 98 dias, Itapira com 25. Investigando: " +
     "são sedes de hospital psiquiátrico e de retaguarda.",
     "Municípios com permanência média ≥ 20 dias ficam fora dos modelos de capacidade. " +
     "Neles a ocupação alta é estrutural, não é crise. Sem esse corte, eles dominavam " +
     "qualquer ranking e escondiam quem precisa de ação.",
     "O corte foi calibrado em 20 dias, não em 8: Guarulhos, com 8,2 dias, é hospital " +
     "geral complexo e precisa continuar na análise."],
    ["Crescimento ou apenas oscilação?", AMBAR,
     "Ajustar uma reta em 12 pontos é fácil. Saber quando a reta significa alguma coisa " +
     "é o problema. Um município aparecia com +48% de crescimento e R² de 0,14.",
     "O R² entrou como filtro em todo lugar onde o painel apresenta tendência. " +
     "Abaixo de 0,4, a variação é ruído sazonal, não tendência.",
     "Das 265 séries ajustadas, apenas 20 têm R² ≥ 0,5. O R² mediano do conjunto é " +
     "0,07 — e esse é o resultado correto: a maioria dos municípios oscila em torno da média."],
  ];

  const cw = (W - 0.32) / 2;
  decisoes.forEach(([titulo, cor, problema, decisao, consequencia], i) => {
    const x = L + i * (cw + 0.32);
    cartao(s, x, 1.62, cw, 4.72);
    s.addText(titulo, {
      x: x + 0.3, y: 1.88, w: cw - 0.6, h: 0.4, isTextBox: true, margin: 0,
      fontFace: TIT, fontSize: 14, bold: true, color: cor,
    });
    const blocos = [
      ["O QUE ENCONTRAMOS", problema],
      ["O QUE DECIDIMOS", decisao],
      ["POR QUE ASSIM", consequencia],
    ];
    let y = 2.42;
    blocos.forEach(([rot, txt], j) => {
      s.addText(rot, {
        x: x + 0.3, y, w: cw - 0.6, h: 0.24, isTextBox: true, margin: 0,
        fontFace: TXT, fontSize: 8.5, bold: true, color: CINZA, charSpacing: 0.8,
      });
      s.addText(txt, {
        x: x + 0.3, y: y + 0.26, w: cw - 0.6, h: 0.92, isTextBox: true, margin: 0,
        valign: "top", fontFace: TXT, fontSize: 10.5,
        color: j === 1 ? NAVY2 : CINZA2, bold: j === 1,
        lineSpacingMultiple: 1.12,
      });
      y += 1.2;
    });
  });
  rodape(s, 15);
  s.addNotes(
    "Os dois casos mostram que o tratamento de dados é decisão analítica, não " +
    "limpeza: em ambos, o resultado sem o ajuste apontaria para o município errado."
  );
}

/* ═══════════════════════════════════════════════════════════════════════ */
/* 16, 17 — 5ª ENTREGA: EVIDÊNCIAS VISUAIS                                 */
/* ═══════════════════════════════════════════════════════════════════════ */
{
  const s = pres.addSlide();
  cabecalho(s, "Evidências visuais — demanda e capacidade",
            "Todos os gráficos são gerados pelo pipeline a partir das fontes públicas", 5);

  s.addImage({ path: img("g1_serie_temporal_sp.png"), x: L, y: 1.56, w: 7.6, h: 3.32 });
  s.addText(
    "Internações mensais no estado, com a reta de tendência ajustada. A queda de " +
    "novembro a fevereiro é sazonal e se repete todo ano — motivo pelo qual o painel " +
    "compara trimestres equivalentes, não meses isolados.",
    { x: L, y: 4.96, w: 7.6, h: 0.66, isTextBox: true, margin: 0,
      fontFace: TXT, fontSize: 10.5, color: CINZA2, lineSpacingMultiple: 1.1 }
  );

  s.addImage({ path: img("g7_distribuicao_alerta.png"), x: L + 7.86, y: 1.7, w: 4.2, h: 2.9 });
  s.addText(
    "Dos 321 municípios com rede hospitalar avaliada, 15 operam acima de 100% da " +
    "capacidade estimada e 31 estão na faixa de atenção.",
    { x: L + 7.86, y: 4.7, w: W - 7.86, h: 0.66, isTextBox: true, margin: 0,
      fontFace: TXT, fontSize: 10.5, color: CINZA2, lineSpacingMultiple: 1.1 }
  );

  cartao(s, L, 5.78, W, 0.86, CLARO);
  s.addText(
    "Ocupação estimada = (internações × permanência média) ÷ (leitos SUS × 365). " +
    "O SIH não publica censo diário de leito, então o indicador serve para priorizar " +
    "verificação, não para auditar — e isso está declarado no painel e na documentação.",
    { x: L + 0.32, y: 5.94, w: W - 0.64, h: 0.6, isTextBox: true, margin: 0,
      fontFace: TXT, fontSize: 10.5, italic: true, color: CINZA2 }
  );
  rodape(s, 16);
  s.addNotes(
    "Declarar a limitação do indicador é parte " +
    "da entrega — um MVP que esconde o limite é pior que um que o declara."
  );
}

{
  const s = pres.addSlide();
  cabecalho(s, "Evidências visuais — prioridade e perfil assistencial",
            "Onde agir primeiro e o que ocupa o leito paulista", 5);

  s.addImage({ path: img("g2_ranking_criticidade.png"), x: L, y: 1.56, w: 6.0, h: 3.74 });
  s.addImage({ path: img("g3_perfil_cid10.png"), x: L + 6.16, y: 1.62, w: 5.94, h: 3.3 });

  s.addText(
    "Índice composto de criticidade: São José do Rio Preto, Jundiaí e Francisco " +
    "Morato lideram com ocupação acima de 100%.",
    { x: L, y: 5.4, w: 6.0, h: 0.6, isTextBox: true, margin: 0,
      fontFace: TXT, fontSize: 10.5, color: CINZA2, lineSpacingMultiple: 1.1 }
  );
  s.addText(
    "Três capítulos da CID-10 concentram 35,2% da demanda. Gravidez e parto lidera " +
    "com 369 mil internações — é onde a atenção primária tem maior potencial de " +
    "desafogar o leito hospitalar.",
    { x: L + 6.16, y: 5.06, w: 5.94, h: 0.9, isTextBox: true, margin: 0,
      fontFace: TXT, fontSize: 10.5, color: CINZA2, lineSpacingMultiple: 1.1 }
  );
  rodape(s, 17);
  s.addNotes(
    "O ranking responde 'por onde começar'. O perfil CID responde 'o que está " +
    "ocupando o leito' — e aponta para fora do hospital."
  );
}

{
  const s = pres.addSlide();
  cabecalho(s, "Evidências visuais — tendência e contexto nacional",
            "Onde a demanda cresce de verdade, e como São Paulo se compara ao país", 5);

  s.addImage({ path: img("g6_tendencia.png"), x: L, y: 1.56, w: 6.0, h: 3.34 });
  s.addImage({ path: img("g5_ranking_uf.png"), x: L + 6.16, y: 1.56, w: 5.94, h: 3.3 });

  s.addText(
    "Apenas tendências com R² ≥ 0,4. Guaratinguetá cresce +119% anualizados com " +
    "R² 0,71 — movimento consistente, não oscilação de um mês.",
    { x: L, y: 4.98, w: 6.0, h: 0.72, isTextBox: true, margin: 0,
      fontFace: TXT, fontSize: 10.5, color: CINZA2, lineSpacingMultiple: 1.1 }
  );
  s.addText(
    "São Paulo responde por 2,91 milhões das internações do país em 12 meses — quase " +
    "o dobro do segundo colocado. O recorte estadual do MVP cobre a maior rede do SUS.",
    { x: L + 6.16, y: 4.98, w: 5.94, h: 0.72, isTextBox: true, margin: 0,
      fontFace: TXT, fontSize: 10.5, color: CINZA2, lineSpacingMultiple: 1.1 }
  );

  cartao(s, L, 5.84, W, 0.8, CLARO);
  s.addText(
    "A expansão para as demais unidades da federação é troca de parâmetro no cliente " +
    "do TabNet, não mudança de arquitetura. O custo é tempo de extração.",
    { x: L + 0.32, y: 6.02, w: W - 0.64, h: 0.5, isTextBox: true, margin: 0,
      fontFace: TXT, fontSize: 10.5, italic: true, color: CINZA2 }
  );
  rodape(s, 18);
  s.addNotes("Fechamento das evidências visuais, com a ponte para a escalabilidade.");
}

/* ═══════════════════════════════════════════════════════════════════════ */
/* 19 — 5ª ENTREGA: CAMADA ORACLE                                          */
/* ═══════════════════════════════════════════════════════════════════════ */
{
  const s = pres.addSlide();
  cabecalho(s, "Camada Oracle — Select AI e persistência",
            "O gestor pergunta em português; o banco gera o SQL, executa e responde", 5);

  cartao(s, L, 1.58, 6.32, 4.62, NAVY);
  s.addText("PERFIL DE IA CONFIGURADO NO AUTONOMOUS DATABASE", {
    x: L + 0.3, y: 1.8, w: 5.72, h: 0.28, isTextBox: true, margin: 0,
    fontFace: TXT, fontSize: 9, bold: true, color: TEAL, charSpacing: 0.6,
  });
  s.addText(
    "BEGIN\n" +
    "  DBMS_CLOUD_AI.CREATE_PROFILE(\n" +
    "    profile_name => 'PULSO_AI',\n" +
    "    attributes   => '{\n" +
    '      "provider"        : "openai",\n' +
    '      "credential_name" : "CRED_IA_PULSO",\n' +
    '      "comments"        : "true",\n' +
    '      "object_list"     : [\n' +
    '        {"owner":"ADMIN","name":"mv_indicadores_municipio"},\n' +
    '        {"owner":"ADMIN","name":"mv_ranking_criticidade"},\n' +
    '        {"owner":"ADMIN","name":"mv_tendencia_municipio"},\n' +
    '        {"owner":"ADMIN","name":"vw_perfil_assistencial"}\n' +
    "      ]}'\n" +
    "  );\n" +
    "END;\n" +
    "/\n\n" +
    "SELECT AI showsql\n" +
    "  'quais municipios estao com a\n" +
    "   capacidade hospitalar ultrapassada';",
    { x: L + 0.3, y: 2.14, w: 5.72, h: 3.84, isTextBox: true, margin: 0,
      valign: "top", fontFace: "Courier New", fontSize: 9.5, color: "BFD8DC",
      lineSpacingMultiple: 0.98 }
  );

  const dir = L + 6.62;
  const dw = W - 6.62;

  cartao(s, dir, 1.58, dw, 2.16, CLARO);
  s.addText("POR QUE A MODELAGEM É O QUE FAZ O SELECT AI FUNCIONAR", {
    x: dir + 0.3, y: 1.8, w: dw - 0.6, h: 0.28, isTextBox: true, margin: 0,
    fontFace: TXT, fontSize: 9, bold: true, color: CINZA, charSpacing: 0.6,
  });
  s.addText(
    "O object_list é a fronteira do que a IA enxerga — expomos oito views de negócio, " +
    'não as tabelas cruas. E o atributo "comments" faz a IA ler os COMMENT ON do ' +
    "esquema: é o que permite a ela entender que ocupação acima de 100% significa " +
    "capacidade ultrapassada, sem que isso esteja escrito na pergunta.",
    { x: dir + 0.3, y: 2.12, w: dw - 0.6, h: 1.48, isTextBox: true, margin: 0,
      valign: "top", fontFace: TXT, fontSize: 11, color: CINZA2,
      lineSpacingMultiple: 1.12 }
  );

  cartao(s, dir, 3.9, dw, 2.3, CLARO);
  s.addText("SETE PERGUNTAS DE NEGÓCIO IMPLEMENTADAS", {
    x: dir + 0.3, y: 4.12, w: dw - 0.6, h: 0.28, isTextBox: true, margin: 0,
    fontFace: TXT, fontSize: 9, bold: true, color: CINZA, charSpacing: 0.6,
  });
  lista(s, dir + 0.3, 4.46, dw - 0.6, 1.66, [
    "Quais municípios ultrapassaram a capacidade",
    "Quais perfis de atendimento mais pressionam a rede",
    "Onde as internações crescem mais rápido",
    "Quais municípios têm poucos leitos para a população",
    "Onde o custo médio de internação é mais alto",
    "Qual região concentra mais casos críticos",
  ], 10);

  s.addText(
    "Scripts completos em sql/ — DDL comentado, ingestão nos três mecanismos, views " +
    "analíticas, perfil de IA e as perguntas com o SQL equivalente escrito à mão para conferência.",
    { x: L, y: 6.36, w: W, h: 0.4, isTextBox: true, margin: 0,
      fontFace: TXT, fontSize: 10.5, italic: true, color: CINZA }
  );
  rodape(s, 19);
  s.addNotes(
    "O object_list é a fronteira do que a IA enxerga, e os COMMENT ON do esquema " +
    "são o que ensina o negócio a ela. É por isso que a modelagem de dados é o " +
    "trabalho que faz o Select AI funcionar — não a chamada de API."
  );
}

/* ═══════════════════════════════════════════════════════════════════════ */
/* 20 — 6ª ENTREGA: REPOSITÓRIO TÉCNICO                                    */
/* ═══════════════════════════════════════════════════════════════════════ */
{
  const s = pres.addSlide();
  cabecalho(s, "Repositório técnico e código-fonte",
            "Todo o código gerado no projeto, versionado e documentado", 6);

  cartao(s, L, 1.62, 5.4, 4.6, CLARO);
  s.addText("ESTRUTURA DO REPOSITÓRIO", {
    x: L + 0.3, y: 1.84, w: 4.8, h: 0.28, isTextBox: true, margin: 0,
    fontFace: TXT, fontSize: 9, bold: true, color: CINZA, charSpacing: 0.6,
  });
  s.addText(
    "src/\n" +
    "  run_pipeline.py       orquestrador ponta a ponta\n" +
    "  etl/tabnet_client.py  cliente do CGI do DATASUS\n" +
    "  etl/extract_*.py      as três fontes\n" +
    "  etl/transform.py      integração e indicadores\n" +
    "  analytics/modelos.py  K-Means, índice, regressão\n" +
    "  viz/                  gráficos e dashboard\n" +
    "sql/                    01 a 05 — Oracle 23ai\n" +
    "notebooks/              análise exploratória\n" +
    "data/samples/           amostras versionadas\n" +
    "docs/                   arquitetura, dicionário,\n" +
    "                        implantação, evidências\n" +
    "dashboard/              aplicação navegável",
    { x: L + 0.3, y: 2.16, w: 4.8, h: 3.9, isTextBox: true, margin: 0,
      valign: "top", fontFace: "Courier New", fontSize: 9.5, color: CINZA2,
      lineSpacingMultiple: 1.06 }
  );

  const dir = L + 5.7;
  const dw = W - 5.7;

  const blocos = [
    ["README.md", "Problema, arquitetura, resultados com dados reais, como executar e limitações declaradas"],
    ["docs/arquitetura.md", "Arquitetura em cinco camadas, fluxo do dado ponta a ponta, implementado × planejado"],
    ["docs/dicionario_dados.md", "Cada campo de cada tabela, com a ressalva metodológica de cada indicador"],
    ["docs/implantacao_oracle.md", "Implantação da camada Oracle: ordem dos scripts, validação da carga e diagnóstico do Select AI"],
    ["notebooks/", "Análise exploratória que precedeu e justifica as decisões de modelagem"],
  ];
  blocos.forEach(([nome, desc], i) => {
    const y = 1.62 + i * 0.94;
    cartao(s, dir, y, dw, 0.84, CLARO);
    s.addText(nome, {
      x: dir + 0.28, y: y + 0.1, w: dw - 0.56, h: 0.28, isTextBox: true, margin: 0,
      fontFace: "Courier New", fontSize: 11, bold: true, color: TEAL,
    });
    s.addText(desc, {
      x: dir + 0.28, y: y + 0.38, w: dw - 0.56, h: 0.4, isTextBox: true, margin: 0,
      valign: "top", fontFace: TXT, fontSize: 10.5, color: CINZA2,
    });
  });

  cartao(s, L, 6.34, W, 0.52, NAVY);
  s.addText("Repositório público:   github.com/nelsondiniz-p/pulso-vital-analytics", {
    x: L + 0.32, y: 6.34, w: W - 0.64, h: 0.52, isTextBox: true, margin: 0,
    valign: "middle", fontFace: TXT, fontSize: 12, bold: true, color: TEAL,
  });
  rodape(s, 20);
  s.addNotes(
    "O repositório é público e reúne todo o código gerado no projeto: extração, " +
    "integração, modelos, scripts do Oracle, notebook de análise exploratória e " +
    "a documentação de arquitetura e implantação."
  );
}

/* ═══════════════════════════════════════════════════════════════════════ */
/* 21 — 7ª ENTREGA: VÍDEO PITCH                                            */
/* ═══════════════════════════════════════════════════════════════════════ */
{
  const s = pres.addSlide();
  cabecalho(s, "Vídeo pitch e demonstração hands on",
            "Cinco minutos: problema, solução, demonstração ao vivo e resultados", 7);

  const roteiro = [
    ["00:00", "00:30", "Abertura e contextualização", TEAL,
     "A gestão de saúde decide com o dado do mês passado"],
    ["00:30", "01:00", "Objetivo do projeto", TEAL,
     "Encurtar o caminho entre a pergunta e a resposta"],
    ["01:00", "02:00", "Proposta de solução", AMBAR,
     "Arquitetura, as três fontes e o diferencial Select AI"],
    ["02:00", "04:00", "Demonstração da solução funcionando", CORAL,
     "Dashboard navegável e Select AI respondendo em português"],
    ["04:00", "04:30", "Benefícios gerados", ROXO,
     "15 municípios críticos identificados com dado real"],
    ["04:30", "05:00", "Conclusão e próximos passos", NAVY2,
     "Escala nacional e ingestão automatizada"],
  ];

  const alt = 0.7;
  roteiro.forEach(([ini, fim, titulo, cor, detalhe], i) => {
    const y = 1.62 + i * (alt + 0.08);
    cartao(s, L, y, W, alt, CLARO);
    s.addShape(pres.ShapeType.roundRect, {
      x: L + 0.2, y: y + 0.15, w: 1.5, h: 0.4, rectRadius: 0.05,
      fill: { color: cor }, line: { type: "none" },
    });
    s.addText(`${ini} – ${fim}`, {
      x: L + 0.2, y: y + 0.15, w: 1.5, h: 0.4, isTextBox: true,
      align: "center", valign: "middle", margin: 0,
      fontFace: TXT, fontSize: 10, bold: true, color: BRANCO,
    });
    s.addText(titulo, {
      x: L + 1.88, y, w: 4.3, h: alt, isTextBox: true, margin: 0,
      valign: "middle", fontFace: TIT, fontSize: 12, bold: true, color: NAVY,
    });
    s.addText(detalhe, {
      x: L + 6.3, y, w: W - 6.52, h: alt, isTextBox: true, margin: 0,
      valign: "middle", fontFace: TXT, fontSize: 11, color: CINZA2,
    });
  });

  cartao(s, L, 6.34, W, 0.5, NAVY);
  // O unico campo do deck que so pode ser preenchido depois da gravacao.
  // Fica em coral para saltar aos olhos na revisao final.
  s.addText([
    { text: "Link do vídeo no YouTube:   ", options: { color: TEAL } },
    { text: "colar aqui antes de fechar a entrega", options: { color: CORAL } },
  ], {
    x: L + 0.32, y: 6.34, w: W - 0.64, h: 0.5, isTextBox: true, margin: 0,
    valign: "middle", fontFace: TXT, fontSize: 12, bold: true,
  });
  rodape(s, 21);
  s.addNotes(
    "A estrutura do pitch segue os seis blocos sugeridos, com dois minutos " +
    "reservados à demonstração ao vivo — que é onde a solução se prova."
  );
}

/* ═══════════════════════════════════════════════════════════════════════ */
/* 22 — 8ª ENTREGA: RESULTADOS ALCANÇADOS                                  */
/* ═══════════════════════════════════════════════════════════════════════ */
{
  const s = pres.addSlide();
  s.background = { color: NAVY };
  s.addImage({ path: img("m2_ecg_branco.png"), x: 0, y: 0.28, w: 13.33, h: 0.72,
               transparency: 86 });

  s.addShape(pres.ShapeType.ellipse, {
    x: L, y: 1.14, w: 0.52, h: 0.52, fill: { color: TEAL },
  });
  s.addText("8", {
    x: L, y: 1.14, w: 0.52, h: 0.52, isTextBox: true,
    align: "center", valign: "middle", margin: 0,
    fontFace: TIT, fontSize: 17, bold: true, color: BRANCO,
  });
  s.addText("Resultados alcançados", {
    x: L + 0.72, y: 1.1, w: W - 0.72, h: 0.5, isTextBox: true, margin: 0,
    valign: "middle", fontFace: TIT, fontSize: 27, bold: true, color: BRANCO,
  });
  s.addText("Números reais, extraídos das fontes públicas em 12 meses — nenhum valor ilustrativo", {
    x: L + 0.72, y: 1.62, w: W - 0.72, h: 0.32, isTextBox: true, margin: 0,
    fontFace: TXT, fontSize: 12.5, color: "9FB6C0",
  });

  const numeros = [
    ["2.913.953", "internações processadas", TEAL],
    ["R$ 5,69 bi", "recurso executado analisado", TEAL],
    ["55.090", "leitos SUS mapeados", TEAL],
    ["645", "municípios cobertos", TEAL],
    ["15", "municípios com capacidade ultrapassada", CORAL],
    ["31", "municípios em faixa de atenção", AMBAR],
    ["20", "municípios com alta consistente (R² ≥ 0,5)", ROXO],
    ["7", "perguntas de negócio respondidas em português", TEAL],
  ];
  const cw = (W - 3 * 0.3) / 4;
  numeros.forEach(([v, r, cor], i) => {
    const col = i % 4, lin = Math.floor(i / 4);
    const x = L + col * (cw + 0.3);
    const y = 2.42 + lin * 1.72;
    s.addShape(pres.ShapeType.roundRect, {
      x, y, w: cw, h: 1.5, rectRadius: 0.08,
      fill: { color: NAVY2 }, line: { type: "none" },
    });
    s.addText(v, {
      x: x + 0.26, y: y + 0.2, w: cw - 0.52, h: 0.62, isTextBox: true, margin: 0,
      valign: "middle", fontFace: TIT, fontSize: 25, bold: true, color: cor,
    });
    s.addText(r, {
      x: x + 0.26, y: y + 0.82, w: cw - 0.52, h: 0.52, isTextBox: true, margin: 0,
      valign: "top", fontFace: TXT, fontSize: 10.5, color: "9FB6C0",
    });
  });

  s.addText(
    "Fontes: SIH/SUS (DATASUS) · CNES (Ministério da Saúde) · IBGE (Localidades e SIDRA) — jul/2025 a jun/2026",
    { x: L, y: 6.36, w: W, h: 0.32, isTextBox: true, margin: 0,
      fontFace: TXT, fontSize: 10, color: CINZA }
  );
  s.addNotes(
    "O ponto a enfatizar é que nenhum número aqui é " +
    "ilustrativo — todos saem de fonte pública verificável."
  );
}

/* ═══════════════════════════════════════════════════════════════════════ */
/* 23 — 8ª ENTREGA: CONCLUSÃO E PRÓXIMOS PASSOS                            */
/* ═══════════════════════════════════════════════════════════════════════ */
{
  const s = pres.addSlide();
  cabecalho(s, "Conclusão e próximos passos",
            "O que o MVP provou e para onde a solução evolui", 8);

  cartao(s, L, 1.62, W / 2 - 0.16, 2.5, CLARO);
  s.addText("O QUE O MVP PROVOU", {
    x: L + 0.3, y: 1.86, w: W / 2 - 0.76, h: 0.28, isTextBox: true, margin: 0,
    fontFace: TXT, fontSize: 9, bold: true, color: TEAL, charSpacing: 0.6,
  });
  lista(s, L + 0.3, 2.2, W / 2 - 0.76, 1.8, [
    "Dado público do SUS é utilizável — o obstáculo é de acesso, não de disponibilidade",
    "A pergunta em linguagem natural elimina a dependência de analista SQL",
    "Tratamento de dados é o que separa um ranking útil de um enganoso",
  ], 11.5);

  cartao(s, L + W / 2 + 0.16, 1.62, W / 2 - 0.16, 2.5, CLARO);
  s.addText("O QUE APRENDEMOS NO CAMINHO", {
    x: L + W / 2 + 0.46, y: 1.86, w: W / 2 - 0.76, h: 0.28, isTextBox: true, margin: 0,
    fontFace: TXT, fontSize: 9, bold: true, color: AMBAR, charSpacing: 0.6,
  });
  lista(s, L + W / 2 + 0.46, 2.2, W / 2 - 0.76, 1.8, [
    "A fonte pública mais importante não tem API — foi preciso construir o cliente",
    "A métrica estatística nem sempre aponta para a decisão certa (k=2 × k=4)",
    "Declarar a limitação do indicador vale mais do que escondê-la",
  ], 11.5);

  cartao(s, L, 4.3, W, 2.02, NAVY);
  s.addText("PRÓXIMOS PASSOS", {
    x: L + 0.34, y: 4.5, w: W - 0.68, h: 0.28, isTextBox: true, margin: 0,
    fontFace: TXT, fontSize: 9, bold: true, color: TEAL, charSpacing: 0.6,
  });
  const passos = [
    ["Curto prazo", "Ingestão agendada e cobertura das 27 unidades da federação"],
    ["Médio prazo", "Modelo preditivo de demanda com Oracle AutoML e alertas ativos ao gestor"],
    ["Longo prazo", "Ocupação medida via integração com a regulação estadual, substituindo a estimativa"],
  ];
  passos.forEach(([prazo, texto], i) => {
    const y = 4.84 + i * 0.44;
    s.addText(prazo, {
      x: L + 0.34, y, w: 1.7, h: 0.34, isTextBox: true, margin: 0,
      valign: "middle", fontFace: TXT, fontSize: 11, bold: true, color: TEAL,
    });
    s.addText(texto, {
      x: L + 2.14, y, w: W - 2.48, h: 0.34, isTextBox: true, margin: 0,
      valign: "middle", fontFace: TXT, fontSize: 11, color: "C9DBE2",
    });
  });

  s.addText(
    "“Transformar dado público em decisão de saúde na velocidade de uma pergunta.”",
    { x: L, y: 6.5, w: W, h: 0.4, isTextBox: true, margin: 0,
      align: "center", fontFace: TIT, fontSize: 14, bold: true, italic: true, color: TEAL }
  );
  rodape(s, 23);
  s.addNotes("Fechamento com a mensagem de impacto do projeto.");
}

/* ═══════════════════════════════════════════════════════════════════════ */
/* 24 — AGRADECIMENTOS                                                     */
/* ═══════════════════════════════════════════════════════════════════════ */
{
  const s = pres.addSlide();
  s.background = { color: NAVY };
  s.addImage({ path: img("m2_ecg_branco.png"), x: 0, y: 2.1, w: 13.33, h: 1.1,
               transparency: 80 });

  s.addText("Obrigado", {
    x: L, y: 3.42, w: W, h: 0.9, isTextBox: true, margin: 0, valign: "bottom",
    fontFace: TIT, fontSize: 44, bold: true, color: BRANCO,
  });
  s.addText(
    "À Oracle e à FIAP, pela proposta de desafio com dado real e problema real. " +
    "Ao professor tutor e ao scrum master, pela orientação ao longo das duas sprints.",
    { x: L, y: 4.42, w: 9.6, h: 0.7, isTextBox: true, margin: 0,
      fontFace: TXT, fontSize: 14, color: "C9DBE2", lineSpacingMultiple: 1.15 }
  );
  s.addShape(pres.ShapeType.rect, {
    x: L, y: 5.4, w: 1.6, h: 0.035, fill: { color: TEAL }, line: { type: "none" },
  });
  s.addText(
    "Giovanny da Silva Santana · RM 570646        Marco Aurélio da Silva Oliveira · RM 569185\n" +
    "Nélson Martins Diniz Neto · RM 573273        Pedro Henrique Inocente · RM 570201",
    { x: L, y: 5.66, w: W, h: 0.7, isTextBox: true, margin: 0,
      fontFace: TXT, fontSize: 12, color: "9FB6C0", lineSpacingMultiple: 1.3 }
  );
  s.addText("Equipe Vital Analytics · Turma 1TSCOA · Challenge Oracle + FIAP 2026", {
    x: L, y: 6.62, w: W, h: 0.32, isTextBox: true, margin: 0,
    fontFace: TXT, fontSize: 11, color: CINZA,
  });
  s.addNotes("Encerramento e agradecimentos.");
}

/* ═══════════════════════════════════════════════════════════════════════ */
pres.writeFile({ fileName: SAIDA }).then(() => {
  console.log("Deck gerado:", SAIDA);
});
