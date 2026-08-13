# Joycon2VRC icon assets

The icon family shows a waist-down real walker with one cyan left-hand controller on their anatomical left thigh, synchronizing to a waist-down cyan virtual walker. Omitting faces and upper bodies keeps the mark graphic and reduces generative-image cues. It intentionally avoids Nintendo, Switch, Joy-Con, and VRChat logos, copied product geometry, recognizable avatars, and wordmarks.

## Deliverables

| Asset | Resolution(s) | Use |
| --- | --- | --- |
| `icon.png` | 512x512 PNG | In-app header and general project icon |
| `icon-detailed.png` / `icon-1024.png` | 1024x1024 PNG | Final full-bleed artwork with no outer frame |
| `icon-full-bleed-master.png` | 1254x1254 PNG | Current source; navy background extends to every edge |
| `icon-waist-down.png` | 1254x1254 PNG | Earlier transparent rounded-tile version retained for reference |
| `icon-left-controller.png` | 1254x1254 PNG | Earlier full-body left-thigh version retained for reference |
| `icon.ico` | 16, 24, 32, 48, 64, 96, 128, 256px | PyInstaller Windows executable |
| `windows/icon-*.png` | matching sizes above | Inspection and future packaging |
| `favicon-16.png` | 16x16 PNG | Browser tab at standard scale |
| `favicon-32.png` / `favicon.png` | 32x32 PNG | Browser tab at high density; compatibility alias |
| `favicon-48.png` | 48x48 PNG | Browser shortcut and larger favicon contexts |
| `favicon.ico` | 16, 32, 48px | Browser fallback |

## Why these sizes

Microsoft's current Win32 guidance says an ICO should include at least 16, 24, 32, 48, and 256px. The 64, 96, and 128px variants reduce scaling at common high-DPI taskbar and Start-menu sizes. The HTML `sizes` attributes let browsers choose among the 16, 32, and 48px PNG favicons.

Regenerate the derived files after changing either master:

```powershell
uv run python scripts/build_icons.py
```

The current masters are `icon-full-bleed-master.png` (detailed walking scene) and `icon-small-master.png` (small-size walking pictogram). Earlier versions remain for reference.
