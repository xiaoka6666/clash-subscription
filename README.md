# GitHub Actions 工作流 - Clash 订阅转换

## 项目结构

```
.
├── .github/
│   └── workflows/
│       └── clash-subscription.yml    # GitHub Actions 工作流
├── scripts/
│   ├── parse_subscription.py         # 订阅解析脚本
│   └── generate_clash_config.py      # Clash 配置生成脚本
├── templates/
│   └── clash_template.yaml           # Clash 配置模板
└── output/                           # 输出目录（自动生成）
    ├── nodes.json                    # 解析后的节点数据
    ├── clash.yaml                    # Clash 配置文件
    ├── clash_meta.yaml               # Clash Meta 配置文件
    └── subscription.txt              # Base64 编码的订阅链接
```

## 使用方法

### 1. 创建 GitHub 仓库

将此项目推送到你的 GitHub 仓库。

### 2. 配置订阅密钥

在仓库中配置你的订阅链接：

1. 进入仓库 **Settings** → **Secrets and variables** → **Actions**
2. 点击 **New repository secret**
3. Name: `SUBSCRIPTION_URL`
4. Value: 你的订阅链接地址

### 3. 启用 GitHub Pages

1. 进入仓库 **Settings** → **Pages**
2. Source 选择 **Deploy from a branch**
3. Branch 选择 **gh-pages**，目录选择 **/(root)**
4. 点击 **Save**

### 4. 运行工作流

工作流支持三种触发方式：

- **定时触发**: 每 6 小时自动运行一次
- **手动触发**: 在 Actions 页面点击 "Run workflow"
- **推送触发**: 推送代码到 main/master 分支时运行

### 5. 获取订阅链接

工作流运行完成后，你的订阅地址为：

```
https://你的用户名.github.io/仓库名/clash.yaml
```

或 Base64 编码版本：

```
https://你的用户名.github.io/仓库名/subscription.txt
```

## 支持的协议

- VMess
- VLESS
- Shadowsocks (SS)
- Trojan

## 自定义配置

### 修改更新频率

编辑 `.github/workflows/clash-subscription.yml` 中的 cron 表达式：

```yaml
schedule:
  - cron: '0 */6 * * *'  # 每 6 小时运行一次
```

### 自定义代理组和规则

编辑 `templates/clash_template.yaml` 文件来自定义代理组和分流规则。

## 注意事项

1. 请确保你的订阅链接有效且可访问
2. GitHub Actions 有运行时间限制，大量节点可能需要优化
3. 订阅内容请合法合规使用
