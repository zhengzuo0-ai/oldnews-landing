# OldNews Landing Page 部署指南

## 你需要准备的

1. 一个 GitHub 账号（免费）
2. 一个 Vercel 账号（免费，用 GitHub 登录）
3. 一个 Resend 账号（免费，resend.com）
4. oldnews.io 域名（去 Namecheap 或 Cloudflare 注册，约 $30-50/年）

## 步骤

### 第一步：注册 Resend，拿 API Key

1. 去 resend.com 注册
2. 左边菜单点 "API Keys"
3. 点 "Create API Key"，名字随便填比如 "oldnews-landing"
4. 复制 API Key（re_开头的那串），待会要用

### 第二步：Resend 里添加域名

1. Resend 左边菜单点 "Domains"
2. 点 "Add Domain"，输入 oldnews.io
3. 它会给你几条 DNS 记录（MX、TXT 等）
4. 去你的域名注册商（Namecheap/Cloudflare）添加这些 DNS 记录
5. 回到 Resend 点 "Verify"，等几分钟到几小时生效

### 第三步：把代码推到 GitHub

1. 在 GitHub 上新建一个 repo，名字叫 oldnews-landing
2. 把 deploy 文件夹里的所有文件推上去：

```bash
cd oldnews-deploy
git init
git add .
git commit -m "initial landing page"
git remote add origin https://github.com/你的用户名/oldnews-landing.git
git branch -M main
git push -u origin main
```

### 第四步：Vercel 部署

1. 去 vercel.com，用 GitHub 登录
2. 点 "Add New Project"
3. 选刚才的 oldnews-landing repo
4. Framework Preset 选 "Other"
5. 在 Environment Variables 里添加：
   - Name: RESEND_API_KEY
   - Value: 粘贴你的 Resend API Key
6. 点 Deploy

### 第五步：绑定域名

1. 部署成功后，进项目 Settings → Domains
2. 输入 oldnews.io
3. Vercel 会告诉你需要设置的 DNS 记录
4. 去域名注册商添加 A 记录或 CNAME 记录
5. 等几分钟生效，完事

## 文件结构

```
oldnews-deploy/
├── public/
│   ├── index.html          ← 英文版（默认）
│   └── cn.html             ← 中文版
├── api/
│   └── subscribe.js        ← Resend 接口（Vercel Serverless Function）
├── vercel.json             ← 路由配置
└── README.md               ← 这个文件
```

## 上线后

- 英文版：oldnews.io
- 中文版：oldnews.io/cn
- 表单提交后邮箱会存到 Resend 的 Contacts 里
- 在 Resend 后台可以看到所有订阅者
