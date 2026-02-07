# 作業進捗表：拡張画面キャプチャ対応

## 問題概要

現状、`ScreenshotOverlay` のオーバーレイが `winfo_screenwidth()` / `winfo_screenheight()` を使用しており、プライマリディスプレイのサイズしか返さないため、拡張ディスプレイ上の範囲を選択・キャプチャできない。

### 該当箇所

`main.py` — `App.start_capture()` 内:

```python
overlay.geometry(
    f"{overlay.winfo_screenwidth()}x{overlay.winfo_screenheight()}+0+0"
)
```

## タスク一覧

| # | タスク | 状態 | 概要 |
|---|--------|------|------|
| 1 | 全ディスプレイのジオメトリ取得 | 完了 | `ctypes` + `user32.dll` の `GetSystemMetrics` で仮想スクリーン情報を取得する `get_virtual_screen_bounds()` を実装 |
| 2 | オーバーレイを全画面に拡張 | 完了 | 仮想スクリーン全体のバウンディングボックスを計算し、オーバーレイが全ディスプレイを覆うように変更 |
| 3 | 座標マッピングの確認 | 完了 | `event.x_root`/`y_root` はスクリーン絶対座標のため追加修正不要 |
| 4 | ImageGrab のキャプチャ修正 | 完了 | `ImageGrab.grab()` に `all_screens=True` を追加（Windows ではこれがないとプライマリのみキャプチャ） |
| 5 | 依存パッケージの確認 | 完了 | 追加パッケージなし（`ctypes` は Python 標準ライブラリ） |
| 6 | ドキュメント更新 | 完了 | README.md / docs にマルチモニター対応・Windows 動作環境を反映 |

## 修正内容まとめ

### 方針

- 追加パッケージを使わず、Python 標準ライブラリの `ctypes` で Windows の `user32.dll` を直接呼び出す
- macOS（開発環境）では `winfo_screenwidth()` / `winfo_screenheight()` によるフォールバック

### 変更ファイル

| ファイル | 変更内容 |
|----------|----------|
| `main.py` | `ctypes`/`sys` インポート追加、`get_virtual_screen_bounds()` を Windows API ベースに実装、`start_capture()` のジオメトリ計算を全画面対応に変更、`ImageGrab.grab()` に `all_screens=True` を追加 |
| `README.md` | マルチモニター対応の記載追加、動作環境を Windows 10 以降に変更 |
| `docs/architecture.md` | 外部依存を更新 |
| `docs/modules.md` | `get_virtual_screen_bounds()` の仕様を更新、外部依存を更新 |
