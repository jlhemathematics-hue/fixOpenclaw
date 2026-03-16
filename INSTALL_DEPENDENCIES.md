# 📦 FixOpenclaw 依赖安装指南

## 当前状态

✅ **核心代码**: 100% 完成
⏳ **依赖安装**: 进行中

---

## 🔧 快速安装 (推荐)

### 方法 1: 一键安装
```bash
cd /Users/hejohnny/Desktop/AI/fixOpenclaw
pip install -r requirements.txt
```

### 方法 2: 手动安装关键依赖
```bash
# 安装关键依赖
pip install pyyaml openai anthropic google-generativeai streamlit tiktoken python-dotenv

# 或使用 pip3
pip3 install pyyaml openai anthropic google-generativeai streamlit tiktoken python-dotenv
```

### 方法 3: 使用虚拟环境 (最佳实践)
```bash
cd /Users/hejohnny/Desktop/AI/fixOpenclaw

# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
source venv/bin/activate  # macOS/Linux
# 或
venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt
```

---

## 📋 依赖清单

### 核心依赖 (必需)
```
pyyaml>=6.0          # YAML 配置文件解析
python-dotenv>=1.0.0 # 环境变量管理
```

### LLM 提供商 (至少选择一个)
```
openai>=1.0.0                    # OpenAI (GPT-4, GPT-3.5)
anthropic>=0.18.0                # Anthropic (Claude)
google-generativeai>=0.3.0       # Google AI (Gemini)
tiktoken>=0.5.0                  # OpenAI token 计数
```

### Web 界面 (可选)
```
streamlit>=1.28.0    # Web 仪表板
```

### 其他依赖
```
pytest>=7.4.0        # 测试框架 (可选)
```

---

## ✅ 验证安装

### 检查已安装的包
```bash
pip list | grep -E "(pyyaml|openai|anthropic|google-generativeai|streamlit|tiktoken)"
```

### 预期输出
```
anthropic            0.84.0
google-generativeai  0.8.6
openai              2.28.0
PyYAML              6.0.1
streamlit           1.28.0
tiktoken            0.12.0
```

### 运行验证脚本
```bash
python verify.py
```

### 预期结果
```
✓ Python version OK
✓ All dependencies installed
✓ Configuration file found
✓ Environment setup complete
```

---

## 🐛 常见问题

### 问题 1: "No module named 'openai'"
**原因**: OpenAI 包未安装或安装到了错误的 Python 环境

**解决方案**:
```bash
# 检查 Python 版本
which python
python --version

# 安装到当前 Python
python -m pip install openai

# 或使用 pip3
pip3 install openai
```

### 问题 2: "No module named 'yaml'"
**原因**: PyYAML 包未安装

**解决方案**:
```bash
pip install pyyaml
# 或
pip3 install pyyaml
```

### 问题 3: 权限错误
**原因**: 没有权限安装到系统 Python

**解决方案 1 - 使用 --user**:
```bash
pip install --user -r requirements.txt
```

**解决方案 2 - 使用虚拟环境**:
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 问题 4: 多个 Python 版本
**原因**: 系统有多个 Python 版本

**解决方案**:
```bash
# 使用特定版本
python3.9 -m pip install -r requirements.txt
# 或
python3.10 -m pip install -r requirements.txt

# 检查 Python 路径
which python
which python3
```

---

## 🎯 安装后测试

### 1. 基础测试 (无需 API 密钥)
```bash
# 测试 Monitor Agent (不需要 LLM)
python -c "from src.agents.monitor_agent import MonitorAgent; print('✓ Monitor Agent OK')"

# 运行快速测试
python quick_test.py
```

### 2. 完整测试 (需要 API 密钥)
```bash
# 配置 API 密钥
cp .env.example .env
# 编辑 .env 添加密钥

# 运行完整测试
python main.py --mode once --log-file logs/openclaw.log
```

---

## 📊 安装进度检查

### 当前安装状态
运行以下命令检查:
```bash
python -c "
import sys
packages = ['yaml', 'openai', 'anthropic', 'google.generativeai', 'streamlit', 'tiktoken']
for pkg in packages:
    try:
        __import__(pkg)
        print(f'✓ {pkg}')
    except ImportError:
        print(f'✗ {pkg} - Not installed')
"
```

---

## 🚀 安装完成后

### 1. 验证安装
```bash
python verify.py
```

### 2. 运行测试
```bash
python quick_test.py
```

### 3. 配置系统
```bash
# 复制环境变量模板
cp .env.example .env

# 编辑配置
nano .env  # 或使用其他编辑器
```

### 4. 开始使用
```bash
# 测试示例数据
python main.py --mode once --log-file logs/openclaw.log

# 启动 Web 界面
python main.py --mode web

# 自主模式
python main.py --mode auto
```

---

## 💡 推荐的完整安装流程

```bash
# 1. 进入项目目录
cd /Users/hejohnny/Desktop/AI/fixOpenclaw

# 2. 创建虚拟环境 (推荐)
python -m venv venv
source venv/bin/activate

# 3. 升级 pip
pip install --upgrade pip

# 4. 安装所有依赖
pip install -r requirements.txt

# 5. 验证安装
python verify.py

# 6. 配置环境
cp .env.example .env
# 编辑 .env 添加 API 密钥

# 7. 运行测试
python quick_test.py

# 8. 测试系统
python main.py --mode once --log-file logs/openclaw.log

# 9. 启动使用
python main.py --mode web
```

---

## 🔍 调试安装问题

### 显示详细错误信息
```bash
pip install -r requirements.txt --verbose
```

### 检查 pip 版本
```bash
pip --version
python -m pip --version
```

### 检查 Python 环境
```bash
python -c "import sys; print(sys.executable); print(sys.version)"
```

### 清理并重新安装
```bash
# 卸载所有依赖
pip uninstall -y pyyaml openai anthropic google-generativeai streamlit tiktoken

# 重新安装
pip install -r requirements.txt
```

---

## 📞 获取帮助

### 如果安装仍有问题

1. **查看错误信息**: 仔细阅读错误消息
2. **检查 Python 版本**: 确保使用 Python 3.10+
3. **使用虚拟环境**: 避免系统 Python 权限问题
4. **查看文档**: README.md, QUICKSTART.md

### 手动安装每个包
如果批量安装失败,可以逐个安装:
```bash
pip install pyyaml
pip install python-dotenv
pip install openai
pip install anthropic
pip install google-generativeai
pip install streamlit
pip install tiktoken
pip install pytest
```

---

## ✅ 安装完成标志

当看到以下输出时,说明安装成功:

```bash
$ python verify.py
============================================================
FixOpenclaw Installation Verification
============================================================

✓ Python 3.13.12
✓ All core files present
✓ All dependencies installed
✓ Configuration file found

============================================================
✓ Installation verified successfully!
============================================================
```

---

## 🎉 下一步

安装完成后:

1. ✅ 配置 API 密钥 (`.env` 文件)
2. ✅ 运行测试 (`python quick_test.py`)
3. ✅ 查看文档 (`README.md`)
4. ✅ 开始使用系统!

---

*安装指南更新时间: 2024-03-16*
*FixOpenclaw v1.0*
