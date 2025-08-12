// grammar.js
module.exports = grammar({
    name: 'api_doc',
  
    extras: $ => [
      /\s/,      // あらゆる空白文字（改行含む）
      /\*+!?/,   // 行頭の*や、/**, */などの記号
    ],
  
    rules: {
      // 1. ソースファイルは、doc_commentの繰り返しで構成される
      source_file: $ => repeat($.doc_comment),
  
      // 2. doc_commentは、/** と */ で囲まれたブロック
      doc_comment: $ => seq(
        '/**',
        repeat(
          choice(
            $.function_tag,
            $.class_tag,
            $.param_tag,
            $.property_tag,
            $.returns_tag,
            $.doc_text
          )
        ),
        '*/'
      ),
  
      // 3. 各種タグの定義
      function_tag: $=> seq('@function',$.identifier),
      class_tag:    $ => seq('@class',    $.identifier),
      param_tag:    $ => seq('@param',    $.type, $.identifier, '-', $.description),
      property_tag: $=> seq('@property',$.type, $.identifier, '-', $.description),
      returns_tag:  $ => seq('@returns',  $.type, $.description),
  
  
      // 4. タグ以外のただのテキスト行
      doc_text: $ => /[^@*/\s]([^\n]*)/,
  
      // 5. 最小単位の定義
      type:        $ => seq('{', /[^{}\n]+/, '}'),         // {型}
      identifier:  $ => /[a-zA-Z_][a-zA-Z0-9_]*/,        // 関数名や変数名
      description: $ => /[^\n]*/                         // タグ行の残りの説明部分
    }
  });