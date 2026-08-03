# 書籍原稿ワークスペース

`docs/` を変更せず、ブログ連載を一冊として見渡せる順序に再構成した編集用ディレクトリです。

## 正本と成果物

- `content/`：7部・32章に分類した本文の正本
- `appendices/`：付録の正本
- `drafts/`：採用しなかった別稿
- `editorial/`：構成、出典対応、編集スタイル
- `book.json`：部・章の順序とファイルパス
- `build/book.md`：全章を結合した自動生成物
- `tools/build_pdf.py`：結合原稿とPDFのビルダー
- `output/pdf/quantum-computing-for-developers-ja.pdf`：通読・レビュー用PDF

## 再生成

ワークスペース付属Pythonで次を実行します。

```powershell
python manuscript/tools/build_pdf.py
```

このコマンドは `content/` と `appendices/` を `book.json` の順序で結合し、`build/book.md` とPDFを更新します。`docs/` は参照しません。結合原稿だけを更新する場合は `--assemble-only` を付けます。

## 編集上の位置づけ

現段階は「書籍構成ドラフト」です。元記事の説明とコードを保持しつつ、連載番号、記事メタデータ、次回予告を除き、学習順に並べ替えています。表示数式は `$$...$$` に統一し、PDFでは実行可能コードを淡い青、説明用テキストを淡いグレー、数式を淡い黄で表示します。コード上部には、フェンスで明示されたファイル名だけを控えめに表示します。Qiskit API、クラウドサービス、ハードウェアの記述は変化が速いため、刊行版では実行確認と出典確認が必要です。
