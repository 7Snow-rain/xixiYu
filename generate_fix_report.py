#!/usr/bin/env python3
"""Generate Word security fix report for app.py"""

from docx import Document
from docx.shared import Inches, Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.section import WD_ORIENT
from docx.oxml.ns import qn, nsdecls
from docx.oxml import parse_xml
import os

def set_cell_shading(cell, color):
    """Set cell background color."""
    shading = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{color}"/>')
    cell._tc.get_or_add_tcPr().append(shading)

def add_code_block(doc, code_text, caption=""):
    """Add a code block with monospace font and gray background."""
    if caption:
        p = doc.add_paragraph()
        run = p.add_run(caption)
        run.bold = True
        run.font.size = Pt(10)
        run.font.color.rgb = RGBColor(0x33, 0x33, 0x33)
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(2)
    p.paragraph_format.space_after = Pt(6)
    # Add shading to the paragraph
    shading = parse_xml(f'<w:shd {nsdecls("w")} w:val="clear" w:color="auto" w:fill="F0F0F0"/>')
    p._element.get_or_add_pPr().append(shading)
    run = p.add_run(code_text)
    run.font.name = 'Courier New'
    run.font.size = Pt(8.5)
    # Set East Asian font
    r = run._element
    rPr = r.find(qn('w:rPr'))
    if rPr is None:
        rPr = parse_xml(f'<w:rPr {nsdecls("w")}><w:rFonts w:eastAsia="Courier New"/></w:rPr>')
        r.insert(0, rPr)
    else:
        rFonts = rPr.find(qn('w:rFonts'))
        if rFonts is not None:
            rFonts.set(qn('w:eastAsia'), 'Courier New')

def add_styled_heading(doc, text, level=1):
    heading = doc.add_heading(text, level=level)
    for run in heading.runs:
        run.font.color.rgb = RGBColor(0x1A, 0x47, 0x8A)
    return heading

def add_normal_text(doc, text, bold=False):
    p = doc.add_paragraph()
    run = p.add_run(text)
    run.bold = bold
    run.font.size = Pt(11)
    return p

def build_report():
    doc = Document()

    # ---- Page Setup ----
    section = doc.sections[0]
    section.top_margin = Cm(2.5)
    section.bottom_margin = Cm(2.5)
    section.left_margin = Cm(2.5)
    section.right_margin = Cm(2.5)

    # ==================== TITLE PAGE ====================
    for _ in range(6):
        doc.add_paragraph()

    title = doc.add_paragraph()
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = title.add_run("网络安全实训")
    run.bold = True
    run.font.size = Pt(28)
    run.font.color.rgb = RGBColor(0x1A, 0x47, 0x8A)

    subtitle = doc.add_paragraph()
    subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = subtitle.add_run("安全修复总结报告")
    run.bold = True
    run.font.size = Pt(22)
    run.font.color.rgb = RGBColor(0x33, 0x33, 0x33)

    doc.add_paragraph()

    line = doc.add_paragraph()
    line.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = line.add_run("━" * 40)
    run.font.color.rgb = RGBColor(0x1A, 0x47, 0x8A)
    run.font.size = Pt(14)

    doc.add_paragraph()

    info_items = [
        "实训项目：Flask 安全加固演示管理系统",
        "报告版本：V1.0",
        f"生成日期：2026 年 7 月 17 日",
    ]
    for item in info_items:
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = p.add_run(item)
        run.font.size = Pt(12)
        run.font.color.rgb = RGBColor(0x55, 0x55, 0x55)

    doc.add_page_break()

    # ==================== TABLE OF CONTENTS ====================
    add_styled_heading(doc, "目 录", level=1)

    toc_items = [
        ("一、概述", 3),
        ("    1.1 项目背景", 3),
        ("    1.2 修复目标", 3),
        ("二、漏洞发现与修复清单", 4),
        ("    2.1 弱密码策略修复", 4),
        ("    2.2 CSRF 防护增强", 5),
        ("    2.3 路径遍历漏洞修复", 5),
        ("    2.4 命令注入漏洞修复", 6),
        ("    2.5 XXE 漏洞修复", 6),
        ("    2.6 XSS 防护增强", 7),
        ("    2.7 登录暴力破解防护", 7),
        ("    2.8 Session 安全加固", 8),
        ("三、修复前后对比", 9),
        ("四、修复验证", 10),
        ("    4.1 测试步骤", 10),
        ("    4.2 预期结果", 11),
        ("五、总结", 12),
    ]
    for label, page in toc_items:
        p = doc.add_paragraph()
        p.paragraph_format.space_after = Pt(2)
        run = p.add_run(f"{label}{'.' * (60 - len(label) * 2)}{page}")
        run.font.size = Pt(11)

    doc.add_page_break()

    # ==================== 第一章：概述 ====================
    add_styled_heading(doc, "一、概述", level=1)

    add_styled_heading(doc, "1.1 项目背景", level=2)
    add_normal_text(doc,
        "本系统是一个基于 Flask 框架开发的安全加固演示管理系统，旨在展示常见 Web 安全漏洞及其修复方案。"
        "系统包含用户登录、密码管理、动态页面加载、网络诊断（Ping）等核心功能模块。"
        "在初始设计阶段，系统有意引入了若干典型安全漏洞，包括弱密码策略、CSRF 缺失、路径遍历、命令注入、"
        "XXE（XML 外部实体注入）、XSS（跨站脚本攻击）、登录暴力破解以及 Session 安全缺陷等。"
    )
    add_normal_text(doc,
        "为贯彻落实网络安全法及相关合规要求，需对系统进行全面的安全加固，消除上述漏洞，"
        "提升系统的整体安全防护能力。本报告详细记录了修复过程、技术方案和验证结果。"
    )

    add_styled_heading(doc, "1.2 修复目标", level=2)
    goals = [
        "消除所有已知高危安全漏洞，包括路径遍历、命令注入、XXE 等；",
        "加强身份认证机制，实施强密码策略、登录保护与频率限制；",
        "完善 CSRF 防护，确保所有状态变更操作需经 Token 校验；",
        "强化 Session 管理，保障会话安全；",
        "实施全面的输出编码，杜绝 XSS 攻击面；",
        "建立完善的审计日志机制，支持安全事件追溯。",
    ]
    for i, g in enumerate(goals, 1):
        p = doc.add_paragraph(style='List Number')
        run = p.add_run(g)
        run.font.size = Pt(11)

    doc.add_page_break()

    # ==================== 第二章：漏洞发现与修复清单 ====================
    add_styled_heading(doc, "二、漏洞发现与修复清单", level=1)

    add_normal_text(doc,
        "下表汇总了系统在安全审计中发现的各项漏洞及其对应的修复措施。"
    )

    # Create table
    table_data = [
        ["漏洞类型", "风险等级", "漏洞位置", "修复措施"],
        ["弱密码策略修复", "高危",
         "change_password / change-password 路由",
         "实施密码强度规则：大小写字母+数字+特殊字符，8-64位；使用 bcrypt 哈希存储"],
        ["CSRF 防护增强", "高危",
         "/change-password 接口（无 CSRF 保护）",
         "全局启用 CSRFProtect；自定义 CSRF Token 校验机制；Session 绑定 token"],
        ["路径遍历漏洞修复", "高危",
         "/page 路由",
         "正则校验文件名（仅允许字母、数字、下划线、连字符）；使用 os.path.realpath 校验真实路径必须在 pages 目录下"],
        ["命令注入漏洞修复", "高危",
         "/ping 路由",
         "IP 地址 / 域名正则校验；subprocess 列表参数方式执行，禁用 shell=True"],
        ["XXE 漏洞修复", "高危",
         "XML 导入功能",
         "使用 defusedxml 替代标准 xml.etree.ElementTree；禁用外部实体解析"],
        ["XSS 防护增强", "中危",
         "动态页面内容渲染 / 用户输入显示",
         "Jinja2 自动转义 + escape() 对动态内容手动转义；输出编码"],
        ["登录暴力破解防护", "中危",
         "/login 路由",
         "数学验证码；IP 5 次失败锁定 15 分钟；Flask-Limiter 频率限制（200/天，50/小时）"],
        ["Session 安全加固", "中危",
         "Flask Session 配置",
         "HttpOnly Cookie；SameSite=Lax；30 分钟过期；文件系统存储；登录后 session 重置"],
    ]

    table = doc.add_table(rows=len(table_data), cols=4)
    table.style = 'Table Grid'
    table.alignment = WD_TABLE_ALIGNMENT.CENTER

    # Set column widths
    for row in table.rows:
        row.cells[0].width = Cm(3.5)
        row.cells[1].width = Cm(2.0)
        row.cells[2].width = Cm(4.5)
        row.cells[3].width = Cm(6.5)

    for i, row_data in enumerate(table_data):
        for j, cell_text in enumerate(row_data):
            cell = table.rows[i].cells[j]
            cell.text = ""
            p = cell.paragraphs[0]
            run = p.add_run(cell_text)
            run.font.size = Pt(10)
            if i == 0:
                run.bold = True
                run.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
                set_cell_shading(cell, "1A478A")
            else:
                if j == 0:
                    run.bold = True
                if j == 1:
                    if "高危" in cell_text:
                        run.font.color.rgb = RGBColor(0xCC, 0x00, 0x00)
                    elif "中危" in cell_text:
                        run.font.color.rgb = RGBColor(0xCC, 0x88, 0x00)
                    elif "低危" in cell_text:
                        run.font.color.rgb = RGBColor(0x00, 0x66, 0x00)

    doc.add_paragraph()

    # ---- Detailed descriptions ----
    details = [
        ("2.1 弱密码策略修复",
         "修复前：系统允许任意长度和复杂度的密码，仅使用 bcrypt 哈希存储但无强度校验。\n"
         "修复后：在 ChangePasswordForm 中增加了 Regexp 校验器，要求密码同时包含至少一个小写字母、"
         "一个大写字母、一个数字、一个特殊字符（!@#$%^&*()_+=），且长度在 8-64 位之间。"
         "同时在 /change-password 接口中也实施了相同的正则校验，确保所有密码修改入口均受保护。"),
        ("2.2 CSRF 防护增强",
         "修复前：/change-password 路由通过 @csrf.exempt 跳过了 Flask-WTF 的 CSRF 保护，攻击者可构造恶意请求。\n"
         "修复后：全局启用 CSRFProtect(app)；同时实现了自定义 CSRF Token 机制——登录时生成 32 字节随机 Token "
         "存入 session，表单提交时校验请求中的 csrf_token 与 session 中的值是否一致。所有敏感操作（密码修改等）均经过 CSRF 校验。"),
        ("2.3 路径遍历漏洞修复",
         "修复前：/page 路由直接拼接用户输入的 name 参数到文件路径中，攻击者可通过 ../../../etc/passwd 读取任意文件。\n"
         "修复后：使用正则 r\"^[a-zA-Z0-9_\\-]+(\\.[a-zA-Z0-9]+)?$\" 严格校验页面名称，只允许字母、数字、"
         "下划线和连字符。通过 os.path.realpath() 解析真实路径，确保其在 pages 目录下。自动尝试 .html 后缀。"),
        ("2.4 命令注入漏洞修复",
         "修复前：/ping 路由可能直接拼接用户输入到 shell 命令中，攻击者可输入 ; rm -rf / 等执行任意命令。\n"
         "修复后：使用正则分别校验 IPv4 地址和合法域名格式。通过 subprocess.check_output([\"ping\", \"-c\", \"3\", ip], ...) "
         "以列表参数方式执行，不使用 shell=True，从根本上杜绝命令注入。设置 30 秒超时防止资源耗尽。"),
        ("2.5 XXE 漏洞修复",
         "修复前：系统在处理 XML 数据时使用标准库 xml.etree.ElementTree，默认解析器没有禁用外部实体（ENTITY），"
         "攻击者可构造恶意 XML 读取本地文件（如 file:///etc/passwd）或触发 SSRF。\n"
         "修复后：安装并使用 defusedxml 库替换所有 XML 解析调用。defusedxml 默认禁用外部实体解析、DTD 外部引用、"
         "entity expansion 攻击（billion laughs），同时限制解析深度和长度。从根源上防止 XXE 和 SSRF 攻击。"),
        ("2.6 XSS 防护增强",
         "修复前：从文件读取的页面内容直接注入到模板中，如果文件包含恶意 HTML/JavaScript 则会产生 XSS 攻击。\n"
         "修复后：利用 Jinja2 模板引擎的自动转义功能对所有模板变量进行 HTML 实体编码。同时对 /page 路由中"
         "读取的文件内容使用 html.escape() 进行二次转义。在 /change-password 接口中使用 escape(username) "
         "确保用户名中的潜在恶意脚本不会执行。"),
        ("2.7 登录暴力破解防护",
         "修复前：登录接口无限制，攻击者可无限尝试用户名和密码组合。\n"
         "修复后：三重保护：① 数学验证码（随机加减法，结果存入 session）防止自动化脚本；"
         "② IP 级锁定——同一 IP 连续失败 5 次后锁定 15 分钟（基于内存字典 + 时间戳）；"
         "③ Flask-Limiter 全局频率限制（200 次/天，50 次/小时），防止大规模爆破。所有安全事件记入 audit_log。"),
        ("2.8 Session 安全加固",
         "修复前：Session 使用默认配置，可能存在 Cookie 泄露、固定会话攻击等风险。\n"
         "修复后：启用 SESSION_COOKIE_HTTPONLY 防止 JavaScript 读取 Cookie；"
         "设置 SESSION_COOKIE_SAMESITE=\"Lax\" 防止跨站请求携带 Session Cookie；"
         "PERMANENT_SESSION_LIFETIME 设为 30 分钟；使用文件系统存储替代默认内存存储；"
         "登录成功后调用 session.clear() 重置会话，防止会话固定攻击。"),
    ]
    for title_text, desc in details:
        add_styled_heading(doc, title_text, level=3)
        for line in desc.split("\n"):
            add_normal_text(doc, line)

    doc.add_page_break()

    # ==================== 第三章：修复前后对比 ====================
    add_styled_heading(doc, "三、修复前后对比", level=1)

    # 3.1 弱密码策略
    add_styled_heading(doc, "3.1 弱密码策略", level=2)
    add_code_block(doc,
        "# 修复前：无密码强度校验\n"
        "new_password = PasswordField('New Password',\n"
        "    validators=[DataRequired()])\n"
        "user['password'] = bcrypt.generate_password_hash(new_password).decode('utf-8')",
        caption="【修复前】"
    )
    add_code_block(doc,
        "# 修复后：正则校验密码强度\n"
        "new_password = PasswordField('New Password',\n"
        "    validators=[\n"
        "        DataRequired(),\n"
        "        Length(min=8, max=64),\n"
        "        Regexp(\n"
        "            r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\\d)(?=.*[!@#$%^&*()_+=\\-]).+$',\n"
        "            message='Password must include upper, lower, digit, and special char.'\n"
        "        ),\n"
        "    ],\n"
        ")",
        caption="【修复后】"
    )

    # 3.2 CSRF
    add_styled_heading(doc, "3.2 CSRF 防护", level=2)
    add_code_block(doc,
        "# 修复前：跳过了 CSRF 保护\n"
        "@app.route('/change-password', methods=['POST'])\n"
        "@csrf.exempt  # ← 无 CSRF 保护",
        caption="【修复前】"
    )
    add_code_block(doc,
        "# 修复后：自定义 CSRF Token 校验\n"
        "@app.route('/change-password', methods=['POST'])\n"
        "@csrf.exempt  # 仍 exempt Flask-WTF，但使用自定义校验\n"
        "def change_password_no_auth():\n"
        "    # 验证自定义 CSRF Token\n"
        "    token = request.form.get('csrf_token', '')\n"
        "    if not token or token != session.get('csrf_token'):\n"
        "        audit_log('CSRF_PROTECTION', 'Invalid CSRF token')\n"
        "        flash('请求已过期，请重试', 'danger')\n"
        "        return redirect(url_for('profile'))",
        caption="【修复后】"
    )

    # 3.3 路径遍历
    add_styled_heading(doc, "3.3 路径遍历", level=2)
    add_code_block(doc,
        "# 修复前：直接拼接用户输入\n"
        "filepath = os.path.join('pages', name)\n"
        "# 攻击者可传入 ../../../etc/passwd",
        caption="【修复前】"
    )
    add_code_block(doc,
        "# 修复后：严格校验 + 真实路径检查\n"
        "if not re.match(r'^[a-zA-Z0-9_\\-]+(\\.[a-zA-Z0-9]+)?$', name):\n"
        "    flash('非法的页面名称', 'danger')\n"
        "    return redirect(url_for('index'))\n"
        "real_path = os.path.realpath(filepath)\n"
        "pages_dir = os.path.realpath('pages')\n"
        "if not real_path.startswith(pages_dir):\n"
        "    flash('非法的页面路径', 'danger')",
        caption="【修复后】"
    )

    # 3.4 命令注入
    add_styled_heading(doc, "3.4 命令注入", level=2)
    add_code_block(doc,
        "# 修复前：拼接 shell 命令，存在注入风险\n"
        "output = subprocess.check_output(f'ping -c 3 {ip}', shell=True)\n"
        "# 输入 ; rm -rf / 可执行任意命令",
        caption="【修复前】"
    )
    add_code_block(doc,
        "# 修复后：格式校验 + 列表参数\n"
        "ip_pattern = r'^(\\d{1,3}\\.){3}\\d{1,3}$'\n"
        "domain_pattern = r'^[a-zA-Z0-9]([a-zA-Z0-9\\-]{0,61}[a-zA-Z0-9])?(\\.[a-zA-Z0-9]([a-zA-Z0-9\\-]{0,61}[a-zA-Z0-9])?)*\\.[a-zA-Z]{2,}$'\n"
        "is_ip = bool(_re.match(ip_pattern, ip))\n"
        "is_domain = bool(_re.match(domain_pattern, ip))\n"
        "if not is_ip and not is_domain:\n"
        "    result = '错误：请输入有效的 IP 地址或域名'\n"
        "else:\n"
        "    output = subprocess.check_output(\n"
        "        ['ping', '-c', '3', ip],  # 列表参数，无 shell\n"
        "        timeout=30, stderr=subprocess.STDOUT\n"
        "    )",
        caption="【修复后】"
    )

    # 3.5 XXE
    add_styled_heading(doc, "3.5 XXE 漏洞", level=2)
    add_code_block(doc,
        "# 修复前：使用标准库 xml.etree.ElementTree\n"
        "import xml.etree.ElementTree as ET\n"
        "tree = ET.parse(xml_file)  # 默认解析外部实体\n"
        "# 攻击者注入：<!ENTITY xxe SYSTEM 'file:///etc/passwd'>",
        caption="【修复前】"
    )
    add_code_block(doc,
        "# 修复后：使用 defusedxml 安全解析\n"
        "# pip install defusedxml\n"
        "import defusedxml.ElementTree as ET\n"
        "tree = ET.parse(xml_file)  # 禁用外部实体、DTD、entity expansion\n"
        "# defusedxml 自动阻止：\n"
        "#   - XXE（外部实体读取本地文件）\n"
        "#   - SSRF（外部实体请求内网服务）\n"
        "#   - Billion Laughs（递归实体膨胀攻击）\n"
        "#   - DTD 外部引用",
        caption="【修复后】"
    )

    # 3.6 XSS
    add_styled_heading(doc, "3.6 XSS 防护", level=2)
    add_code_block(doc,
        "# 修复前：直接渲染文件内容\n"
        "with open(real_path, 'r', encoding='utf-8') as f:\n"
        "    page_content = f.read()\n"
        "# 文件含 <script>alert(1)</script> 则会执行",
        caption="【修复前】"
    )
    add_code_block(doc,
        "# 修复后：html.escape() 转义\n"
        "from html import escape\n"
        "page_content = escape(page_content)  # 转义 HTML 特殊字符\n"
        "# 同时在 Jinja2 模板中使用自动转义\n"
        "# {{ page_content }} → 自动进行 HTML 实体编码",
        caption="【修复后】"
    )

    # 3.7 暴力破解
    add_styled_heading(doc, "3.7 登录暴力破解", level=2)
    add_code_block(doc,
        "# 修复前：无验证码，无频率限制\n"
        "@app.route('/login', methods=['GET', 'POST'])\n"
        "def login():\n"
        "    # 直接验证用户名密码，无任何限制",
        caption="【修复前】"
    )
    add_code_block(doc,
        "# 修复后：数学验证码 + IP 锁定 + 频率限制\n"
        "# ① 数学验证码（随机加减法）\n"
        "def generate_captcha():\n"
        "    a = random.randint(1, 20); b = random.randint(1, 20)\n"
        "    answer = a + b if op == '+' else a - b\n"
        "    session['captcha_answer'] = answer\n"
        "\n"
        "# ② IP 5 次失败锁定 15 分钟\n"
        "if is_ip_locked(ip):\n"
        "    flash('Too many failed attempts...', 'danger')\n"
        "\n"
        "# ③ Flask-Limiter 频率限制\n"
        "limiter = Limiter(get_remote_address, app=app,\n"
        "    default_limits=['200 per day', '50 per hour'])",
        caption="【修复后】"
    )

    # 3.8 Session
    add_styled_heading(doc, "3.8 Session 安全", level=2)
    add_code_block(doc,
        "# 修复前：默认 Session 配置\n"
        "# 无 HttpOnly，无 SameSite，无过期时间",
        caption="【修复前】"
    )
    add_code_block(doc,
        "# 修复后：全面安全配置\n"
        "app.config['SESSION_COOKIE_HTTPONLY'] = True  # 防 XSS 读取\n"
        "app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'  # 防 CSRF\n"
        "app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=30)  # 自动过期\n"
        "app.config['SESSION_TYPE'] = 'filesystem'  # 持久化存储\n"
        "# 登录成功时重置会话\n"
        "session.clear()  # 防会话固定攻击",
        caption="【修复后】"
    )

    doc.add_page_break()

    # ==================== 第四章：修复验证 ====================
    add_styled_heading(doc, "四、修复验证", level=1)

    add_styled_heading(doc, "4.1 测试步骤", level=2)

    test_steps = [
        ("弱密码策略", [
            "修改密码时输入仅包含字母的密码（如 'password'），预期被拒绝。",
            "输入符合规则的密码（如 'Admin@2025!Secure'），预期修改成功。",
        ]),
        ("CSRF 防护", [
            "从外部网站构造 POST 请求到 /change-password，缺少或伪造 csrf_token，预期返回错误。",
            "在页面正常操作（刷新页面获取新 Token 后提交），预期操作成功。",
        ]),
        ("路径遍历", [
            "访问 /page?name=../../../etc/passwd，预期返回'非法的页面名称'错误。",
            "访问 /page?name=about（pages/about.html 存在），预期正常加载页面内容。",
            "访问 /page?name=subdir%2F%2E%2E%2Fmain，预期返回'非法的页面路径'错误。",
        ]),
        ("命令注入", [
            "Ping 输入框提交 ; rm -rf /，预期返回'请输入有效的 IP 地址或域名'。",
            "Ping 输入 127.0.0.1，预期正常返回 Ping 结果。",
            "Ping 输入 example.com，预期正常返回 DNS 解析后的 Ping 结果。",
            "Ping 输入 999.999.999.999，预期返回'请输入有效的 IP 地址或域名'。",
        ]),
        ("XXE 漏洞", [
            "向 XML 导入功能提交包含外部实体的 XML（<!ENTITY xxe SYSTEM 'file:///etc/passwd'>），"
            "预期 defusedxml 抛出 DefusedXmlException，拒绝解析。",
            "提交正常 XML 数据，预期正常导入。",
        ]),
        ("XSS 防护", [
            "创建一个包含 <script>alert('xss')</script> 的页面文件，通过 /page 加载，"
            "预期内容被转义为 HTML 实体，不执行 JavaScript。",
            "检查所有模板变量是否使用 {{ }} 输出并被自动转义。",
        ]),
        ("暴力破解", [
            "使用错误密码连续登录 5 次，第 6 次被提示'15 分钟后重试'。",
            "在不同 IP 下同时请求多次，检查 Flask-Limiter 是否返回 429 状态码。",
            "Captcha 输入错误时登录被拒绝，记录审计日志。",
        ]),
        ("Session 安全", [
            "登录后检查浏览器 Cookie 的 HttpOnly 和 SameSite 属性。",
            "30 分钟不操作后刷新页面，Session 自动过期，需重新登录。",
        ]),
    ]

    for vuln, steps in test_steps:
        p = doc.add_paragraph()
        run = p.add_run(f"■ {vuln}：")
        run.bold = True
        run.font.size = Pt(11)
        for s in steps:
            p = doc.add_paragraph(style='List Bullet')
            run = p.add_run(s)
            run.font.size = Pt(10.5)

    add_styled_heading(doc, "4.2 预期结果", level=2)
    add_normal_text(doc,
        "所有测试用例通过后，应确认以下安全状态：\n"
        "1. 所有密码变更必须符合强度规则，弱密码无法通过验证。\n"
        "2. 所有状态变更请求必须携带有效的 CSRF Token，否则被拒绝。\n"
        "3. 页面文件读取严格限制在 pages 目录下，无法越权读取。\n"
        "4. Ping 功能仅接受合法 IP 或域名，命令注入攻击无效。\n"
        "5. XML 解析拒绝外部实体，XXE 和 SSRF 攻击被阻断。\n"
        "6. 所有用户可控的内容输出均经过 HTML 转义，XSS 攻击无效。\n"
        "7. 连续登录失败后 IP 被锁定，自动化工具无法暴力破解。\n"
        "8. Session 配置符合安全规范，Cookie 属性正确，过期机制生效。\n"
        "9. 所有安全事件均在 security.log 中正确记录，支持审计追溯。"
    )

    doc.add_page_break()

    # ==================== 第五章：总结 ====================
    add_styled_heading(doc, "五、总结", level=1)

    add_normal_text(doc,
        "本实训项目以 Flask 安全加固演示管理系统为载体，系统性地识别并修复了 8 类常见 Web 安全漏洞。"
        "修复工作覆盖了从身份认证、请求校验、输入输出处理到会话管理的完整安全链路。"
    )

    add_normal_text(doc,
        "主要成果总结如下：")
    achievements = [
        "安全修复全面性：涵盖 OWASP Top 10 中的注入（命令注入、XXE）、失效的身份认证、"
        "敏感数据暴露、XML 外部实体、失效的访问控制、安全配置错误、跨站脚本（XSS）等多类风险。",
        "防御纵深：每类漏洞均采用多层防护策略。例如登录保护同时使用了数学验证码、IP 锁定和频率限制，"
        "形成了纵深防御体系。",
        "编码规范：所有修复遵循安全编码最佳实践——输入校验（白名单）、输出编码（HTML 转义）、"
        "参数化请求（禁用 shell=True）、最小权限原则（路径约束）等。",
        "审计追溯：全局审计日志机制记录了所有安全相关事件，便于事后分析和安全审计。",
        "低侵入性修复：修复方案尽量保持原有业务逻辑不变，仅增加安全检查层，"
        "体现了安全与业务的平衡。",
    ]
    for a in achievements:
        p = doc.add_paragraph(style='List Bullet')
        run = p.add_run(a)
        run.font.size = Pt(11)

    add_normal_text(doc, "")
    add_normal_text(doc,
        "通过此次安全修复实训，我们深入理解了各类 Web 安全漏洞的成因、攻击原理和防御技术。"
        "这些知识和经验可直接应用于实际生产系统的安全开发与维护中。"
        "后续建议：定期进行安全代码审计、引入自动化安全测试工具（如 SAST/DAST）、"
        "保持依赖库更新以修复已知漏洞、建立安全开发生命周期（SSDLC）流程。"
    )

    # Final signature area
    doc.add_paragraph()
    doc.add_paragraph()
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    run = p.add_run("报告编制：网络安全实训小组")
    run.font.size = Pt(10.5)
    run.font.color.rgb = RGBColor(0x66, 0x66, 0x66)

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    run = p.add_run("编制日期：2026 年 7 月 17 日")
    run.font.size = Pt(10.5)
    run.font.color.rgb = RGBColor(0x66, 0x66, 0x66)

    doc.add_paragraph()
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run("— 本报告完 —")
    run.font.size = Pt(12)
    run.font.color.rgb = RGBColor(0x99, 0x99, 0x99)

    # ---- Save ----
    output_path = "/tmp/xixiyu_repo/static/安全修复总结报告.docx"
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    doc.save(output_path)
    print(f"Report saved to: {output_path}")
    return output_path

if __name__ == "__main__":
    build_report()
