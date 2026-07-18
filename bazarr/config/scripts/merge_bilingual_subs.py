#!/usr/bin/env python3
"""
Bazarr post-processing script: merge Chinese and English subtitles into bilingual subtitle.

This script is called by Bazarr after a subtitle is downloaded.
It checks if both .zh.srt and .en.srt exist for the same video,
and creates a .zh+en.srt bilingual subtitle.

Environment variables provided by Bazarr:
- BAZARR_EPISODE_PATH / BAZARR_MOVIE_PATH: path to video file
- BAZARR_SUBTITLE_PATH: path to downloaded subtitle
- BAZARR_SUBTITLE_LANGUAGE: language of downloaded subtitle (en, zh, etc.)
"""

import os
import sys
import re
import glob
from pathlib import Path


def parse_srt(content):
    """Parse SRT content into list of (index, start, end, text)."""
    entries = []
    # Normalize line endings
    content = content.replace('\r\n', '\n').replace('\r', '\n')
    # Split by double newline
    blocks = re.split(r'\n\s*\n', content.strip())
    for block in blocks:
        lines = block.strip().split('\n')
        if len(lines) < 3:
            continue
        index = lines[0].strip()
        timing = lines[1].strip()
        text = '\n'.join(lines[2:]).strip()
        if not text:
            continue
        m = re.match(r'(\d{2}:\d{2}:\d{2},\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2},\d{3})', timing)
        if not m:
            continue
        entries.append({
            'index': index,
            'start': m.group(1),
            'end': m.group(2),
            'text': text
        })
    return entries


def format_srt(entries):
    """Format entries back to SRT content."""
    output = []
    for i, e in enumerate(entries, 1):
        output.append(str(i))
        output.append(f"{e['start']} --> {e['end']}")
        output.append(e['text'])
        output.append('')
    return '\n'.join(output).strip() + '\n'


def is_bilingual_zh_srt(zh_path):
    """检测一个 .zh.srt 是否本身已经是中英双语字幕。

    判断逻辑：统计所有字幕条目，如果包含纯 ASCII/英文单词的行数
    占总行数一定比例，则认为该文件已经是中英双语。
    """
    try:
        with open(zh_path, 'r', encoding='utf-8-sig', errors='ignore') as f:
            entries = parse_srt(f.read())
    except Exception as e:
        print(f"Failed to parse {zh_path}: {e}")
        return False

    if not entries:
        return False

    total_lines = 0
    english_lines = 0
    for e in entries:
        for line in e['text'].split('\n'):
            line = line.strip()
            if not line:
                continue
            total_lines += 1
            # 包含连续英文字母/数字，且中文字符较少的行算作英文行
            has_ascii_word = bool(re.search(r'[a-zA-Z]{2,}', line))
            chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', line))
            if has_ascii_word and chinese_chars < 3:
                english_lines += 1

    if total_lines == 0:
        return False

    ratio = english_lines / total_lines
    print(f"{zh_path}: {english_lines}/{total_lines} lines look English-only (ratio {ratio:.2f})")
    # 如果超过 30% 的行是英文，认为已经是中英双语
    return ratio >= 0.30


def create_bilingual_from_zh(zh_path, output_path):
    """直接把已有的中英双语 .zh.srt 复制为 .zh+en.srt。"""
    try:
        with open(zh_path, 'r', encoding='utf-8-sig', errors='ignore') as f:
            content = f.read()
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Created bilingual subtitle from existing bilingual zh.srt: {output_path}")
        return True
    except Exception as e:
        print(f"Failed to copy bilingual subtitle: {e}")
        return False


def merge_subtitles(en_path, zh_path, output_path):
    """Merge English and Chinese subtitles."""
    with open(en_path, 'r', encoding='utf-8-sig', errors='ignore') as f:
        en_entries = parse_srt(f.read())
    with open(zh_path, 'r', encoding='utf-8-sig', errors='ignore') as f:
        zh_entries = parse_srt(f.read())

    if not en_entries or not zh_entries:
        print("Empty subtitle entries, skip merging")
        return False

    # Match entries by start time
    en_by_start = {e['start']: e for e in en_entries}
    merged = []
    for zh in zh_entries:
        start = zh['start']
        en = en_by_start.get(start)
        if en:
            # Chinese on top, English below
            text = f"{zh['text']}\n{en['text']}"
            merged.append({
                'start': start,
                'end': zh['end'],
                'text': text
            })
        else:
            merged.append(zh)

    # Add any English entries not matched
    zh_starts = {e['start'] for e in zh_entries}
    for en in en_entries:
        if en['start'] not in zh_starts:
            merged.append(en)

    # Sort by start time
    merged.sort(key=lambda x: x['start'])

    srt_content = format_srt(merged)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(srt_content)
    print(f"Created bilingual subtitle: {output_path}")
    return True


def main():
    subtitle_path = os.environ.get('BAZARR_SUBTITLE_PATH', '')
    if not subtitle_path:
        print("No BAZARR_SUBTITLE_PATH, exit")
        sys.exit(0)

    sub_file = Path(subtitle_path)
    if not sub_file.exists():
        print(f"Subtitle not found: {subtitle_path}")
        sys.exit(0)

    # Determine video stem and language
    # Subtitle filename patterns:
    #   movie.en.srt, movie.zh.srt
    #   movie.en.hi.srt, movie.zh.hi.srt  (hearing impaired variant)
    name = sub_file.stem  # e.g. movie.en or movie.en.hi
    suffix = sub_file.suffix  # .srt
    parent = sub_file.parent

    parts = name.split('.')
    if len(parts) < 2:
        print(f"Cannot detect language from {name}")
        sys.exit(0)

    # Strip optional hearing-impaired marker so it doesn't confuse language detection
    if parts[-1].lower() == 'hi':
        parts = parts[:-1]

    if len(parts) < 2:
        print(f"Cannot detect language from {name}")
        sys.exit(0)

    lang = parts[-1].lower()
    stem = '.'.join(parts[:-1])  # movie

    def find_subtitle(parent, stem, lang, suffix):
        """Find a subtitle, preferring the .hi variant but falling back to plain."""
        hi_path = parent / f"{stem}.{lang}.hi{suffix}"
        if hi_path.exists():
            return hi_path
        return parent / f"{stem}.{lang}{suffix}"

    en_sub = find_subtitle(parent, stem, 'en', suffix)
    zh_sub = find_subtitle(parent, stem, 'zh', suffix)
    bilingual_sub = parent / f"{stem}.zh+en{suffix}"

    if lang == 'en':
        if zh_sub.exists():
            if is_bilingual_zh_srt(zh_sub):
                create_bilingual_from_zh(zh_sub, bilingual_sub)
            else:
                merge_subtitles(en_sub, zh_sub, bilingual_sub)
    elif lang == 'zh':
        if is_bilingual_zh_srt(sub_file):
            create_bilingual_from_zh(sub_file, bilingual_sub)
        elif en_sub.exists():
            merge_subtitles(en_sub, zh_sub, bilingual_sub)
        else:
            print(f"No English subtitle found and zh.srt is not bilingual, skip")
    else:
        print(f"Language {lang} not en/zh, skip merging")


if __name__ == '__main__':
    main()
