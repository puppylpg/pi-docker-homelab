# 树莓派电影自动下载站使用说明

## 已部署服务

| 服务 | 地址 | 用途 |
|------|------|------|
| **Radarr** | http://192.168.1.7:7878 | 电影搜索、管理、自动整理 |
| **Jackett** | http://192.168.1.7:9117 | 种子索引器聚合 |
| **qBittorrent** | http://192.168.1.7:8085 | BT 下载客户端 |
| **Bazarr** | http://192.168.1.7:6767 | 自动下载字幕 |

## 默认账号

- **qBittorrent**
  - 用户名：`admin`
  - 密码：`pi123456`
  - 如需修改：登录后 → 设置 → Web UI

- **Radarr / Jackett**
  - 当前未设置密码（内网使用）
  - 如需设置：进入各自 Settings → General → Authentication

## 已完成的配置

我已经帮你把三个服务串好了：

- **Jackett** 已添加 The Pirate Bay 索引器，走 V2Ray HTTP 代理访问外网。
- **Radarr** 已添加：
  - 下载器 qBittorrent（容器内地址 `qbittorrent:8085`）
  - 索引器 TPB（通过 Jackett 的 Torznab 接口）
  - 电影根目录 `/movies`（对应 Samba 的 `/share/Movies`）
  - 4K 画质配置 **Ultra-HD**（优先 REMUX → BluRay-2160p → WEB-DL-2160p，排除低质量 HDTV-2160p）
- **Bazarr** 已部署，配置了中英文双语字幕配置：
  - 电影下载完成后自动搜索 **中文 + 英文字幕**
  - 两个字幕都下好后，自动生成 **中英双语字幕**（`.zh+en.srt`，中文在上、英文在下）
  - ⚠️ 字幕来源目前主要依赖 **OpenSubtitles.com**，需要你免费注册一个账号并填入用户名密码才能用
- **测试下载**：已自动开始下载《速度与激情 1》（The Fast and the Furious, 2001）**4K UHD BluRay 版本**。

## 目录说明

| 路径 | 用途 |
|------|------|
| `/share/Downloads` | qBittorrent 临时下载目录 |
| `/share/Movies` | Radarr 整理后的电影目录（即 Samba 共享的 Movies） |

下载完成后，Radarr 会自动把电影重命名并整理到 `/share/Movies/<电影名>/<电影名>.mkv`。

## 使用流程

1. 打开 **Radarr**：http://192.168.1.7:7878
2. 点击 **Add New**
3. 搜索电影英文名（如 `The Fast and the Furious`）
4. 选择电影后，在 **Quality Profile** 里选择：
   - **Ultra-HD**：优先下载 4K
   - **HD-1080p**：下载 1080p（更快、文件更小）
5. Radarr 会自动搜索 TPB，选择版本下载
6. 在 **qBittorrent** 里可以看到下载进度
7. 下载完成后在 `/share/Movies` 里看成品

## 指定画质的方法

### 全局调整 4K 配置

进入 **Radarr → Settings → Profiles → Ultra-HD**：

- 从上到下是优先级，越上面越优先。
- 已配置为：`Remux-2160p` > `Bluray-2160p` > `WEB-DL-2160p` > `WEBRip-2160p`
- `HDTV-2160p` 已禁用（画质差）。

### 排除特定小组（如 YIFY）

1. **Settings → Custom Formats → Add**
2. Name 填 `YIFY`
3. Conditions → `Release Title` contains `YIFY`
4. 在 **Ultra-HD** 或 **HD-1080p** Profile 里，把 YIFY 分数设为 `-10000`（直接排除）

## 字幕说明

### 自动下载流程

1. Radarr 下载完电影后，会自动通知 Bazarr
2. Bazarr 搜索 **中文 + 英文字幕**
3. 下载完成后，Bazarr 的脚本会自动合并成一条 **中英双语字幕**（`.zh+en.srt`）
4. 最终文件结构示例：
   ```
   /share/Movies/The Fast and the Furious (2001)/
   ├── The Fast and the Furious (2001).mkv
   ├── The Fast and the Furious (2001).en.srt      # 英文字幕
   ├── The Fast and the Furious (2001).zh.srt      # 中文字幕
   └── The Fast and the Furious (2001).zh+en.srt   # 中英双语字幕
   ```

### 为什么现在还没下字幕？

因为字幕源 **OpenSubtitles.com 需要你注册账号**。

注册方法：
1. 打开 https://www.opensubtitles.com/
2. 点击右上角 Sign Up，用邮箱注册
3. 登录后进入 **Profile → API Key**，记下用户名和密码
4. 打开 Bazarr：http://192.168.1.7:6767
5. 进入 **Settings → Providers → OpenSubtitles.com**
6. 填入用户名和密码，保存

填好后，已下载的电影会自动补字幕，新电影下载完也会自动下字幕。

### 播放器选择字幕

大多数播放器（VLC、PotPlayer、Kodi、Infuse）都会自动识别同目录下的 `.srt` 字幕：
- 想看中英双语 → 选 `.zh+en.srt`
- 只看中文 → 选 `.zh.srt`
- 只看英文 → 选 `.en.srt`

## 代理说明

实测不代理无法访问公开 BT 站，所以 Jackett 已经配了代理：

- Jackett 通过 Docker 环境变量走 V2Ray HTTP 代理：
  ```yaml
  - HTTP_PROXY=http://172.18.0.1:10809
  - HTTPS_PROXY=http://172.18.0.1:10809
  - NO_PROXY=localhost,127.0.0.1,qbittorrent,radarr,jackett,jellyfin
  ```
- qBittorrent 的 BT 下载目前**没走代理**，速度取决于种子热度和你网络的公网连通性。
- 如需给 qBittorrent 配代理：进入 qBittorrent WebUI → 工具 → 选项 → 连接 → 代理，类型选 SOCKS5，地址填 `172.18.0.1`，端口 `10808`。

## 常用维护命令

```bash
cd /home/pi/docker

# 查看状态
docker compose ps

# 重启所有服务
docker compose restart

# 只看日志
docker compose logs -f radarr jackett qbittorrent bazarr

# 停止电影下载相关服务
docker compose stop radarr jackett qbittorrent bazarr
```

## 注意事项

- 当前磁盘剩余约 30GB，下载 4K 电影前留意空间（一部 4K 通常 15-30GB）。
- BT 下载需要公网 IP 或做好端口映射（`6881`）才能有更好速度。
- 老电影或冷门的 4K 资源可能种子少、速度很慢，必要时可切回 1080p。
- Jackett 目前未设置密码，建议只在可信内网使用，或设置 Admin Password。
- 部分资源涉及版权问题，请遵守当地法律法规。
