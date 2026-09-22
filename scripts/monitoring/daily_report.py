#!/usr/bin/env python3
"""
每日汇总报告 — 每日 08:00 发送

采集：容器状态、磁盘、MySQL、Redis、API 请求统计
"""

import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
sys.path.insert(0, str(SCRIPT_DIR))

from send_alert import send_email

CONTAINERS = [
    "icube_db", "icube_redis", "icube_api",
    "icube_front", "icube_nginx", "icube_cloudflared",
]

REQUEST_PATTERN = re.compile(
    r"API_REQUEST method=(\w+) path=(\S+) status=(\d+) duration=([\d.]+)"
)


def run(cmd):
    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True, timeout=30
        )
        return result.stdout.strip()
    except Exception:
        return "N/A"


def get_container_status():
    rows = ""
    for name in CONTAINERS:
        status = run(f"docker inspect -f '{{{{.State.Status}}}}' {name} 2>/dev/null")
        uptime = run(f"docker inspect -f '{{{{.State.StartedAt}}}}' {name} 2>/dev/null")
        color = "#48c977" if status == "running" else "#e74c3c"
        rows += f"<tr><td>{name}</td><td style='color:{color};font-weight:bold'>{status or 'N/A'}</td><td>{uptime or 'N/A'}</td></tr>"
    return rows


def get_disk_status():
    output = run("df -h --output=target,size,used,avail,pcent 2>/dev/null")
    lines = output.strip().splitlines()
    rows = ""
    for line in lines:
        parts = line.split()
        if len(parts) >= 5:
            usage = parts[-1].replace("%", "")
            try:
                pct = int(usage)
            except ValueError:
                continue
            color = "#e74c3c" if pct >= 85 else "#48c977"
            rows += f"<tr><td>{parts[0]}</td><td>{parts[1]}</td><td>{parts[2]}</td><td>{parts[3]}</td><td style='color:{color}'>{parts[4]}</td></tr>"
    return rows


def get_mysql_status():
    conn = run("docker exec icube_db mysql -uroot -picube_root123 -N -e 'SHOW STATUS WHERE Variable_name IN (\"Threads_connected\",\"Slow_queries\",\"Uptime\")' 2>/dev/null")
    rows = ""
    if conn and conn != "N/A":
        for line in conn.strip().splitlines():
            parts = line.split()
            if len(parts) >= 2:
                rows += f"<tr><td>{parts[0]}</td><td>{parts[1]}</td></tr>"
    return rows or "<tr><td colspan='2'>N/A</td></tr>"


def get_redis_status():
    info = run("docker exec icube_redis redis-cli INFO 2>/dev/null")
    metrics = {}
    for line in info.splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            metrics[k.strip()] = v.strip()
    rows = ""
    for key in ["used_memory_human", "maxmemory_human", "connected_clients",
                "keyspace_hits", "keyspace_misses", "uptime_in_days"]:
        rows += f"<tr><td>{key}</td><td>{metrics.get(key, 'N/A')}</td></tr>"
    return rows or "<tr><td colspan='2'>N/A</td></tr>"


def get_api_status():
    output = run("docker exec icube_api tail -n 50000 /var/log/icube/cube-all.log 2>/dev/null")
    requests = []
    for line in output.splitlines():
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

    if not requests:
        return "<tr><td colspan='4'>无数据</td></tr>"

    total = len(requests)
    errors_5xx = [r for r in requests if r["status"] >= 500]
    errors_4xx = [r for r in requests if 400 <= r["status"] < 500]
    avg_duration = sum(r["duration"] for r in requests) / total

    slowest = sorted(requests, key=lambda r: r["duration"], reverse=True)[:5]
    slowest_html = "".join(
        f"<tr><td>{r['method']}</td><td>{r['path']}</td><td>{r['status']}</td><td>{r['duration']:.3f}s</td></tr>"
        for r in slowest
    )

    return f"""
    <tr><td>总请求数</td><td>{total}</td><td>5xx 错误</td><td style='color:#e74c3c'>{len(errors_5xx)}</td></tr>
    <tr><td>4xx 错误</td><td style='color:#e67e22'>{len(errors_4xx)}</td><td>平均响应时间</td><td>{avg_duration:.3f}s</td></tr>
    {slowest_html}
    """


def build_html():
    today = datetime.now().strftime("%Y-%m-%d")
    return f"""
    <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;">
    <h2 style="color:#2c3e50;">ICube 每日监控报告 — {today}</h2>

    <h3 style="color:#2c3e50; border-bottom:2px solid #3498db; padding-bottom:5px;">容器状态</h3>
    <table border="1" cellpadding="6" style="border-collapse:collapse;width:100%;">
    <tr style="background:#f8f9fa"><th>容器</th><th>状态</th><th>启动时间</th></tr>
    {get_container_status()}
    </table>

    <h3 style="color:#2c3e50; border-bottom:2px solid #3498db; padding-bottom:5px;">磁盘使用</h3>
    <table border="1" cellpadding="6" style="border-collapse:collapse;width:100%;">
    <tr style="background:#f8f9fa"><th>挂载点</th><th>总量</th><th>已用</th><th>可用</th><th>使用率</th></tr>
    {get_disk_status()}
    </table>

    <h3 style="color:#2c3e50; border-bottom:2px solid #3498db; padding-bottom:5px;">MySQL</h3>
    <table border="1" cellpadding="6" style="border-collapse:collapse;width:100%;">
    <tr style="background:#f8f9fa"><th>指标</th><th>值</th></tr>
    {get_mysql_status()}
    </table>

    <h3 style="color:#2c3e50; border-bottom:2px solid #3498db; padding-bottom:5px;">Redis</h3>
    <table border="1" cellpadding="6" style="border-collapse:collapse;width:100%;">
    <tr style="background:#f8f9fa"><th>指标</th><th>值</th></tr>
    {get_redis_status()}
    </table>

    <h3 style="color:#2c3e50; border-bottom:2px solid #3498db; padding-bottom:5px;">API 请求统计（今日日志）</h3>
    <table border="1" cellpadding="6" style="border-collapse:collapse;width:100%;">
    <tr style="background:#f8f9fa"><th>指标</th><th>值</th><th>指标</th><th>值</th></tr>
    {get_api_status()}
    </table>

    <p style="color:#95a5a6;font-size:12px;margin-top:20px;">由 ICube 监控系统自动生成 — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    </div>
    """


if __name__ == "__main__":
    today = datetime.now().strftime("%Y-%m-%d")
    send_email(
        subject=f"每日监控报告 {today}",
        html_body=build_html(),
        skip_cooldown=True,
    )
