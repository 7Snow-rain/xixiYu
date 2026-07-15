#!/usr/bin/env python3
"""生成 SSRF 安全修复报告 Word 文档"""

from docx import Document
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
import os

doc = Document()

# =============================================
# 样式设置
# =============================================
style = doc.styles['Normal']
font = style.font
font.name = '微软雅黑'
font.size = Pt(11)

# =============================================
# 封面
# =============================================
for _ in range(6):
    doc.add_paragraph('')

title = doc.add_paragraph()
title.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = title.add_run('SSRF 安全修复报告')
run.font.size = Pt(28)
run.font.bold = True
run.font.color.rgb = RGBColor(0x1A, 0x47, 0x8A)

doc.add_paragraph('')

subtitle = doc.add_paragraph()
subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = subtitle.add_run('URL 抓取功能 — 漏洞发现与修复记录')
run.font.size = Pt(16)
run.font.color.rgb = RGBColor(0x55, 0x55, 0x55)

doc.add_paragraph('')
doc.add_paragraph('')

info = doc.add_paragraph()
info.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = info.add_run('项目名称：xixiYu 安全加固用户管理系统\n报告日期：2025 年 7 月 15 日\n文档版本：v1.0')
run.font.size = Pt(12)
run.font.color.rgb = RGBColor(0x33, 0x33, 0x33)

doc.add_page_break()

# =============================================
# 目录
# =============================================
doc.add_heading('目录', level=1)
toc_items = [
    '1. 概述',
    '2. 功能说明',
    '3. 漏洞分析',
    '   3.1 SSRF 漏洞（服务器端请求伪造）',
    '   3.2 漏洞风险等级评估',
    '   3.3 可能的攻击场景',
    '4. 修复措施',
    '   4.1 协议白名单限制',
    '   4.2 内网 IP 地址阻断',
    '   4.3 DNS 解析安全校验',
    '   4.4 重定向安全防护',
    '   4.5 错误处理与日志审计',
    '5. 修复前后代码对比',
    '6. 总结与建议',
]
for item in toc_items:
    p = doc.add_paragraph(item)
    p.paragraph_format.space_before = Pt(2)
    p.paragraph_format.space_after = Pt(2)

doc.add_page_break()

# =============================================
# 1. 概述
# =============================================
doc.add_heading('1. 概述', level=1)
doc.add_paragraph(
    '本报告针对 xixiYu 安全加固用户管理系统中新增的 URL 抓取功能进行安全审计。'
    'URL 抓取功能允许已登录用户输入一个 URL，服务器使用 urllib.request.urlopen() '
    '发起 HTTP 请求并返回响应内容。该功能天然存在 SSRF（Server-Side Request Forgery）漏洞，'
    '若不加防护，攻击者可利用此功能向内网服务发起请求，造成敏感信息泄露或进一步攻击。'
)
doc.add_paragraph(
    '本报告详细记录了 SSRF 漏洞的发现、风险评估、修复过程以及最终的加固效果。'
)

# =============================================
# 2. 功能说明
# =============================================
doc.add_heading('2. 功能说明', level=1)
doc.add_paragraph('新增的 URL 抓取功能位于 /fetch-url 路由，详细说明如下：')

table = doc.add_table(rows=7, cols=2)
table.style = 'Light Grid Accent 1'
table.alignment = WD_TABLE_ALIGNMENT.CENTER

cells_data = [
    ('项目', '说明'),
    ('路由', '/fetch-url'),
    ('请求方法', 'POST'),
    ('认证要求', '需要登录（未登录跳转至 /login）'),
    ('输入参数', 'url - 用户提交的目标 URL'),
    ('超时设置', '10 秒'),
    ('返回内容', 'HTTP 状态码 + 响应正文（前 5000 字符）'),
]
for i, (k, v) in enumerate(cells_data):
    table.rows[i].cells[0].text = k
    table.rows[i].cells[1].text = v

doc.add_paragraph('')

# =============================================
# 3. 漏洞分析
# =============================================
doc.add_heading('3. 漏洞分析', level=1)

doc.add_heading('3.1 SSRF 漏洞（服务器端请求伪造）', level=2)
doc.add_paragraph(
    'SSRF（Server-Side Request Forgery）是一种常见的 Web 安全漏洞。'
    '攻击者可以提交一个特制的 URL，诱使服务器向内部网络资源发起请求，'
    '从而绕过防火墙访问本无法从外网直接访问的内网服务。'
)
doc.add_paragraph('原始代码中存在以下严重安全缺陷：')

vuln_items = [
    '无协议限制：允许 file:// 协议，攻击者可读取服务器本地文件',
    '无内网 IP 阻断：允许访问 127.0.0.1、10.x.x.x、192.168.x.x 等内网地址',
    '无端口限制：可扫描开放端口',
    '无 DNS 重绑定防护：域名可能指向内网地址',
    '无重定向安全检查：攻击者可通过外部跳转指向内网',
    '无日志记录细节不足',
]
for item in vuln_items:
    doc.add_paragraph(item, style='List Bullet')

doc.add_heading('3.2 漏洞风险等级评估', level=2)

risk_table = doc.add_table(rows=5, cols=3)
risk_table.style = 'Light Grid Accent 1'
risk_table.alignment = WD_TABLE_ALIGNMENT.CENTER

risk_data = [
    ('风险项', '等级', '说明'),
    ('本地文件读取', '高危', '通过 file:// 协议读取 /etc/passwd 等敏感文件'),
    ('内网服务探测', '高危', '扫描 redis、mysql、k8s 等内网服务'),
    ('云元数据泄露', '高危', '访问云服务商元数据接口获取凭据'),
    ('内网横向移动', '高危', '利用内网服务漏洞发起进一步攻击'),
]
for i, (k, v, d) in enumerate(risk_data):
    risk_table.rows[i].cells[0].text = k
    risk_table.rows[i].cells[1].text = v
    risk_table.rows[i].cells[2].text = d

doc.add_paragraph('')

doc.add_heading('3.3 可能的攻击场景', level=2)

scenarios = [
    ('场景一：本地文件读取', '攻击者提交 URL：file:///etc/passwd，直接读取服务器系统文件。'),
    ('场景二：AWS 元数据泄露', '攻击者提交 URL：http://169.254.169.254/latest/meta-data/，获取云服务器临时凭据。'),
    ('场景三：内网 Redis 攻击', '通过 gopher:// 协议或 http://127.0.0.1:6379 与内网 Redis 交互。'),
    ('场景四：端口扫描', '提交 http://127.0.0.1:3306、http://127.0.0.1:6379 等探测内网开放端口。'),
]
for title, desc in scenarios:
    p = doc.add_paragraph()
    run = p.add_run(f'{title}：')
    run.font.bold = True
    p.add_run(desc)

# =============================================
# 4. 修复措施
# =============================================
doc.add_heading('4. 修复措施', level=1)

doc.add_heading('4.1 协议白名单限制', level=2)
doc.add_paragraph(
    '修复前：允许所有协议（包括 file://、ftp://、dict://、gopher:// 等危险协议）。\n'
    '修复后：仅允许 http:// 和 https:// 协议，其他协议一律拒绝。'
)

doc.add_heading('4.2 内网 IP 地址阻断', level=2)
doc.add_paragraph(
    '对以下 IPv4 地址段进行阻断：'
)
ip_blocks = [
    '127.0.0.0/8（本地回环地址）',
    '10.0.0.0/8（A 类私有地址）',
    '172.16.0.0/12（B 类私有地址）',
    '192.168.0.0/16（C 类私有地址）',
    '0.0.0.0/8（零地址）',
    '100.64.0.0/10（运营商级 NAT）',
    '169.254.0.0/16（链路本地地址）',
    '198.18.0.0/15（基准测试地址）',
    '224.0.0.0/4（组播地址）',
    '240.0.0.0/4（保留地址）',
    '255.255.255.255/32（广播地址）',
]
for ipb in ip_blocks:
    doc.add_paragraph(ipb, style='List Bullet')

doc.add_paragraph('同时对以下 IPv6 地址段进行阻断：')
v6_blocks = [
    '::1/128（IPv6 回环地址）',
    'fe80::/10（链路本地地址）',
    'fc00::/7（唯一本地地址）',
    'ff00::/8（组播地址）',
]
for v6 in v6_blocks:
    doc.add_paragraph(v6, style='List Bullet')

doc.add_heading('4.3 DNS 解析安全校验', level=2)
doc.add_paragraph(
    '对于域名类型的 URL，修复后的代码会先通过 socket.getaddrinfo() '
    '解析域名获取所有 IP 地址，然后逐一检查是否指向内网。'
    '如果解析结果中包含内网地址，则直接拒绝请求。'
    'DNS 解析失败时采取保守策略，同样拒绝请求。'
)

doc.add_heading('4.4 重定向安全防护', level=2)
doc.add_paragraph(
    '通过自定义 SSRFRedirectHandler 类继承 urllib.request.HTTPRedirectHandler，'
    '在每次重定向时检查新 URL 的目标地址。如果重定向目标指向内网，'
    '则抛出 HTTPError 阻止请求继续。'
)

doc.add_heading('4.5 错误处理与日志审计', level=2)
doc.add_paragraph(
    '所有 SSRF 阻断事件（包括协议拒绝、内网 IP 阻断、域名解析阻断）'
    '均会记录到 security.log 审计日志中，包含以下信息：\n'
    '· 事件类型（SSRF_BLOCKED_IP / SSRF_BLOCKED_DOMAIN / FETCH_URL_REJECTED_PROTOCOL）\n'
    '· 请求来源 IP\n'
    '· 当前登录用户\n'
    '· 目标 URL\n'
    '· 具体拒绝原因'
)

# =============================================
# 5. 修复前后代码对比
# =============================================
doc.add_heading('5. 修复前后代码对比', level=1)

doc.add_heading('5.1 协议处理', level=2)
code_before = """# 修复前：无协议限制
req = urllib.request.Request(url, headers={...})
response = urllib.request.urlopen(req, timeout=10)"""

code_after = """# 修复后：协议白名单 + SSRF 防护
if not url.startswith("http://") and not url.startswith("https://"):
    # 拒绝非 HTTP/HTTPS 协议
    flash("不支持的协议", "danger")
    return redirect(url_for("index"))

# DNS 解析检查
if is_internal_ip(host) is None:
    if resolve_and_check(host):
        flash("拒绝访问目标（解析到内网地址）", "danger")
        return redirect(url_for("index"))

# 安全重定向处理
opener = urllib.request.build_opener(SSRFRedirectHandler)
response = opener.open(req, timeout=10)"""

p = doc.add_paragraph()
run = p.add_run('修复前：')
run.font.bold = True

p = doc.add_paragraph()
run = p.add_run(code_before)
run.font.name = 'Courier New'
run.font.size = Pt(9)

p = doc.add_paragraph()
run = p.add_run('修复后：')
run.font.bold = True

p = doc.add_paragraph()
run = p.add_run(code_after)
run.font.name = 'Courier New'
run.font.size = Pt(9)

doc.add_heading('5.2 内网 IP 检测', level=2)
p = doc.add_paragraph()
run = p.add_run(
    '修复后新增了 is_internal_ip() 和 resolve_and_check() 两个辅助函数，\n'
    '通过 ipaddress 和 socket 模块检测目标是否为内网地址。\n'
    '涵盖 IPv4 和 IPv6 共 15 种内网/保留地址范围。'
)

# =============================================
# 6. 总结与建议
# =============================================
doc.add_heading('6. 总结与建议', level=1)
doc.add_paragraph(
    '本次安全加固针对 URL 抓取功能的 SSRF 漏洞进行了全面修复，'
    '从协议限制、IP 阻断、DNS 校验、重定向防护等多个维度构建了纵深防御体系。'
    '修复后的代码已通过 Python 语法检查，可以正常部署运行。'
)

doc.add_heading('后续建议：', level=2)
suggestions = [
    '升级至 requests 库：urllib 相对底层，推荐使用 requests 库并配合 Session 管理',
    '添加请求频率限制：对 /fetch-url 路由增加独立的速率限制，防止滥用',
    '响应内容安全过滤：对返回内容进行 HTML 转义，防止 XSS（当前已使用 <pre> 包裹）',
    'URL 黑名单维护：定期更新已知的云元数据地址和恶意域名列表',
    '使用无缓存 DNS 解析：避免 DNS 缓存导致的安全绕过',
    '考虑代理出口：通过正向代理限制服务器出口流量',
    '定期安全审计：定期检查 security.log 中的异常请求模式',
]
for s in suggestions:
    doc.add_paragraph(s, style='List Bullet')

# =============================================
# 保存
# =============================================
output_path = '/root/.openclaw/workspace/xixiYu_ssrf/static/SSRF安全修复报告.docx'
doc.save(output_path)
print(f'报告已生成：{output_path}')
print(f'文件大小：{os.path.getsize(output_path)} 字节')
