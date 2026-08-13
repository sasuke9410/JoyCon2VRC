# JoyCon2VRC - Joy-Con(L) ロコモーション コントローラー

Nintendo Switchの **Joy-Con (L)** のモーションセンサーを活用し、脚部のステップ動作によって VRChat 内を移動（歩行・走行）させるアプリケーションです。

---

## 主な機能

* **自動移動判別 (WALK / RUN)**: ステップ動作のケイデンス（ピッチ速度）から歩行と走行を自動識別。
* **静音モード**: 接地インパクトを出さず、膝の屈伸動作だけで静かに前進移動。
* **自動キャリブレーション**: 短時間の動作測定により、個人の動作特性に合わせて感度と速度閾値を自動調整。
* **VRChat Native OSC 対応**: VRChat標準のOSC (`/input/Vertical`, `/input/Run`, UDP Port `9000`) へリアルタイム送信。
* **仮想キーボード送信**: Windows `SendInput` APIによる `W` / `Shift` キー送信にも対応。

---

## 動作環境

* **OS**: Windows 10 / 11 (Bluetooth対応)
* **機器**: Nintendo Switch Joy-Con (L)
* **固定用具**: 脚部にJoy-Conを固定するバンド等
* **対象アプリ**: VRChat (PC版 / VR版)

---

## 使い方

### 1. アプリケーションの起動
配布された `JoyCon2VRC.exe` を起動します。

※ソースコードから起動する場合:
```powershell
uv sync
uv run python main.py
```

### 2. Joy-Con (L) の接続
1. PCのWindows設定から Joy-Con (L) をBluetoothペアリングします。
2. アプリを起動すると自動的に検出・接続されます（ステータス表示が「Joy-Con(L) 接続中」になります）。

### 3. キャリブレーション（推奨）
1. 画面上の「キャリブレーション」をクリックします。
2. 画面の指示に従い、静止（3秒） $\rightarrow$ 歩行（5秒） $\rightarrow$ 走行（5秒）を行ってください。

### 4. VRChatとの連動
1. VRChat内で **`R` キー長押し** $\rightarrow$ **`Options`** $\rightarrow$ **`OSC`** $\rightarrow$ **`Enabled: True`** に設定します。
2. アプリ画面の「VRChat連携: OFF」をクリックして **`ON`** に切り替えます。
3. 脚部を動かすとアバターが移動します。

---

## 注意事項

* **VRChatのOSC受信設定**: VRChat側でOSCが有効（Enabled）になっていない場合、移動パケットは受信されません。
* **管理者権限について**: VRChatを管理者権限で起動している場合、仮想キーボード送信がブロックされることがあります。その場合はVRChatを通常権限で起動してください。

---

## ディレクトリ構成

```text
JoyCon2VRC/
├── dist/JoyCon2VRC.exe    # Windows用実行ファイル
├── main.py                # デスクトップアプリ エントリーポイント
├── bridge_server.py       # バックグラウンド通信・OSC送信サーバー
├── test_app.html          # GUIダッシュボード
├── test_system_automated.py # 自動テストスイート
└── pyproject.toml         # 依存関係設定
```

---

## ライセンス

[MIT License](LICENSE)
