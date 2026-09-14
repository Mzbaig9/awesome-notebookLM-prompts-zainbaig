const fs = require('fs');
const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell, WidthType,
  AlignmentType, BorderStyle, ShadingType, HeightRule, PageBreak, LevelFormat,
  HeadingLevel, VerticalAlign, TabStopType
} = require('docx');

const FONT = 'Arial';
const W = 9360; // 6.5in text width in DXA
const GREY = 'E8EEF5';
const BLUE = '1F4E79';
const LIGHT = 'F3F6FA';

const border = { style: BorderStyle.SINGLE, size: 8, color: '7F7F7F' };
const borders = { top: border, bottom: border, left: border, right: border };
const noBorder = { style: BorderStyle.NONE, size: 0, color: 'FFFFFF' };
const noBorders = { top: noBorder, bottom: noBorder, left: noBorder, right: noBorder };

function p(text, opts = {}) {
  return new Paragraph({
    alignment: opts.align || AlignmentType.LEFT,
    spacing: { before: opts.before ?? 60, after: opts.after ?? 60, line: opts.line },
    children: [new TextRun({ text, font: FONT, size: opts.size || 22, bold: opts.bold, italics: opts.italic, color: opts.color })]
  });
}
function runs(parts, opts = {}) {
  return new Paragraph({
    spacing: { before: opts.before ?? 60, after: opts.after ?? 60 },
    children: parts.map(([t, o]) => new TextRun({ text: t, font: FONT, size: opts.size || 22, ...o }))
  });
}
function title(text) {
  return new Paragraph({
    alignment: AlignmentType.CENTER, spacing: { before: 0, after: 200 },
    children: [new TextRun({ text, font: FONT, size: 40, bold: true, color: BLUE })]
  });
}
function h(text) {
  return new Paragraph({
    spacing: { before: 240, after: 120 },
    border: { bottom: { style: BorderStyle.SINGLE, size: 12, color: BLUE, space: 2 } },
    children: [new TextRun({ text, font: FONT, size: 30, bold: true, color: BLUE })]
  });
}
function bullet(text, ref = 'bul') {
  return new Paragraph({
    numbering: { reference: ref, level: 0 }, spacing: { before: 40, after: 40 },
    children: [new TextRun({ text, font: FONT, size: 22 })]
  });
}
function check(text) {
  return new Paragraph({
    spacing: { before: 80, after: 80 },
    children: [new TextRun({ text: '☐  ' + text, font: FONT, size: 22 })]
  });
}
// Fill-in box: label row (shaded) + empty lined area
function box(label, hint, lines, opts = {}) {
  const rows = [];
  rows.push(new TableRow({
    children: [new TableCell({
      width: { size: W, type: WidthType.DXA }, borders, shading: { type: ShadingType.CLEAR, fill: opts.fill || GREY, color: 'auto' },
      margins: { top: 80, bottom: 80, left: 120, right: 120 },
      children: [
        new Paragraph({ spacing: { before: 0, after: hint ? 40 : 0 }, children: [new TextRun({ text: label, font: FONT, size: 24, bold: true, color: BLUE })] }),
        ...(hint ? [new Paragraph({ spacing: { before: 0, after: 0 }, children: [new TextRun({ text: hint, font: FONT, size: 20, italics: true, color: '404040' })] })] : [])
      ]
    })]
  }));
  const lineParas = [];
  for (let i = 0; i < lines; i++) {
    lineParas.push(new Paragraph({
      spacing: { before: 0, after: 0, line: 480 },
      border: { bottom: { style: BorderStyle.DOTTED, size: 6, color: '9E9E9E', space: 1 } },
      children: [new TextRun({ text: ' ', font: FONT, size: 22 })]
    }));
  }
  rows.push(new TableRow({
    children: [new TableCell({
      width: { size: W, type: WidthType.DXA }, borders, margins: { top: 60, bottom: 120, left: 160, right: 160 },
      children: lineParas
    })]
  }));
  return new Table({ width: { size: W, type: WidthType.DXA }, columnWidths: [W], rows });
}
function spacer(after = 160) { return new Paragraph({ spacing: { before: 0, after }, children: [new TextRun({ text: '' })] }); }
// Word bank strip
function bank(label, words) {
  return new Table({
    width: { size: W, type: WidthType.DXA }, columnWidths: [W],
    rows: [new TableRow({ children: [new TableCell({
      width: { size: W, type: WidthType.DXA }, borders: { top: { style: BorderStyle.SINGLE, size: 6, color: BLUE }, bottom: { style: BorderStyle.SINGLE, size: 6, color: BLUE }, left: { style: BorderStyle.SINGLE, size: 6, color: BLUE }, right: { style: BorderStyle.SINGLE, size: 6, color: BLUE } },
      shading: { type: ShadingType.CLEAR, fill: LIGHT, color: 'auto' }, margins: { top: 80, bottom: 80, left: 120, right: 120 },
      children: [runs([[label + '  ', { bold: true, color: BLUE }], [words, {}]], { size: 20, before: 0, after: 0 })]
    })] })]
  });
}
// Header info grid
function infoGrid(pairs) {
  const half = W / 2;
  const rows = [];
  for (let i = 0; i < pairs.length; i += 2) {
    const cells = [pairs[i], pairs[i + 1] || ''].map(lbl => new TableCell({
      width: { size: half, type: WidthType.DXA }, borders: noBorders, margins: { top: 100, bottom: 100, left: 60, right: 60 },
      children: [new Paragraph({
        tabStops: [{ type: TabStopType.RIGHT, position: half - 120 }],
        border: { bottom: { style: BorderStyle.SINGLE, size: 6, color: '7F7F7F', space: 1 } },
        children: [new TextRun({ text: lbl ? lbl + ' : ' : '', font: FONT, size: 22, bold: true })]
      })]
    }));
    rows.push(new TableRow({ children: cells }));
  }
  return new Table({ width: { size: W, type: WidthType.DXA }, columnWidths: [half, half], rows });
}
// Three-column overview map of the text
function textMap() {
  const c = W / 3;
  const cell = (head, body, fill) => new TableCell({
    width: { size: c, type: WidthType.DXA }, borders, verticalAlign: VerticalAlign.TOP,
    shading: { type: ShadingType.CLEAR, fill, color: 'auto' }, margins: { top: 100, bottom: 100, left: 120, right: 120 },
    children: [
      new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 0, after: 80 }, children: [new TextRun({ text: head, font: FONT, size: 24, bold: true, color: BLUE })] }),
      ...body.map(t => new Paragraph({ spacing: { before: 20, after: 20 }, children: [new TextRun({ text: t, font: FONT, size: 20 })] }))
    ]
  });
  return new Table({
    width: { size: W, type: WidthType.DXA }, columnWidths: [c, c, c],
    rows: [new TableRow({ children: [
      cell('1. INTRODUCTION', ['1 paragraphe', 'J’accroche le lecteur.', 'Je nomme mon sujet.', 'J’annonce mes aspects.'], LIGHT),
      cell('2. DÉVELOPPEMENT', ['2 ou 3 paragraphes', 'Un intertitre par aspect.', 'Une idée principale par paragraphe.', 'Des exemples et des explications.'], 'FFFFFF'),
      cell('3. CONCLUSION', ['1 paragraphe', 'Je rappelle mon sujet.', 'Je résume mes aspects.', 'Je termine avec une phrase forte.'], LIGHT)
    ] })]
  });
}

const children = [];

// ---------- PAGE 1 : couverture / plan général ----------
children.push(title('Mon plan de texte'));
children.push(p('Introduction, développement, conclusion et intertitres', { align: AlignmentType.CENTER, size: 24, italic: true, color: '404040', after: 200 }));
children.push(infoGrid(['Nom', 'Groupe', 'Date', 'Type de texte (descriptif, explicatif, informatif)', 'Titre provisoire', 'Pour qui j’écris (destinataire)']));
children.push(spacer(120));
children.push(h('Étape 1 : Je prépare mon texte'));
children.push(runs([['Mon intention : ', { bold: true }], ['je veux informer, décrire ou expliquer …  ______________________________________________', {}]]));
children.push(runs([['Mon sujet en un mot ou une expression : ', { bold: true }], ['____________________________________________', {}]]));
children.push(runs([['Mes trois aspects (ce dont je vais parler) :  ', { bold: true }], ['1. _______________   2. _______________   3. _______________', {}]]));
children.push(spacer(120));
children.push(h('La carte de mon texte'));
children.push(textMap());
children.push(spacer(120));
children.push(bank('Rappel :', 'un titre en haut, un intertitre avant chaque partie du développement, un espace (blanc) entre les paragraphes.'));
children.push(new Paragraph({ children: [new PageBreak()] }));

// ---------- PAGE 2 : introduction ----------
children.push(h('Étape 2 : Mon introduction (1 paragraphe)'));
children.push(p('Mon introduction contient trois phrases ou plus. Chaque partie a un rôle.', { italic: true, color: '404040' }));
children.push(box('a) J’accroche le lecteur (sujet amené)', 'Une question, un fait surprenant, une petite anecdote ou une phrase qui donne envie de lire.', 3));
children.push(spacer(100));
children.push(box('b) Je nomme mon sujet (sujet posé)', 'De quoi mon texte parle-t-il ? Une phrase claire.', 2));
children.push(spacer(100));
children.push(box('c) J’annonce mes aspects (sujet divisé)', 'Je nomme, dans l’ordre, les 2 ou 3 aspects que je vais présenter. Ce sont mes futurs intertitres.', 3));
children.push(spacer(100));
children.push(bank('Mots utiles :', 'Savais-tu que … ?  ·  As-tu déjà … ?  ·  Dans ce texte, je vais te présenter …  ·  Tu découvriras d’abord …, ensuite …, et enfin …'));
children.push(new Paragraph({ children: [new PageBreak()] }));

// ---------- PAGES 3-4 : développement ----------
const devSection = (n) => [
  h(`Étape 3 : Mon développement, partie ${n}`),
  box(`Intertitre ${n}`, 'Un titre court (2 à 5 mots) qui annonce l’aspect de ce paragraphe. Pas de phrase complète, pas de point final.', 1),
  spacer(80),
  box('Mon idée principale', 'La première phrase de mon paragraphe dit de quoi je parle.', 2),
  spacer(80),
  box('Mes idées secondaires', 'Deux ou trois phrases qui expliquent, décrivent ou donnent des exemples. Mes informations sont vraies et vérifiées.', 5),
  spacer(80),
  box('Mon marqueur de relation pour ce paragraphe', 'Le mot qui relie ce paragraphe au reste du texte.', 1),
  spacer(100)
];
children.push(...devSection(1));
children.push(bank('Mots utiles :', 'D’abord  ·  Premièrement  ·  Pour commencer  ·  Par exemple  ·  En effet  ·  C’est-à-dire  ·  De plus'));
children.push(new Paragraph({ children: [new PageBreak()] }));
children.push(...devSection(2));
children.push(bank('Mots utiles :', 'Ensuite  ·  Deuxièmement  ·  Puis  ·  De plus  ·  Aussi  ·  Par ailleurs  ·  Par exemple'));
children.push(new Paragraph({ children: [new PageBreak()] }));
children.push(...devSection(3));
children.push(bank('Mots utiles :', 'Enfin  ·  Troisièmement  ·  Finalement  ·  Pour terminer  ·  De plus  ·  Par exemple'));
children.push(p('Si mon texte a seulement deux aspects, je laisse cette page vide.', { italic: true, color: '404040', size: 20, before: 120 }));
children.push(new Paragraph({ children: [new PageBreak()] }));

// ---------- PAGE 6 : conclusion ----------
children.push(h('Étape 4 : Ma conclusion (1 paragraphe)'));
children.push(p('Ma conclusion n’apporte pas de nouvelle information. Elle ferme mon texte.', { italic: true, color: '404040' }));
children.push(box('a) Je rappelle mon sujet et je résume mes aspects', 'En une ou deux phrases, je redis l’essentiel avec d’autres mots.', 4));
children.push(spacer(100));
children.push(box('b) Ma phrase de fermeture', 'Un souhait, un conseil, une question au lecteur ou une idée pour aller plus loin (ouverture).', 3));
children.push(spacer(100));
children.push(bank('Mots utiles :', 'En conclusion  ·  Pour terminer  ·  En résumé  ·  Bref  ·  Finalement  ·  Maintenant, tu sais que …  ·  J’espère que …'));
children.push(spacer(160));
children.push(h('Étape 5 : Mon titre final'));
children.push(p('Je choisis mon titre à la fin, quand je sais vraiment de quoi parle mon texte. Il est court et il donne envie de lire.', { italic: true, color: '404040' }));
children.push(box('Mon titre', '', 1));
children.push(new Paragraph({ children: [new PageBreak()] }));

// ---------- PAGE 7 : liste de vérification ----------
children.push(h('Étape 6 : Je révise mon texte'));
children.push(p('Je coche chaque case après avoir vérifié dans mon texte, pas dans ma tête.', { italic: true, color: '404040' }));
children.push(p('La structure', { bold: true, color: BLUE, before: 160 }));
children.push(check('Mon texte a un titre.'));
children.push(check('Mon introduction accroche le lecteur, nomme le sujet et annonce mes aspects.'));
children.push(check('Chaque partie du développement a un intertitre qui correspond à son contenu.'));
children.push(check('Chaque paragraphe présente une seule idée principale, avec des exemples ou des explications.'));
children.push(check('Mes paragraphes sont séparés par un espace (un blanc).'));
children.push(check('Ma conclusion rappelle le sujet, résume mes aspects et se termine par une phrase forte.'));
children.push(check('L’ordre de mes aspects dans l’introduction est le même que dans le développement.'));
children.push(p('La cohérence', { bold: true, color: BLUE, before: 160 }));
children.push(check('J’utilise des marqueurs de relation (d’abord, ensuite, enfin, par exemple, en conclusion).'));
children.push(check('Je reprends mon sujet avec des pronoms ou des synonymes pour éviter les répétitions.'));
children.push(check('Toutes mes phrases parlent de mon sujet. J’ai enlevé ce qui n’a pas rapport.'));
children.push(check('Je garde le même temps de verbe dans tout le texte (surtout le présent).'));
children.push(p('La langue', { bold: true, color: BLUE, before: 160 }));
children.push(check('Chaque phrase commence par une majuscule et finit par un point, un point d’interrogation ou un point d’exclamation.'));
children.push(check('J’ai vérifié les accords dans le groupe du nom (déterminant, nom, adjectif).'));
children.push(check('J’ai vérifié l’accord du verbe avec son sujet.'));
children.push(check('J’ai vérifié l’orthographe des mots dans le dictionnaire ou la liste orthographique.'));
children.push(check('J’ai relu mon texte à voix basse et il se lit bien.'));
children.push(new Paragraph({ children: [new PageBreak()] }));

// ---------- PAGE 8 : note à l'enseignant(e) ----------
children.push(h('Note pour l’enseignante ou l’enseignant'));
children.push(p('Ce gabarit accompagne la compétence « Écrire des textes variés » du Programme de formation de l’école québécoise (français, langue d’enseignement, primaire). Il suit la démarche d’écriture du programme : planifier, rédiger, réviser, corriger, puis mettre au propre et diffuser. Chaque page du gabarit correspond à une étape de cette démarche.', { after: 120 }));
children.push(p('Attentes de la Progression des apprentissages ciblées', { bold: true, color: BLUE, before: 160 }));
children.push(bullet('Organisation et cohérence du texte : structure en introduction, développement et conclusion, regroupement des idées en paragraphes, séparation des paragraphes par un blanc.'));
children.push(bullet('Marques d’organisation du texte : titre, intertitres, paragraphes, et éléments visuels au besoin.'));
children.push(bullet('Marqueurs de relation et organisateurs textuels qui marquent l’ordre, l’ajout, l’exemple et la conclusion.'));
children.push(bullet('Reprise de l’information par des pronoms et des synonymes.'));
children.push(bullet('Stratégies de planification : préciser l’intention et le destinataire, choisir le type de texte, dresser un plan avant de rédiger.'));
children.push(bullet('Stratégies de révision et de correction : relire pour vérifier la structure, la cohérence et l’orthographe à l’aide d’une liste de vérification.'));
children.push(p('Adaptation selon le cycle', { bold: true, color: BLUE, before: 160 }));
children.push(bullet('2e cycle (3e et 4e année) : viser deux aspects plutôt que trois, fournir les intertitres ou les choisir en groupe, garder le sujet amené facultatif, réviser avec les cases de la section « structure » seulement.'));
children.push(bullet('3e cycle (5e et 6e année) : utiliser le gabarit au complet, exiger que l’élève formule ses propres intertitres et respecte l’ordre annoncé dans le sujet divisé, utiliser la liste de vérification complète.'));
children.push(bullet('Élèves en difficulté : remplir la carte du texte (page 1) oralement avec l’élève avant l’écriture, puis un seul paragraphe de développement à la fois.'));
children.push(p('Suggestion d’utilisation', { bold: true, color: BLUE, before: 160 }));
children.push(p('Modeler d’abord le gabarit en grand groupe avec un texte court lu en classe : faire repérer le titre, les intertitres, les trois parties et les marqueurs de relation, puis remplir le gabarit à rebours à partir de ce texte. Les élèves remplissent ensuite leur propre plan avant la rédaction, rédigent à partir du plan, et terminent par la liste de vérification en dyade avant la correction par l’enseignante ou l’enseignant.', { after: 120 }));
children.push(p('Dar Al-Ulum Montréal, français langue d’enseignement, primaire.', { size: 18, italic: true, color: '7F7F7F', before: 240 }));

const doc = new Document({
  creator: 'Dar Al-Ulum Montréal',
  title: 'Mon plan de texte',
  styles: { default: { document: { run: { font: FONT, size: 22 } } } },
  numbering: { config: [{ reference: 'bul', levels: [{ level: 0, format: LevelFormat.BULLET, text: '•', alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 540, hanging: 270 } } } }] }] },
  sections: [{
    properties: { page: { size: { width: 12240, height: 15840 }, margin: { top: 1080, bottom: 1080, left: 1440, right: 1440 } } },
    children
  }]
});
Packer.toBuffer(doc).then(buf => { fs.writeFileSync('Mon_plan_de_texte_primaire.docx', buf); console.log('ok', buf.length); });
