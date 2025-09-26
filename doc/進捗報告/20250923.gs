/**
* @OnlyCurrentDoc
* このスクリプトは、指定されたデザインテンプレートに基づきGoogleスライドを自動生成します。
* Version: 17.0 (Generalized Version)
* Prompt Design: まじん式プロンプト
* Author: Googleスライド自動生成マスター
* Description: 指定されたslideData配列とカスタムメニューの設定に基づき、Googleのデザイン原則に準拠したスライドを生成します。
*/


// --- 1. 実行設定 ---
const SETTINGS = {
SHOULD_CLEAR_ALL_SLIDES: true,
TARGET_PRESENTATION_ID: null
};

// --- 2. マスターデザイン設定 (Pixel Perfect Ver.) ---
const CONFIG = {
BASE_PX: { W: 960, H: 540 },

// レイアウトの基準となる不変のpx値
POS_PX: {
titleSlide: {
logo:       { left: 55,  top: 105,  width: 135 },
title:      { left: 50,  top: 200, width: 830, height: 90 },
date:       { left: 50,  top: 450, width: 250, height: 40 },
},

// 共通ヘッダーを持つ各スライド  
contentSlide: {  
  headerLogo:     { right: 20, top: 20, width: 75 },  
  title:          { left: 25, top: 50,  width: 830, height: 65 },  
  titleUnderline: { left: 25, top: 118, width: 260, height: 4 },  
  subhead:        { left: 25, top: 130, width: 830, height: 40 },  
  body:           { left: 25, top: 172, width: 910, height: 290 },  
  twoColLeft:     { left: 25,  top: 172, width: 440, height: 290 },  
  twoColRight:    { left: 495, top: 172, width: 440, height: 290 }  
},  
compareSlide: {  
  headerLogo:     { right: 20, top: 20, width: 75 },  
  title:          { left: 25, top: 50,  width: 830, height: 65 },  
  titleUnderline: { left: 25, top: 118, width: 260, height: 4 },  
  subhead:        { left: 25, top: 130, width: 830, height: 40 },  
  leftBox:        { left: 25,  top: 152, width: 430, height: 290 },  
  rightBox:       { left: 485, top: 152, width: 430, height: 290 }  
},  
progressSlide: {  
  headerLogo:     { right: 20, top: 20, width: 75 },  
  title:          { left: 25, top: 50,  width: 830, height: 65 },  
  titleUnderline: { left: 25, top: 118, width: 260, height: 4 },  
  subhead:        { left: 25, top: 130, width: 830, height: 40 },  
  area:           { left: 25, top: 172, width: 910, height: 290 }  
},

sectionSlide: {  
  title:      { left: 55, top: 230, width: 840, height: 80 },  
  ghostNum:   { left: 35, top: 120, width: 400, height: 200 }
},

footer: {  
  leftText:  { left: 15, top: 505, width: 250, height: 20 },  
  rightPage: { right: 15, top: 505, width: 50,  height: 20 }  
},  
bottomBar: { left: 0, top: 534, width: 960, height: 6 }  

},

FONTS: {
family: 'Arial', // デフォルト、プロパティから動的に変更可能
sizes: {
title: 40, date: 16, sectionTitle: 38, contentTitle: 28, subhead: 18,
body: 14, footer: 9, chip: 11, laneTitle: 13, small: 10,
processStep: 14, axis: 12, ghostNum: 180
}
},
COLORS: {
primary_color: '#4285F4', text_primary: '#333333', background_white: '#FFFFFF',
background_gray: '#f8f9fa', faint_gray: '#e8eaed', lane_title_bg: '#f8f9fa',
table_header_bg: '#f8f9fa', lane_border: '#dadce0', card_bg: '#ffffff',
card_border: '#dadce0', neutral_gray: '#9e9e9e', ghost_gray: '#efefed'
},
DIAGRAM: {
laneGap_px: 24, lanePad_px: 10, laneTitle_h_px: 30, cardGap_px: 12,
cardMin_h_px: 48, cardMax_h_px: 70, arrow_h_px: 10, arrowGap_px: 8
},

LOGOS: {
header: '',
closing: ''
},

FOOTER_TEXT: ``
};

// --- 3. スライドデータ（このブロックを生成内容で完全置換） ---
const slideData = [
  { type: 'title', title: 'RAG・AIエージェント実践入門 進捗報告', date: '2025.09.23', notes: '本日の進捗報告では RAG パイプラインの構築状況と高度化の要点を整理し、検索方針と Graph RAG 連携の設計を共有します。' },
  {
    type: 'content',
    title: 'アジェンダ',
    points: ['RAGパイプラインの構築', '高度なRAG技術', 'doc_preprocessor_hybrid 概要', 'ドキュメント検索とGraph RAG'],
    notes: '章立てに沿って全体像から詳細、検索方針、Graph RAG の順で説明します。'
  },

  { type: 'section', title: '1. RAGパイプラインの構築', notes: 'まずはドキュメント読み込みからベクトル化と格納までの標準パイプラインを確認します。' },
  {
    type: 'content',
    title: 'Document loader の要点',
    points: ['テキスト PDF Web など多形式対応', 'DirectoryLoader で一括読み込み', 'Unstructured で構造保持とメタデータ', 'Elements モードと精度選択'],
    notes: '多様な形式を安定して取り込み、構造とメタデータを保持することが後段の分割と検索精度に効きます。'
  },
  {
    type: 'content',
    title: 'Transformer と分割戦略',
    points: ['階層分割 chunk 1000 overlap 200', 'Token ベース分割の選択', 'HTML2Text で前処理', 'メタデータ付与と正規化'],
    notes: '分割は再現性のあるルールを採用し、サイズと重なりを調整して検索時のリコールを担保します。'
  },
  {
    type: 'content',
    title: 'Embedding と Vector store',
    points: ['埋め込みは OpenAI bge ST から選定', 'Chroma で高速ベクトル検索', '類似度と k のチューニング', '生成前の要約整形'],
    notes: '用途とコストに応じて埋め込みを選び、Chroma を基盤として取得件数や整形手順を調整します。'
  },

  { type: 'section', title: '2. 高度なRAG技術', notes: 'HyDE と MultiQuery による取得の強化、ハイブリッドとリランクの設計を扱います。' },
  {
    type: 'content',
    title: 'HyDE と MultiQuery の活用',
    points: ['HyDE で仮想回答を生成して検索', 'MultiQuery でクエリ多様化', '空振り時のみ発火して再取得', '網羅性と精度の両立'],
    notes: '初期取得が不足した場合にのみ HyDE や MultiQuery を用いて再取得し、無駄なコストを抑えつつ再現率を高めます。'
  },
  {
    type: 'compare',
    title: 'BM25 と ベクトル検索',
    leftTitle: 'BM25 検索',
    rightTitle: 'ベクトル検索',
    leftItems: ['語一致とレア語に強い', '高速軽量で説明容易', 'スペル揺れに弱い', '同義語や文脈理解は弱い'],
    rightItems: ['言い換えや多言語に強い', '意味的な概念検索', 'モデル依存で説明が難しい', 'メモリコストが高め'],
    notes: 'BM25 は語一致に強く軽量、ベクトルは意味理解に強い。両者の特性を踏まえハイブリッドで相互補完します。'
  },
  {
    type: 'content',
    title: 'RAG Fusion とリランク',
    points: ['EnsembleRetriever で統合', 'RRF または重み付き融合', 'Cross Encoder や Cohere で再ランキング', 'コストと精度の調整'],
    notes: '初期取得を融合後、必要時のみリランクを適用して品質を上げつつ遅延と費用を最適化します。'
  },

  { type: 'section', title: '3. doc_preprocessor_hybrid 概要', notes: 'EVO.SHIP API を対象にルール抽出と限定的 LLM 補強で構造化成果物を生成します。' },
  {
    type: 'content',
    title: '目的と出力物',
    points: ['ルール抽出と限定的 LLM 補強', 'structured_api と enriched JSON を生成', 'graph_payload と vector_chunks を出力', '監査可能なソース断片とハッシュ'],
    notes: '決定的な抽出を優先し、不足は差分適用で補強。構造化 JSON やグラフペイロードを成果物として出力します。'
  },
  {
    type: 'content',
    title: '処理フローの概略',
    points: ['CLI から pipeline を起動', 'ルール抽出後に必要箇所のみ LLM 補強', 'グラフ構築とベクターチャンク生成', 'Neo4j と Chroma へ任意保存'],
    notes: 'CLI から一括実行し、既存成果物を再利用しながら出力を生成。必要に応じて外部ストアへ保存します。'
  },
  {
    type: 'progress',
    title: '実装進捗',
    items: [
      { label: 'ルール抽出強化', percent: 80 },
      { label: 'LLM 補強', percent: 60 },
      { label: 'グラフ構築', percent: 70 },
      { label: 'Neo4j 保存', percent: 50 },
      { label: 'Chroma 保存', percent: 50 }
    ],
    notes: '主要機能は概ね実装済みで、外部保存と評価基盤の整備を継続しています。'
  },

  { type: 'section', title: '4. ドキュメント検索の方針', notes: '標準フローとプロファイルを定義し、状況に応じて手法の重みを調整します。' },
  {
    type: 'content',
    title: '標準フロー',
    points: ['メタデータ前処理', 'BM25 50 と Dense 50 を並列取得', 'RRF または重み付きで統合', '軽量整形とリランク 30 から 5', '不足時のみ MultiQuery HyDE'],
    notes: 'まず並列で BM25 と Dense を取得し融合、必要に応じリランク。空振り時のみ再取得系を発火させます。'
  },
  {
    type: 'content',
    title: 'プロファイルと選択指針',
    points: ['低遅延 BM25 20 Dense 20 リランク無し', '標準 BM25 50 Dense 50 リランク適用', '高精度 MultiQuery HyDE 追加', '固有名詞中心は BM25 重みと k を増加', '抽象質問は Dense 重みを増加'],
    notes: 'SLA と質問特性に応じてプロファイルを切替え、BM25 と Dense の重みを適切に調整します。'
  },

  { type: 'section', title: '5. Neo4j を用いた Graph RAG', notes: '構造情報をグラフ化し、検索の根拠提示や依存関係の追跡に活用します。' },
  {
    type: 'content',
    title: 'Graph RAG の役割',
    points: ['Object Method Type Parameter をノード化', 'BELONGS_TO RETURNS HAS_PARAMETER HAS_TYPE', '構造検索と根拠提示を支援', '本文はベクトルDBに分離'],
    notes: '構造はグラフで管理し、本文はベクトルDBに保持。役割分担で可観測性と拡張性を両立します。'
  },
  {
    type: 'content',
    title: 'Cypher パターン例',
    points: ['引数名からメソッド候補を特定', '型に紐づく API 一覧を取得', '階層探索でメソッドと引数を収集'],
    notes: '典型的な Cypher パターンを用いて対象集合を作成し、後段のベクトル検索へ繋ぎます。'
  },
  {
    type: 'content',
    title: 'LangChain と LlamaIndex 連携',
    points: ['Neo4j で候補取得しクエリ拡張', 'Chroma で該当チャンクを検索', 'LCEL で生成まで連結', 'サブセット再インデックスで高速化'],
    notes: 'グラフから候補を抽出し、ベクトル検索と組み合わせて生成まで到達する統合フローを運用します。'
  },

  { type: 'closing', notes: '以上で進捗報告は終了です。次回は評価ログと運用プロファイルの改善結果を共有します。' }
];


// --- 4. メイン実行関数（エントリーポイント） ---
let __SECTION_COUNTER = 0; // 章番号カウンタ（ゴースト数字用）

/**
 * プレゼンテーション生成のメイン関数
 * 実行時間: 約3-6分
 * 最大スライド数: 50枚
 */
function generatePresentation() {
  const userSettings = PropertiesService.getScriptProperties().getProperties();
  if (userSettings.primaryColor) CONFIG.COLORS.primary_color = userSettings.primaryColor;
  if (userSettings.footerText) CONFIG.FOOTER_TEXT = userSettings.footerText;
  if (userSettings.headerLogoUrl) CONFIG.LOGOS.header = userSettings.headerLogoUrl;
  if (userSettings.closingLogoUrl) CONFIG.LOGOS.closing = userSettings.closingLogoUrl;
  if (userSettings.fontFamily) CONFIG.FONTS.family = userSettings.fontFamily;

  let presentation;
  try {
    presentation = SETTINGS.TARGET_PRESENTATION_ID
      ? SlidesApp.openById(SETTINGS.TARGET_PRESENTATION_ID)
      : SlidesApp.getActivePresentation();
    if (!presentation) throw new Error('対象のプレゼンテーションが見つかりません。');

    if (SETTINGS.SHOULD_CLEAR_ALL_SLIDES) {
      const slides = presentation.getSlides();
      for (let i = slides.length - 1; i >= 0; i--) slides[i].remove();
    }

    __SECTION_COUNTER = 0;

    const layout = createLayoutManager(presentation.getPageWidth(), presentation.getPageHeight());

    let pageCounter = 0;
    for (const data of slideData) {
      try {
        const generator = slideGenerators[data.type];
        if (data.type !== 'title' && data.type !== 'closing') pageCounter++;
        if (generator) {
          const slide = presentation.appendSlide(SlidesApp.PredefinedLayout.BLANK);
          generator(slide, data, layout, pageCounter);

          if (data.notes) {
            try {
              const notesShape = slide.getNotesPage().getSpeakerNotesShape();
              if (notesShape) {
                notesShape.getText().setText(data.notes);
              }
            } catch (e) {
              Logger.log(`スピーカーノートの設定に失敗しました: ${e.message}`);
            }
          }
        }
      } catch (e) {
        Logger.log(`スライドの生成をスキップしました (エラー発生)。 Type: ${data.type}, Title: ${data.title || 'N/A'}, Error: ${e.message}`);
      }
    }

  } catch (e) {
    Logger.log(`処理が中断されました: ${e.message}\nStack: ${e.stack}`);
  }
}

// --- 5. カスタムメニュー設定関数 ---
function onOpen(e) {
  SlidesApp.getUi()
    .createMenu('カスタム設定')
    .addItem('🎨 スライドを生成', 'generatePresentation')
    .addSeparator()
    .addSubMenu(SlidesApp.getUi().createMenu('⚙️ 設定')
      .addItem('プライマリカラー', 'setPrimaryColor')
      .addItem('フォント', 'setFont')
      .addItem('フッターテキスト', 'setFooterText')
      .addItem('ヘッダーロゴ', 'setHeaderLogo')
      .addItem('クロージングロゴ', 'setClosingLogo'))
    .addItem('🔄 リセット', 'resetSettings')
    .addToUi();
}

// プライマリカラー設定
function setPrimaryColor() {
  const ui = SlidesApp.getUi();
  const props = PropertiesService.getScriptProperties();
  const currentValue = props.getProperty('primaryColor') || '#4285F4';
  
  const result = ui.prompt(
    'プライマリカラー設定',
    `カラーコードを入力してください（例: #4285F4）\n現在値: ${currentValue}\n\n空欄で既定値にリセットされます。`,
    ui.ButtonSet.OK_CANCEL
  );
  
  if (result.getSelectedButton() === ui.Button.OK) {
    const value = result.getResponseText().trim();
    if (value === '') {
      props.deleteProperty('primaryColor');
      ui.alert('プライマリカラーをリセットしました。');
    } else {
      props.setProperty('primaryColor', value);
      ui.alert('プライマリカラーを保存しました。');
    }
  }
}

// フォント設定（プルダウン形式）
function setFont() {
  const ui = SlidesApp.getUi();
  const props = PropertiesService.getScriptProperties();
  const currentValue = props.getProperty('fontFamily') || 'Arial';
  
  const fonts = [
    'Arial',
    'Noto Sans JP',
    'M PLUS 1p',
    'Noto Serif JP'
  ];
  
  const fontList = fonts.map((font, index) => 
    `${index + 1}. ${font}${font === currentValue ? ' (現在)' : ''}`
  ).join('\n');
  
  const result = ui.prompt(
    'フォント設定',
    `使用するフォントの番号を入力してください:\n\n${fontList}\n\n※ 空欄で既定値（Arial）にリセット`,
    ui.ButtonSet.OK_CANCEL
  );
  
  if (result.getSelectedButton() === ui.Button.OK) {
    const input = result.getResponseText().trim();
    if (input === '') {
      props.deleteProperty('fontFamily');
      ui.alert('フォントをリセットしました（Arial）。');
    } else {
      const index = parseInt(input) - 1;
      if (index >= 0 && index < fonts.length) {
        props.setProperty('fontFamily', fonts[index]);
        ui.alert(`フォントを「${fonts[index]}」に設定しました。`);
      } else {
        ui.alert('無効な番号です。設定をキャンセルしました。');
      }
    }
  }
}

// フッターテキスト設定
function setFooterText() {
  const ui = SlidesApp.getUi();
  const props = PropertiesService.getScriptProperties();
  const currentValue = props.getProperty('footerText') || '未設定';
  
  const result = ui.prompt(
    'フッターテキスト設定',
    `フッターに表示するテキストを入力してください\n現在値: ${currentValue}\n\n空欄でリセットされます。`,
    ui.ButtonSet.OK_CANCEL
  );
  
  if (result.getSelectedButton() === ui.Button.OK) {
    const value = result.getResponseText().trim();
    if (value === '') {
      props.deleteProperty('footerText');
      ui.alert('フッターテキストをリセットしました。');
    } else {
      props.setProperty('footerText', value);
      ui.alert('フッターテキストを保存しました。');
    }
  }
}

// ヘッダーロゴ設定
function setHeaderLogo() {
  const ui = SlidesApp.getUi();
  const props = PropertiesService.getScriptProperties();
  const currentValue = props.getProperty('headerLogoUrl') || '未設定';
  
  const result = ui.prompt(
    'ヘッダーロゴ設定',
    `ヘッダーロゴのURLを入力してください\n現在値: ${currentValue}\n\n空欄でリセットされます。`,
    ui.ButtonSet.OK_CANCEL
  );
  
  if (result.getSelectedButton() === ui.Button.OK) {
    const value = result.getResponseText().trim();
    if (value === '') {
      props.deleteProperty('headerLogoUrl');
      ui.alert('ヘッダーロゴをリセットしました。');
    } else {
      props.setProperty('headerLogoUrl', value);
      ui.alert('ヘッダーロゴを保存しました。');
    }
  }
}

// クロージングロゴ設定
function setClosingLogo() {
  const ui = SlidesApp.getUi();
  const props = PropertiesService.getScriptProperties();
  const currentValue = props.getProperty('closingLogoUrl') || '未設定';
  
  const result = ui.prompt(
    'クロージングロゴ設定',
    `クロージングページのロゴURLを入力してください\n現在値: ${currentValue}\n\n空欄でリセットされます。`,
    ui.ButtonSet.OK_CANCEL
  );
  
  if (result.getSelectedButton() === ui.Button.OK) {
    const value = result.getResponseText().trim();
    if (value === '') {
      props.deleteProperty('closingLogoUrl');
      ui.alert('クロージングロゴをリセットしました。');
    } else {
      props.setProperty('closingLogoUrl', value);
      ui.alert('クロージングロゴを保存しました。');
    }
  }
}

function resetSettings() {
  const ui = SlidesApp.getUi();
  const result = ui.alert('設定のリセット', 'すべてのカスタム設定をリセットしますか？', ui.ButtonSet.YES_NO);
  
  if (result === ui.Button.YES) {
    PropertiesService.getScriptProperties().deleteAllProperties();
    ui.alert('すべての設定をリセットしました。\n\n• プライマリカラー: #4285F4\n• フォント: Arial\n• フッター/ロゴ: 未設定');
  }
}

// --- 6. スライド生成ディスパッチャ ---
const slideGenerators = {
  title: createTitleSlide,
  section: createSectionSlide,
  content: createContentSlide,
  compare: createCompareSlide,
  progress: createProgressSlide,
  closing: createClosingSlide,
};

// --- 7. スライド生成関数群（未使用パターンは省略） ---
function createTitleSlide(slide, data, layout) {
  slide.getBackground().setSolidFill(CONFIG.COLORS.background_white);

  const logoRect = layout.getRect('titleSlide.logo');
  try {
    const logo = slide.insertImage(CONFIG.LOGOS.header);
    const aspect = logo.getHeight() / logo.getWidth();
    logo.setLeft(logoRect.left).setTop(logoRect.top).setWidth(logoRect.width).setHeight(logoRect.width * aspect);
  } catch (e) {
    // 画像挿入に失敗した場合はスキップして他の要素を描画
  }

  const titleRect = layout.getRect('titleSlide.title');
  const titleShape = slide.insertShape(SlidesApp.ShapeType.TEXT_BOX, titleRect.left, titleRect.top, titleRect.width, titleRect.height);
  setStyledText(titleShape, data.title, { size: CONFIG.FONTS.sizes.title, bold: true });

  const dateRect = layout.getRect('titleSlide.date');
  const dateShape = slide.insertShape(SlidesApp.ShapeType.TEXT_BOX, dateRect.left, dateRect.top, dateRect.width, dateRect.height);
  dateShape.getText().setText(data.date || '');
  applyTextStyle(dateShape.getText(), { size: CONFIG.FONTS.sizes.date });

  drawBottomBar(slide, layout);
}

function createSectionSlide(slide, data, layout, pageNum) {
  slide.getBackground().setSolidFill(CONFIG.COLORS.background_gray);

  // 透かし番号：sectionNo > タイトル先頭の数字 > 自動連番
  __SECTION_COUNTER++;
  const parsedNum = (() => {
    if (Number.isFinite(data.sectionNo)) return Number(data.sectionNo);
    const m = String(data.title || '').match(/^\s*(\d+)[\.．]/);
    return m ? Number(m[1]) : __SECTION_COUNTER;
  })();
  const num = String(parsedNum).padStart(2, '0');

  const ghostRect = layout.getRect('sectionSlide.ghostNum');
  const ghost = slide.insertShape(SlidesApp.ShapeType.TEXT_BOX, ghostRect.left, ghostRect.top, ghostRect.width, ghostRect.height);
  ghost.getText().setText(num);
  applyTextStyle(ghost.getText(), { size: CONFIG.FONTS.sizes.ghostNum, color: CONFIG.COLORS.ghost_gray, bold: true });
  try { ghost.setContentAlignment(SlidesApp.ContentAlignment.MIDDLE); } catch(e) {}

  const titleRect = layout.getRect('sectionSlide.title');
  const titleShape = slide.insertShape(SlidesApp.ShapeType.TEXT_BOX, titleRect.left, titleRect.top, titleRect.width, titleRect.height);
  titleShape.setContentAlignment(SlidesApp.ContentAlignment.MIDDLE);
  setStyledText(titleShape, data.title, { size: CONFIG.FONTS.sizes.sectionTitle, bold: true, align: SlidesApp.ParagraphAlignment.CENTER });

  addCucFooter(slide, layout, pageNum);
}

// content（1/2カラム + 小見出し + 画像）
function createContentSlide(slide, data, layout, pageNum) {
  slide.getBackground().setSolidFill(CONFIG.COLORS.background_white);
  drawStandardTitleHeader(slide, layout, 'contentSlide', data.title);
  const dy = 0; // アジェンダパターンでは小見出しを使用しない

  // アジェンダ安全装置
  const isAgenda = isAgendaTitle(data.title || '');
  let points = Array.isArray(data.points) ? data.points.slice(0) : [];
  if (isAgenda && (!points || points.length === 0)) {
    points = buildAgendaFromSlideData();
    if (points.length === 0) points = ['本日の目的', '進め方', '次のアクション'];
  }

  const hasImages = Array.isArray(data.images) && data.images.length > 0;
  const isTwo = !!(data.twoColumn || data.columns);

  if ((isTwo && (data.columns || points)) || (!isTwo && points && points.length > 0)) {
    if (isTwo) {
      let L = [], R = [];
      if (Array.isArray(data.columns) && data.columns.length === 2) {
        L = data.columns[0] || []; R = data.columns[1] || [];
      } else {
        const mid = Math.ceil(points.length / 2);
        L = points.slice(0, mid); R = points.slice(mid);
      }
      const leftRect = offsetRect(layout.getRect('contentSlide.twoColLeft'), 0, dy);
      const rightRect = offsetRect(layout.getRect('contentSlide.twoColRight'), 0, dy);
      const leftShape = slide.insertShape(SlidesApp.ShapeType.TEXT_BOX, leftRect.left, leftRect.top, leftRect.width, leftRect.height);
      const rightShape = slide.insertShape(SlidesApp.ShapeType.TEXT_BOX, rightRect.left, rightRect.top, rightRect.width, rightRect.height);
      setBulletsWithInlineStyles(leftShape, L);
      setBulletsWithInlineStyles(rightShape, R);
    } else {
      const bodyRect = offsetRect(layout.getRect('contentSlide.body'), 0, dy);
      if (isAgenda) {
        drawNumberedItems(slide, layout, bodyRect, points);
      } else {
        const bodyShape = slide.insertShape(SlidesApp.ShapeType.TEXT_BOX, bodyRect.left, bodyRect.top, bodyRect.width, bodyRect.height);
        setBulletsWithInlineStyles(bodyShape, points);
      }
    }
  }

  // 画像（任意）
  if (hasImages) {
    const area = offsetRect(layout.getRect('contentSlide.body'), 0, dy);
    renderImagesInArea(slide, layout, area, normalizeImages(data.images));
  }

  drawBottomBarAndFooter(slide, layout, pageNum);
}

// compare（左右ボックス：ヘッダー色＋白文字）＋インライン装飾対応
function createCompareSlide(slide, data, layout, pageNum) {
  slide.getBackground().setSolidFill(CONFIG.COLORS.background_white);
  drawStandardTitleHeader(slide, layout, 'compareSlide', data.title);
  const dy = drawSubheadIfAny(slide, layout, 'compareSlide', data.subhead);

  const leftBox = offsetRect(layout.getRect('compareSlide.leftBox'), 0, dy);
  const rightBox = offsetRect(layout.getRect('compareSlide.rightBox'), 0, dy);
  drawCompareBox(slide, leftBox, data.leftTitle || '選択肢A', data.leftItems || []);
  drawCompareBox(slide, rightBox, data.rightTitle || '選択肢B', data.rightItems || []);

  drawBottomBarAndFooter(slide, layout, pageNum);
}
function drawCompareBox(slide, rect, title, items) {
  const box = slide.insertShape(SlidesApp.ShapeType.RECTANGLE, rect.left, rect.top, rect.width, rect.height);
  box.getFill().setSolidFill(CONFIG.COLORS.lane_title_bg);
  box.getBorder().getLineFill().setSolidFill(CONFIG.COLORS.lane_border);
  box.getBorder().setWeight(1);

  const th = 0.75 * 40; // 約30px相当
  const titleBar = slide.insertShape(SlidesApp.ShapeType.RECTANGLE, rect.left, rect.top, rect.width, th);
  titleBar.getFill().setSolidFill(CONFIG.COLORS.primary_color);
  titleBar.getBorder().setTransparent();
  setStyledText(titleBar, title, { size: CONFIG.FONTS.sizes.laneTitle, bold: true, color: CONFIG.COLORS.background_white, align: SlidesApp.ParagraphAlignment.CENTER });

  const pad = 0.75 * 12;
  const textRect = { left: rect.left + pad, top: rect.top + th + pad, width: rect.width - pad * 2, height: rect.height - th - pad * 2 };
  const body = slide.insertShape(SlidesApp.ShapeType.TEXT_BOX, textRect.left, textRect.top, textRect.width, textRect.height);
  setBulletsWithInlineStyles(body, items);
}

// progress（進捗バー）
function createProgressSlide(slide, data, layout, pageNum) {
  slide.getBackground().setSolidFill(CONFIG.COLORS.background_white);
  drawStandardTitleHeader(slide, layout, 'progressSlide', data.title);
  const dy = drawSubheadIfAny(slide, layout, 'progressSlide', data.subhead);

  const area = offsetRect(layout.getRect('progressSlide.area'), 0, dy);
  const items = Array.isArray(data.items) ? data.items : [];
  const n = Math.max(1, items.length);
  const rowH = area.height / n;

  for (let i = 0; i < n; i++) {
    const rowCenterY = area.top + i * rowH + rowH / 2;
    const textHeight = layout.pxToPt(18);
    const barHeight = layout.pxToPt(14);
    
    // 全要素を行の中央に配置するための基準Y座標を計算
    const textY = rowCenterY - textHeight / 2;
    const barY = rowCenterY - barHeight / 2;

    const label = slide.insertShape(SlidesApp.ShapeType.TEXT_BOX, area.left, textY, layout.pxToPt(150), textHeight);
    setStyledText(label, String(items[i].label || ''), { size: CONFIG.FONTS.sizes.body });
    try { label.setContentAlignment(SlidesApp.ContentAlignment.MIDDLE); } catch(e){}

    const barLeft = area.left + layout.pxToPt(160);
    const barW    = area.width - layout.pxToPt(300);
    const barBG = slide.insertShape(SlidesApp.ShapeType.RECTANGLE, barLeft, barY, barW, barHeight);
    barBG.getFill().setSolidFill(CONFIG.COLORS.faint_gray); barBG.getBorder().setTransparent();

    const p = Math.max(0, Math.min(100, Number(items[i].percent || 0)));
    if (p > 0) {
      const barFG = slide.insertShape(SlidesApp.ShapeType.RECTANGLE, barLeft, barY, barW * (p/100), barHeight);
      barFG.getFill().setSolidFill(CONFIG.COLORS.primary_color); barFG.getBorder().setTransparent();
    }

    const pct = slide.insertShape(SlidesApp.ShapeType.TEXT_BOX, barLeft + barW + layout.pxToPt(10), textY, layout.pxToPt(80), textHeight);
    pct.getText().setText(String(p) + '%');
    applyTextStyle(pct.getText(), { size: CONFIG.FONTS.sizes.small, color: CONFIG.COLORS.neutral_gray });
    try { pct.setContentAlignment(SlidesApp.ContentAlignment.MIDDLE); } catch(e){}
  }

  drawBottomBarAndFooter(slide, layout, pageNum);
}

// closing（結び）
function createClosingSlide(slide, data, layout) {
slide.getBackground().setSolidFill(CONFIG.COLORS.background_white);
try {
  const image = slide.insertImage(CONFIG.LOGOS.closing);
  const imgW_pt = layout.pxToPt(450) * layout.scaleX;
  const aspect = image.getHeight() / image.getWidth();
  image.setWidth(imgW_pt).setHeight(imgW_pt * aspect);
  image.setLeft((layout.pageW_pt - imgW_pt) / 2).setTop((layout.pageH_pt - (imgW_pt * aspect)) / 2);
} catch (e) {
  // 画像挿入に失敗した場合はスキップして他の要素を描画
}
}

// --- 8. ユーティリティ関数群 ---
function createLayoutManager(pageW_pt, pageH_pt) {
const pxToPt = (px) => px * 0.75;
const baseW_pt = pxToPt(CONFIG.BASE_PX.W);
const baseH_pt = pxToPt(CONFIG.BASE_PX.H);
const scaleX = pageW_pt / baseW_pt;
const scaleY = pageH_pt / baseH_pt;

const getPositionFromPath = (path) => path.split('.').reduce((obj, key) => obj[key], CONFIG.POS_PX);
return {
scaleX, scaleY, pageW_pt, pageH_pt, pxToPt,
getRect: (spec) => {
const pos = typeof spec === 'string' ? getPositionFromPath(spec) : spec;
let left_px = pos.left;
if (pos.right !== undefined && pos.left === undefined) {
left_px = CONFIG.BASE_PX.W - pos.right - pos.width;
}
return {
left:   left_px !== undefined ? pxToPt(left_px) * scaleX : undefined,
top:    pos.top !== undefined ? pxToPt(pos.top) * scaleY : undefined,
width:  pos.width !== undefined ? pxToPt(pos.width) * scaleX : undefined,
height: pos.height !== undefined ? pxToPt(pos.height) * scaleY : undefined,
};
}
};
}

function offsetRect(rect, dx, dy) {
return { left: rect.left + (dx || 0), top: rect.top + (dy || 0), width: rect.width, height: rect.height };
}

function drawStandardTitleHeader(slide, layout, key, title) {
const logoRect = layout.getRect(`${key}.headerLogo`);
try {
  const logo = slide.insertImage(CONFIG.LOGOS.header);
  const asp = logo.getHeight() / logo.getWidth();
  logo.setLeft(logoRect.left).setTop(logoRect.top).setWidth(logoRect.width).setHeight(logoRect.width * asp);
} catch (e) {
  // 画像挿入に失敗した場合はスキップして他の要素を描画
}

const titleRect = layout.getRect(`${key}.title`);
const titleShape = slide.insertShape(SlidesApp.ShapeType.TEXT_BOX, titleRect.left, titleRect.top, titleRect.width, titleRect.height);
setStyledText(titleShape, title || '', { size: CONFIG.FONTS.sizes.contentTitle, bold: true });

const uRect = layout.getRect(`${key}.titleUnderline`);
const u = slide.insertShape(SlidesApp.ShapeType.RECTANGLE, uRect.left, uRect.top, uRect.width, uRect.height);
u.getFill().setSolidFill(CONFIG.COLORS.primary_color);
u.getBorder().setTransparent();
}

function drawSubheadIfAny(slide, layout, key, subhead) {
if (!subhead) return 0;
const rect = layout.getRect(`${key}.subhead`);
const box = slide.insertShape(SlidesApp.ShapeType.TEXT_BOX, rect.left, rect.top, rect.width, rect.height);
setStyledText(box, subhead, { size: CONFIG.FONTS.sizes.subhead, color: CONFIG.COLORS.text_primary });
return layout.pxToPt(36);
}

function drawBottomBar(slide, layout) {
const barRect = layout.getRect('bottomBar');
const bar = slide.insertShape(SlidesApp.ShapeType.RECTANGLE, barRect.left, barRect.top, barRect.width, barRect.height);
bar.getFill().setSolidFill(CONFIG.COLORS.primary_color);
bar.getBorder().setTransparent();
}

function drawBottomBarAndFooter(slide, layout, pageNum) {
drawBottomBar(slide, layout);
addCucFooter(slide, layout, pageNum);
}

function addCucFooter(slide, layout, pageNum) {
const leftRect = layout.getRect('footer.leftText');
const leftShape = slide.insertShape(SlidesApp.ShapeType.TEXT_BOX, leftRect.left, leftRect.top, leftRect.width, leftRect.height);
leftShape.getText().setText(CONFIG.FOOTER_TEXT);
applyTextStyle(leftShape.getText(), { size: CONFIG.FONTS.sizes.footer, color: CONFIG.COLORS.text_primary });

if (pageNum > 0) {
const rightRect = layout.getRect('footer.rightPage');
const rightShape = slide.insertShape(SlidesApp.ShapeType.TEXT_BOX, rightRect.left, rightRect.top, rightRect.width, rightRect.height);
rightShape.getText().setText(String(pageNum));
applyTextStyle(rightShape.getText(), { size: CONFIG.FONTS.sizes.footer, color: CONFIG.COLORS.primary_color, align: SlidesApp.ParagraphAlignment.END });
}
}

function applyTextStyle(textRange, opt) {
const style = textRange.getTextStyle();
style.setFontFamily(CONFIG.FONTS.family);
style.setForegroundColor(opt.color || CONFIG.COLORS.text_primary);
style.setFontSize(opt.size || CONFIG.FONTS.sizes.body);
style.setBold(opt.bold || false);
if (opt.align) {
try { textRange.getParagraphs().forEach(p => p.getRange().getParagraphStyle().setParagraphAlignment(opt.align)); } catch (e) {}
}
}

function setStyledText(shapeOrCell, rawText, baseOpt) {
const parsed = parseInlineStyles(rawText || '');
const tr = shapeOrCell.getText();
tr.setText(parsed.output);
applyTextStyle(tr, baseOpt || {});
applyStyleRanges(tr, parsed.ranges);
}

function setBulletsWithInlineStyles(shape, points) {
const joiner = '\n\n';
let combined = '';
const ranges = [];

(points || []).forEach((pt, idx) => {
const parsed = parseInlineStyles(String(pt || ''));
const bullet = '• ' + parsed.output;
if (idx > 0) combined += joiner;
const start = combined.length;
combined += bullet;

parsed.ranges.forEach(r => {
  ranges.push({ start: start + 2 + r.start, end: start + 2 + r.end, bold: r.bold, color: r.color });
});
});

const tr = shape.getText();
tr.setText(combined || '• —');
applyTextStyle(tr, { size: CONFIG.FONTS.sizes.body });

try {
tr.getParagraphs().forEach(p => {
const ps = p.getRange().getParagraphStyle();
ps.setLineSpacing(100);
ps.setSpaceBelow(6);
});
} catch (e) {}

applyStyleRanges(tr, ranges);
}

function parseInlineStyles(s) {
const ranges = [];
let out = '';
for (let i = 0; i < s.length; ) {
if (s[i] === '[' && s[i+1] === '[') {
const close = s.indexOf(']]', i + 2);
if (close !== -1) {
const content = s.substring(i + 2, close);
const start = out.length;
out += content;
const end = out.length;
ranges.push({ start, end, bold: true, color: CONFIG.COLORS.primary_color });
i = close + 2; continue;
}
}
if (s[i] === '*' && s[i+1] === '*') {
const close2 = s.indexOf('**', i + 2);
if (close2 !== -1) {
const content2 = s.substring(i + 2, close2);
const start2 = out.length;
out += content2;
const end2 = out.length;
ranges.push({ start: start2, end: end2, bold: true });
i = close2 + 2; continue;
}
}
out += s[i]; i++;
}
return { output: out, ranges };
}

function applyStyleRanges(textRange, ranges) {
ranges.forEach(r => {
try {
const sub = textRange.getRange(r.start, r.end);
if (!sub) return;
const st = sub.getTextStyle();
if (r.bold) st.setBold(true);
if (r.color) st.setForegroundColor(r.color);
} catch (e) {}
});
}

function normalizeImages(arr) {
return (arr || []).map(v => {
if (typeof v === 'string') return { url: v };
if (v && typeof v.url === 'string') return { url: v.url, caption: v.caption || '' };
return null;
}).filter(Boolean).slice(0, 6);
}

function renderImagesInArea(slide, layout, area, images) {
if (!images || images.length === 0) return;
const n = Math.min(6, images.length);
let cols = 1, rows = 1;
if (n === 1) { cols = 1; rows = 1; }
else if (n === 2) { cols = 2; rows = 1; }
else if (n <= 4) { cols = 2; rows = 2; }
else { cols = 3; rows = 2; }

const gap = layout.pxToPt(10);
const cellW = (area.width - gap * (cols - 1)) / cols;
const cellH = (area.height - gap * (rows - 1)) / rows;

for (let i = 0; i < n; i++) {
const r = Math.floor(i / cols), c = i % cols;
const left = area.left + c * (cellW + gap);
const top  = area.top  + r * (cellH + gap);
try {
const img = slide.insertImage(images[i].url);
const scale = Math.min(cellW / img.getWidth(), cellH / img.getHeight());
const w = img.getWidth() * scale;
const h = img.getHeight() * scale;
img.setWidth(w).setHeight(h);
img.setLeft(left + (cellW - w) / 2).setTop(top + (cellH - h) / 2);
} catch(e) {}
}
}

function isAgendaTitle(title) {
const t = String(title || '').toLowerCase();
return /(agenda|アジェンダ|目次|本日お伝えすること)/.test(t);
}

function buildAgendaFromSlideData() {
const pts = [];
for (const d of slideData) {
if (d && d.type === 'section' && typeof d.title === 'string' && d.title.trim()) pts.push(d.title.trim());
}
if (pts.length > 0) return pts.slice(0, 5);
const alt = [];
for (const d of slideData) {
if (d && d.type === 'content' && typeof d.title === 'string' && d.title.trim()) alt.push(d.title.trim());
}
return alt.slice(0, 5);
}

function drawNumberedItems(slide, layout, area, items) {
const n = Math.max(1, items.length);
const topPadding = layout.pxToPt(30);
const bottomPadding = layout.pxToPt(10);
const drawableHeight = area.height - topPadding - bottomPadding;
const gapY = drawableHeight / Math.max(1, n - 1);
const cx = area.left + layout.pxToPt(44);
const top0 = area.top + topPadding;

for (let i = 0; i < n; i++) {
const cy = top0 + gapY * i;
const sz = layout.pxToPt(28);
const numBox = slide.insertShape(SlidesApp.ShapeType.RECTANGLE, cx - sz/2, cy - sz/2, sz, sz);
numBox.getFill().setSolidFill(CONFIG.COLORS.primary_color);
numBox.getBorder().setTransparent();
const num = numBox.getText(); num.setText(String(i + 1));
applyTextStyle(num, { size: 12, bold: true, color: CONFIG.COLORS.background_white, align: SlidesApp.ParagraphAlignment.CENTER });

// 元の箇条書きテキストから先頭の数字を除去
let cleanText = String(items[i] || '');
cleanText = cleanText.replace(/^\s*\d+[\.\s]*/, '');

const txt = slide.insertShape(SlidesApp.ShapeType.TEXT_BOX, cx + layout.pxToPt(28), cy - layout.pxToPt(16), area.width - layout.pxToPt(70), layout.pxToPt(32));
setStyledText(txt, cleanText, { size: CONFIG.FONTS.sizes.processStep });
try { txt.setContentAlignment(SlidesApp.ContentAlignment.MIDDLE); } catch(e){}
}
}
