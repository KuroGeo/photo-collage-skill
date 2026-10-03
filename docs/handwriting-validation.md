# 自然手写标注：原因与实际修正

2026-10-03。用户反馈“README 感觉不是手写”，本轮先实际打开公开 README 和点击后的高清图，没有仅凭 push 判断。

## 根因证据

README 与图片文件页显示提交 `2284d4f`。直接下载 README 当时引用的 WebP 与点击后的 PNG，二者与该提交文件逐字节一致：预览 SHA256 `2f22b0fee335ef95b5701922d90995c85b3b8b2faed75a32db540fb3e006461d`，高清 SHA256 `813b3cbec8fac9c9ed14eddcc407648f40f4465d407603c6b9389c8b6267a582`。放大可见日期和中文均很规整；没有发现本次载入旧图片缓存的证据，也没有系统字体回退。原因是文楷式字形没有达到自然笔记的审美要求。

## 实际修正版

[旧线上文字与新手写对比](../examples/handwriting-before-after.png)：上方裁自实际下载的公开旧图，下方裁自新排字图，相同区域放大。新增 [单独明信片高清](../examples/postcard-only-handwritten.png)和[上下原图对照高清](../examples/postcard-stacked-handwritten.png)；README 的预览与点击高清均改为新文件名，避免沿用上一版图片缓存路径。

- 中文明确选用悠哉 Regular 0.868，英文/数字明确选用 Caveat 2.000；两款均为手写字形。不同字符使用两款明确选择的字体，不是系统 fallback，不把中文交给黑体。
- 中文原字号与左下起点保持，拉丁手写字号为其 1.15 倍以匹配字面高度；暖棕 `#AE7E63`、原文 `2026.10.03 17:30` 与 `合成山湖` 保持。
- 新旧单卡片只改变文字区域 3,784 个像素；主体、纸张、布局不变。上下图顶部原片的 RGBA 像素哈希仍相等。
- 实际渲染“福建省厦门市思明区环岛南路曾厝垵文创村海边观景步道 · Xiamen Seaside Walk”，两份字体分别覆盖所负责字符，无缺字；缺字和放不下的长文报错而不输出错误图片。七项测试通过。独立复核亦确认两模式、长地点和字体路由；其指出的英文拆词已修正为普通英文单词整体换行，并重新渲染检查。
- 辰宇落雁体曾作为候选检查，但测试文本缺少多个简体字且本地字体渲染报错，因此未采用，也未用其他字体悄悄补字。

[结构化实测](natural-handwriting-validation.json)记录字体、路由、原文、像素差异与上一版线上图哈希。[上一版文楷测试记录](handwriting-validation.json)保留为历史，不能替代本版视觉验收。最终是否达到用户想要的手写感觉，以实际对比图由用户判断；不称已获得用户认可。

## 许可

字体取自 [悠哉官方项目](https://github.com/lxgw/yozai-font)与 [Google Fonts 的 Caveat](https://github.com/google/fonts/tree/main/ofl/caveat)。两份字体均未修改，分别随包附带完整 [悠哉 OFL 1.1](../skills/photo-collage/assets/fonts/Yozai-OFL.txt)、[Caveat OFL 1.1](../skills/photo-collage/assets/fonts/Caveat-OFL.txt)和[版本/哈希记录](../skills/photo-collage/assets/fonts/provenance.json)。不安装系统字体，不配置密钥；两款字体不适用本项目 MIT。
