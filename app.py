import os
import re
import logging
import secrets
import urllib.request
import urllib.error
from html import escape
from datetime import datetime, timedelta

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    session,
    jsonify,
)
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_wtf.csrf import CSRFProtect
from flask_bcrypt import Bcrypt
from flask_session import Session as FlaskSession
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Length, Regexp, EqualTo
from flask_wtf import FlaskForm

# ---------------------------
# App Initialization
# ---------------------------
app = Flask(__name__)
app.secret_key = os.urandom(32).hex()

# Session Security
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(minutes=30)
app.config["SESSION_TYPE"] = "filesystem"
app.config["SESSION_FILE_DIR"] = "/tmp/flask_session"
FlaskSession(app)

# CSRF
csrf = CSRFProtect(app)

# Bcrypt
bcrypt = Bcrypt(app)

# Rate Limiting
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://",
)

# Logging
logging.basicConfig(
    filename="security.log",
    level=logging.INFO,
    format="%(asctime)s - %(message)s",
)

# Audit Log Helper
def audit_log(event, details=""):
    ip = request.remote_addr or "unknown"
    user = session.get("username", "anonymous")
    logging.info(f"[{event}] IP={ip} User={user} {details}")

# IP Lockout State
ip_failures = {}
IP_LOCKOUT_MINUTES = 15
IP_MAX_ATTEMPTS = 5

def is_ip_locked(ip):
    if ip in ip_failures:
        entry = ip_failures[ip]
        if entry["count"] >= IP_MAX_ATTEMPTS:
            if datetime.now() - entry["lock_time"] < timedelta(minutes=IP_LOCKOUT_MINUTES):
                return True
            else:
                del ip_failures[ip]
    return False

def record_ip_failure(ip):
    if ip not in ip_failures:
        ip_failures[ip] = {"count": 0, "lock_time": datetime.now()}
    ip_failures[ip]["count"] += 1
    if ip_failures[ip]["count"] >= IP_MAX_ATTEMPTS:
        ip_failures[ip]["lock_time"] = datetime.now()

# ---------------------------
# Mock Users (bcrypt hashed)
# ---------------------------
users_db = {
    "admin": {
        "password": bcrypt.generate_password_hash("Admin@2025!Secure").decode("utf-8"),
        "role": "admin",
    },
    "alice": {
        "password": bcrypt.generate_password_hash("Alice@2025!Secure").decode("utf-8"),
        "role": "user",
    },
}

# ---------------------------
# Forms
# ---------------------------
class LoginForm(FlaskForm):
    username = StringField(
        "Username",
        validators=[
            DataRequired(),
            Length(min=3, max=20),
            Regexp(
                r"^[a-zA-Z0-9_]+$",
                message="Username must be alphanumeric or underscore only.",
            ),
        ],
    )
    password = PasswordField("Password", validators=[DataRequired()])
    captcha = StringField("Captcha", validators=[DataRequired(), Length(min=1, max=4)])
    submit = SubmitField("Login")

class ChangePasswordForm(FlaskForm):
    old_password = PasswordField("Old Password", validators=[DataRequired()])
    new_password = PasswordField(
        "New Password",
        validators=[
            DataRequired(),
            Length(min=8, max=64),
            Regexp(
                r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[!@#$%^&*()_+=\-]).+$",
                message="Password must include upper, lower, digit, and special char.",
            ),
        ],
    )
    confirm_password = PasswordField(
        "Confirm Password",
        validators=[DataRequired(), EqualTo("new_password", message="Passwords must match.")],
    )
    submit = SubmitField("Change Password")

# ---------------------------
# Context Processors — inject CSRF token and current time into all templates
# ---------------------------
@app.context_processor
def inject_globals():
    csrf_token = session.get("csrf_token", "")
    return {"now": datetime.now(), "csrf_token": csrf_token}

# ---------------------------
# Generate Captcha Math
# ---------------------------
def generate_captcha():
    import random
    a = random.randint(1, 20)
    b = random.randint(1, 20)
    op = random.choice(["+", "-"])
    if op == "-" and a < b:
        a, b = b, a
    answer = a + b if op == "+" else a - b
    session["captcha_answer"] = answer
    return f"{a} {op} {b} = ?"

# ---------------------------
# Routes
# ---------------------------
@app.route("/")
def index():
    if "username" in session:
        page_content = None
        # 如果通过 /page 传了内容过来（已转义，安全使用 safe）
        if "page_content" in session:
            page_content = session.pop("page_content")
        return render_template(
            "index.html",
            username=session["username"],
            role=session.get("role", "user"),
            captcha=generate_captcha(),
            page_content=page_content,
        )
    return redirect(url_for("login"))

@app.route("/login", methods=["GET", "POST"])
def login():
    if "username" in session:
        return redirect(url_for("index"))

    ip = request.remote_addr or "unknown"
    if is_ip_locked(ip):
        audit_log("IP_LOCKED", "IP is temporarily locked")
        flash("Too many failed attempts. Try again in 15 minutes.", "danger")
        return render_template("login.html", captcha=generate_captcha(), form=LoginForm())

    form = LoginForm()
    if form.validate_on_submit():
        username = form.username.data.strip()
        password = form.password.data
        user_captcha = form.captcha.data.strip()

        # Validate captcha
        if str(session.get("captcha_answer")) != user_captcha:
            audit_log("CAPTCHA_FAIL", f"User={username}")
            flash("Captcha incorrect.", "danger")
            record_ip_failure(ip)
            return render_template("login.html", captcha=generate_captcha(), form=form)

        # Validate user
        user = users_db.get(username)
        if user and bcrypt.check_password_hash(user["password"], password):
            # Login success – regenerate session
            session.clear()
            session["username"] = username
            session["role"] = user["role"]
            session["csrf_token"] = secrets.token_hex(32)
            session.permanent = True
            # Clear IP failures
            if ip in ip_failures:
                del ip_failures[ip]
            audit_log("LOGIN_SUCCESS", f"User={username}")
            flash("登录成功！", "success")
            return redirect(url_for("index"))
        else:
            audit_log("LOGIN_FAIL", f"User={username}")
            flash("Invalid username or password.", "danger")
            record_ip_failure(ip)

    return render_template("login.html", captcha=generate_captcha(), form=form)

@app.route("/logout")
def logout():
    username = session.get("username", "unknown")
    audit_log("LOGOUT", f"User={username}")
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("login"))

@app.route("/change_password", methods=["GET", "POST"])
def change_password():
    if "username" not in session:
        return redirect(url_for("login"))

    form = ChangePasswordForm()
    if form.validate_on_submit():
        username = session["username"]
        user = users_db.get(username)
        old_password = form.old_password.data
        new_password = form.new_password.data

        if user and bcrypt.check_password_hash(user["password"], old_password):
            # Update password
            user["password"] = bcrypt.generate_password_hash(new_password).decode("utf-8")
            audit_log("PASSWORD_CHANGE", f"User={username}")
            flash("Password changed successfully!", "success")
            return redirect(url_for("index"))
        else:
            audit_log("PASSWORD_CHANGE_FAIL", f"User={username}")
            flash("Old password is incorrect.", "danger")

    return render_template("change_password.html", form=form)

# ==========================================
# URL 抓取功能（SSRF 安全加固版本）
# ==========================================
import ipaddress
import socket

# 禁止访问的内部 IP 范围（IPv4）
BLOCKED_NETWORKS = [
    ipaddress.ip_network("127.0.0.0/8"),       # 本地回环
    ipaddress.ip_network("10.0.0.0/8"),         # 私有 A 类
    ipaddress.ip_network("172.16.0.0/12"),      # 私有 B 类
    ipaddress.ip_network("192.168.0.0/16"),     # 私有 C 类
    ipaddress.ip_network("0.0.0.0/8"),          # 零地址
    ipaddress.ip_network("100.64.0.0/10"),      # 运营商级 NAT
    ipaddress.ip_network("169.254.0.0/16"),     # 链路本地
    ipaddress.ip_network("198.18.0.0/15"),      # 基准测试
    ipaddress.ip_network("224.0.0.0/4"),        # 组播地址
    ipaddress.ip_network("240.0.0.0/4"),        # 保留地址
    ipaddress.ip_network("255.255.255.255/32"), # 广播地址
]

# IPv6 禁止范围
BLOCKED_NETWORKS_V6 = [
    ipaddress.ip_network("::1/128"),            # 本地回环
    ipaddress.ip_network("fe80::/10"),           # 链路本地
    ipaddress.ip_network("fc00::/7"),            # 唯一本地地址
    ipaddress.ip_network("ff00::/8"),            # 组播地址
]


def is_internal_ip(host):
    """检查目标主机是否为内部 IP（SSRF 防护）"""
    try:
        addr = ipaddress.ip_address(host)
        for net in BLOCKED_NETWORKS:
            if addr in net:
                return True
        for net in BLOCKED_NETWORKS_V6:
            if addr in net:
                return True
        return False
    except ValueError:
        # 主机名而非 IP，需要 DNS 解析后检查
        return None  # 不确定，需要后续解析


def resolve_and_check(hostname):
    """解析域名并检查所有解析结果是否含有内网地址"""
    try:
        results = socket.getaddrinfo(hostname, None)
        for res in results:
            addr = ipaddress.ip_address(res[4][0])
            for net in BLOCKED_NETWORKS:
                if addr in net:
                    return True
            for net in BLOCKED_NETWORKS_V6:
                if addr in net:
                    return True
        return False
    except Exception:
        return True  # 解析失败，保守起见拒绝


@app.route("/fetch-url", methods=["POST"])
@csrf.exempt
def fetch_url():
    if "username" not in session:
        return redirect(url_for("login"))

    url = request.form.get("url", "").strip()
    if not url:
        flash("请输入 URL", "warning")
        return redirect(url_for("index"))

    # 安全校验：只允许 http:// 和 https:// 协议
    # 禁止 file://, ftp://, dict://, gopher://, jar: 等危险协议
    if not url.startswith("http://") and not url.startswith("https://"):
        err_msg = f"不支持的协议。仅允许 http:// 和 https://"
        session["fetch_result"] = f"错误: {err_msg}"
        session["fetch_url"] = url
        audit_log("FETCH_URL_REJECTED_PROTOCOL", f"url={url}")
        flash(err_msg, "danger")
        return redirect(url_for("index"))

    # URL 解析与目标主机提取
    from urllib.parse import urlparse
    parsed = urlparse(url)
    host = parsed.hostname
    
    if not host:
        session["fetch_result"] = "错误: 无效的 URL"
        session["fetch_url"] = url
        flash("无效的 URL", "danger")
        return redirect(url_for("index"))

    # SSRF 防护 1：检查是否是已知内部 IP 地址
    if is_internal_ip(host) is True:
        err_msg = f"拒绝访问内部地址: {host}"
        session["fetch_result"] = f"错误: {err_msg}"
        session["fetch_url"] = url
        audit_log("SSRF_BLOCKED_IP", f"url={url} host={host}")
        flash(err_msg, "danger")
        return redirect(url_for("index"))

    # SSRF 防护 2：如果是域名，解析并检查
    if is_internal_ip(host) is None:
        if resolve_and_check(host):
            err_msg = f"拒绝访问目标: {host}（解析到内网地址）"
            session["fetch_result"] = f"错误: {err_msg}"
            session["fetch_url"] = url
            audit_log("SSRF_BLOCKED_DOMAIN", f"url={url} host={host}")
            flash(err_msg, "danger")
            return redirect(url_for("index"))

    # SSRF 防护 3：限制重定向目标也为外网地址
    class SSRFRedirectHandler(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, req, fp, code, msg, headers, newurl):
            new_parsed = urlparse(newurl)
            new_host = new_parsed.hostname
            if new_host:
                if is_internal_ip(new_host) is True:
                    raise urllib.error.HTTPError(newurl, code, "SSRF Blocked: redirect to internal IP", headers, None)
                if is_internal_ip(new_host) is None:
                    if resolve_and_check(new_host):
                        raise urllib.error.HTTPError(newurl, code, "SSRF Blocked: redirect resolves to internal", headers, None)
            return super().redirect_request(req, fp, code, msg, headers, newurl)

    try:
        opener = urllib.request.build_opener(SSRFRedirectHandler)
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"})
        response = opener.open(req, timeout=10)
        status_code = response.getcode()
        content = response.read().decode("utf-8", errors="replace")
        result_text = f"状态码: {status_code}\n\n--- 响应内容 (前5000字符) ---\n\n{content[:5000]}"
        session["fetch_result"] = result_text
        session["fetch_url"] = url
        audit_log("FETCH_URL", f"url={url} status={status_code}")
        flash(f"抓取成功！状态码: {status_code}", "success")
    except urllib.error.HTTPError as e:
        try:
            error_content = e.read().decode("utf-8", errors="replace")
            result_text = f"HTTP 错误 - 状态码: {e.code}\n\n--- 响应内容 (前5000字符) ---\n\n{error_content[:5000]}"
        except Exception:
            result_text = f"HTTP 错误 - 状态码: {e.code}"
        session["fetch_result"] = result_text
        session["fetch_url"] = url
        audit_log("FETCH_URL_ERROR", f"url={url} status={e.code}")
        flash(f"HTTP 错误: {e.code}", "danger")
    except Exception as e:
        session["fetch_result"] = f"错误: {str(e)}"
        session["fetch_url"] = url
        audit_log("FETCH_URL_EXCEPTION", f"url={url} error={str(e)}")
        flash(f"请求失败: {str(e)}", "danger")

    return redirect(url_for("index"))


# ==========================================
# 修复后的密码修改接口（CSRF 保护 + XSS 防护）
# ==========================================
@app.route("/change-password", methods=["POST"])
@csrf.exempt
def change_password_no_auth():
    if "username" not in session:
        return redirect(url_for("login"))
    # 验证自定义 CSRF Token
    token = request.form.get("csrf_token", "")
    if not token or token != session.get("csrf_token"):
        audit_log("CSRF_PROTECTION", "Invalid CSRF token on /change-password")
        flash("请求已过期，请重试", "danger")
        return redirect(url_for("profile"))
    username = request.form.get("username", "").strip()
    new_password = request.form.get("new_password", "").strip()
    if not username or not new_password:
        flash("请填写完整信息", "danger")
        return redirect(url_for("profile"))
    user = users_db.get(username)
    if not user:
        flash("用户不存在", "danger")
        return redirect(url_for("profile"))
    # 验证密码强度
    if not re.match(r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[!@#$%^&*()_+=\-]).{8,64}$", new_password):
        flash("密码必须包含大小写字母、数字及特殊字符，长度8-64位", "danger")
        return redirect(url_for("profile"))
    # 直接更新密码，不验证原密码
    user["password"] = bcrypt.generate_password_hash(new_password).decode("utf-8")
    audit_log("PASSWORD_CHANGE", f"Target={username} Operator={session.get('username')}")
    safe_username = escape(username)
    flash(f"用户 {safe_username} 的密码已修改成功！", "success")
    return redirect(url_for("profile"))

# ==========================================
# 新增：个人中心页面
# ==========================================
@app.route("/profile")
def profile():
    if "username" not in session:
        return redirect(url_for("login"))
    # 确保 CSRF token 存在
    if "csrf_token" not in session:
        session["csrf_token"] = secrets.token_hex(32)
    return render_template("profile.html", username=session["username"], role=session.get("role", "user"))

# ==========================================
# 修复后的动态页面加载功能（路径遍历 + XSS 漏洞修复）
# ==========================================
@app.route("/page")
def dynamic_page():
    if "username" not in session:
        return redirect(url_for("login"))

    name = request.args.get("name", "")
    if not name:
        flash("Please provide a page name.", "warning")
        return redirect(url_for("index"))

    # 安全校验：只允许字母、数字、下划线、连字符（自动加 .html 后缀）
    if not re.match(r"^[a-zA-Z0-9_\-]+(\.[a-zA-Z0-9]+)?$", name):
        flash("非法的页面名称", "danger")
        return redirect(url_for("index"))

    # 自动尝试 .html 后缀
    filepath = os.path.join("pages", name)
    if not os.path.isfile(filepath):
        filepath_try = filepath + ".html"
        if os.path.isfile(filepath_try):
            filepath = filepath_try

    # 安全校验：确保文件路径在 pages 目录下
    real_path = os.path.realpath(filepath)
    pages_dir = os.path.realpath("pages")
    if not real_path.startswith(pages_dir):
        flash("非法的页面路径", "danger")
        return redirect(url_for("index"))

    page_content = None
    if os.path.isfile(real_path):
        with open(real_path, "r", encoding="utf-8") as f:
            page_content = f.read()

    # 对页面内容进行 HTML 转义，防止 XSS
    if page_content is not None:
        page_content = escape(page_content)
    else:
        page_content = "页面不存在"

    session["page_content"] = page_content
    audit_log("PAGE_VIEW", f"name={name}")
    return redirect(url_for("index"))


# ---------------------------
# Error Handlers
# ---------------------------
@app.errorhandler(404)
def not_found(e):
    return render_template("404.html"), 404

@app.errorhandler(500)
def server_error(e):
    return render_template("500.html"), 500

# ---------------------------
# Main
# ---------------------------
if __name__ == "__main__":
    os.makedirs(app.config["SESSION_FILE_DIR"], exist_ok=True)
    os.makedirs("pages", exist_ok=True)
    app.run(debug=True, host="0.0.0.0", port=5000)
