# 附件检测系统

[![License](https://img.shields.io/github/license/liudonghua123/attachements_detect_system)](https://github.com/liudonghua123/attachements_detect_system/blob/main/LICENSE)
[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104.1-green)](https://fastapi.tiangolo.com/)
[![Vue.js](https://img.shields.io/badge/Vue.js-3.0%2B-brightgreen)](https://vuejs.org/)

一个强大的Web应用程序，用于扫描、处理和识别远程数据库中的附件中包含的敏感信息。该系统提供全面的工具，用于检测身份证、电话号码和其他敏感数据，支持模式匹配和AI驱动的分析功能。

## 目录

- [功能特点](#功能特点)
- [架构](#架构)
- [系统要求](#系统要求)
- [安装](#安装)
- [配置](#配置)
- [使用方法](#使用方法)
- [API文档](#api文档)
- [前端概述](#前端概述)
- [OCR配置](#ocr配置)
- [AI集成](#ai集成)
- [开发指南](#开发指南)
- [测试](#测试)
- [部署](#部署)
- [故障排除](#故障排除)
- [贡献](#贡献)
- [许可证](#许可证)
- [支持](#支持)
- [更新日志](#更新日志)

## 功能特点

- **数据库同步**: 从远程PostgreSQL数据库同步站点和附件数据
- **多格式处理**: 支持PDF、DOCX、XLSX、TXT、图像和存档文件（ZIP/RAR）
- **OCR功能**: 使用PaddleOCR或Tesseract从图像中提取高级文本
- **敏感数据检测**: 基于模式匹配的身份证号码和电话号码检测
- **AI分析**: 可选的OpenAI集成，用于高级内容分析
- **Web界面**: 基于Vue.js的前端，具有直观的仪表板和搜索功能
- **进度跟踪**: 批量操作期间通过WebSocket进行实时进度显示
- **数据分析**: 集成Chart.js用于数据可视化和统计
- **实时更新**: 长时间运行操作的WebSocket基础进度通知
- **高级搜索**: 具有多种过滤器和条件的综合搜索功能
- **响应式设计**: 针对各种屏幕尺寸的移动优先响应式布局

## 架构

### 核心组件

- `main.py`: 具有REST API端点的FastAPI应用程序
- `models.py`: 用于站点和附件的SQLAlchemy数据库模型
- `config.py`: 使用Pydantic Settings的应用程序配置
- `sync.py`: 远程站点和附件的数据库同步逻辑
- `download.py`: 文件下载、缓存和处理功能
- `utils.py`: 用于文本提取、OCR、模式匹配和AI分析的实用函数
- `static/index.html`: 使用Tailwind CSS样式的Vue.js前端

### 数据库结构

- **站点表**: 存储站点信息（所有者、账户、名称、域名、状态、别名）
- **附件表**: 存储附件元数据和分析结果（文本内容、OCR内容、LLM内容、敏感数据标志）

### 技术栈

- **后端**: Python, FastAPI, SQLAlchemy
- **数据库**: SQLite（默认），PostgreSQL, MySQL
- **前端**: Vue 3, Tailwind CSS, Chart.js
- **OCR**: PaddleOCR或Tesseract
- **AI**: OpenAI GPT-4集成
- **WebSocket**: 实时进度更新

## 系统要求

### 系统要求
- Python 3.8或更高版本
- 2GB+ RAM推荐
- 500MB+磁盘空间用于初始设置
- 互联网连接用于下载附件和可选AI服务

### 数据库要求
- PostgreSQL（可选，用于远程数据库连接）
- SQLite（默认本地数据库）- 无需额外安装
- MySQL（可选）- 需要PyMySQL

### 可选依赖
- PaddleOCR: paddlepaddle和paddleocr包
- Tesseract: pytesseract和tesseract-ocr
- AI功能: OpenAI API密钥

## 安装

### 快速设置

1. 克隆仓库：
   ```bash
   git clone https://github.com/liudonghua123/attachements_detect_system
   cd attachements_detect_system
   ```

2. 创建虚拟环境：
   ```bash
   python -m venv venv
   ```

3. 激活虚拟环境：
   ```bash
   # Windows
   venv\Scripts\activate
   
   # macOS/Linux
   source venv/bin/activate
   ```

4. 安装依赖：
   ```bash
   pip install -r requirements.txt
   ```

### OCR设置

如果使用PaddleOCR：

```bash
pip install paddlepaddle paddleocr
```

如果使用Tesseract:
- 安装Tesseract OCR引擎（系统级安装）
- Windows: 从 [tesseract-ocr.github.io](https://tesseract-ocr.github.io/) 下载
- macOS: `brew install tesseract`
- Ubuntu/Debian: `sudo apt-get install tesseract-ocr`

## 配置

1. 复制 `.env.example` 为 `.env`：
   ```bash
   cp .env.example .env
   ```

2. 更新 `.env` 文件中的数据库连接设置和API密钥：

   ```env
   # 远程数据库配置
   REMOTE_DB_HOST=your_remote_host
   REMOTE_DB_PORT=5432
   REMOTE_DB_NAME=your_remote_db_name
   REMOTE_DB_USER=your_username
   REMOTE_DB_PASSWORD=your_password

   # 本地数据库配置
   LOCAL_DB_TYPE=sqlite
   LOCAL_DB_PATH=./local_attachments.db

   # 缓存配置
   ATTACHMENT_CACHE_DIR=./attachments_cache

   # OCR配置
   OCR_ENGINE=paddle  # 选项: paddle, tesseract

   # OpenAI API配置
   OPENAI_API_KEY=your_openai_api_key
   MODEL=gpt-4
   OPENAI_BASE_URL=https://api.openai.com/v1

   # AI分析提示
   PROMPTS=分析以下内容并识别任何敏感信息，如个人身份号码、电话号码、地址或其他私人数据。如果检测到敏感数据，回应"SENSITIVE: [找到的敏感数据类型]"，否则回应"CLEAN: 未找到敏感数据。"

   # 附件基础URL
   ATTACHMENT_DEFAULT_BASE_URL=https://example.com
   ```

## 使用方法

### 启动应用程序

1. 启动应用程序：
   ```bash
   python main.py
   ```
   
   或直接使用uvicorn：
   ```bash
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

2. 在 `http://localhost:8000` 访问应用程序

3. API文档请访问 `http://localhost:8000/docs`

### 基本工作流程

1. **同步数据**: 使用同步功能从远程数据库检索站点和附件信息
2. **搜索**: 使用搜索界面根据各种条件查找附件
3. **处理/检测**: 处理单个附件或对整个站点运行批量检测
4. **查看结果**: 检查仪表板以获取统计信息和已识别的敏感数据
5. **导出**: 根据需要导出结果以进行进一步处理

## API文档

### 身份验证

大多数端点都是公开的。如果配置，某些功能可能需要API密钥。

### 核心端点

- `GET /api/sites` - 获取所有站点及其元数据
- `GET /api/attachments` - 获取附件（支持过滤选项）
- `POST /api/sync` - 完全同步站点和附件
- `POST /api/sync-sites` - 仅同步站点
- `POST /api/sync-attachments` - 仅同步附件
- `POST /api/process-attachment/{id}` - 处理单个附件
- `POST /api/process-attachment-ai/{id}` - 使用AI分析处理单个附件
- `POST /api/process-site/{id}` - 处理站点的所有附件
- `GET /api/stats` - 获取系统统计信息
- `POST /api/detect-site/{id}` - 检测站点所有附件中的敏感内容
- `GET /ws/{ws_id}` - 用于进度更新的WebSocket端点
- `GET /docs` - 交互式API文档（Swagger UI）
- `GET /redoc` - 替代API文档（ReDoc）

### 过滤参数

`/api/attachments` 端点支持以下查询参数：

| 参数 | 类型 | 说明 |
|------|------|------|
| `site_id` | 整数 | 按站点ID过滤 |
| `site_owner` | 字符串 | 按站点所有者过滤 |
| `site_state` | 整数 | 按站点状态过滤（0=活动，1=非活动，2=暂停） |
| `text_content_search` | 字符串 | 在提取的文本内容中搜索 |
| `ocr_content_search` | 字符串 | 在OCR内容中搜索 |
| `has_id_card` | 布尔值 | 按身份证检测过滤 |
| `has_phone` | 布尔值 | 按电话号码检测过滤 |
| `file_ext` | 字符串 | 按文件扩展名过滤 |
| `manual_verified_sensitive` | 布尔值 | 按手动验证状态过滤 |
| `skip` | 整数 | 分页偏移量（默认：0） |
| `limit` | 整数 | 分页限制（默认：100） |

### API使用示例

```bash
# 获取特定站点的所有附件
curl "http://localhost:8000/api/attachments?site_id=1&has_id_card=true"

# 处理单个附件
curl -X POST "http://localhost:8000/api/process-attachment/123"

# 获取系统统计信息
curl "http://localhost:8000/api/stats"

# 同步所有数据
curl -X POST "http://localhost:8000/api/sync"
```

## 前端概述

前端使用现代Web技术构建，提供最佳用户体验：

### 仪表板功能
- 带有可视化图表的系统统计信息
- 站点和附件计数
- 敏感数据检测指标
- 使用Chart.js进行数据可视化

### 搜索界面
- 高级过滤选项
- 实时搜索建议
- 分页控件
- 导出功能

### 处理功能
- 带进度跟踪的批量处理
- 单个附件处理
- AI驱动的分析选项
- 基于WebSocket的进度更新

### 响应式设计
- 移动优先方法
- 平板电脑和桌面优化
- 触摸友好界面
- 跨浏览器兼容性

## OCR配置

系统支持两种OCR引擎，各有不同优势：

### PaddleOCR（中文文本推荐）
- 对中文字符更准确
- 更好地处理复杂布局
- 对扫描文档具有更高准确性

### Tesseract（英文文本更好）
- 更通用且广泛支持
- 对英文和基于拉丁的文本更好
- 对清晰文档性能良好

要在OCR引擎之间切换，请在 `.env` 文件中将 `OCR_ENGINE` 设置为 `paddle` 或 `tesseract`。

## AI集成

系统支持使用OpenAI的GPT模型进行AI驱动的内容分析：

### 设置
1. 在 `.env` 文件中设置 `OPENAI_API_KEY`
2. 在设置中配置模型类型（默认：`gpt-4`）
3. 根据需要调整分析提示

### 功能
- 上下文感知敏感数据检测
- 复杂模式的识别
- 自然语言理解
- 高级隐私风险评估

### 端点
- `/api/process-attachment-ai/{id}` - 使用AI分析处理
- AI分析增强传统模式匹配

## 开发指南

### 代码规范
- 遵循PEP 8 Python代码标准
- 为函数参数和返回值使用类型提示
- 为复杂函数和类编写文档字符串
- 保持一致的命名约定

### 数据库模型
- 使用SQLAlchemy ORM进行数据库操作
- 在 `models.py` 中定义模型
- 为性能优化包含适当的索引
- 遵循命名约定以保持一致性

### API设计
- 使用Pydantic模型进行请求/响应验证
- 遵循RESTful API原则
- 实现适当的错误处理和HTTP异常代码
- 用示例记录API端点

### 测试
- 为实用函数编写单元测试
- 使用适当的测试用例测试API端点
- 验证OCR和文本提取功能
- 测试错误处理场景

### 安全性
- 验证和清理所有输入
- 使用参数化查询防止SQL注入
- 在需要时实现适当的身份验证
- 遵循安全最佳实践

## 测试

### 单元测试
使用pytest运行单元测试：

```bash
pytest tests/
```

### API测试
使用内置测试客户端测试API端点：

```bash
pytest tests/test_api.py
```

### 端到端测试
如果可用，运行端到端测试：

```bash
pytest tests/e2e/
```

## 部署

### 生产设置

对于生产部署，请考虑：

1. **使用WSGI服务器**:
   ```bash
   # 使用Gunicorn
   gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app
   
   # 使用Uvicorn和多个工作进程
   uvicorn main:app --workers 4 --host 0.0.0.0 --port 8000
   ```

2. **配置反向代理**（推荐Nginx）

3. **设置适当的日志记录**

4. **使用生产数据库**（推荐PostgreSQL）

### 环境配置

对于生产环境：

```env
# 生产设置
DEBUG=false
LOG_LEVEL=info
WORKERS=4
MAX_WORKERS=4
TIMEOUT=300

# 生产数据库设置
LOCAL_DB_TYPE=postgresql
LOCAL_DB_HOST=your_db_host
LOCAL_DB_PORT=5432
LOCAL_DB_NAME=your_db_name
LOCAL_DB_USER=your_db_user
LOCAL_DB_PASSWORD=your_db_password

# 安全设置
ALLOWED_HOSTS=yourdomain.com,subdomain.yourdomain.com
CORS_ALLOW_ORIGINS=https://yourdomain.com
```

## 故障排除

### 常见问题

1. **OCR不工作**
   - 检查是否安装OCR引擎: `pip list | grep ocr`
   - 验证Tesseract已在系统级别安装
   - 检查.env文件中的OCR_ENGINE设置

2. **数据库连接问题**
   - 验证.env中的数据库凭据
   - 检查数据库服务是否正在运行
   - 确保数据库访问的适当权限

3. **AI API错误**
   - 确认OpenAI API密钥有效
   - 检查网络连接
   - 验证未超过速率限制

4. **文件处理失败**
   - 检查附件缓存目录权限
   - 验证文件下载URL可访问
   - 确保有足够的磁盘空间

### 调试

通过在.env文件中设置 `DEBUG=true` 启用调试模式。这将提供更详细的错误消息，但绝不应在生产环境中使用。

### 日志记录

应用程序记录到标准输出。对于生产环境，配置日志记录以写入文件：

```python
import logging
logging.basicConfig(level=logging.INFO, filename='app.log')
```

## 贡献

我们欢迎贡献！这是您如何帮助的方法：

### 报告问题
- 使用GitHub问题跟踪器
- 提供详细的重现步骤
- 包含环境信息
- 在可能时建议解决方案

### 拉取请求
1. Fork仓库
2. 创建功能分支 (`git checkout -b feature/amazing-feature`)
3. 进行更改
4. 确保测试通过 (`pytest`)
5. 为新功能添加文档
6. 提交拉取请求

### 开发流程
- 遵循现有的代码风格
- 为新功能编写测试
- 根据需要更新文档
- 确保向后兼容性

## 许可证

本项目基于MIT许可证 - 详情请见 [LICENSE](LICENSE) 文件。

## 支持

### 获取帮助
- 检查 [GitHub Issues](https://github.com/liudonghua123/attachements_detect_system/issues) 寻找类似问题
- 为错误或功能请求开设新问题
- 报告问题时包含系统信息

### 联系方式
- 仓库: [https://github.com/liudonghua123/attachements_detect_system](https://github.com/liudonghua123/attachements_detect_system)
- 问题: [GitHub Issues](https://github.com/liudonghua123/attachements_detect_system/issues)

## 更新日志

### v1.0.0
- 初始版本
- 基本附件处理
- 敏感数据检测
- 基于Vue.js的Web界面

---

如需更多信息，请访问 [GitHub仓库](https://github.com/liudonghua123/attachements_detect_system) 或为问题和建议开设议题。