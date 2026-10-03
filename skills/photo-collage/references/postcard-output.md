# 明信片交付参数与确定性后处理

- `output_mode=postcard_only`：单独明信片，默认模式。
- `output_mode=stacked_original`：一张上下拼接图，上方为授权原片，下方为生成明信片。先生成无字卡片，再用确定性合成粘贴原片；不要让图像模型重画上方原片。保留原片的显示朝向和原尺寸，只按原片宽度缩放下方卡片；不拉伸或裁切原片。整体比例由两个面板实际尺寸决定，4:5 是卡片比例。
- `location`、`date`、`time`：可选原样文字。未提供就不添加该项，不从照片猜地点/时间，不读取 EXIF 位置或拍摄时间后自动发布。只在输出离不开信息时提问；缺值不阻止无字交付。

参考观察：抖音原图在上、暖白卡片在下，两块大致各半；日期是下卡片左下的细小暖棕字，地点在下一行，不出现在上方照片。用户进一步指定手写感：默认使用附带的霞鹜文楷 Regular，中文、英文与数字都来自同一字体；暖棕 `#AE7E63`（RGBA `174,126,99,255`）保持不变。对 `drybrush-postcard` 生成提示词写明给下卡片左下留文字空白，不让模型画指定文字；卡片生成后再排字，核对每个字符。

## 实际可用的辅助工具

本包附 `scripts/postcard_output.py`。需要已有 Python + Pillow；文字默认使用 `assets/fonts/LXGWWenKai-Regular.ttf`，字体文件未修改，完整 [OFL 1.1 许可](../assets/fonts/OFL.txt)和[来源/版本/哈希](../assets/fonts/provenance.json)随包提供，字体不按 Skill 的 MIT 重新授权。只从文件读取字体，不安装系统字体。缺少依赖/字体就说明阻塞，不假设可运行、不静默安装软件。也可用环境已有并实际验证的确定性合成工具。

以下命令在技能目录运行，`card.png` 是已生成的无字卡片；输入文件名与字体应替换为实际存在的路径：

```bash
python3 scripts/postcard_output.py compose --postcard card.png --output-mode postcard_only --output postcard.png
python3 scripts/postcard_output.py compose --original original.png --postcard card.png --output-mode stacked_original --output stacked.png --report stacked.json
```

提供文字时加入 `--location '用户原文' --date '用户原文' --time '用户原文'`，无需另选字体。仅提供需要的参数。用户明确另选字体时可用 `--font '<实际字体路径>'` 覆盖；必须确认中文、英文和数字都受支持，不能用只含西文的 script 字体加黑体中文回退。脚本在下卡片左下排字，长地点可换行；字符缺字/放不下会报错，不能截断或替用户编造内容。报告记录实际字体文件名、哈希及不变的文字颜色。

生成无损 PNG 母版后，另建压缩展示预览：

```bash
python3 scripts/postcard_output.py preview --input stacked.png --output stacked-preview.webp --width 560 --quality 86
```

网页展示使用预览，单独提供母版链接；压缩/缩放不会生成新内容，输入和母版不能被覆盖。上方原图像素一致性以无损 PNG 母版为准；有损预览不能用于该证明。保存并检查报告中的上方像素哈希相等、文本参数、输出尺寸及体积，同时视觉检查位置、缺字和下方风格。

辅助脚本按 EXIF 显示朝向转换为 8 位 RGBA，未保留 ICC 色彩配置。报告证明的是这种转换后的显示像素相等，不能称为任意照片的高位深或色彩配置无损归档。原文件保留；若用户要求保留高位深或 ICC，需要另用支持这些信息的合成工具并实际验证，不能拿本示例的像素哈希代替该验证。
