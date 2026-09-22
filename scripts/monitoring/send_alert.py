#!/usr/bin/env python3
"""
告警邮件发送 + 防刷机制

用法:
    python3 send_alert.py --subject "磁盘告警" --body "<h3>/dev/vda1 使用率 92%</h3>"
    python3 send_alert.py --subject "每日报告" --body "..." --no-cooldown
"""

import argparse
import hashlib
import os
import smtplib
import sys
import time
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

SMTP_HOST = "smtp.qq.com"
SMTP_PORT = 465
SMTP_USER = "1154406467@qq.com"
ALERT_RECIPIENT = "1154406467@qq.com"
COOLDOWN_SECONDS = 1800  # 30 分钟
CACHE_DIR = Path("/tmp/icube_monitor_cache")

CONFIG_PATH = Path(__file__).parent / "config.sh"


def load_config():
    """从 config.sh 读取 SMTP_AUTH_CODE"""
    auth_code = os.environ.get("MONITOR_MAIL_AUTH_CODE", "")
    if not auth_code and CONFIG_PATH.exists():
        for line in CONFIG_PATH.read_text().splitlines():
            if "MONITOR_MAIL_AUTH_CODE" in line and "=" in line:
                val = line.split("=", 1)[1].strip()
                if val and not val.startswith("${"):
                    auth_code = val.strip('"').strip("'")
    return auth_code


def send_email(subject, html_body, skip_cooldown=False):
    if not skip_cooldown:
        alert_key = hashlib.md5(subject.encode()).hexdigest()
        if should_cooldown(alert_key):
            return False

    auth_code = load_config()
    if not auth_code:
        print("[ALERT] MONITOR_MAIL_AUTH_CODE 未配置，跳过邮件发送", file=sys.stderr)
        return False

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"[ICube监控] {subject}"
    msg["From"] = f"ICube监控 <{SMTP_USER}>"
    msg["To"] = ALERT_RECIPIENT
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    try:
        with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, timeout=30) as smtp:
            smtp.login(SMTP_USER, auth_code)
            smtp.sendmail(SMTP_USER, [ALERT_RECIPIENT], msg.as_string())
        print(f"[ALERT] 邮件已发送: {subject}")
        return True
    except Exception as e:
        print(f"[ALERT] 邮件发送失败: {e}", file=sys.stderr)
        return False


def should_cooldown(alert_key):
    """检查同一告警是否在冷却期内"""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_file = CACHE_DIR / f"{alert_key}.cache"
    if cache_file.exists():
        elapsed = time.time() - cache_file.stat().st_mtime
        if elapsed < COOLDOWN_SECONDS:
            print(f"[ALERT] {alert_key} 在冷却期内（{int(COOLDOWN_SECONDS - elapsed)}s 剩余），跳过")
            return True
    cache_file.write_text(str(time.time()))
    return False


def main():
    parser = argparse.ArgumentParser(description="发送告警邮件")
    parser.add_argument("--subject", required=True, help="邮件主题")
    parser.add_argument("--body", required=True, help="HTML 正文")
    parser.add_argument("--no-cooldown", action="store_true", help="跳过防刷检查")
    args = parser.parse_args()

    send_email(args.subject, args.body, skip_cooldown=args.no_cooldown)


if __name__ == "__main__":
    main()
