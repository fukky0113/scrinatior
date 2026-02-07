# モジュール仕様書（スクショット）

対象ソース: `main.py`

## 1. 構成一覧

| 要素 | 種別 | 役割 |
| --- | --- | --- |
| `main()` | 関数 | アプリ起動、初期画面表示 |
| `get_virtual_screen_bounds()` | 関数 | 全ディスプレイを包含する仮想スクリーンの原点とサイズを返す |
| `App` | クラス | ウィンドウ管理と画面遷移 |
| `ScreenshotOverlay` | クラス | 範囲選択用オーバーレイ |
| `PreviewWindow` | クラス | 撮影画像のプレビュー/編集 |

## 2. 各モジュール詳細

### 2.1 `main()`

| 項目 | 内容 |
| --- | --- |
| 入力 | なし |
| 出力 | 終了コード（`int`） |
| 役割 | Tk rootを作成し、`App`を起動する |

処理概要:
- `root` を生成し非表示
- `App.start_capture()` を呼び出し、範囲選択を開始
- `root.mainloop()` でイベントループ実行

### 2.2 `get_virtual_screen_bounds()`

| 項目 | 内容 |
| --- | --- |
| 入力 | `fallback_widget: tk.Widget` — 非Windows環境でのフォールバック用ウィジェット |
| 出力 | `(x, y, width, height)` — 仮想スクリーン全体の原点とサイズ |
| 役割 | Windows では `user32.dll` の `GetSystemMetrics` で全ディスプレイの仮想スクリーン情報を取得する |

補足:
- Windows: `SM_XVIRTUALSCREEN` (76), `SM_YVIRTUALSCREEN` (77), `SM_CXVIRTUALSCREEN` (78), `SM_CYVIRTUALSCREEN` (79) を使用
- プライマリの左側にあるディスプレイは負の x 座標を持つ
- macOS/Linux: `winfo_screenwidth()` / `winfo_screenheight()` によるプライマリディスプレイのみのフォールバック

### 2.3 `App`

| 項目 | 内容 |
| --- | --- |
| 役割 | ウィンドウの登録/終了管理、画面遷移 |
| 管理データ | `windows: set[tk.Toplevel]` |

主要メソッド:
- `register_window(window)`: ウィンドウ登録と終了監視
- `close_window(window)`: 指定ウィンドウを閉じる
- `start_capture()`: 全ディスプレイを覆うオーバーレイを表示し範囲選択へ
- `show_preview(image)`: プレビュー画面を開く

終了条件:
- 登録ウィンドウがすべて閉じられた時にアプリ終了

### 2.4 `ScreenshotOverlay`

| 項目 | 内容 |
| --- | --- |
| 役割 | 画面を覆う半透明オーバーレイ、範囲選択 |
| 入力 | `window: tk.Toplevel`, `on_capture: Callable` |
| 出力 | 選択範囲の画像（`PIL.Image`） |

主要イベント:
- `<ButtonPress-1>`: 開始座標を記録
- `<B1-Motion>`: 矩形を更新
- `<ButtonRelease-1>`: 範囲確定してキャプチャ

補足:
- オーバーレイは撮影直前に `withdraw()` して写り込みを防止

### 2.5 `PreviewWindow`

| 項目 | 内容 |
| --- | --- |
| 役割 | 撮影結果の表示、簡易編集 |
| 入力 | `image: PIL.Image` |
| 出力 | 保存時に画像ファイル |

主要機能:
- 右クリックメニュー（保存/ズーム）
- `Ctrl + ドラッグ` で赤線描画
- 追加撮影ボタンで新規オーバーレイ起動

描画仕様:
- 赤線は `annotated_image` に反映
- 表示倍率は `scale` で管理

## 3. 例外/エラーハンドリング

- 範囲サイズが極小の場合は撮影をキャンセル
- 保存ダイアログのキャンセルは無処理

## 4. 外部依存

- Tkinter: GUI/イベント
- Pillow: 画面キャプチャ/画像描画/表示
- ctypes + user32.dll: マルチモニターの仮想スクリーン情報取得（Windows、標準ライブラリ）

## 5. 今後の拡張候補（任意）

- Undo/Redoの追加
- 図形/テキストの注釈
- 保存先プリセット
