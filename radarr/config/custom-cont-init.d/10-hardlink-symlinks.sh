#!/usr/bin/with-contenv bash
# 让 radarr 沿用已配置路径 /movies、/downloads，
# 但两者软链到单一 /share 挂载下，使导入时可硬链接而非复制。

make_link() {
  link="$1"
  target="$2"
  if [ -L "$link" ]; then
    ln -sfn "$target" "$link"
    return
  fi
  if [ -d "$link" ]; then
    if mountpoint -q "$link"; then
      echo "[hardlink-symlinks] $link 是挂载点，保持不变"
      return
    fi
    if ! rmdir "$link" 2>/dev/null; then
      echo "[hardlink-symlinks] $link 非空目录，保持不变"
      return
    fi
  fi
  ln -s "$target" "$link"
}

make_link /movies /share/Movies
make_link /downloads /share/Downloads
