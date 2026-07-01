# 自动下载字幕完整说明

这篇文档专门讲字幕：怎么配置、怎么工作、遇到问题怎么办。

## 一、整体架构

```
Radarr 下载完电影
        ↓
   自动通知 Bazarr
        ↓
Bazarr 搜索中文字幕 + 英文字幕
        ↓
  下载两个字幕文件
        ↓
  自动合并成中英双语字幕
        ↓
  放在电影同目录下
```

## 二、访问 Bazarr

打开：

```
http://192.168.1.7:6767
```

首次打开无需密码。

## 三、为什么必须注册 OpenSubtitles.com

Bazarr 需要从网上的字幕源下载字幕。目前免费的、支持中英文的、比较稳定的是 **OpenSubtitles.com**。

它要求注册账号（免费），因为服务器资源有限，需要限流。

### 注册步骤

1. 打开 https://www.opensubtitles.com/
2. 点击右上角 **Sign Up**
3. 用邮箱注册一个账号
4. 登录后，进入 **Profile / 个人资料**
5. 找到 **API Key** 或 **API consumer**
6. 记下你的：**用户名** 和 **密码**

> 注意：是 OpenSubtitles.**com**，不是 .org。

### 填入 Bazarr

1. 打开 http://192.168.1.7:6767
2. 点击顶部 **Settings**
3. 左侧选择 **Providers**
4. 找到 **OpenSubtitles.com**
5. 填入：
   - **Username**：你的用户名
   - **Password**：你的密码
6. 点击 **Save**
7. 回到 Bazarr 首页，等待它自动搜索字幕

## 四、怎么知道字幕在下了

在 Bazarr 首页，你会看到电影列表：

- 绿色勾：字幕已下载完成
- 黄色感叹号：正在搜索或缺少字幕
- 点击电影，可以看到具体缺少哪种语言的字幕

## 五、最终文件结构

电影下载完成后，电影目录里会有：

```
/share/Movies/The Fast and the Furious (2001)/
├── The Fast and the Furious (2001).mkv
├── The Fast and the Furious (2001).en.srt      # 英文字幕
├── The Fast and the Furious (2001).zh.srt      # 中文字幕
└── The Fast and the Furious (2001).zh+en.srt   # 中英双语字幕
```

## 六、播放器里怎么选字幕

主流播放器会自动识别同目录的 `.srt` 文件：

| 你想看的 | 选择的字幕文件 |
|----------|----------------|
| 中英双语同屏 | `.zh+en.srt` |
| 只看中文 | `.zh.srt` |
| 只看英文 | `.en.srt` |
| 不看字幕 | 关闭字幕 |

## 七、如果不想用双语字幕

如果你只想要单独的中文字幕和英文字幕，不想要 `.zh+en.srt` 合并文件：

1. 打开 `/home/pi/docker/bazarr/config/config/config.yaml`
2. 找到：
   ```yaml
   postprocessing_cmd: 'python3 /config/scripts/merge_bilingual_subs.py'
   use_postprocessing: true
   ```
3. 改成：
   ```yaml
   postprocessing_cmd: ''
   use_postprocessing: false
   ```
4. 重启 Bazarr：
   ```bash
   cd /home/pi/docker && docker compose restart bazarr
   ```

## 八、如果某部电影没下到字幕

可能原因：

1. **OpenSubtitles.com 账号没填** → 按第三节配置
2. **这部电影在 OpenSubtitles 上没有中文字幕** → 老电影或冷门电影常见
3. **文件名太奇怪，匹配不到** → Bazarr 靠电影名匹配，文件名尽量规范
4. **网络问题** → 检查 V2Ray 是否正常运行

### 手动补救

1. 打开 Bazarr 首页
2. 找到那部电影
3. 点击 **Search** 或放大镜图标
4. 手动选择一个字幕下载

## 九、常用命令

```bash
cd /home/pi/docker

# 重启 Bazarr
docker compose restart bazarr

# 看 Bazarr 日志
docker compose logs -f bazarr

# 手动触发一部电影的字幕搜索
# 在 Bazarr 网页里点击电影 → Search
```

## 十、注意事项

- 字幕下载是在电影文件下载**完成之后**才开始的。
- 合并双语字幕的脚本已经放在 `/home/pi/docker/bazarr/config/scripts/merge_bilingual_subs.py`。
- 如果以后想增加更多字幕源（如 Subscene、SubHD），可以在 Bazarr 的 Providers 里添加，但大多数都需要账号或反验证码。
