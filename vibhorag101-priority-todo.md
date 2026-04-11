# vibhorag101 项目改造优先级 Todo List

## 文档说明

- 基于文件：`vibhorag101-gap-analysis.md`
- 目标：把参考项目 `vibhorag101/ECommerce-Grocery-Store` 改造成更符合 COMP7640 课程要求的版本
- 排序原则：
  - 先补“题目明确要求但当前缺失”的核心功能
  - 再补“影响系统建模是否合理”的数据库结构问题
  - 最后再处理“展示效果、规范贴合度、技术清理”

## P0：必须最先完成

这些内容直接决定项目是否满足题目核心要求。

- [ ] 重构订单模型，支持“一个订单包含多个商品及其数量”
  - 原因：当前数据库没有把订单项数量规范存库，这是后续所有订单功能的基础
  - 目标：增加 `order_item` 或等价设计，至少记录 `order_id`、`product_id`、`vendor_id`、`quantity`、`unit_price`

- [ ] 支持“单个订单跨多个 vendor”
  - 原因：这是题目明确要求，当前项目没有清晰支持
  - 目标：用户一个订单里可以购买多个 vendor 的商品，并且数据库里能明确区分每个商品来自哪个 vendor

- [ ] 增加 `transaction` 实体设计
  - 原因：题目明确要求 transaction，当前项目没有独立建模
  - 目标：至少记录 `transaction_id`、`order_id`、`customer_id`、`vendor_id`、`amount`、`payment_method`、`transaction_time`

- [ ] 给订单增加 `status` 字段和状态流转
  - 原因：没有订单状态，就无法支持“发货前修改 / 取消订单”
  - 目标：至少支持 `placed`、`processing`、`shipped`、`cancelled`

- [ ] 实现“发货前修改订单 / 取消订单”
  - 原因：这是题目明确要求的功能
  - 目标：
    - 用户可以删除订单中的某个商品
    - 用户可以在 `shipped` 前取消整个订单

- [ ] 给商品增加 `stock quantity`
  - 原因：题目要求 product 必须有库存数量
  - 目标：product 或 vendor-product 库存表中能正确记录并更新库存

- [ ] 给商品增加 `tags` 设计
  - 原因：题目要求每个商品最多 3 个 tags
  - 目标：选择以下两种方案之一：
    - `product_tag` 关系表
    - `tag1/tag2/tag3` 三列固定字段

- [ ] 实现按 `tag` 或商品名部分匹配的搜索
  - 原因：这是题目明确要求且当前完全缺失
  - 目标：搜索输入后，返回名称匹配或 tag 匹配的商品

## P1：高优先级，P0 完成后立刻做

这些内容决定系统是否真正像题目要求的“multi-vendor marketplace”。

- [ ] 重构 `seller` 为更明确的 `vendor profile`
  - 原因：当前 seller 只有基本信息，不够贴合题目里的 vendor 描述
  - 目标：vendor 至少补齐：
    - vendor ID
    - business name
    - geographical presence
    - average rating
    - inventory summary

- [ ] 让前台界面明确展示 vendor 信息
  - 原因：当前用户视角更像单店 grocery store，不像 marketplace
  - 目标：
    - 商品卡片显示 vendor 名称
    - 商品详情页显示 vendor 信息
    - 支持按 vendor 浏览商品

- [ ] 调整系统叙事，从 grocery store 改成 marketplace
  - 原因：第 9 点指出当前项目包装不符合题目表达
  - 目标：
    - README 改写
    - 首页文案改写
    - 报告和演示统一改成“multi-vendor marketplace”叙事

- [ ] 增加一个可演示的个性化功能
  - 原因：题目提到 `personalized user experiences`
  - 建议最低可行方案：
    - 根据历史购买 category / tag 推荐商品
    - 或展示“你可能还想买”
    - 或按地区优先展示本地 vendor

## P2：中优先级，属于结构优化

这些内容不是最先卡住作业的部分，但会影响实现质量和后续扩展。

- [ ] 去掉购物车相关的全局变量，改成数据库驱动
  - 原因：当前 `cart_id`、`total_val`、`total_count`、`customer_cart_list` 都在 Python 全局变量里，不适合多用户
  - 目标：把购物车状态完整存到数据库

- [ ] 重构 cart 逻辑
  - 原因：当前 cart 和 order 的衔接过于依赖内存状态
  - 目标：
    - cart_item 单独建模
    - 数量、价格、vendor 信息都落库

- [ ] 优化登录和查询方式
  - 原因：当前很多登录逻辑是“查整张表后在 Python 中循环匹配”
  - 目标：改成带条件的 SQL 查询

- [ ] 改善密码存储方式
  - 原因：当前看起来是明文密码
  - 目标：至少改成哈希存储

## P3：低优先级，属于规范贴合和收尾工作

这些内容重要，但优先级低于核心功能补齐。

- [ ] 决定是否把 `flask_mysqldb` 切换为 `PyMySQL`
  - 原因：PDF 更明确提到了 `PyMySQL`
  - 当前建议：
    - 如果时间紧，可先不改
    - 如果时间允许，后期切换会更贴题

- [ ] 清理并统一数据库访问层
  - 原因：如果后期改成 `PyMySQL`，最好顺便统一数据库操作方式
  - 目标：让连接、查询、事务提交逻辑更清晰

- [ ] 更新 README
  - 原因：最后提交需要清楚说明如何运行项目
  - 目标：写清环境、数据库恢复、运行命令、测试账号、功能说明

- [ ] 更新 ER 图、关系模式图、SQL 脚本
  - 原因：只改代码不改文档，最后展示会前后不一致
  - 目标：
    - 新 ER 图
    - 新关系模式
    - 新建表 SQL
    - 新 sample data

- [ ] 整理最终报告和 presentation 逻辑
  - 原因：这门课评分非常看重讲解清晰度
  - 目标：确保报告、ER 图、demo、README、代码实现一致

## 推荐执行顺序

建议你们按下面顺序推进：

1. 先改数据库 schema
   - `vendor`
   - `product`
   - `orders`
   - `order_item`
   - `transaction`
   - `tags`

2. 再改核心业务流程
   - 搜索
   - 下单
   - 跨 vendor 订单
   - 修改 / 取消订单
   - 库存更新

3. 再改 marketplace 表达与个性化
   - vendor 展示
   - 推荐逻辑
   - 首页和 README 文案

4. 最后做技术清理和交付材料
   - `PyMySQL` 决策
   - README
   - ER 图
   - 报告
   - 演示

## 当前最值得先开工的三个任务

- [x] 任务 1：设计新的数据库 schema 草稿
- [x] 任务 2：设计 `order_item + transaction + order status`
- [ ] 任务 3：设计 `product tags + search`

## 当前已确认的第一阶段范围

这一阶段已经确定采用“重建一套更干净的新表结构，再逐步迁移逻辑”的路线，不走在旧表上小修小补的方案。

### 第一阶段目标

- [x] 以题目要求为准，重建核心 schema
- [ ] 新 schema 主体命名统一使用 `vendor`
- [x] 同步规划需要迁移的关键 Flask 路由
- [ ] 暂时不优先处理页面美化
- [ ] 暂时不优先处理 `PyMySQL` 切换

### 第一阶段建议的新核心表

- [x] `vendor`
- [x] `customer`
- [x] `product`
- [x] `product_tag`
- [x] `orders`
- [x] `order_item`
- [x] `transaction`

### 第一阶段要解决的关键关系

- [x] 一个 `vendor` 对应多个 `product`
- [x] 一个 `product` 最多 3 个 `tag`
- [x] 一个 `customer` 对应多个 `orders`
- [x] 一个 `order` 对应多个 `order_item`
- [x] 一个 `order` 可以跨多个 `vendor`
- [x] 一个跨 vendor 的 `order` 可以拆成多条 `transaction`

### 第一阶段要规划的关键路由

- [x] 商品浏览路由
- [x] 商品搜索路由
- [ ] 加入购物车 / 准备下单路由
- [x] 创建订单路由
- [x] 修改订单路由
- [x] 取消订单路由
- [x] vendor 商品管理路由

### 第一阶段完成标准

- [x] 能画出新的 ER 图核心结构
- [x] 能明确写出核心表字段和主外键关系
- [x] 能说明旧路由哪些保留、哪些重写、哪些废弃
- [x] 能把后续开发重点收敛到 `order_item / transaction / tags / search / order status`

### 第一阶段已产出文件

- [x] `vibhorag101-stage1-schema-design.md`

## 一句话结论

如果你们想最快把这个项目改造成符合题目的版本，最先不要碰页面美化，也不要先纠结 `PyMySQL`，而是优先把 `订单结构、跨 vendor、transaction、库存、tags、搜索、订单修改/取消` 这几个数据库和业务核心补齐。
