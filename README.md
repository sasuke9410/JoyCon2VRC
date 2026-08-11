# Joycon2VRC

Nintendo Switch Joy-Con (L) を太ももに固定して、その場足踏み（通常＆階下静音サイレントモード）で VRChat 空間を移動するプロジェクトです。

## 使い方 (uv)

### センサー導通テスト
```powershell
uv run test_joycon_hid.py
```

### VRChat移動アプリ起動
```powershell
# 通常足踏みモード
uv run joycon_vrchat_live.py normal

# サイレントモード (静音)
uv run joycon_vrchat_live.py silent
```
