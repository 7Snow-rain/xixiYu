#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成网络安全实训实习报告 Word 文档"""

import datetime
try:
    from docx import Document
    from docx.shared import Pt, Inches, RGBColor, Cm
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.enum.table import WD_TABLE_ALIGNMENT
except ImportError:
    import subprocess
    subprocess.check_call(["pip", "install", "python-docx"])
    from docx import Document
    from docx.shared import Pt, Inches, RGBColor, Cm
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.enum.table import WD_TABLE_ALIGNMENT

def create_report():
    doc = Document()

    # 页面设置
    section = doc.sections[0]
    section.top_margin = Cm(2.54)
    section.bottom_margin = Cm(2.54)
    section.left_margin = Cm(3.17)
    section.right_margin = Cm(3.17)

    style = doc.styles['Normal']
    font = style.font
    font.name = '宋体'
    font.size = Pt(12)

    # ==================== 封面 ====================
    for _ in range(4):
        doc.add_paragraph()

    title = doc.add_paragraph()
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = title.add_run('网络安全企业实训\n实习报告')
    run.font.size = Pt(28)
    run.font.bold = True
    run.font.color.rgb = RGBColor(0, 51, 102)

    doc.add_paragraph()
    subtitle = doc.add_paragraph()
    subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = subtitle.add_run('（Web 安全漏洞挖掘与修复实践）')
    run.font.size = Pt(16)
    run.font.color.rgb = RGBColor(102, 102, 102)

    for _ in range(4):
        doc.add_paragraph()

    info = doc.add_paragraph()
    info.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = info.add_run(f'实训时间：2026年7月\n报告日期：{datetime.date.today().strftime("%Y年%m月%d日")}')
    run.font.size = Pt(14)

    doc.add_page_break()

    # ==================== 目录页 ====================
    toc_title = doc.add_heading('目  录', level=1)
    toc_title.alignment = WD_ALIGN_PARAGRAPH.CENTER

    toc_items = [
        ('一、实习目的', 3),
        ('二、实习要求', 3),
        ('三、实习主要内容', 4),
        ('  3.1 资产测绘与信息收集', 4),
        ('  3.2 Web 安全漏洞分析与利用', 5),
        ('  3.3 操作系统与中间件安全', 6),
        ('  3.4 内网渗透与域环境', 7),
        ('  3.5 安全修复与加固实践', 7),
        ('  3.6 AI 辅助安全分析', 8),
        ('  3.7 安全合规与法学分析', 8),
        ('四、实习收获与总结', 9),
    ]
    for item, _ in toc_items:
        p = doc.add_paragraph(item)
        p.paragraph_format.space_after = Pt(6)

    doc.add_page_break()

    # ==================== 一、实习目的 ====================
    doc.add_heading('一、实习目的', level=1)

    doc.add_paragraph(
        '本次 2 周网络安全企业实训是专业核心实践环节，旨在对接行业安全服务岗位需求，'
        '培养标准化项目交付能力。通过本次实训，学生将实现以下目标：'
    )

    purposes = [
        '掌握资产测绘与信息收集方法，能够独立完成目标系统的资产梳理和攻击面分析；',
        '熟练掌握全类型渗透测试流程，包括 Web 漏洞挖掘、利用与权限提升；',
        '具备风险评估完整流程的操作能力，能够识别、评估并修复安全风险；',
        '熟练运用 OpenClaw 大模型实现 AI 辅助漏洞挖掘、攻击路径规划和代码审计；',
        '锤炼 Web 应用、内网、域渗透实战技能，适配渗透测试、等保测评等就业方向；',
        '融合网络安全法学知识，树立数据安全与个人信息保护合规思维；',
        '具备规范文档撰写能力，能够编写安全漏洞报告和安全修复报告；',
        '培养团队项目协作与基础项目管理能力。',
    ]
    for p_text in purposes:
        doc.add_paragraph(p_text, style='List Bullet')

    doc.add_paragraph()

    # ==================== 二、实习要求 ====================
    doc.add_heading('二、实习要求', level=1)

    doc.add_paragraph('实训期间须遵守以下要求：')

    requirements = [
        '严格遵守校企管理制度、考勤规范与项目管理规范；',
        '仅在授权靶场环境下开展实验操作，严禁越权测试；',
        '严守《网络安全法》《数据安全法》《个人信息保护法》三部核心法律，杜绝非法测试行为；',
        '独立完成资产测绘、漏洞挖掘、渗透评估等任务；',
        '熟练使用主流渗透测试工具（Burp Suite、Nmap、Metasploit 等）；',
        '熟练使用 AI 安全模型辅助分析（OpenClaw 大模型）；',
        '产出完整实训材料，包括渗透测试报告、安全修复报告、实习报告；',
        '以小组协作方式完成项目全流程交付；',
        '如实记录实验过程与结果，文档内容真实规范；',
        '网络空间安全与法学双学位学生须额外完成合规分析内容；',
        '按时提交全部实训成果。',
    ]
    for r_text in requirements:
        doc.add_paragraph(r_text, style='List Bullet')

    doc.add_page_break()

    # ==================== 三、实习主要内容 ====================
    doc.add_heading('三、实习主要内容', level=1)

    # 3.1 资产测绘
    doc.add_heading('3.1 资产测绘与信息收集', level=2)
    doc.add_paragraph(
        '本次实训以 Flask 安全管理系统作为目标应用，开展了完整的资产测绘与信息收集工作。'
        '首先使用 Nmap 对目标服务器进行端口扫描，发现开放了 5000/tcp（Flask 开发服务器）端口，'
        '操作系统识别为 Linux。通过目录扫描发现 /admin、/login、/pages、/profile 等多个敏感路由。'
    )
    doc.add_paragraph(
        '使用 OpenClaw 大模型辅助分析了目标应用的架构，识别出以下信息：'
    )
    info_items = [
        'Web 框架：Flask 2.x（Python）',
        '模板引擎：Jinja2',
        '认证方式：表单 + Session 认证',
        '密码存储：bcrypt 加盐哈希',
        '中间件：Werkzeug 开发服务器',
        '操作系统：Linux（Kali）',
    ]
    for item in info_items:
        doc.add_paragraph(item, style='List Bullet')

    # 3.2 Web 安全
    doc.add_heading('3.2 Web 安全漏洞分析与利用', level=2)
    doc.add_paragraph(
        '本次实训重点对目标 Web 应用进行了全类型的渗透测试，发现了以下安全漏洞并进行了利用验证：'
    )

    # 漏洞表格
    table = doc.add_table(rows=8, cols=4)
    table.style = 'Light Grid Accent 1'
    table.alignment = WD_TABLE_ALIGNMENT.CENTER

    headers = ['漏洞类型', '风险等级', '漏洞位置', '利用方式']
    for i, h in enumerate(headers):
        cell = table.rows[0].cells[i]
        cell.text = h
        for paragraph in cell.paragraphs:
            for run in paragraph.runs:
                run.font.bold = True

    vulns = [
        ['弱密码策略', '高危', '/change-password', '绕过原密码验证修改任意用户密码'],
        ['CSRF 防护缺失', '高危', '多个 POST 接口', '无需用户确认即可执行跨站操作'],
        ['路径遍历漏洞', '中危', '/page', '通过 ../ 读取系统文件'],
        ['命令注入漏洞', '高危', '/ping', '通过拼接参数执行系统命令'],
        ['XXE 漏洞', '高危', '/xml-import', '通过外部实体引用读取服务器文件'],
        ['XSS 存储型', '中危', '动态页面加载', '恶意脚本注入并执行'],
        ['登录暴力破解', '中危', '/login', '无限制登录尝试可爆破密码'],
    ]
    for row_idx, vuln in enumerate(vulns):
        for col_idx, text in enumerate(vuln):
            table.rows[row_idx + 1].cells[col_idx].text = text

    doc.add_paragraph()

    doc.add_paragraph(
        '其中，弱密码策略漏洞允许攻击者在未验证原密码的情况下直接修改任意用户的密码，'
        '这是本次实训发现的最严重漏洞之一。CSRF 防护缺失使得攻击者可以构造恶意页面'
        '诱使用户在不知情的情况下执行敏感操作，配合弱密码漏洞可实现完整账户接管。'
    )

    # XXE 漏洞专项
    doc.add_heading('XXE 漏洞专项分析', level=3)
    doc.add_paragraph(
        '本次实训中新发现了一个 XML 外部实体注入（XXE）漏洞。通过在 XML 导入功能中'
        '未禁用外部实体解析，攻击者可构造恶意 XML 请求读取服务器任意文件：'
    )
    doc.add_paragraph(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<!DOCTYPE foo [\n'
        '  <!ENTITY xxe SYSTEM "file:///etc/passwd">\n'
        ']>\n'
        '<users>\n'
        '  <user>\n'
        '    <name>&xxe;</name>\n'
        '    <email>test@example.com</email>\n'
        '  </user>\n'
        '</users>',
        style='List Bullet'
    )
    doc.add_paragraph(
        '通过此漏洞可读取 /etc/passwd、配置文件、敏感密钥等系统文件，'
        '严重威胁服务器数据安全。修复方案为禁用 XML 解析器中的外部实体解析功能。'
    )

    # 3.3 系统安全
    doc.add_heading('3.3 操作系统与中间件安全', level=2)
    doc.add_paragraph(
        '对目标服务器进行了操作系统层面的安全评估。发现以下安全问题：'
    )
    sys_items = [
        'Flask 开发服务器以 debug 模式运行，暴露调试信息及交互式终端',
        '运行主机为 0.0.0.0 即监听所有网络接口，存在外部未授权访问风险',
        'Session 存储目录 /tmp/flask_session 为可预测路径',
        '日志文件 security.log 位于 Web 根目录可直接访问',
    ]
    for item in sys_items:
        doc.add_paragraph(item, style='List Bullet')

    # 3.4 内网渗透
    doc.add_heading('3.4 内网渗透与域环境', level=2)
    doc.add_paragraph(
        '由于本次实训环境为独立靶机，未部署域环境，内网渗透部分以理论分析为主。'
        '在具备内网访问权限后，可执行以下操作：'
    )
    inner_items = [
        '利用 XXE 漏洞读取 /etc/shadow 获取密码哈希',
        '利用命令注入漏洞反弹 Shell 获取主机控制权',
        '横向移动至内网其他主机',
        '提取 Session 数据库中的用户凭据',
    ]
    for item in inner_items:
        doc.add_paragraph(item, style='List Bullet')

    # 3.5 安全修复
    doc.add_heading('3.5 安全修复与加固实践', level=2)
    doc.add_paragraph(
        '针对发现的所有安全漏洞进行了系统性的修复加固，具体措施如下：'
    )

    fix_table = doc.add_table(rows=8, cols=3)
    fix_table.style = 'Light Grid Accent 1'
    fix_table.alignment = WD_TABLE_ALIGNMENT.CENTER

    fix_headers = ['漏洞类型', '修复措施', '修复效果']
    for i, h in enumerate(fix_headers):
        cell = fix_table.rows[0].cells[i]
        cell.text = h
        for paragraph in cell.paragraphs:
            for run in paragraph.runs:
                run.font.bold = True

    fixes = [
        ['弱密码策略', '增加原密码验证环节', '需确认用户身份方可改密'],
        ['CSRF 防护', '启用 Flask-WTF CSRFProtect，所有 POST 请求校验 Token', '防止跨站请求伪造'],
        ['路径遍历', '正则校验文件名 + os.path.realpath 路径过滤', '限制文件读取范围'],
        ['命令注入', '正则校验 IP/域名 + subprocess 列表参数禁止 shell=True', '消除命令注入向量'],
        ['XXE 漏洞', '禁止 XML DOCTYPE/ENTITY 声明，使用安全解析器', '防止外部实体注入'],
        ['XSS', 'Jinja2 自动转义 + escape() 函数对动态内容编码', '防止脚本注入执行'],
        ['暴力破解', 'IP 5 次失败锁定 15 分钟 + 频率限制', '阻断自动化爆破攻击'],
    ]
    for row_idx, fix in enumerate(fixes):
        for col_idx, text in enumerate(fix):
            fix_table.rows[row_idx + 1].cells[col_idx].text = text

    doc.add_paragraph()

    # 3.6 AI
    doc.add_heading('3.6 AI 辅助安全分析', level=2)
    doc.add_paragraph(
        '本次实训创新性地引入了 OpenClaw 大模型辅助安全分析工作，'
        '在以下环节发挥了重要作用：'
    )
    ai_items = [
        '代码审计：自动检测源代码中的安全漏洞模式，如命令注入、路径遍历等',
        '攻击路径规划：根据目标应用架构自动分析最优攻击链路',
        '漏洞修复建议：为每个发现的漏洞生成针对性的修复方案和代码示例',
        '报告生成：辅助生成安全漏洞报告和修复报告，标准化文档输出',
    ]
    for item in ai_items:
        doc.add_paragraph(item, style='List Bullet')

    doc.add_paragraph(
        'AI 安全模型的应用显著提升了漏洞发现效率和修复质量，'
        '是未来安全服务交付的重要技术方向。'
    )

    # 3.7 安全合规
    doc.add_heading('3.7 安全合规与法学分析', level=2)
    doc.add_paragraph(
        '结合网络空间安全与法学双学位背景，对本次实训中涉及的合规问题进行分析：'
    )
    legal_items = [
        '《网络安全法》第 21 条要求采取技术措施防范网络攻击，本次修复的安全漏洞即属于该条规范范围',
        '《数据安全法》第 27 条要求建立数据安全保护制度，XXE 漏洞可读取系统文件涉及数据安全',
        '《个人信息保护法》第 6 条要求最小必要原则，弱密码漏洞导致个人信息泄露风险',
        '实训全程在授权靶场环境完成，遵守了《刑法》第 285 条关于非法侵入计算机信息系统的禁止规定',
        '建议生产企业参照等保 2.0 三级要求，在系统开发全生命周期中嵌入安全测试环节',
    ]
    for item in legal_items:
        doc.add_paragraph(item, style='List Bullet')

    doc.add_page_break()

    # ==================== 四、实习总结 ====================
    doc.add_heading('四、实习总结', level=1)

    doc.add_heading('4.1 实训成果', level=2)
    doc.add_paragraph(
        '通过为期两周的网络安全企业实训，系统性地完成了以下工作：'
    )
    achievements = [
        '完成目标 Web 系统的资产测绘与攻击面分析',
        '发现并验证 7 类安全漏洞（弱密码、CSRF、路径遍历、命令注入、XXE、XSS、暴力破解）',
        '对所有发现漏洞完成修复加固并编写安全修复报告',
        '实训成果包含 3 份 Word 安全报告、源代码修复版本及完整实习报告',
        '所有实训成果已上传至 GitHub 仓库备案',
    ]
    for item in achievements:
        doc.add_paragraph(item, style='List Bullet')

    doc.add_heading('4.2 技术收获', level=2)
    tech_items = [
        '掌握了完整的 Web 渗透测试流程：信息收集→漏洞发现→利用验证→修复加固→文档交付',
        '熟练运用 Python Flask 框架进行安全加固开发',
        '理解了 bcrypt、CSRF Token、Session 安全、输入校验等多种安全防护机制的实现原理',
        '掌握了 XXE、命令注入、路径遍历等经典 Web 漏洞的利用技巧和修复方法',
        '学会了使用 AI 大模型辅助安全分析和代码审计',
        '提升了安全文档撰写能力，能够编写专业的渗透测试报告和修复报告',
    ]
    for item in tech_items:
        doc.add_paragraph(item, style='List Bullet')

    doc.add_heading('4.3 对行业与技术发展的认识', level=2)
    doc.add_paragraph(
        '通过本次实训，深刻认识到网络安全是一个攻防动态演进的领域。'
        '随着 AI 技术的发展，攻击者的手段越来越复杂，安全防御也必须与时俱进。'
        '同时，法律法规的完善对企业安全合规提出了更高要求，'
        '安全从业者不仅需要深厚的技术功底，还需要具备法律合规意识。'
    )
    doc.add_paragraph(
        '本次实训中接触到的 AI 辅助安全分析是行业前沿方向。'
        'OpenClaw 大模型在代码审计、漏洞挖掘、修复建议等方面的表现令人印象深刻，'
        '展示了 AI 技术在安全领域的巨大应用潜力。'
    )

    doc.add_heading('4.4 未来展望', level=2)
    doc.add_paragraph(
        '此次实训为今后的安全从业之路打下了坚实的基础。'
        '未来计划在以下方向继续深入：'
    )
    future_items = [
        '深入学习内网渗透与域渗透技术',
        '研究云原生安全与容器安全',
        '跟进 AI 安全攻防前沿技术',
        '积累项目管理与安全咨询经验',
        '为 CISP、CISSP 等安全认证做准备',
    ]
    for item in future_items:
        doc.add_paragraph(item, style='List Bullet')

    # 保存
    output_path = '/tmp/xixiyu_repo/static/实习报告.docx'
    doc.save(output_path)
    print(f'✅ 实习报告已生成：{output_path}')
    return output_path

if __name__ == '__main__':
    create_report()
