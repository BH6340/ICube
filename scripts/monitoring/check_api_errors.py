#!/usr/bin/env python3
"""
解析 Django 日志，计算最近 10 分钟 API 错误率和平均响应时间

日志格式（Loguru JSON）:
  {"timestamp": "...", "level": "INFO", "message": "API_REQUEST method=GET path=/api/... status=200 duration=0.123"}

触发条件:
  - 5xx 率 > API_ERROR_RATE_THRESHOLD %
  - 平均响应时间 > API_SLOW_THRESHOLD 秒
"""

import json
import os
import re
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
sys.path.insert(0, str(SCRIPT_DIR))

from send_alert import send_email

LOG_DIR = os.environ.get("LOG_DIR", "/var/log/icube")
LOG_FILE = f"{LOG_DIR}/cube-all.log"
TIME_WINDOW = 10  # 分钟

ERROR_RATE_THRESHOLD = 5.0  # 5xx 率 %
SLOW_THRESHOLD = 2.0  # 平均响应时间秒

REQUEST_PATTERN = re.compile(
    r"API_REQUEST method=(\w+) path=(\S+) status=(\d+) duration=([\d.]+)"
)


def read_recent_logs(minutes):
    """从 Docker 容器中读取最近 N 分钟的日志"""
    since = (datetime.now() - timedelta(minutes=minutes)).strftime("%Y-%m-%dT%H:%M")
    try:
        result = subprocess.run(
            [
                "docker", "exec", "icube_api",
                "tail", "-n", "10000", f"/var/log/icube/cube-all.log",
            ],
            capture_output=True, text=True, timeout=30,
        )
        return result.stdout
    except Exception as e:
        print(f"[API_CHECK] 读取日志失败: {e}", file=sys.stderr)
        return ""


def parse_requests(log_text):
    """解析日志中的 API_REQUEST 行"""
    requests = []
    for line in log_text.strip().splitlines():
        if "API_REQUEST" not in line:
            continue
        match = REQUEST_PATTERN.search(line)
        if match:
            requests.append({
                "method": match.group(1),
                "path": match.group(2),
                "status": int(match.group(3)),
                "duration": float(match.group(4)),
            })
    return requests


def check():
    log_text = read_recent_logs(TIME_WINDOW)
    requests = parse_requests(log_text)

    if not requests:
        print("[API_CHECK] 最近 10 分钟无 API 请求记录")
        return

    total = len(requests)
    errors_5xx = [r for r in requests if r["status"] >= 500]
    avg_duration = sum(r["duration"] for r in requests) / total
    error_rate = len(errors_5xx) / total * 100

    # 最慢 Top5
    slowest = sorted(requests, key=lambda r: r["duration"], reverse=True)[:5]

    alerts = []
    if error_rate > ERROR_RATE_THRESHOLD:
        alerts.append(
            f"5xx 错误率 {error_rate:.1f}% 超过阈值 {ERROR_RATE_THRESHOLD}%（{len(errors_5xx)}/{total}）"
        )
    if avg_duration > SLOW_THRESHOLD:
        alerts.append(
            f"平均响应时间 {avg_duration:.3f}s 超过阈值 {SLOW_THRESHOLD}s"
        )

    if alerts:
        slowest_html = "".join(
            f"<tr><td>{r['method']}</td><td>{r['path']}</td><td>{r['status']}</td><td>{r['duration']:.3f}s</td></tr>"
            for r in slowest
        )
        body = f"""
        <h3>API 指标异常</h3>
        <p>最近 {TIME_WINDOW} 分钟共 {total} 次请求，{len(errors_5xx)} 次 5xx 错误</p>
        <p><b>告警项：</b></p>
        <ul>{''.join(f'<li>{a}</li>' for a in alerts)}</ul>
        <h4>最慢 Top5 接口</h4>
        <table border='1' cellpadding='6' style='border-collapse:collapse'>
        <tr><th>方法</th><th>路径</th><th>状态码</th><th>耗时</th></tr>
        {slowest_html}
        </table>
        """
        send_email("API 指标告警", body)
    else:
        print(f"[API_CHECK] 正常: {total} 次请求, 5xx={len(errors_5xx)}, 平均={avg_duration:.3f}s")


if __name__ == "__main__":
    check()
