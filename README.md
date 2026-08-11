# 🎮 JoyCon2VRC - Joy-Con(L) 太もも固定 足踏みVRChat移動システム

Nintendo Switchの **Joy-Con (L)** を左太moも（太もも）にバンド固定し、その場足踏み運動によって VRChat 空間内をスムーズに歩行・走行移動できるようにするシステムです。

リングフィットアドベンチャーのような運動体験をVRChatで再現しつつ、マンション等の階下への騒音・振動を防ぐ **「階下静音サイレントモード」** や、ユーザー個人の歩き方・脚の振りに全自動でフィットさせる **「🧙‍♂️ 3ステップ個人適応キャリブレーション」** 機能を備えています。

---

## ✨ 主な特徴

* **2段階移動判定 (WALK & RUN)**: ゆったりした足踏み（歩き）と素早い足踏み（走り / ダッシュ）を自動識別。
* **🤫 階下静音サイレントモード**: 床を着地衝撃で踏み込まず、かかとをつけたまま膝を曲げ伸ばしする動作だけで静かに前進。
* **🧙‍♂️ 3ステップ個人適応キャリブレーション**: 静止・歩行・走行の動きを数秒間プロファイリングし、衝撃感度・RUN切り替え速度・着地ホールド時間を個人に自動最適化。
* **🌐 VRChat Native OSC 対応**: VRChat標準のOSC (`/input/Vertical`, `/input/Run`, ポート `9000`) への直結送信で、アナログスティックのような滑らかなアバター移動を実現。
* **⌨️ 仮想キーボードバックアップ**: Windows `SendInput` APIによる `W` キー / `Shift` キーの仮想入力にも対応。
* **🖥️ Web統合ダッシュボード**: Chrome / Edge などのブラウザから直感的に全操作・波形デバッグ・1クリックVRChat送信が可能。

---

## 📋 前提条件 (Prerequisites)

### ハードウェア
* **PC**: Windows 10 / 11 (Bluetooth 3.0 以上対応)
* **コントローラー**: Nintendo Switch **Joy-Con (L)** (左)
* **固定具**: 左太もも表面にJoy-Conを密着固定できるバンド (スマホ用ランニングバンド、ウエストポーチ、面ファスナーバンド等)

### ソフトウェア環境
* **Python**: Python 3.10 以上 (高速環境管理ツール [`uv`](https://github.com/astral-sh/uv) を推奨)
* **Webブラウザ**: Google Chrome または Microsoft Edge (WebHID API 対応)
* **ゲーム環境**: VRChat (PC版 / VR版)

---

## 🚀 クイックスタート・使用方法

### Step 1. リポジトリの準備
```powershell
git clone https://github.com/sasuke9410/JoyCon2VRC.git
cd JoyCon2VRC

# uv を使用して依存関係 (.venv) を自動準備
uv sync
```

### Step 2. Joy-Con (L) の Bluetooth ペアリング
1. Windowsの「設定」 $\rightarrow$ 「Bluetooth とデバイス」を開きます。
2. Joy-Con (L) のシンクロボタンを長押ししてペアリングモードにし、PCとBluetooth接続します。

### Step 3. Web統合ダッシュボードの起動
```powershell
# ローカルWebサーバー ＆ VRChatブリッジサーバーを起動
uv run python -m http.server 8080
```
別ウィンドウのターミナルで以下を起動します:
```powershell
uv run python bridge_server.py
```
ブラウザで [**http://localhost:8080/test_app.html**](http://localhost:8080/test_app.html) を開きます。

### Step 4. キャリブレーション & VRChatへの送信
1. Web画面で **「🔌 Joy-Con (L) 接続」** を押し、Joy-Conを選択。
2. **「🧙‍♂️ 個人キャリブレーション (3ステップ)」** を押し、画面指示（静止 3秒 $\rightarrow$ 歩行 5秒 $\rightarrow$ 走行 5秒）に従います。
3. **「🚀 VRChat移動送信を開始 (OFF)」** ボタンを押して **`ON`** に切り替えます。

### Step 5. VRChat側の受信用設定
1. VRChat内で **`R` キー長押し** (アクションメニュー) $\rightarrow$ **`Options`** $\rightarrow$ **`OSC`** を開きます。
2. **`Enabled: True` (有効)** に設定します。
3. VRChat内でその場足踏みを行うと、アバターが移動します！

---

## 🐍 (参考) Python CLI スタンドアロン実行

Webブラウザを使わず、Pythonターミナルから直接Joy-Conと通信してVRChatを操作することも可能です。

```powershell
# 通常足踏みモード
uv run python joycon_vrchat_live.py normal

# 階下静音サイレントモード
uv run python joycon_vrchat_live.py silent
```

---

## ⚠️ 制約事項 & トラブルシューティング

### 1. VRChatでアバターが動かない場合
* **OSCポート番号**: VRChatの入力受信用ポートは **`UDP 127.0.0.1:9000`** です。
* **VRChat内のOSC有効化**: VRChat内で `OSC Enabled: True` に設定されていないとパケットがドロップされます。VRChatの `Esc` メニュー $\rightarrow$ `Settings` $\rightarrow$ `Developer` $\rightarrow$ `OSC Debug Window` をONにすることで受信ログを確認できます。

### 2. Windows 仮想キー (`W`キー) の権限制約 (UIPI)
* VRChatを「管理者として実行」している場合、Windowsのセキュリティ制限により非管理者プロセスからの仮想キー入力がブロックされます。VRChatを通常ユーザー権限で起動するか、プロンプトを管理者権限で起動してください。

### 3. Bluetooth 通信安定性
* PCのBluetoothアダプターの受信感度によってはパケット遅延が発生する場合があります。BluetoothアンテナをPCに接続するか、USB拡張ケーブルでレシーバーを近くに設置することを推奨します。

---

## 📁 ディレクトリ構造

```text
JoyCon2VRC/
├── test_app.html          # Web統合ダッシュボード (キャリブレーション, 波形描画)
├── bridge_server.py       # Webアプリ ↔ VRChat OSC/キー入力ローカルブリッジ (Port 9011)
├── joycon_vrchat_live.py  # Python HID直結スタンドアロン型移動エンジン
├── joycon_vrchat.py       # OSC/仮想キー送信コアモジュール
├── debug_osc_vrc.py       # VRChat OSC 疎通・強制移動テストスクリプト
├── test_joycon_hid.py     # Joy-Con 6軸IMUセンサー動作疎通確認用スクリプト
├── pyproject.toml         # Pythonプロジェクト / uv 依存関係設定
└── README.md              # 本ドキュメント
```

---

## 📄 ライセンス

[MIT License](LICENSE)
