# JoyCon2VRC - Joy-Con(L) ロコモーション コントローラー

Nintendo Switchの **Joy-Con (L)** のモーションセンサーを活用し、脚部のステップ動作によって VRChat 内を直感的に移動（歩行・走行）させるデスクトップアプリケーションです。

---

## ⚡ クイックスタート (EXE版の使い方)

PCにPython環境等がなくても、ビルド済みの `.exe` ファイルのみで今すぐ使用できます。

1. **Joy-Conの準備**
   * Windowsの「設定」 -> 「Bluetooth とデバイス」から、Joy-Con (L) をペアリングします。
2. **アプリの起動**
   * [**dist/JoyCon2VRC.exe**](file:///c:/Users/sasuke/Documents/Joycon2VRC/dist/JoyCon2VRC.exe) をダブルクリックして起動します。ペアリング済みのJoy-Conがバックグラウンドで自動検出・接続されます（ステータスが「Joy-Con(L) 接続中」になります）。
3. **キャリブレーション（初回推奨）**
   * 画面上の「キャリブレーション」をクリックし、インジケーターの色とカウントダウンに合わせて、**静止（3秒）** -> **歩行（5秒）** -> **走行（5秒）** を行います。
4. **VRChat側の設定**
   * VRChat内で `R` キー長押し（アクションメニュー） -> `Options` -> `OSC` -> **`Enabled: True`** に設定します。
5. **連動開始**
   * アプリ画面の「VRChat連携: OFF」をクリックして **`ON`** に切り替えます。足踏みを行うとアバターが移動します。

---

## ✨ 主な機能

* **自動移動判別 (WALK / RUN)**: ステップ動作のケイデンス（ピッチ速度）から歩行と走行を自動識別。パケット揺らぎによる「WALK中の意図しない一時的なRUN昇格」を防ぐため、2ステップ連続判定（ヒステリシス）を採用。
* **静音モード**: 接地インパクトを出さず、膝の屈伸動作だけで静かに前進移動。
* **直感的キャリブレーション**: 測定中のステータス（準備中＝オレンジ、測定中＝緑）を視覚的に瞬時に判別できるモーダルUI。ボタンの二重押し防止ロック機能を搭載。
* **VRChat Native OSC 対応**: VRChat標準のOSC (`/input/Vertical`, `/input/Run`, UDP Port `9000`) にリアルタイム送信。
* **自動クリーンアップ（停止フック）**: アプリの `X` ボタンでの終了時や強制終了（クラッシュ含む）時に、VRChat側のアバターが走り続けてしまうのを防ぐため、停止信号（0.0）を自動で連打送信して安全に終了。
* **仮想キーボード送信**: Windows `SendInput` APIによる `W` / `Shift` キー送信にも対応。

---

## 動作環境

* **OS**: Windows 10 / 11 (Bluetooth対応)
* **機器**: Nintendo Switch Joy-Con (L)
* **固定用具**: 脚部にJoy-Conを固定するバンド等
* **対象アプリ**: VRChat (PC版 / VR版)

---

## 🐍 開発者向け起動方法

ソースコードから実行・開発する場合は以下をご使用ください。

```powershell
# 依存関係のセットアップ
uv sync

# アプリケーションの起動
uv run python main.py

# 自動テストの実行
uv run pytest test_system_automated.py
```

---

## 注意事項

* **VRChatのOSC受信設定**: VRChat側でOSCが有効（Enabled）になっていない場合、移動パケットは受信されません。
* **管理者権限について**: VRChatを管理者権限で起動している場合、仮想キーボード送信がブロックされることがあります。その場合はVRChatを通常権限で起動してください。

---

## ディレクトリ構成

```text
JoyCon2VRC/
├── dist/JoyCon2VRC.exe    # Windows用実行ファイル (アイコン適用済)
├── assets/                # アプリケーション画像・アイコンアセット
├── main.py                # デスクトップアプリ エントリーポイント
├── bridge_server.py       # バックグラウンド通信・OSC送信サーバー
├── test_app.html          # GUIダッシュボード
├── test_system_automated.py # 自動テストスイート
└── pyproject.toml         # 依存関係設定
```

---

## ライセンス

[MIT License](LICENSE)
