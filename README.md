# FlowTrack demo 页面

以真实视频编辑效果为核心的静态英文论文展示页，无需 npm、模型权重或推理服务。

## 本地预览

```sh
python3 /home/maviuserzjl/zjl_edit/it2v_edit_zjl/nips/demo/serve.py
```

访问 http://127.0.0.1:8765/ 。其他端口可通过 `--port 8080` 指定。服务支持 byte-range 请求，便于拖动视频时间轴。

## 页面功能

- 26 个精选正面案例：主体、创意、颜色、材质和添加五类编辑。
- 动态结果墙：桌面每行两组，手机每行一组；默认 24 例，可展开至 26。
- 全部案例只展示 Source / FlowTrack 双列对比，突出 FlowTrack 的实际编辑效果。
- 可拖动前后对照、同步时间轴、半速播放、重播和全屏。
- 搜索、分类筛选、暂停动态预览、完整 source / target prompt 和案例分享链接。
- 完整 FiVE-Bench Table 1、论文和代码下载。
- 桌面及移动端适配，离屏暂停，尊重系统减少动态效果设置。

## 内容依据

Demo 只展示经过逐帧人工抽查的正面结果；未达到展示标准的添加、删除和不稳定编辑已从选择清单与静态资源中移除。

论文依据 `../34925_FlowTrack_Controlling_Ed.pdf`，方法核对 `../code/wan/text2video.py` 的 carrying 与 Otsu support 实现。评测保留全部原始数值、方向和 CLIP trade-off，不将精选数量与完整评测数量混写。

Source 来自 `../../videos/`，FlowTrack 来自 `../FlowTrack/FlowTrack/edit1…edit6/`。完整 prompt 来自工作区 `bench/FiVE-Bench/files/flowtrack_ablation_direct_execution_edit*_existing.json`。

未使用临时参数扫描、其他论文结果或合成占位视频。每例的 Source / FlowTrack 视频具有相同分辨率、帧率、帧数与时长。只做 H.264 CRF 22 网页重编码和 faststart，不裁切、插帧或改变原始速度。图库封面裁切仅影响卡片显示，主播放器保留完整画面。

约 52 段网页视频，体积随筛选结果自动生成。大播放器只加载当前案例；首屏与结果墙的动态预览只在进入视口时加载，并在离屏时暂停。素材映射和 metadata 见 `assets/provenance.json`。

`assets/FlowTrack-code.zip` 打包 `../code/`，排除 `.git` 和缓存，不包含模型权重。当前 GitHub 地址无法公开访问，因此使用本地代码下载；公开仓库就绪后可替换下载链接。

当前 PDF 仍是匿名投稿版，页面未编造作者、机构、arXiv、DOI 或 BibTeX。正式信息就绪后，在 `index.html` 补入作者机构，并替换 `assets/FlowTrack-paper.pdf`。

## 更新和部署

修改 `scripts/prepare_assets.py` 中的 `SELECTION` 后，在完整工作区执行：

```sh
python3 it2v_edit_zjl/nips/demo/scripts/prepare_assets.py
```

使用 `--force` 可重新编码已有视频。需要 FFmpeg / FFprobe。脚本检查素材匹配、生成视频和封面、更新案例数据和来源记录，复制论文并打包实现。

发布时将整个 demo 目录上传至 GitHub Pages、Netlify 或静态 HTTP 服务即可，无需构建；相对资源路径支持子目录部署。`serve.py`、`scripts/`、README 无需上传。

## 设计参考

本轮从外部论文主页重新调研，并整体替换上一版视觉设计；未参考工作区其他 demo。详细观察、设计取舍与验证记录见 [DESIGN_REFERENCES.md](DESIGN_REFERENCES.md)。

- TokenFlow：https://diffusion-tokenflow.github.io/
- RAVE：https://rave-video.github.io/
- FlowEdit：https://matankleiner.github.io/flowedit/
- Dreamix：https://dreamix-video-editing.github.io/

Manrope 字体本地自托管，授权见 `assets/fonts/OFL.txt`。页面不请求外部字体、脚本或视频服务。
