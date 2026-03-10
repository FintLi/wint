# 村圳 API

轻量级 Node API，用来给 `apps/cunzhen-miniapp` 提供远程数据源。

## 能力

- `GET /health`
- `POST /api/admin/login`
- `GET /api/listings`
- `GET /api/listings/all`
- `GET /api/listings/:id`
- `POST /api/leads`
- `POST /api/viewings`
- `POST /api/listings/intake`
- `GET /api/admin/summary`
- `POST /api/admin/listings/:id/status`
- `POST /api/admin/leads/:id/status`
- `POST /api/admin/viewings/:id/status`
- `POST /api/dev/reset`

## 启动

```bash
cd /Users/fint/Public/projects/wint/apps/cunzhen-api
npm start
```

默认端口：`3010`

可通过环境变量覆盖：

```bash
CUNZHEN_API_PORT=3011 npm start
CUNZHEN_ADMIN_PASSWORD=your-pass CUNZHEN_ADMIN_TOKEN=your-token npm start
```

## 数据

- 默认持久化文件：`/Users/fint/Public/projects/wint/apps/cunzhen-api/data/state.json`
- 如果文件不存在，会自动用小程序里的演示数据初始化

## 对接小程序

把小程序里的 `/Users/fint/Public/projects/wint/apps/cunzhen-miniapp/services/env.js` 改成：

```js
const DATA_SOURCE = 'remote'
const API_BASE_URL = 'http://127.0.0.1:3010'
```

然后在微信开发者工具里打开“不校验合法域名”进行本地联调。

## 默认管理员

- 密码：`cunzhen-admin`
- token：默认由登录接口返回
