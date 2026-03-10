# 村圳小程序 MVP

这是一个原生微信小程序 MVP，目标是把“深圳城中村真房源成交助手”的核心流程先跑通。

## 当前包含

- 租客端：首页、房源列表、房源详情、求租卡、预约看房
- 供给端：邀约式房源提报表
- 运营端：登录、漏斗概览、房源状态管理、线索状态管理、带看状态管理
- 本地业务规则：房源字段校验、72 小时失效、版本快照、线索优先级、预约状态
- 数据源切换：可在本地 `storage` 和远程 API 间切换

## 目录结构

- `app.json` / `app.js` / `app.wxss`：应用入口
- `data/mock.js`：演示数据
- `utils/`：常量、格式化、房源规则
- `services/store.js`：本地数据仓库与业务方法
- `services/repository.js`：本地 / 远程数据源适配层
- `services/env.js`：数据源和 API 地址配置
- `pages/`：页面实现

## 页面说明

- `pages/home/index`：核心价值、运营指标、精选房源
- `pages/listings/index`：按预算、片区、房型和电梯筛选房源
- `pages/listing-detail/index`：真房源详情、核验时间、避坑标签、预约入口
- `pages/demand-form/index`：租客求租卡
- `pages/viewing-booking/index`：预约看房
- `pages/supply-form/index`：合作方邀约式提报
- `pages/admin/index`：运营登录、房源 / 线索 / 带看状态管理

## 业务规则

- 房源缺少 `租金 / 水电规则 / 核验时间 / 视频链接` 任一字段时不可发布
- 房源距离最近核验超过 `72` 小时时自动转为失效
- 同一房源保留 `versions` 快照，前台只显示最新有效版本
- 求租线索按入住期限自动分层为 `A / B / C`
- 看房预约会把房源状态标记为 `已预约`
- 带看标记为 `爽约` 时，预约占用的房源会自动回到 `可发布`

## 如何导入微信开发者工具

1. 打开微信开发者工具
2. 选择“导入项目”
3. 项目目录指向 `/Users/fint/Public/projects/wint/apps/cunzhen-miniapp`
4. `appid` 可先使用测试号或你自己的小程序 `appid`
5. 进入后直接预览即可，数据会自动初始化到本地缓存

## 如何切远程 API

1. 先启动 `/Users/fint/Public/projects/wint/apps/cunzhen-api`
2. 打开 `/Users/fint/Public/projects/wint/apps/cunzhen-miniapp/services/env.js`
3. 把 `DATA_SOURCE` 从 `local` 改成 `remote`
4. 在微信开发者工具里关闭“合法域名校验”或配置开发域名

## 管理员登录

- 本地模式默认密码：`cunzhen-admin`
- 远程模式默认密码：`cunzhen-admin`
- 远程模式默认 token 由 API 管理，不需要手动填写

## 下一步建议

- 把远程 API 从 JSON 文件升级到 SQLite / Postgres
- 对接飞书 / 企业微信消息提醒
- 给运营端加结算管理和权限分级
- 给房源增加真正的媒体上传和审核记录
