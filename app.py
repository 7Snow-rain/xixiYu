import os
import re
import logging
import secrets
import subprocess
import platform
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


# ==========================================
# Ping 网络诊断功能（含命令注入漏洞，需修复）
# ==========================================
@app.route("/ping", methods=["GET", "POST"])
def ping():
    if "username" not in session:
        return redirect(url_for("login"))

    result = None
    if request.method == "POST":
        ip = request.form.get("ip", "").strip()
        # 安全修复：校验 IP 地址或域名格式，防止命令注入
        import re as _re
        # 检查是否为合法 IP 地址 (IPv4) 或合法域名
        ip_pattern = r"^(\d{1,3}\.){3}\d{1,3}$"
        domain_pattern = r"^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*\.[a-zA-Z]{2,}$"
        is_ip = bool(_re.match(ip_pattern, ip))
        is_domain = bool(_re.match(domain_pattern, ip))
        if not is_ip and not is_domain:
            result = "错误：请输入有效的 IP 地址或域名"
            audit_log("PING_INVALID_INPUT", f"ip={ip}")
        else:
            # 安全修复：使用列表参数方式执行命令，不使用 shell=True
            try:
                output = subprocess.check_output(["ping", "-c", "3", ip], timeout=30, stderr=subprocess.STDOUT)
                result = output.decode("utf-8", errors="replace")
            except subprocess.CalledProcessError as e:
                result = e.output.decode("utf-8", errors="replace")
            except subprocess.TimeoutExpired:
                result = "Ping 命令执行超时（30秒）"
            except Exception as e:
                result = f"执行出错: {str(e)}"
            audit_log("PING_EXEC", f"ip={ip}")

    return render_template("ping.html", result=result)


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
